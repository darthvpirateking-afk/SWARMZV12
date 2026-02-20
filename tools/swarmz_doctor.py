# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""SWARMZ Doctor (product layer)

Usage:
  python tools/swarmz_doctor.py

Performs environment sanity checks without mutating repo state. The script prints
PASS/FAIL per check plus Windows CMD and PowerShell fix commands.
"""
from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple
from urllib import request, error

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
CONFIG_DIR = ROOT / "config"
RUNTIME_CONFIG = CONFIG_DIR / "runtime.json"
DEFAULT_PORTS = [8012, 3000]


class CheckResult:
    def __init__(self, name: str, status: str, info: str, fixes: List[Tuple[str, str]] | None = None):
        self.name = name
        self.status = status  # PASS | FAIL | WARN
        self.info = info
        self.fixes = fixes or []

    @property
    def ok(self) -> bool:
        return self.status == "PASS"


def _print_header(title: str) -> None:
    print("\n" + "=" * 10 + f" {title} " + "=" * 10)


def _load_runtime_config() -> Dict[str, str]:
    if not RUNTIME_CONFIG.exists():
        return {}
    try:
        return json.loads(RUNTIME_CONFIG.read_text())
    except Exception:
        return {}


def run_self_check() -> CheckResult:
    script = ROOT / "tools" / "self_check.py"
    if not script.exists():
        return CheckResult("self_check", "WARN", "tools/self_check.py missing")
    proc = subprocess.run([sys.executable, str(script)], cwd=ROOT)
    status = "PASS" if proc.returncode == 0 else "FAIL"
    return CheckResult("self_check", status, f"exit={proc.returncode}")


def check_workdir() -> CheckResult:
    correct = Path.cwd().resolve() == ROOT
    info = f"cwd={Path.cwd()} expected={ROOT}"
    fixes = [
        ("CMD", f"cd /d \"{ROOT}\""),
        ("PS", f"Set-Location \"{ROOT}\""),
    ]
    return CheckResult("Working directory", "PASS" if correct else "FAIL", info, fixes)


def check_shadow_dirs() -> CheckResult:
    shadows = []
    for parent in ROOT.iterdir():
        if parent.is_dir():
            dup = parent / parent.name
            if dup.exists():
                shadows.append(str(dup.relative_to(ROOT)))
    pkg_jsons = [p for p in ROOT.rglob("package.json") if "node_modules" not in p.parts and ".git" not in p.parts]
    info_parts = []
    if shadows:
        info_parts.append("shadow dirs: " + ", ".join(shadows))
    if len(pkg_jsons) > 1:
        info_parts.append("multiple package.json roots: " + ", ".join(str(p.relative_to(ROOT)) for p in pkg_jsons))
    if shadows:
        status = "WARN"
    elif len(pkg_jsons) > 1:
        status = "WARN"
    else:
        status = "PASS"
    fixes = [
        ("CMD", "Remove duplicate nested dirs (e.g., rmdir /s web\\web) or consolidate package roots."),
        ("PS", "Remove duplicate nested dirs (Remove-Item -Recurse -Force web/web) or consolidate package roots."),
    ]
    return CheckResult("Shadow dirs / package roots", status, "; ".join(info_parts) or "ok", fixes)


def check_bom() -> CheckResult:
    bad = []
    for path in ROOT.rglob("*.json"):
        try:
            with open(path, "rb") as fh:
                start = fh.read(3)
                if start.startswith(b"\xef\xbb\xbf"):
                    bad.append(str(path.relative_to(ROOT)))
        except Exception:
            continue
    status = "FAIL" if bad else "PASS"
    info = "BOM found: " + ", ".join(bad) if bad else "no BOM detected"
    fixes = []
    for rel in bad:
        abspath = ROOT / rel
        fixes.append((
            "CMD",
            f"powershell -Command \"(Get-Content -Raw '{abspath}') -replace '^\\uFEFF','' | Set-Content '{abspath}' -Encoding UTF8\"",
        ))
        fixes.append((
            "PS",
            f"(Get-Content -Raw '{abspath}') -replace '^\uFEFF','' | Set-Content '{abspath}' -Encoding UTF8",
        ))
    return CheckResult("BOM in JSON", status, info, fixes)


def check_scripts() -> CheckResult:
    pkg = ROOT / "package.json"
    if not pkg.exists():
        return CheckResult("npm scripts", "WARN", "package.json missing")
    try:
        data = json.loads(pkg.read_text())
    except Exception as exc:
        return CheckResult("npm scripts", "FAIL", f"parse failed: {exc}")
    scripts = data.get("scripts", {}) if isinstance(data, dict) else {}
    missing = [s for s in ("dev", "build", "start") if s not in scripts]
    if missing:
        fixes = [
            ("CMD", " && ".join([f"npm set-script {s} \"<cmd>\"" for s in missing])),
            ("PS", "; ".join([f"npm set-script {s} '<cmd>'" for s in missing])),
        ]
        return CheckResult("npm scripts", "FAIL", f"missing: {', '.join(missing)}", fixes)
    return CheckResult("npm scripts", "PASS", "dev/build/start present")


def _ports_in_use(ports: List[int]) -> List[int]:
    busy = []
    for port in ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", port))
                busy.append(port)
            except Exception:
                continue
    return busy


def check_ports() -> CheckResult:
    busy = _ports_in_use(DEFAULT_PORTS)
    status = "FAIL" if busy else "PASS"
    fixes = [
        ("CMD", " & ".join([f"netstat -ano | findstr :{p}" for p in busy]) or ""),
        ("PS", "; ".join([f"Get-NetTCPConnection -LocalPort {p}" for p in busy]) or ""),
    ]
    info = "ports busy: " + ", ".join(map(str, busy)) if busy else "ports free"
    return CheckResult("Ports", status, info, fixes)


def check_env_and_config() -> CheckResult:
    cfg = _load_runtime_config()
    missing_cfg = [k for k in ("apiBaseUrl", "uiBaseUrl", "bind", "port") if k not in cfg]
    env_warn = []
    if not os.getenv("SWARMZ_OPERATOR_PIN"):
        env_warn.append("SWARMZ_OPERATOR_PIN not set (auto-generated will be used)")
    status = "FAIL" if missing_cfg else "PASS"
    info_parts = []
    if missing_cfg:
        info_parts.append("missing config keys: " + ", ".join(missing_cfg))
    if env_warn:
        info_parts.append("; ".join(env_warn))
    fixes = [
        ("CMD", "python tools\\swarmz_onboard.py"),
        ("PS", "python tools/swarmz_onboard.py"),
    ]
    return CheckResult("Env & config", status, "; ".join(info_parts) or "ok", fixes)


def check_writable_dirs() -> CheckResult:
    dirs = [DATA_DIR, CONFIG_DIR]
    failures = []
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
            test_file = d / ".doctor_write_test"
            test_file.write_text("ok")
            test_file.unlink(missing_ok=True)
        except Exception as exc:
            failures.append(f"{d}: {exc}")
    status = "FAIL" if failures else "PASS"
    fixes = [
        ("CMD", "Run shell as Administrator or fix permissions on data/ and config/"),
        ("PS", "Run as Administrator or take ownership: takeown /F data /A /R")
    ]
    return CheckResult("Writable dirs", status, "; ".join(failures) or "ok", fixes)


def check_health() -> CheckResult:
    cfg = _load_runtime_config()
    base = cfg.get("apiBaseUrl") or cfg.get("api_base") or "http://127.0.0.1:8012"
    url = base.rstrip("/") + "/v1/health"
    try:
        with request.urlopen(url, timeout=5) as resp:
            body = resp.read().decode("utf-8", errors="ignore")
            try:
                data = json.loads(body)
            except Exception:
                data = {"raw": body}
            ok = isinstance(data, dict) and data.get("ok") is True
            status = "PASS" if ok else "FAIL"
            info = json.dumps(data, indent=2)
    except error.URLError as exc:
        status = "WARN"
        info = f"cannot reach {url}: {exc}"
    fixes = [
        ("CMD", "python run_server.py --port 8012"),
        ("PS", "python run_server.py --port 8012"),
    ]
    return CheckResult("Health endpoint", status, info, fixes)


def print_result(res: CheckResult) -> None:
    print(f"[{res.status}] {res.name}")
    print(f"  {res.info}")
    if res.status != "PASS" and res.fixes:
        for shell, cmd in res.fixes:
            if not cmd:
                continue
            print(f"  Fix ({shell}): {cmd}")


def main():
    _print_header("SWARMZ Doctor")
    checks = [
        run_self_check(),
        check_workdir(),
        check_shadow_dirs(),
        check_bom(),
        check_scripts(),
        check_ports(),
        check_env_and_config(),
        check_writable_dirs(),
        check_health(),
    ]

    fails = [c for c in checks if c.status == "FAIL"]
    warns = [c for c in checks if c.status == "WARN"]

    for c in checks:
        print_result(c)

    _print_header("SUMMARY")
    print(f"PASS: {len([c for c in checks if c.status=='PASS'])}")
    print(f"WARN: {len(warns)}")
    print(f"FAIL: {len(fails)}")

    if fails:
        print("Verdict: FAIL")
        sys.exit(1)
    print("Verdict: PASS")


if __name__ == "__main__":
    main()

