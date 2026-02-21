# SWARMZ Source Available License
# Commercial use, hosting, and resale prohibited.
# See LICENSE file for details.
#!/usr/bin/env python3
"""
Generate/refresh launcher scripts and fix a known typo in server entrypoints.

Outputs (overwritten in-place):
- SWARMZ_UP.ps1
- SWARMZ_UP.cmd
- SWARMZ_SMOKE.ps1
- SWARMZ_SMOKE.cmd

Also patches lines that accidentally start with "urn {" to "return {" in
server.py and run_server.py if those files exist.
"""

from __future__ import annotations

import socket
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def _lan_ip() -> str:
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"


def write_file(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")
    print(f"wrote {path.relative_to(ROOT)}")


def patch_typo(target: Path) -> None:
    if not target.exists():
        return
    lines = target.read_text(encoding="utf-8").splitlines()
    changed = False
    fixed = []
    for line in lines:
        if line.lstrip().startswith("urn {"):
            fixed_line = line.replace("urn {", "return {", 1)
            fixed.append(fixed_line)
            changed = True
        else:
            fixed.append(line)
    if changed:
        target.write_text("\n".join(fixed) + "\n", encoding="utf-8")
        print(f"patched return typo in {target.relative_to(ROOT)}")


def main() -> None:
    lan = _lan_ip()

    ps_up = f"""#!/usr/bin/env pwsh
param([string]$Host = "0.0.0.0", [int]$Port = 8012)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

Write-Host "SWARMZ_UP" -ForegroundColor Cyan
if (Test-Path "tools/self_check.py") {{
  try {{ python tools/self_check.py }} catch {{ Write-Host "self_check failed (continuing)" -ForegroundColor Yellow }}
}}

Write-Host "Starting server on $Host:$Port" -ForegroundColor Green
python run_server.py --host $Host --port $Port
"""

    cmd_up = r"""@echo off
setlocal
set HOST=0.0.0.0
set PORT=8012
cd /d %~dp0
echo SWARMZ_UP
if exist tools\self_check.py (
  python tools\self_check.py
)
echo Starting server on %HOST%:%PORT%
python run_server.py --host %HOST% --port %PORT%
endlocal
"""

    ps_smoke = f"""#!/usr/bin/env pwsh
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$url = "http://127.0.0.1:8012/v1/health"
Write-Host "SWARMZ_SMOKE" -ForegroundColor Cyan
try {{
  $res = Invoke-RestMethod -Uri $url -TimeoutSec 5
  if ($res.ok -eq $true) {{ Write-Host "Health OK" -ForegroundColor Green; exit 0 }}
  Write-Host "Health endpoint returned unexpected body" -ForegroundColor Yellow
  $res | ConvertTo-Json
  exit 1
}} catch {{
  Write-Host "Health check failed: $_" -ForegroundColor Red
  exit 1
}}
"""

    cmd_smoke = r"""@echo off
setlocal
set URL=http://127.0.0.1:8012/v1/health
echo SWARMZ_SMOKE
curl -s %URL% | find "\"ok\":true" >nul
if errorlevel 1 (
  echo Health check failed at %URL%
  exit /b 1
) else (
  echo Health OK
)
endlocal
"""

    write_file(ROOT / "SWARMZ_UP.ps1", ps_up)
    write_file(ROOT / "SWARMZ_UP.cmd", cmd_up)
    write_file(ROOT / "SWARMZ_SMOKE.ps1", ps_smoke)
    write_file(ROOT / "SWARMZ_SMOKE.cmd", cmd_smoke)

    for target in [ROOT / "server.py", ROOT / "run_server.py"]:
        patch_typo(target)


if __name__ == "__main__":
    main()
