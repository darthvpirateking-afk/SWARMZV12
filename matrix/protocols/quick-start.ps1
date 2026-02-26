$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "SWARMZ ONE-BUTTON START" -ForegroundColor Cyan

# Always use local profile for one-button desktop/phone-on-LAN usage
python tools/switch_runtime_profile.py local | Out-Null

# Auto-free default port if blocked
$env:KILL_PORT = "1"

& "$PSScriptRoot\SWARMZ_UP.ps1"
exit $LASTEXITCODE
