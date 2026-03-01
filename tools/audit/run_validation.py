from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUT = PROJECT_ROOT / "artifacts" / "audit" / "validation_summary.json"
DEFAULT_BASELINE = PROJECT_ROOT / ".validation_baseline.json"


@dataclass
class CmdResult:
    name: str
    argv: list[str]
    ok: bool
    exit_code: int
    duration_ms: int
    stdout_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "argv": self.argv,
            "ok": self.ok,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "stdout_path": self.stdout_path,
        }


def _extract_failure_count(name: str, output: str) -> int | None:
    if name in {"mypy", "ruff"}:
        match = re.search(r"Found\s+(\d+)\s+errors?", output)
        if match:
            return int(match.group(1))
    if name == "pytest":
        failed_matches = re.findall(r"(\d+)\s+failed", output)
        error_matches = re.findall(r"(\d+)\s+errors?", output)
        failed = int(failed_matches[-1]) if failed_matches else 0
        errors = int(error_matches[-1]) if error_matches else 0
        if failed or errors:
            return failed + errors
    return None


def _build_failure_fingerprint(results: list[CmdResult]) -> dict[str, dict[str, Any]]:
    fingerprint: dict[str, dict[str, Any]] = {}
    for result in results:
        log_path = PROJECT_ROOT / result.stdout_path
        output = ""
        if log_path.exists():
            output = log_path.read_text(encoding="utf-8", errors="replace")
        error_count = _extract_failure_count(result.name, output)
        severity = error_count if error_count is not None else (0 if result.ok else 1)
        fingerprint[result.name] = {
            "ok": result.ok,
            "exit_code": result.exit_code,
            "error_count": error_count,
            "severity": int(severity),
        }
    return fingerprint


def _run_scoped_bridge(
    *,
    python_exe: str,
    out_dir: Path,
    timeout_pytest: int,
    timeout_ruff: int,
    timeout_mypy: int,
) -> list[CmdResult]:
    checks: list[tuple[str, list[str], Path, int]] = [
        (
            "ruff",
            [
                python_exe,
                "-m",
                "ruff",
                "check",
                "swarmz_runtime/bridge",
                "tests/bridge",
            ],
            out_dir / "validation_bridge_ruff.txt",
            timeout_ruff,
        ),
        (
            "mypy",
            [python_exe, "-m", "mypy", "swarmz_runtime/bridge", "--strict"],
            out_dir / "validation_bridge_mypy.txt",
            timeout_mypy,
        ),
        (
            "pytest",
            [python_exe, "-m", "pytest", "tests/bridge", "-x"],
            out_dir / "validation_bridge_pytest.txt",
            timeout_pytest,
        ),
    ]
    results: list[CmdResult] = []
    for name, argv, out_path, timeout_s in checks:
        result = _run(
            name=name,
            argv=argv,
            cwd=PROJECT_ROOT,
            out_path=out_path,
            timeout_s=timeout_s,
        )
        results.append(result)
        if not result.ok:
            break
    return results


def _compute_regressions(
    *,
    baseline: dict[str, Any],
    current: dict[str, dict[str, Any]],
) -> list[str]:
    regressions: list[str] = []
    baseline_fingerprint = baseline.get("fingerprint", {})
    if not isinstance(baseline_fingerprint, dict):
        return regressions

    for name, current_entry in current.items():
        baseline_entry = baseline_fingerprint.get(name)
        if not isinstance(baseline_entry, dict):
            if not bool(current_entry.get("ok", False)):
                regressions.append(f"{name}: failed with no baseline entry")
            continue

        baseline_ok = bool(baseline_entry.get("ok", False))
        current_ok = bool(current_entry.get("ok", False))
        baseline_severity = int(baseline_entry.get("severity", 0))
        current_severity = int(current_entry.get("severity", 0))

        if baseline_ok and not current_ok:
            regressions.append(f"{name}: transitioned from pass to fail")
        elif (not baseline_ok) and (not current_ok) and current_severity > baseline_severity:
            regressions.append(
                f"{name}: failure severity increased ({baseline_severity} -> {current_severity})"
            )

    return regressions


def _total_severity(fingerprint: dict[str, dict[str, Any]]) -> int:
    total = 0
    for entry in fingerprint.values():
        total += int(entry.get("severity", 0))
    return total


def _pick_python(explicit: str | None) -> str:
    if explicit:
        return explicit
    venv_py = PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    if venv_py.exists():
        return str(venv_py)
    return sys.executable


def _run(
    *,
    name: str,
    argv: list[str],
    cwd: Path,
    out_path: Path,
    timeout_s: int,
) -> CmdResult:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    t0 = time.monotonic()
    try:
        proc = subprocess.run(
            argv,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_s,
        )
        output = proc.stdout or ""
        exit_code = int(proc.returncode)
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + "\n[TIMEOUT]\n"
        exit_code = 124
    duration_ms = int((time.monotonic() - t0) * 1000)

    # Keep artifacts bounded: truncate very large outputs.
    max_chars = 250_000
    if len(output) > max_chars:
        head = output[:max_chars]
        tail_note = f"\n[TRUNCATED] original_chars={len(output)} kept_chars={len(head)}\n"
        output = head + tail_note

    out_path.write_text(output, encoding="utf-8", errors="replace")
    return CmdResult(
        name=name,
        argv=argv,
        ok=exit_code == 0,
        exit_code=exit_code,
        duration_ms=duration_ms,
        stdout_path=str(out_path.relative_to(PROJECT_ROOT)).replace("\\", "/"),
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run audit validation checks and write summary JSON.")
    parser.add_argument("--python", dest="python_path", type=str, default=os.environ.get("NEXUSMON_PYTHON"))
    parser.add_argument("--out", type=str, default=str(DEFAULT_OUT))
    parser.add_argument("--scope", choices=["bridge"], default=None)
    parser.add_argument("--capture-baseline", action="store_true")
    parser.add_argument("--baseline", type=str, default=str(DEFAULT_BASELINE))
    parser.add_argument("--timeout-pytest", type=int, default=240)
    parser.add_argument("--timeout-ruff", type=int, default=240)
    parser.add_argument("--timeout-mypy", type=int, default=420)
    args = parser.parse_args(argv)
    if args.scope and args.capture_baseline:
        parser.error("--capture-baseline cannot be used with --scope.")

    python_exe = _pick_python(args.python_path)
    out_json = Path(args.out)
    baseline_path = Path(args.baseline)

    out_dir = out_json.parent
    pytest_out = out_dir / "validation_pytest.txt"
    ruff_out = out_dir / "validation_ruff.txt"
    mypy_out = out_dir / "validation_mypy.txt"

    results: list[CmdResult] = []

    if args.scope == "bridge":
        results = _run_scoped_bridge(
            python_exe=python_exe,
            out_dir=out_dir,
            timeout_pytest=int(args.timeout_pytest),
            timeout_ruff=int(args.timeout_ruff),
            timeout_mypy=int(args.timeout_mypy),
        )
        scoped_ok = len(results) == 3 and all(result.ok for result in results)
        payload = {
            "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "project_root": str(PROJECT_ROOT),
            "python": python_exe,
            "mode": "scope:bridge",
            "overall_ok": scoped_ok,
            "results": [result.to_dict() for result in results],
        }
        out_json.parent.mkdir(parents=True, exist_ok=True)
        out_json.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        print(f"[validate] wrote {out_json}")
        for result in results:
            print(
                f"[validate] {result.name}: ok={result.ok} "
                f"exit={result.exit_code} ms={result.duration_ms} log={result.stdout_path}"
            )
        return 0 if scoped_ok else 1

    results.append(
        _run(
            name="pytest",
            argv=[python_exe, "-m", "pytest", "-q"],
            cwd=PROJECT_ROOT,
            out_path=pytest_out,
            timeout_s=int(args.timeout_pytest),
        )
    )
    results.append(
        _run(
            name="ruff",
            argv=[python_exe, "-m", "ruff", "check", "."],
            cwd=PROJECT_ROOT,
            out_path=ruff_out,
            timeout_s=int(args.timeout_ruff),
        )
    )
    results.append(
        _run(
            name="mypy",
            argv=[python_exe, "-m", "mypy", "core"],
            cwd=PROJECT_ROOT,
            out_path=mypy_out,
            timeout_s=int(args.timeout_mypy),
        )
    )

    fingerprint = _build_failure_fingerprint(results)
    baseline_exists = baseline_path.exists()
    regressions: list[str] = []
    baseline_mode = False
    baseline_total_severity = 0
    current_total_severity = _total_severity(fingerprint)

    if args.capture_baseline:
        baseline_payload = {
            "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "project_root": str(PROJECT_ROOT),
            "fingerprint": fingerprint,
        }
        baseline_path.parent.mkdir(parents=True, exist_ok=True)
        baseline_path.write_text(
            json.dumps(baseline_payload, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
    elif baseline_exists:
        baseline_mode = True
        baseline_payload = json.loads(baseline_path.read_text(encoding="utf-8"))
        regressions = _compute_regressions(baseline=baseline_payload, current=fingerprint)
        baseline_fingerprint = baseline_payload.get("fingerprint", {})
        if isinstance(baseline_fingerprint, dict):
            baseline_total_severity = _total_severity(baseline_fingerprint)
        severity_delta = current_total_severity - baseline_total_severity
        if severity_delta > 10:
            regressions.append(
                f"global: severity exceeded ceiling by {severity_delta} (limit +10)"
            )

    overall_ok = all(result.ok for result in results)
    exit_code = 0 if overall_ok else 1
    if args.capture_baseline:
        exit_code = 0
    elif baseline_mode:
        overall_ok = len(regressions) == 0
        exit_code = 0 if overall_ok else 1

    payload = {
        "generated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "project_root": str(PROJECT_ROOT),
        "python": python_exe,
        "mode": "full",
        "baseline_path": str(baseline_path),
        "baseline_mode": baseline_mode,
        "capture_baseline": bool(args.capture_baseline),
        "overall_ok": overall_ok,
        "regressions": regressions,
        "total_severity": current_total_severity,
        "baseline_total_severity": baseline_total_severity,
        "fingerprint": fingerprint,
        "results": [result.to_dict() for result in results],
    }
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"[validate] wrote {out_json}")
    for result in results:
        print(
            f"[validate] {result.name}: ok={result.ok} "
            f"exit={result.exit_code} ms={result.duration_ms} log={result.stdout_path}"
        )
    if args.capture_baseline:
        print(f"[validate] baseline captured at {baseline_path}")
    elif baseline_mode:
        if regressions:
            print(f"[validate] regressions detected: {regressions}")
        else:
            print("[validate] no regressions compared to baseline")
            unchanged_failures = [
                name
                for name, entry in fingerprint.items()
                if not bool(entry.get("ok", False))
            ]
            if unchanged_failures:
                print(
                    "[validate] informational: pre-existing failures tolerated: "
                    + ", ".join(unchanged_failures)
                )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
