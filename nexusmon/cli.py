from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from nexusmon.runtime.context import build_context
from nexusmon.runtime.executor import execute_worker
from nexusmon.runtime.registry import get_worker, list_workers


def _load_input_payload(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(payload, dict):
        raise ValueError("input payload must be a JSON object")
    return payload


def _cmd_worker_list(args: argparse.Namespace) -> int:
    workers = list_workers(args.registry)
    print(json.dumps(workers, indent=2))
    return 0


def _cmd_worker_describe(args: argparse.Namespace) -> int:
    worker = get_worker(args.worker_id, args.registry)
    print(json.dumps(worker, indent=2))
    return 0


def _cmd_worker_run(args: argparse.Namespace) -> int:
    worker = get_worker(args.worker_id, args.registry)
    worker_id = str(worker.get("id", args.worker_id))
    worker_dir = args.workers_root / worker_id

    payload = _load_input_payload(args.input)
    context = build_context(Path.cwd(), operator=args.operator)
    result = execute_worker(worker_dir, payload, context)
    print(json.dumps(result, indent=2))
    return 0


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="nexusmon")
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path("nexusmon/workers/registry.json"),
        help="Path to worker registry JSON.",
    )
    parser.add_argument(
        "--workers-root",
        type=Path,
        default=Path("workers"),
        help="Path to worker root directory.",
    )
    parser.add_argument(
        "--operator",
        default="local-operator",
        help="Operator context id.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)
    worker_parser = subparsers.add_parser("worker", help="Worker operations")
    worker_subparsers = worker_parser.add_subparsers(dest="worker_command", required=True)

    worker_list = worker_subparsers.add_parser("list", help="List registered workers")
    worker_list.set_defaults(func=_cmd_worker_list)

    worker_describe = worker_subparsers.add_parser("describe", help="Describe one worker")
    worker_describe.add_argument("worker_id", help="Registered worker id")
    worker_describe.set_defaults(func=_cmd_worker_describe)

    worker_run = worker_subparsers.add_parser("run", help="Run a worker from input JSON")
    worker_run.add_argument("worker_id", help="Registered worker id")
    worker_run.add_argument("--input", type=Path, required=True, help="Path to input JSON file")
    worker_run.set_defaults(func=_cmd_worker_run)
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.func(args))
    except Exception as exc:
        print(
            json.dumps({"error": str(exc), "ok": False}),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
