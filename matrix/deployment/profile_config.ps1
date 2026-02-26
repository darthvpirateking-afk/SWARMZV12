param(
  [ValidateSet('local','render')]
  [string]$Profile
)

Set-Location $PSScriptRoot

if (-not $Profile) {
  Write-Host "Usage: ./SWARMZ_PROFILE.ps1 <local|render>" -ForegroundColor Yellow
  python tools/switch_runtime_profile.py --show
  exit 1
}

python tools/switch_runtime_profile.py $Profile
exit $LASTEXITCODE
