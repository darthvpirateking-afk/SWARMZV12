from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .context import RuntimeContext, build_context
from .loader import get_worker_functions, load_worker_metadata, load_worker_module


def _artifact_timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")


def _relative_or_abs(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(Path.cwd().resolve())).replace("\\", "/")
    except Exception:
        return str(path.resolve()).replace("\\", "/")


def execute_worker(
    worker_dir: Path | str,
    input_payload: Dict[str, Any],
    context: RuntimeContext | None = None,
) -> Dict[str, Any]:
    worker_path = Path(worker_dir)
    runtime_context = context or build_context(Path.cwd())

    metadata = load_worker_metadata(worker_path)
    module = load_worker_module(worker_path)
    functions = get_worker_functions(module)

    validate_fn = functions["validate"]
    run_fn = functions["run"]
    emit_fn = functions.get("emit_artifacts")

    validate_fn(input_payload)
    output = run_fn(input_payload)
    if not isinstance(output, dict):
        raise TypeError("worker run() must return a dict")

    timestamp = _artifact_timestamp()
    artifact_dir = worker_path / "artifacts" / timestamp
    artifact_dir.mkdir(parents=True, exist_ok=True)

    generated_files: list[str] = []
    if emit_fn is not None:
        emit_result = emit_fn(output, artifact_dir)
        if isinstance(emit_result, dict):
            generated_files = [
                str(p).replace("\\", "/") for p in emit_result.get("generated_files", [])
            ]
    if not generated_files:
        default_result_file = artifact_dir / "result.json"
        default_result_file.write_text(json.dumps(output, indent=2), encoding="utf-8")
        generated_files = [_relative_or_abs(default_result_file)]

    result_envelope = {
        "status": output.get("status", "planned"),
        "summary": output.get("summary", ""),
        "generated_files": output.get("generated_files", generated_files),
        "requirements": output.get("requirements", []),
        "timestamp": output.get("timestamp", datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")),
    }

    return {
        "artifact_dir": _relative_or_abs(artifact_dir),
        "context": {
            "created_at_utc": runtime_context.created_at_utc,
            "operator": runtime_context.operator,
            "workspace": _relative_or_abs(runtime_context.workspace),
        },
        "ok": True,
        "result": result_envelope,
        "worker_id": str(metadata.get("id", worker_path.name)),
    }
