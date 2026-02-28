"""Manifest-first registry with schema enforcement and hot update support."""
from __future__ import annotations

import copy
import json
import os
import subprocess
import threading
from collections.abc import Callable
from pathlib import Path
from typing import Any

import jsonschema  # type: ignore[import-untyped]

_SCHEMA_PATH = Path(__file__).resolve().parent.parent / "schemas" / "agent-manifest.v1.json"


class ManifestRegistry:
    def __init__(self, schema_path: Path = _SCHEMA_PATH) -> None:
        self._schema_path = schema_path
        self._schema = json.loads(schema_path.read_text(encoding="utf-8-sig"))
        self._validator = jsonschema.Draft7Validator(self._schema)
        self._lock = threading.RLock()
        self._by_id: dict[str, dict[str, Any]] = {}
        self._by_capability: dict[str, list[str]] = {}
        self._source_files: dict[str, str] = {}
        self._listeners: list[Callable[[str, dict[str, Any]], None]] = []

    def validate_manifest(self, manifest: dict[str, Any], source: str = "<memory>") -> list[str]:
        errors = sorted(self._validator.iter_errors(manifest), key=lambda err: err.json_path)
        return [f"{source}: [{error.json_path}] {error.message}" for error in errors]

    def load_all(
        self,
        path: str = "config/manifests/",
        reject_duplicates: bool = True,
    ) -> list[dict[str, Any]]:
        manifests_path = Path(path)
        files = sorted(manifests_path.glob("*.json"))
        temp_by_id: dict[str, dict[str, Any]] = {}
        temp_source: dict[str, str] = {}
        duplicates: dict[str, list[str]] = {}

        for file_path in files:
            data = json.loads(file_path.read_text(encoding="utf-8-sig"))
            errors = self.validate_manifest(data, source=file_path.name)
            if errors:
                raise ValueError("Manifest validation failed:\n" + "\n".join(errors))

            manifest_id = str(data["id"])
            if manifest_id in temp_by_id:
                duplicates.setdefault(
                    manifest_id,
                    [temp_source[manifest_id]],
                ).append(file_path.name)
                continue

            temp_by_id[manifest_id] = data
            temp_source[manifest_id] = file_path.name

        if reject_duplicates and duplicates:
            details = []
            for manifest_id in sorted(duplicates):
                details.append(f"{manifest_id}: {', '.join(sorted(duplicates[manifest_id]))}")
            raise ValueError("Duplicate manifest id detected:\n" + "\n".join(details))

        with self._lock:
            self._by_id = {mid: copy.deepcopy(temp_by_id[mid]) for mid in sorted(temp_by_id)}
            self._source_files = dict(temp_source)
            self._reindex_locked()
            return [copy.deepcopy(self._by_id[mid]) for mid in sorted(self._by_id)]

    def add_listener(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        with self._lock:
            self._listeners.append(callback)

    def remove_listener(self, callback: Callable[[str, dict[str, Any]], None]) -> None:
        with self._lock:
            if callback in self._listeners:
                self._listeners.remove(callback)

    def get(self, manifest_id: str) -> dict[str, Any] | None:
        with self._lock:
            if manifest_id in self._by_id:
                return copy.deepcopy(self._by_id[manifest_id])

            if "@" not in manifest_id:
                candidates = [mid for mid in self._by_id if mid.startswith(f"{manifest_id}@")]
                if candidates:
                    selected = sorted(candidates)[-1]
                    return copy.deepcopy(self._by_id[selected])

                for mid, manifest in self._by_id.items():
                    alias = str(manifest.get("extensions", {}).get("legacy_alias", "")).strip()
                    if alias == manifest_id:
                        return copy.deepcopy(self._by_id[mid])

            return None

    def query(self, capability: str) -> list[dict[str, Any]]:
        with self._lock:
            ids = list(self._by_capability.get(capability, []))
            return [copy.deepcopy(self._by_id[mid]) for mid in ids]

    def all(self) -> list[dict[str, Any]]:
        with self._lock:
            return [copy.deepcopy(self._by_id[mid]) for mid in sorted(self._by_id)]

    def remove(self, manifest_id: str) -> bool:
        with self._lock:
            if manifest_id not in self._by_id:
                return False
            del self._by_id[manifest_id]
            self._source_files.pop(manifest_id, None)
            self._reindex_locked()
            return True

    def clear(self) -> None:
        with self._lock:
            self._by_id.clear()
            self._by_capability.clear()
            self._source_files.clear()

    def _reindex_locked(self) -> None:
        by_capability: dict[str, list[str]] = {}
        for manifest_id in sorted(self._by_id):
            for capability in sorted(self._by_id[manifest_id].get("capabilities", [])):
                by_capability.setdefault(capability, []).append(manifest_id)
        self._by_capability = by_capability

    def _current_sha(self) -> str | None:
        env_sha = os.getenv("GITHUB_SHA")
        if env_sha:
            return env_sha
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout.strip()
        except Exception:
            return None

    def _ci_gate_allows(self, status_path: str) -> bool:
        path = Path(status_path)
        if not path.exists():
            return False
        try:
            payload = json.loads(path.read_text(encoding="utf-8-sig"))
        except Exception:
            return False

        status = str(payload.get("status", "")).lower().strip()
        artifact_sha = str(payload.get("sha", "")).strip()
        current_sha = self._current_sha()

        if status != "pass":
            return False
        return not (artifact_sha and current_sha and artifact_sha != current_sha)

    def apply_update(
        self,
        manifest_id: str,
        manifest: dict[str, Any],
        actor: str = "watcher",
        ci_status_path: str = "artifacts/manifest-validation-status.json",
        enforce_ci_gate: bool = True,
    ) -> tuple[bool, str]:
        if str(manifest.get("id", "")) != manifest_id:
            return False, "manifest_id mismatch"

        errors = self.validate_manifest(manifest, source=f"update:{manifest_id}")
        if errors:
            return False, "validation_failed: " + "; ".join(errors)

        if enforce_ci_gate and not self._ci_gate_allows(ci_status_path):
            return False, "ci_gate_blocked"

        with self._lock:
            self._by_id[manifest_id] = copy.deepcopy(manifest)
            self._reindex_locked()
            listeners = list(self._listeners)

        for callback in listeners:
            try:
                callback(actor, copy.deepcopy(manifest))
            except Exception:
                continue

        return True, "applied"

    def handle_manifest_updated(
        self,
        manifest_id: str,
        manifest: dict[str, Any],
        actor: str = "watcher",
        ci_status_path: str = "artifacts/manifest-validation-status.json",
    ) -> tuple[bool, str]:
        return self.apply_update(
            manifest_id=manifest_id,
            manifest=manifest,
            actor=actor,
            ci_status_path=ci_status_path,
            enforce_ci_gate=True,
        )


registry = ManifestRegistry()
