from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, Dict

REQUIRED_FUNCTIONS = ("validate", "run")


def _load_yaml_or_json(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    try:
        import yaml  # type: ignore

        data = yaml.safe_load(text)
    except ImportError:
        data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError(f"worker metadata must be an object: {path}")
    return data


def load_worker_metadata(worker_dir: Path | str) -> Dict[str, Any]:
    worker_path = Path(worker_dir)
    metadata_path = worker_path / "worker.yaml"
    if not metadata_path.exists():
        raise FileNotFoundError(f"missing worker metadata: {metadata_path}")
    metadata = _load_yaml_or_json(metadata_path)
    metadata.setdefault("id", worker_path.name)
    return metadata


def load_worker_module(worker_dir: Path | str) -> ModuleType:
    worker_path = Path(worker_dir)
    run_path = worker_path / "run.py"
    if not run_path.exists():
        raise FileNotFoundError(f"missing worker run file: {run_path}")

    module_name = f"nexusmon_worker_{worker_path.name.replace('-', '_')}"
    spec = importlib.util.spec_from_file_location(module_name, run_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"unable to load worker module: {run_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def get_worker_functions(module: ModuleType) -> Dict[str, Callable[..., Any]]:
    functions: Dict[str, Callable[..., Any]] = {}
    for name in REQUIRED_FUNCTIONS:
        fn = getattr(module, name, None)
        if not callable(fn):
            raise AttributeError(f"worker is missing required function: {name}")
        functions[name] = fn

    emit = getattr(module, "emit_artifacts", None)
    if callable(emit):
        functions["emit_artifacts"] = emit
    return functions
