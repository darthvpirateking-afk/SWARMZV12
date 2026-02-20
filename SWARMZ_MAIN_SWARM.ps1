$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "CONNECTING TO MAIN SWARM" -ForegroundColor Cyan
python tools/switch_runtime_profile.py render
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Start-Process "https://swarmzV10-.onrender.com"
Write-Host "Opened: https://swarmzV10-.onrender.com" -ForegroundColor Green
