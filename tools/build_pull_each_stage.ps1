param(
  [int]$StartStage = 6,
  [int]$EndStage = 30
)

$ErrorActionPreference = 'Stop'

if ($StartStage -lt 1 -or $EndStage -gt 30 -or $StartStage -gt $EndStage) {
  throw "Invalid stage range. Use 1..30 and StartStage <= EndStage."
}

$python = "C:/Users/Gaming PC/AppData/Local/Python/pythoncore-3.14-64/python.exe"

for ($stage = $StartStage; $stage -le $EndStage; $stage++) {
  Write-Host ("=== BUILD {0} syncing from GitHub ===" -f $stage)
  git fetch --all --prune --tags
  git pull --rebase --autostash

  Write-Host ("=== BUILD {0} applying stage ===" -f $stage)
  & $python -c "from api.build_milestones_service import BuildMilestonesService; s=BuildMilestonesService(data_dir='data'); r=s.promote($stage); print(r.message)"
}

Write-Host "Completed BUILD $StartStage through BUILD $EndStage with pull-before-each-stage."
