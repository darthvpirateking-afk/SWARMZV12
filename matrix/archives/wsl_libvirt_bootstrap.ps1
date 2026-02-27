param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

function Write-Section($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Get-PreferredDistro {
    $distros = & wsl -l -q 2>$null
    if (-not $distros) {
        return $null
    }

    $distros = $distros | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ }

    $preferred = @('Ubuntu-24.04', 'Ubuntu-22.04', 'Ubuntu')
    foreach ($candidate in $preferred) {
        if ($distros -contains $candidate) {
            return $candidate
        }
    }

    $ubuntuLike = $distros | Where-Object { $_ -like 'Ubuntu*' }
    if ($ubuntuLike) {
        return ($ubuntuLike | Select-Object -First 1)
    }

    return $null
}

function Invoke-InWSL($distro, $command) {
    & wsl -d $distro -e bash -lc $command
}

function Test-WSLCommand($distro, $name) {
    $resolved = & wsl -d $distro -e bash -lc "command -v $name" 2>$null
    if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
        return $resolved.Trim()
    }
    return $null
}

function Test-WSLLaunchable($distro) {
    & wsl -d $distro -e bash -lc "echo launch_ok" 2>$null | Out-Null
    return ($LASTEXITCODE -eq 0)
}

Write-Section 'SWARMZ V5 WSL2 libvirt bootstrap'
Write-Host 'Prepares WSL Ubuntu with qemu/libvirt tools for virsh and libvirtd support.'

if (-not (Test-Cmd 'wsl')) {
    throw 'WSL is not installed. Install WSL first: wsl --install -d Ubuntu'
}

$distro = Get-PreferredDistro
if (-not $distro) {
    if (-not $Apply) {
        Write-Host 'No WSL distro found. Dry-run recommendation: wsl --install -d Ubuntu' -ForegroundColor Yellow
        exit 0
    }

    Write-Host 'No distro found. Installing Ubuntu via WSL...' -ForegroundColor Yellow
    wsl --install -d Ubuntu
    Write-Host 'WSL distro install requested. Re-run this script after installation completes.' -ForegroundColor Yellow
    exit 0
}

Write-Host "Using WSL distro: $distro"

if (-not (Test-WSLLaunchable $distro)) {
    Write-Host "WSL distro '$distro' is installed but cannot start." -ForegroundColor Red
    Write-Host 'Try host-level recovery: reboot Windows, run `wsl --shutdown`, then launch distro once manually.' -ForegroundColor Yellow
    Write-Host 'If still failing, repair/reinstall WSL from elevated PowerShell.' -ForegroundColor Yellow
    exit 1
}

$installCommand = @'
set -e
if command -v apt-get >/dev/null 2>&1; then
  sudo apt-get update
  sudo apt-get install -y qemu-kvm libvirt-daemon-system libvirt-clients bridge-utils virtinst
  sudo service libvirtd start || true
  sudo usermod -aG libvirt "$USER" || true
  sudo usermod -aG kvm "$USER" || true
else
  echo "apt-get unavailable in this distro."
  exit 1
fi
'@

if (-not $Apply) {
    Write-Section 'Dry run'
    Write-Host 'Would execute in WSL:'
    Write-Host $installCommand -ForegroundColor DarkGray
} else {
    Write-Section 'Applying install in WSL'
    Invoke-InWSL $distro $installCommand
}

Write-Section 'Verification'
$checks = @('virsh', 'libvirtd', 'qemu-system-x86_64')
foreach ($bin in $checks) {
    $resolved = Test-WSLCommand $distro $bin
    if ($resolved) {
        Write-Host "$bin = FOUND ($resolved)" -ForegroundColor Green
    } else {
        Write-Host "$bin = MISSING" -ForegroundColor Red
    }
}

Write-Section 'Note'
Write-Host 'If group membership changed, restart WSL session: wsl --shutdown' -ForegroundColor Yellow
