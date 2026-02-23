param(
    [switch]$InstallSystemDeps,
    [switch]$InstallPythonDeps,
    [switch]$BootstrapWSL
)

$ErrorActionPreference = 'Stop'

function Write-Section($text) {
    Write-Host "`n=== $text ===" -ForegroundColor Cyan
}

function Test-Cmd($name) {
    return [bool](Get-Command $name -ErrorAction SilentlyContinue)
}

function Get-WSLBinaryPath($name) {
    if (-not (Test-Cmd 'wsl')) {
        return $null
    }

    $distros = & wsl -l -q 2>$null
    if (-not $distros) {
        return $null
    }

    $distros = $distros | ForEach-Object { ($_ -replace "`0", '').Trim() } | Where-Object { $_ }

    $preferred = @('Ubuntu-24.04', 'Ubuntu-22.04', 'Ubuntu')
    $selected = $null
    foreach ($candidate in $preferred) {
        if ($distros -contains $candidate) {
            $selected = $candidate
            break
        }
    }
    if (-not $selected) {
        $ubuntuLike = $distros | Where-Object { $_ -like 'Ubuntu*' }
        if ($ubuntuLike) {
            $selected = ($ubuntuLike | Select-Object -First 1)
        }
    }
    if (-not $selected) {
        return $null
    }

    try {
        $resolved = & wsl -d $selected -e bash -lc "command -v $name" 2>$null
        if ($LASTEXITCODE -eq 0 -and -not [string]::IsNullOrWhiteSpace($resolved)) {
            return "wsl://$selected/$resolved"
        }
    } catch {
        return $null
    }

    return $null
}

function Resolve-BinaryPath($name) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue
    if ($cmd) {
        return $cmd.Source
    }

    if ($name -eq 'tshark') {
        $tsharkPath = 'C:/Program Files/Wireshark/tshark.exe'
        if (Test-Path $tsharkPath) {
            return $tsharkPath
        }
    }

    if ($name -eq 'qemu-img') {
        $fallback = Join-Path $env:USERPROFILE 'AppData/Local/Microsoft/WinGet/Packages/cloudbase.qemu-img_Microsoft.Winget.Source_8wekyb3d8bbwe/qemu-img.exe'
        if (Test-Path $fallback) {
            return $fallback
        }
    }

    if ($name -eq 'qemu-system-x86_64') {
        $qemuCandidates = @(
            'C:/Program Files/QEMU/qemu-system-x86_64.exe',
            'C:/Program Files/qemu/qemu-system-x86_64.exe',
            (Join-Path $env:LOCALAPPDATA 'Microsoft/WinGet/Packages/SoftwareFreedomConservancy.QEMU_Microsoft.Winget.Source_8wekyb3d8bbwe/qemu-system-x86_64.exe')
        )
        foreach ($candidate in $qemuCandidates) {
            if (Test-Path $candidate) {
                return $candidate
            }
        }
    }

    if ($name -eq 'virsh' -or $name -eq 'libvirtd') {
        $wslPath = Get-WSLBinaryPath $name
        if ($wslPath) {
            return $wslPath
        }
    }

    return $null
}

function Find-PythonExe {
    $candidates = @(
        "./venv/Scripts/python.exe",
        "./.venv/Scripts/python.exe",
        "python"
    )
    foreach ($c in $candidates) {
        if ($c -eq 'python') {
            if (Test-Cmd 'python') { return 'python' }
            continue
        }
        if (Test-Path $c) { return $c }
    }
    throw 'No Python executable found (expected ./venv/Scripts/python.exe or python on PATH).'
}

function Install-If-Winget($id, $name) {
    if (-not (Test-Cmd 'winget')) {
        Write-Warning "winget not found. Install $name manually."
        return $false
    }
    Write-Host "Installing $name ($id) via winget..."
    winget install --id $id --exact --silent --disable-interactivity --accept-package-agreements --accept-source-agreements
    if ($LASTEXITCODE -ne 0) {
        $installed = winget list --id $id --exact 2>$null
        if ($LASTEXITCODE -eq 0 -and $installed -and ($installed -join "`n") -match [regex]::Escape($id)) {
            Write-Host "$name already present; continuing." -ForegroundColor Yellow
            return $true
        }
        Write-Warning "winget install failed for $name (exit code $LASTEXITCODE)."
        return $false
    }
    return $true
}

function Install-QemuWithFallback {
    $qemuPackageIds = @(
        'SoftwareFreedomConservancy.QEMU',
        'WsSolInfor.Qemu'
    )

    foreach ($packageId in $qemuPackageIds) {
        $ok = Install-If-Winget $packageId 'QEMU'
        if ($ok) {
            return $true
        }
    }

    Write-Warning 'All automated QEMU install attempts failed. Install QEMU manually from qemu.org if qemu-system-x86_64 is required on Windows host.'
    return $false
}

Write-Section 'SWARMZ V5 live readiness setup'
Write-Host 'This script prepares host/runtime dependencies for live (non-mocked) V5 features.'

$pythonExe = Find-PythonExe
Write-Host "Using Python: $pythonExe"

if ($InstallPythonDeps) {
    Write-Section 'Installing Python dependencies'
    & $pythonExe -m pip install --upgrade pip
    & $pythonExe -m pip install playwright scapy pyshark
    & $pythonExe -m playwright install chromium --no-shell
} else {
    Write-Section 'Python dependencies (dry run)'
    Write-Host 'Run with -InstallPythonDeps to install: playwright, scapy, pyshark, chromium browser.'
}

if ($InstallSystemDeps) {
    Write-Section 'Installing system dependencies (Windows)'
    Install-If-Winget 'WiresharkFoundation.Wireshark' 'Wireshark (tshark + Npcap)'
    Install-QemuWithFallback | Out-Null

    Write-Host 'libvirt/virsh are not native on Windows. Use WSL2 + Ubuntu for libvirt stack if needed.' -ForegroundColor Yellow
} else {
    Write-Section 'System dependencies (dry run)'
    Write-Host 'Run with -InstallSystemDeps to attempt winget installs for Wireshark and QEMU.'
}

Write-Section 'Dependency checks'
$checks = @(
    'tshark',
    'qemu-system-x86_64',
    'qemu-img',
    'virsh',
    'libvirtd'
)

foreach ($bin in $checks) {
    $resolved = Resolve-BinaryPath $bin
    if ($resolved) {
        Write-Host "$bin = FOUND" -ForegroundColor Green
        Write-Host "  -> $resolved" -ForegroundColor DarkGray
    } else {
        Write-Host "$bin = MISSING" -ForegroundColor Red
    }
}

Write-Section 'Cloud credential variables (required for live VPN provisioner)'
$vars = @(
    'AWS_ACCESS_KEY_ID',
    'AWS_SECRET_ACCESS_KEY',
    'AWS_DEFAULT_REGION',
    'DO_TOKEN',
    'LINODE_TOKEN',
    'VULTR_API_KEY',
    'PLAYWRIGHT_BROWSERS_PATH'
)

foreach ($v in $vars) {
    $val = [Environment]::GetEnvironmentVariable($v)
    if ([string]::IsNullOrWhiteSpace($val)) {
        Write-Host "$v = MISSING" -ForegroundColor Red
    } else {
        Write-Host "$v = SET" -ForegroundColor Green
    }
}

Write-Section 'Example env setup (current shell)'
Write-Host '$env:DO_TOKEN="<your_token>"'
Write-Host '$env:LINODE_TOKEN="<your_token>"'
Write-Host '$env:VULTR_API_KEY="<your_token>"'
Write-Host '$env:PLAYWRIGHT_BROWSERS_PATH="0"'

if ($BootstrapWSL) {
    Write-Section 'WSL2 libvirt bootstrap'
    $bootstrapScript = Join-Path $PSScriptRoot 'SWARMZ_V5_WSL_LIBVIRT_BOOTSTRAP.ps1'
    if (Test-Path $bootstrapScript) {
        & $bootstrapScript -Apply
    } else {
        Write-Warning "Missing bootstrap script: $bootstrapScript"
    }
}

Write-Section 'Next step'
Write-Host 'After dependencies/vars are ready, run: python -m pytest tests/ -v --tb=short'
