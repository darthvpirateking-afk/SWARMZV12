param(
    [switch]$Apply,
    [switch]$ForceReinstallWSL,
    [switch]$SkipSfc,
    [switch]$SkipDism
)

$ErrorActionPreference = 'Stop'

function Write-Section($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Write-Step($text) {
    Write-Host "[+] $text" -ForegroundColor Gray
}

function Test-IsAdmin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($id)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Invoke-SafeCommand($label, $command) {
    Write-Step $label
    Write-Host "    $command" -ForegroundColor DarkGray
    try {
        Invoke-Expression $command
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "$label finished with exit code $LASTEXITCODE"
        }
    } catch {
        Write-Warning "$label failed: $($_.Exception.Message)"
    }
}

function Show-WSLStatus {
    Write-Section 'WSL status snapshot'
    Invoke-SafeCommand 'wsl --status' 'wsl --status'
    Invoke-SafeCommand 'wsl -l -v' 'wsl -l -v'
}

Write-Section 'SWARMZ WSL Host Recovery'
Write-Host 'Repairs host-level WSL startup failures (e.g., E_UNEXPECTED / E_FAIL) for SWARMZ live runtime prerequisites.'

$needsAdmin = $Apply -or $ForceReinstallWSL

if ($needsAdmin -and -not (Test-IsAdmin)) {
    Write-Host 'This script needs elevated PowerShell for repair actions.' -ForegroundColor Red
    Write-Host 'Re-run as Administrator.' -ForegroundColor Yellow
    Write-Host 'Example:' -ForegroundColor Yellow
    Write-Host '  powershell -ExecutionPolicy Bypass -File .\SWARMZ_WSL_HOST_RECOVERY.ps1 -Apply' -ForegroundColor DarkGray
    exit 1
}

Show-WSLStatus

if (-not $Apply) {
    Write-Section 'Dry run plan'
    Write-Host 'Would execute:' -ForegroundColor Yellow
    if (-not $SkipSfc) {
        Write-Host '  1) sfc /scannow' -ForegroundColor DarkGray
    }
    if (-not $SkipDism) {
        Write-Host '  2) DISM /Online /Cleanup-Image /RestoreHealth' -ForegroundColor DarkGray
    }
    Write-Host '  3) wsl --shutdown' -ForegroundColor DarkGray
    Write-Host '  4) Launch Ubuntu once: wsl -d Ubuntu -e bash -lc "echo WSL_OK"' -ForegroundColor DarkGray
    if ($ForceReinstallWSL) {
        Write-Host '  5) Force reinstall path: wsl --unregister Ubuntu ; wsl --install -d Ubuntu' -ForegroundColor DarkGray
    }
    Write-Section 'Next'
    Write-Host 'Run with -Apply to perform repairs.'
    exit 0
}

Write-Section 'Repair actions'

if (-not $SkipSfc) {
    Invoke-SafeCommand 'System file check' 'sfc /scannow'
}

if (-not $SkipDism) {
    Invoke-SafeCommand 'DISM health restore' 'DISM /Online /Cleanup-Image /RestoreHealth'
}

Invoke-SafeCommand 'Shutdown WSL' 'wsl --shutdown'
Start-Sleep -Seconds 2

if ($ForceReinstallWSL) {
    Write-Section 'Force reinstall path'
    Invoke-SafeCommand 'Unregister Ubuntu distro' 'wsl --unregister Ubuntu'
    Invoke-SafeCommand 'Install Ubuntu distro' 'wsl --install -d Ubuntu'
    Write-Host 'A reboot may be required before Ubuntu first launch.' -ForegroundColor Yellow
}

Write-Section 'Post-repair validation'
Show-WSLStatus
Invoke-SafeCommand 'Launch Ubuntu test' 'wsl -d Ubuntu -e bash -lc "echo WSL_OK && uname -a"'

Write-Section 'SWARMZ follow-up'
Write-Host 'If Ubuntu launches successfully, run:' -ForegroundColor Yellow
Write-Host '  .\SWARMZ_V5_WSL_LIBVIRT_BOOTSTRAP.ps1 -Apply' -ForegroundColor DarkGray
Write-Host '  .\SWARMZ_V5_LIVE_SETUP.ps1' -ForegroundColor DarkGray
