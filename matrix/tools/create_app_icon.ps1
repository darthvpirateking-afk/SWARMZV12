# SWARMZ Desktop App Shortcut Creator
# Creates a desktop shortcut that opens SWARMZ in the browser with a custom icon.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$iconPath = Join-Path $repoRoot "web_ui\icons\icon-512.png"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "SWARMZ.url"

if (-not (Test-Path $iconPath)) {
    Write-Host "ERROR: Icon not found at $iconPath" -ForegroundColor Red
    exit 1
}

$content = @"
[InternetShortcut]
URL=http://localhost:8012/
IconFile=$iconPath
IconIndex=0
"@

Set-Content -Path $shortcutPath -Value $content -Encoding ASCII

Write-Host "SWARMZ shortcut created:" -ForegroundColor Green
Write-Host "  $shortcutPath"
Write-Host ""
Write-Host "Start SWARMZ first with RUN.ps1, then open the SWARMZ desktop icon."
