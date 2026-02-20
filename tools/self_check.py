# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
SWARMZ Self Check

- Detect wrong working directory
- Detect nested-shadowed package.json
- Detect BOM in JSON files
- Detect missing scripts/dev dependencies (Node) and requirements.txt
- Print suggested FIX commands

Standard library only.
"""
import json
import socket
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parent.parent
EXPECTED_FILES = ["run_swarmz.py", "swarmz_server.py", "requirements.txt", "package.json"]
IGNORE_DIRS = {"node_modules", ".git", "__pycache__", "build", "dist"}
DEFAULT_PORTS = [8012, 3000]


def info(msg: str):
    print(f"[INFO] {msg}")


def warn(msg: str):
    print(f"[WARN] {msg}")


def err(msg: str):
    print(f"[ERROR] {msg}")


def check_cwd():
    cwd = Path.cwd().resolve()
    if cwd != ROOT:
        warn(f"Working directory is {cwd}, expected {ROOT}")
        print("  FIX: cd \"" + str(ROOT) + "\"")
        return False
    info("Working directory OK")
    return True


def find_package_json() -> List[Path]:
    matches = []
    for path in ROOT.rglob("package.json"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        matches.append(path)
    return matches


def check_nested_package_json():
    pkgs = find_package_json()
    if not pkgs:
        warn("No package.json found")
        return False
    root_pkg = ROOT / "package.json"
    if root_pkg not in pkgs:
        warn("package.json missing at repo root")
    if len(pkgs) > 1:
        warn("Nested package.json detected; choose a single authoritative root at runtime")
        for p in pkgs:
            print(f"  - {p.relative_to(ROOT)}")
        print("  FIX: run Node commands in repo root or set NODE_PATH explicitly")
        return True  # warn but do not hard-fail
    info("package.json OK")
    return True


def check_bom_in_json():
    bad = []
    for path in ROOT.rglob("*.json"):
        if any(part in IGNORE_DIRS for part in path.parts):
            continue
        try:
            with path.open("rb") as f:
                start = f.read(3)
                if start.startswith(b"\xef\xbb\xbf"):
                    bad.append(path)
        except Exception:
            continue
    if bad:
        warn("BOM detected in JSON files:")
        for p in bad:
            print(f"  - {p.relative_to(ROOT)}")
        print("  FIX: remove BOM, e.g. using: python - <<'PY' ...")
        return False
    info("No JSON BOM issues")
    return True


def check_scripts_and_deps():
    pkg_path = ROOT / "package.json"
    ok = True
    if pkg_path.exists():
        try:
            pkg = json.loads(pkg_path.read_text())
            scripts = pkg.get("scripts", {})
            required_scripts = ["build", "test"]
            missing_scripts = [s for s in required_scripts if s not in scripts]
            for s in missing_scripts:
                warn(f"package.json missing script: {s}")
                ok = False
            dev_deps = pkg.get("devDependencies", {})
            needed = ["typescript", "jest", "ts-jest", "@types/node"]
            for dep in needed:
                if dep not in dev_deps:
                    warn(f"Dev dependency missing: {dep}")
                    ok = False
            if missing_scripts:
                print("  FIX (CMD): " + " & ".join([f"npm set-script {s} \"<cmd>\"" for s in missing_scripts]))
                print("  FIX (PS): " + "; ".join([f"npm set-script {s} '<cmd>'" for s in missing_scripts]))
            missing_deps = [dep for dep in needed if dep not in dev_deps]
            if missing_deps:
                print("  FIX (CMD): npm install -D " + " ".join(missing_deps))
                print("  FIX (PS): npm install -D " + " ".join(missing_deps))
        except Exception as exc:
            err(f"Failed to parse package.json: {exc}")
            ok = False
    else:
        warn("package.json not found")
        ok = False
    req = ROOT / "requirements.txt"
    if not req.exists():
        warn("requirements.txt missing")
        ok = False
    else:
        info("requirements.txt present")
        print("  TIP: pip install -r requirements.txt")
    return ok


def check_expected_files():
    missing = []
    for name in EXPECTED_FILES:
        if not (ROOT / name).exists():
            missing.append(name)
    if missing:
        warn("Missing expected files: " + ", ".join(missing))
        print("  FIX: ensure you run from repo root; verify checkout")
        return False
    info("Expected files present")
    return True


def check_port_conflicts():
    busy = []
    for port in DEFAULT_PORTS:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(0.5)
            try:
                s.connect(("127.0.0.1", port))
                busy.append(port)
            except Exception:
                continue
    if busy:
        warn("Port conflicts detected: " + ", ".join(map(str, busy)))
        print("  FIX (CMD): " + " & ".join([f"netstat -ano ^| findstr :{p}" for p in busy]))
        print("  FIX (PS): " + "; ".join([f"Get-NetTCPConnection -LocalPort {p}" for p in busy]))
        return False
    info("Ports available: " + ", ".join(map(str, DEFAULT_PORTS)))
    return True


def main():
    overall_ok = True
    if not check_cwd():
        overall_ok = False
    if not check_expected_files():
        overall_ok = False
    if not check_nested_package_json():
        overall_ok = False
    if not check_bom_in_json():
        overall_ok = False
    if not check_scripts_and_deps():
        overall_ok = False
    if not check_port_conflicts():
        overall_ok = False

    print("\n=== SUMMARY ===")
    if overall_ok:
        print("OK: No blocking issues detected")
        sys.exit(0)
    else:
        print("WARN: Issues detected above. See FIX hints.")
        sys.exit(1)


if __name__ == "__main__":
    main()

