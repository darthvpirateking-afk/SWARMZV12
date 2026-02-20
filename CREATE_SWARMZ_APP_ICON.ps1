# SWARMZ Desktop App Shortcut Creator
# Creates a desktop shortcut that starts SWARMZ (RUN.ps1) with a custom icon.

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$iconPath = Join-Path $repoRoot "web_ui\icons\icon-512.png"
$desktop = [Environment]::GetFolderPath("Desktop")
$shortcutPath = Join-Path $desktop "SWARMZ Start.lnk"
$runScript = Join-Path $repoRoot "RUN.ps1"

if (-not (Test-Path $iconPath)) {
    Write-Host "ERROR: Icon not found at $iconPath" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $runScript)) {
    Write-Host "ERROR: RUN.ps1 not found at $runScript" -ForegroundColor Red
    exit 1
}

$wsh = New-Object -ComObject WScript.Shell
$shortcut = $wsh.CreateShortcut($shortcutPath)
$shortcut.TargetPath = "powershell.exe"
$shortcut.Arguments = "-ExecutionPolicy Bypass -NoProfile -File `"$runScript`""
$shortcut.WorkingDirectory = $repoRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Save()

Write-Host "SWARMZ shortcut created:" -ForegroundColor Green
Write-Host "  $shortcutPath"
Write-Host ""
Write-Host "Double-click this shortcut to run full SWARMZ startup."
