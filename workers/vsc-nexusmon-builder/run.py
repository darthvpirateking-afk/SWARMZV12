from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _normalize_requirements(raw: Any) -> List[str]:
    if isinstance(raw, str):
        value = raw.strip()
        return [value] if value else []
    if isinstance(raw, list):
        normalized = []
        for item in raw:
            text = str(item).strip()
            if text:
                normalized.append(text)
        return normalized
    raise ValueError("requirements must be a string or list of strings")


def validate(input: Dict[str, Any]) -> None:
    if not isinstance(input, dict):
        raise ValueError("input must be an object")
    module_name = str(input.get("module_name", "")).strip()
    if not module_name:
        raise ValueError("module_name is required")
    if module_name.startswith(".") or "/" in module_name or "\\" in module_name:
        raise ValueError("module_name must be a simple folder name")
    _normalize_requirements(input.get("requirements", []))


def run(input: Dict[str, Any]) -> Dict[str, Any]:
    validate(input)
    module_name = str(input["module_name"]).strip()
    requirements = _normalize_requirements(input.get("requirements", []))

    generated_files = [
        f"plugins/{module_name}/manifest.json",
        f"plugins/{module_name}/index.js",
        f"plugins/{module_name}/README.md",
    ]
    return {
        "status": "planned",
        "summary": f"Prepared scaffold plan for plugin '{module_name}'.",
        "generated_files": generated_files,
        "requirements": requirements,
        "timestamp": _utc_now_iso(),
    }


def emit_artifacts(output: Dict[str, Any], artifact_dir: Path) -> Dict[str, Any]:
    artifact_dir.mkdir(parents=True, exist_ok=True)
    result_path = artifact_dir / "result.json"
    result_path.write_text(json.dumps(output, indent=2), encoding="utf-8")

    summary_path = artifact_dir / "artifact_summary.txt"
    summary_lines = [
        f"status: {output.get('status', '')}",
        f"summary: {output.get('summary', '')}",
        f"timestamp: {output.get('timestamp', '')}",
    ]
    summary_path.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")

    return {
        "generated_files": [
            str(result_path).replace("\\", "/"),
            str(summary_path).replace("\\", "/"),
        ]
    }
