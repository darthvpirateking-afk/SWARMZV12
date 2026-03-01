from __future__ import annotations

import ast
from dataclasses import dataclass, field
from typing import Any

from core.agent_manifest import AgentManifest, validate_dict
from core.observability import AgentEvent, ObservabilityEmitter
from core.spawn_context import SpawnContext
from plugins.helper1_internal_life_stubs import (
    build_module_stub_registry,
    get_module_stub,
)

emitter = ObservabilityEmitter(success_sample_rate=1.0)

_ALLOWED_COMMANDS = {"echo", "validate_manifest", "validate_proposal"}


@dataclass
class ValidationReport:
    valid: bool = True
    risk_score: float = 0.0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "valid": self.valid,
            "risk_score": round(max(0.0, min(1.0, self.risk_score)), 3),
            "errors": list(self.errors),
            "warnings": list(self.warnings),
            "suggestions": list(self.suggestions),
            "summary": self.summary,
        }


class Helper1Plugin:
    def __init__(self) -> None:
        self.manifest: AgentManifest | None = None
        self._active = False
        self._trace_id = ""
        self._session_id: str | None = None

    async def on_init(self, manifest: AgentManifest, context: SpawnContext) -> None:
        self.manifest = manifest
        self._trace_id = context.trace_id
        self._session_id = context.session_id
        emitter.emit(
            AgentEvent(
                agent_id=manifest.id,
                trace_id=self._trace_id,
                session_id=self._session_id,
                event="plugin.helper1.init",
                decision="initialized",
                inputs_hash="",
                outcome="success",
                payload={"version": "0.2.0"},
            )
        )

    async def on_activate(self, context: SpawnContext) -> None:
        if self._active:
            return
        self._active = True
        emitter.emit(
            AgentEvent(
                agent_id=self.manifest.id if self.manifest else "helper1@0.2.0",
                trace_id=self._trace_id,
                session_id=context.session_id,
                event="plugin.helper1.activate",
                decision="activated",
                inputs_hash="",
                outcome="success",
            )
        )

    async def run(self, command: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if not self._active:
            raise RuntimeError("Helper1 not activated")

        payload = payload or {}
        command_name = str(command or "echo").strip()

        if command_name == "echo":
            result = {"echo": payload, "source": "helper1"}
            outcome = "success"
        elif command_name == "validate_manifest":
            result = self._validate_manifest(payload.get("manifest"))
            outcome = "success" if bool(result.get("valid")) else "failure"
        elif command_name == "validate_proposal":
            result = self._validate_proposal(payload)
            outcome = "success" if bool(result.get("valid")) else "failure"
        else:
            result = {"valid": False, "error": "unknown_command", "allowed": sorted(_ALLOWED_COMMANDS)}
            outcome = "failure"

        emitter.emit(
            AgentEvent(
                agent_id=self.manifest.id if self.manifest else "helper1@0.2.0",
                trace_id=self._trace_id,
                session_id=self._session_id,
                event="plugin.helper1.run",
                decision=command_name,
                inputs_hash="",
                outcome=outcome,
                payload={
                    "command": command_name,
                    "risk_score": result.get("risk_score") if isinstance(result, dict) else None,
                    "error_count": len(result.get("errors", [])) if isinstance(result, dict) else 0,
                },
            )
        )
        return result

    async def on_deactivate(self, context: SpawnContext) -> None:
        if not self._active:
            return
        self._active = False
        emitter.emit(
            AgentEvent(
                agent_id=self.manifest.id if self.manifest else "helper1@0.2.0",
                trace_id=self._trace_id,
                session_id=context.session_id,
                event="plugin.helper1.deactivate",
                decision="deactivated",
                inputs_hash="",
                outcome="success",
            )
        )

    def unload(self) -> None:
        return None

    def _validate_manifest(self, manifest_data: Any) -> dict[str, Any]:
        report = ValidationReport()

        if not isinstance(manifest_data, dict):
            report.valid = False
            report.risk_score = 1.0
            report.errors.append("payload.manifest must be an object")
            report.summary = "Manifest validation failed: payload.manifest missing or invalid."
            return report.to_dict()

        schema_errors = validate_dict(manifest_data)
        if schema_errors:
            report.valid = False
            report.risk_score = max(report.risk_score, 0.9)
            report.errors.extend(schema_errors)

        report = self._check_manifest_invariants(manifest_data, report)
        manifest_id = str(manifest_data.get("id", "<unknown>"))
        report.summary = f"Manifest {manifest_id} validation completed with {len(report.errors)} error(s)."
        if report.errors:
            report.valid = False
        return report.to_dict()

    def _validate_proposal(self, payload: dict[str, Any]) -> dict[str, Any]:
        report = ValidationReport()

        nested_manifest = payload.get("manifest")
        if nested_manifest is not None:
            manifest_report = self._validate_manifest(nested_manifest)
            report.errors.extend(manifest_report.get("errors", []))
            report.warnings.extend(manifest_report.get("warnings", []))
            report.suggestions.extend(manifest_report.get("suggestions", []))
            report.risk_score = max(report.risk_score, float(manifest_report.get("risk_score", 0.0)))

        code_snippet = payload.get("code_snippet")
        if isinstance(code_snippet, str):
            report = self._check_code_safety(code_snippet, report)

        approved_for_ritual = report.risk_score < 0.3 and len(report.errors) == 0
        report.valid = len(report.errors) == 0
        report.summary = (
            f"Proposal validation completed with {len(report.errors)} error(s), "
            f"{len(report.warnings)} warning(s)."
        )
        data = report.to_dict()
        data["approved_for_ritual"] = approved_for_ritual
        return data

    def _check_manifest_invariants(
        self, manifest_data: dict[str, Any], report: ValidationReport
    ) -> ValidationReport:
        mutation_intent = str(manifest_data.get("mutation_intent", "")).strip().lower()
        if mutation_intent and mutation_intent != "additive_only":
            report.warnings.append("Mutation intent is not additive_only.")
            report.risk_score = max(report.risk_score, 0.35)

        boundaries = manifest_data.get("boundaries")
        if isinstance(boundaries, dict):
            if bool(boundaries.get("touches_core")):
                report.warnings.append("Proposal indicates core-boundary mutation risk.")
                report.risk_score = max(report.risk_score, 0.5)

        safety = manifest_data.get("safety_state")
        if isinstance(safety, dict) and str(safety.get("life_state", "")).lower() == "death":
            report.warnings.append("Death-state safety marker detected; operator review required.")
            report.risk_score = max(report.risk_score, 0.7)

        ext = manifest_data.get("extensions")
        if isinstance(ext, dict):
            pantheon = ext.get("pantheon")
            quantum = ext.get("quantum")
            cosmic = ext.get("cosmic")
            if isinstance(pantheon, dict) and not str(pantheon.get("tradition", "")).strip():
                report.errors.append("extensions.pantheon.tradition is required when pantheon extension is set.")
                report.risk_score = max(report.risk_score, 0.7)
            if isinstance(quantum, dict) and not isinstance(quantum.get("eligible"), bool):
                report.errors.append("extensions.quantum.eligible must be boolean when quantum extension is set.")
                report.risk_score = max(report.risk_score, 0.7)
            if isinstance(cosmic, dict) and not isinstance(cosmic.get("enabled"), bool):
                report.warnings.append("extensions.cosmic.enabled should be boolean when cosmic extension is set.")
                report.risk_score = max(report.risk_score, 0.4)

        return report

    def _check_code_safety(self, code_snippet: str, report: ValidationReport) -> ValidationReport:
        denylist_tokens = (
            "import os",
            "from os",
            "import subprocess",
            "from subprocess",
            "eval(",
            "exec(",
            "__import__(",
        )
        lowered = code_snippet.lower()
        for token in denylist_tokens:
            if token in lowered:
                report.errors.append(f"Dangerous token detected in code_snippet: '{token}'")
                report.risk_score = max(report.risk_score, 0.8)

        try:
            ast.parse(code_snippet)
        except SyntaxError as exc:
            report.errors.append(f"code_snippet syntax error: {exc.msg}")
            report.risk_score = max(report.risk_score, 0.9)
            return report

        return report


def _legacy_stub_actions(task: dict[str, Any]) -> dict[str, Any] | None:
    action = str(task.get("action", "")).strip().lower()
    if action == "list_module_stubs":
        return {
            "result": "helper1 module stubs listed",
            "module_stub_ids": sorted(build_module_stub_registry().keys()),
            "symbolic_only": True,
        }

    module_id = str(task.get("module_stub_id", "")).strip()
    if action == "get_module_stub" and module_id:
        return {
            "result": "helper1 module stub fetched",
            "module_stub": get_module_stub(module_id),
            "symbolic_only": True,
        }

    return None


def run(task: dict[str, Any]) -> dict[str, Any]:
    """
    Legacy sync wrapper for older callers.
    Supports:
    - query-only mode
    - command/payload mode
    - existing stub actions
    """
    legacy = _legacy_stub_actions(task)
    if legacy is not None:
        return legacy

    command = str(task.get("command", "")).strip() or "echo"
    payload = task.get("payload")
    if not isinstance(payload, dict):
        payload = {}
    query = str(task.get("query", ""))
    if command == "echo" and query:
        payload = {**payload, "query": query}

    plugin = Helper1Plugin()
    manifest_data = {
        "id": "helper1@0.2.0",
        "version": "0.2.0",
        "capabilities": ["data.read", "agent.introspect"],
        "limits": {"max_depth": 1, "max_children": 4},
    }
    manifest = AgentManifest.from_dict(manifest_data)
    context = SpawnContext.root_from_manifest(manifest)

    import asyncio

    async def _exec() -> dict[str, Any]:
        await plugin.on_init(manifest, context)
        await plugin.on_activate(context)
        result = await plugin.run(command, payload)
        await plugin.on_deactivate(context)
        return result

    return asyncio.run(_exec())
