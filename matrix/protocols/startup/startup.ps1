#!/usr/bin/env pwsh
# =============================================================================
# SWARMZ ONE-BUTTON STARTUP
# Full initialization and launch of all SWARMZ components
# Usage: .\startup.ps1 [--skip-browser] [--skip-ollama] [--force-kill]
#                      [--verbose] [--port 8012] [--no-frontend-build]
#                      [--check-only]
# =============================================================================

param(
    [switch]$SkipBrowser,
    [switch]$SkipOllama,
    [switch]$ForcKill,
    [switch]$Verbose,
    [switch]$NoFrontendBuild,
    [switch]$CheckOnly,
    [int]$Port = 0
)

# Also parse raw args for --force-kill (camel case variant)
$rawArgs = $MyInvocation.UnboundArguments + $args
$ForcKill = $ForcKill -or ($rawArgs -contains "--force-kill") -or ($env:KILL_PORT -eq "1")
$SkipBrowser = $SkipBrowser -or ($rawArgs -contains "--skip-browser")
$SkipOllama = $SkipOllama -or ($rawArgs -contains "--skip-ollama")
$Verbose = $Verbose -or ($rawArgs -contains "--verbose")
$NoFrontendBuild = $NoFrontendBuild -or ($rawArgs -contains "--no-frontend-build")
$CheckOnly = $CheckOnly -or ($rawArgs -contains "--check-only")

$ErrorActionPreference = "Stop"
$SWARMZ_ROOT = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $PSScriptRoot))
Set-Location $SWARMZ_ROOT

# ── Dot-source logging library ──────────────────────────────────────────────
. "$PSScriptRoot\lib\startup-logging.ps1"
$script:VerboseOutput = $Verbose
$startTime = Get-Date

# ── Load startup config ──────────────────────────────────────────────────────
$startupConfig = @{
    port                     = 8012
    host                     = "0.0.0.0"
    ollamaModel              = "llama3.1:8b-instruct-q5_K_M"
    ollamaEndpoint           = "http://localhost:11434"
    serverReadinessTimeout   = 30
    healthCheckPath          = "/health"
}

$startupJsonPath = "$PSScriptRoot\config\startup.json"
if (Test-Path $startupJsonPath) {
    try {
        $cfg = Get-Content $startupJsonPath -Raw | ConvertFrom-Json
        if ($cfg.server.port)                   { $startupConfig.port                   = [int]$cfg.server.port }
        if ($cfg.server.host)                   { $startupConfig.host                   = $cfg.server.host }
        if ($cfg.ollama.model)                  { $startupConfig.ollamaModel            = $cfg.ollama.model }
        if ($cfg.ollama.endpoint)               { $startupConfig.ollamaEndpoint         = $cfg.ollama.endpoint }
        if ($cfg.timeouts.server_readiness)     { $startupConfig.serverReadinessTimeout = [int]$cfg.timeouts.server_readiness }
        if ($cfg.server.health_check_path)      { $startupConfig.healthCheckPath        = $cfg.server.health_check_path }
        Log-Debug "Loaded startup.json configuration"
    } catch {
        Log-Warn "Could not parse startup.json, using defaults"
    }
}

# Load runtime.json overrides
$runtimeJson = Join-Path $SWARMZ_ROOT "config\runtime.json"
if (Test-Path $runtimeJson) {
    try {
        $rt = Get-Content $runtimeJson -Raw | ConvertFrom-Json
        if (-not $env:PORT -and $rt.port)  { $startupConfig.port = [int]$rt.port }
        if (-not $env:HOST -and $rt.bind)  { $startupConfig.host = [string]$rt.bind }
        if ($rt.offlineMode)               { $env:OFFLINE_MODE = "1" }
        Log-Debug "Loaded config/runtime.json"
    } catch {
        Log-Warn "Could not parse config/runtime.json"
    }
}

# Env and arg overrides
if ($env:PORT)        { $startupConfig.port = [int]$env:PORT }
if ($env:HOST)        { $startupConfig.host = $env:HOST }
if ($Port -gt 0)      { $startupConfig.port = $Port }

$Port     = $startupConfig.port
$HostBind = $startupConfig.host

# ── Track failed phases (non-fatal) ─────────────────────────────────────────
$warnings = @{}

# =============================================================================
# BANNER
# =============================================================================
Write-Host ""
Write-Host "  ____  _      __   _    ____  __  __ ______" -ForegroundColor Cyan
Write-Host " / ___`|/ \    / /  / \  / __ \/ / / //___  /" -ForegroundColor Cyan
Write-Host " \___ / / \  / /  / _ \/ /_/ / /_/ /   / /" -ForegroundColor Cyan
Write-Host " ___/ / / /\/ /  / /_\ \ _, _/ __  /  / /__" -ForegroundColor Cyan
Write-Host "/____/ /_/  \_/ /_/   \_\_/ \_\_/ /_/ /____/" -ForegroundColor Cyan
Write-Host ""
Write-Host "  ONE-BUTTON STARTUP  |  Port: $Port  |  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor DarkCyan
Write-Host ""

if ($CheckOnly) {
    Write-Host "  [CHECK-ONLY MODE — no services will be started]" -ForegroundColor Yellow
    Write-Host ""
}

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

function Find-Python {
    foreach ($cmd in @("python3", "python")) {
        try {
            $ver = & $cmd --version 2>&1
            if ($LASTEXITCODE -eq 0 -and $ver -match "Python (\d+)\.(\d+)") {
                $major = [int]$Matches[1]
                $minor = [int]$Matches[2]
                if ($major -gt 3 -or ($major -eq 3 -and $minor -ge 11)) {
                    Log-Debug "Found Python $major.$minor at: $cmd"
                    return $cmd
                }
            }
        } catch {}
    }
    return $null
}

function Get-LanIp {
    try {
        $udp = New-Object System.Net.Sockets.UdpClient
        $udp.Connect("8.8.8.8", 53)
        $ip = $udp.Client.LocalEndPoint.Address.ToString()
        $udp.Close()
        return $ip
    } catch { return $null }
}

function Get-ListeningPid($port) {
    $lines = netstat -ano | Select-String -Pattern (":$port\s") | Select-String "LISTENING"
    foreach ($l in $lines) {
        $parts = ($l.Line -split "\s+") | Where-Object { $_ -ne "" }
        if ($parts.Count -ge 5) {
            $pid = $parts[-1]
            if ($pid -match "^\d+$") { return [int]$pid }
        }
    }
    return $null
}

function Test-OllamaRunning {
    try {
        $req = [System.Net.HttpWebRequest]::Create("$($startupConfig.ollamaEndpoint)/api/tags")
        $req.Timeout = 2000
        $resp = $req.GetResponse()
        $resp.Close()
        return $true
    } catch { return $false }
}

function Get-OllamaModels {
    try {
        $req = [System.Net.HttpWebRequest]::Create("$($startupConfig.ollamaEndpoint)/api/tags")
        $req.Timeout = 3000
        $resp = $req.GetResponse()
        $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
        $body = $reader.ReadToEnd()
        $reader.Close()
        $resp.Close()
        $json = $body | ConvertFrom-Json
        return @($json.models | ForEach-Object { $_.name })
    } catch { return @() }
}

function Find-OllamaExe {
    $candidates = @(
        "$env:PROGRAMFILES\Ollama\ollama.exe",
        "$env:LOCALAPPDATA\Programs\Ollama\ollama.exe",
        "$env:USERPROFILE\AppData\Local\Programs\Ollama\ollama.exe"
    )
    foreach ($path in $candidates) {
        if (Test-Path $path) { return $path }
    }
    # Check PATH
    try {
        $found = (Get-Command "ollama" -ErrorAction SilentlyContinue).Source
        if ($found) { return $found }
    } catch {}
    return $null
}

function Wait-ServerReady($port, $path, $timeoutSec) {
    $url = "http://127.0.0.1:$port$path"
    $deadline = (Get-Date).AddSeconds($timeoutSec)
    $attempts = 0
    while ((Get-Date) -lt $deadline) {
        try {
            $req = [System.Net.HttpWebRequest]::Create($url)
            $req.Timeout = 1500
            $resp = $req.GetResponse()
            $resp.Close()
            return $true
        } catch {}
        Start-Sleep -Milliseconds 1000
        $attempts++
        if ($attempts % 5 -eq 0) {
            Log-Debug "Still waiting for server ($attempts s)..."
        }
    }
    return $false
}

# =============================================================================
# PHASE 1: ENVIRONMENT CHECKS
# =============================================================================
Log-Phase "PHASE 1: Environment Validation"

# Python
$pythonCmd = Find-Python
if (-not $pythonCmd) {
    Log-ErrorWithRemediation "Python 3.11+ not found in PATH" `
        "Install Python 3.11 or higher" `
        "winget install Python.Python.3.11"
    exit 1
}
$pyVerStr = (& $pythonCmd --version 2>&1)
Log-Success "Python found: $pyVerStr ($pythonCmd)"

# Node.js
$nodeVersion = $null
try {
    $nodeVersion = (& node --version 2>&1)
    if ($LASTEXITCODE -ne 0) { $nodeVersion = $null }
} catch { $nodeVersion = $null }

if (-not $nodeVersion) {
    if ($NoFrontendBuild) {
        Log-Warn "Node.js not found — skipping frontend build (--no-frontend-build active)"
        $NoFrontendBuild = $true
    } else {
        Log-ErrorWithRemediation "Node.js not found in PATH" `
            "Install Node.js 16 or higher" `
            "winget install OpenJS.NodeJS.LTS"
        exit 1
    }
} else {
    Log-Success "Node.js found: $nodeVersion"
}

# npm
if (-not $NoFrontendBuild) {
    $npmVersion = $null
    try {
        $npmVersion = (& npm --version 2>&1)
        if ($LASTEXITCODE -ne 0) { $npmVersion = $null }
    } catch { $npmVersion = $null }

    if (-not $npmVersion) {
        Log-ErrorWithRemediation "npm not found" "Reinstall Node.js (npm ships with it)" "winget install OpenJS.NodeJS.LTS"
        exit 1
    }
    Log-Success "npm found: v$npmVersion"
}

if ($CheckOnly) {
    Log-Success "Environment validation complete (check-only mode)"
    exit 0
}

# =============================================================================
# PHASE 2: VIRTUAL ENVIRONMENT SETUP
# =============================================================================
Log-Phase "PHASE 2: Python Virtual Environment"

$venvDir = Join-Path $SWARMZ_ROOT "venv"
$venvPy  = Join-Path $venvDir "Scripts\python.exe"

if (Test-Path $venvPy) {
    Log-Info "Existing venv found at: $venvDir"
} else {
    Log-Info "Creating virtual environment..."
    try {
        & $pythonCmd -m venv $venvDir
        if ($LASTEXITCODE -ne 0) { throw "venv creation returned exit code $LASTEXITCODE" }
    } catch {
        Log-ErrorWithRemediation "Failed to create virtual environment: $_" `
            "Try: python -m pip install virtualenv, then re-run" `
            "python -m venv venv"
        exit 1
    }
}

if (-not (Test-Path $venvPy)) {
    Log-ErrorWithRemediation "venv python.exe missing after creation" `
        "Delete the venv\ folder and re-run startup.ps1" `
        "Remove-Item -Recurse -Force venv"
    exit 1
}

Log-Success "Virtual environment ready: $venvPy"

# =============================================================================
# PHASE 3: PYTHON DEPENDENCIES
# =============================================================================
Log-Phase "PHASE 3: Python Dependencies"

$requirementsTxt = Join-Path $SWARMZ_ROOT "requirements.txt"
if (-not (Test-Path $requirementsTxt)) {
    Log-Warn "requirements.txt not found — skipping pip install"
    $warnings["Phase3-Deps"] = "requirements.txt not found"
} else {
    Log-Info "Upgrading pip..."
    & $venvPy -m pip install --upgrade pip --quiet 2>$null | Out-Null

    Log-Info "Installing Python dependencies (this may take a few minutes)..."
    & $venvPy -m pip install -r $requirementsTxt --quiet
    if ($LASTEXITCODE -ne 0) {
        Log-ErrorWithRemediation "pip install failed" `
            "Check your internet connection and try again" `
            "& venv\Scripts\python.exe -m pip install -r requirements.txt"
        exit 1
    }
    Log-Success "Python dependencies installed"
}

# =============================================================================
# PHASE 4: FRONTEND BUILD
# =============================================================================
if (-not $NoFrontendBuild) {
    Log-Phase "PHASE 4: Frontend Build (npm)"

    $frontendDir = Join-Path $SWARMZ_ROOT "frontend"
    if (-not (Test-Path "$frontendDir\package.json")) {
        Log-Warn "frontend/package.json not found — skipping frontend build"
        $warnings["Phase4-Frontend"] = "frontend/package.json not found"
    } else {
        Push-Location $frontendDir

        Log-Info "Installing npm packages..."
        & npm install --legacy-peer-deps
        if ($LASTEXITCODE -ne 0) {
            Pop-Location
            Log-ErrorWithRemediation "npm install failed" `
                "Check Node.js version (need 16+) and internet connection" `
                "cd frontend && npm install"
            exit 1
        }

        Log-Info "Building production bundle (TypeScript + Vite)..."
        & npm run build
        if ($LASTEXITCODE -ne 0) {
            Pop-Location
            Log-ErrorWithRemediation "npm run build failed" `
                "Check for TypeScript errors in the frontend source" `
                "cd frontend && npm run build"
            exit 1
        }

        Pop-Location

        $distDir = Join-Path $frontendDir "dist"
        if (Test-Path $distDir) {
            $distSizeBytes = (Get-ChildItem $distDir -Recurse -File | Measure-Object -Property Length -Sum).Sum
            $distSizeMB = [math]::Round($distSizeBytes / 1MB, 1)
            Log-Success "Frontend built: $distDir ($distSizeMB MB)"
        } else {
            Log-Warn "dist/ directory not found after build — frontend may not serve correctly"
            $warnings["Phase4-Dist"] = "dist/ directory not created by npm run build"
        }
    }
} else {
    Log-Info "Skipping frontend build (--no-frontend-build)"
}

# =============================================================================
# PHASE 5: COLD-START / DATABASE INIT
# =============================================================================
Log-Phase "PHASE 5: Database Initialization"

$dataDir = Join-Path $SWARMZ_ROOT "data"
if (-not (Test-Path $dataDir)) {
    New-Item -ItemType Directory -Path $dataDir | Out-Null
    Log-Info "Created data/ directory"
}

# Try Python cold-start if module exists
$coldStartCheck = & $venvPy -c "import importlib.util; print('ok' if importlib.util.find_spec('core.cold_start') is not None else 'skip')" 2>$null
if ($coldStartCheck -eq "ok") {
    Log-Info "Running cold-start initialization..."
    try {
        & $venvPy -c "from core.cold_start import ensure_cold_start; ensure_cold_start()" 2>$null
        Log-Success "Cold-start initialization complete"
    } catch {
        Log-Warn "Cold-start failed (non-fatal): $_"
        $warnings["Phase5-ColdStart"] = "cold_start module failed to run"
    }
} else {
    Log-Info "No cold_start module found — using data/ directory as-is"
}

# =============================================================================
# PHASE 6: OLLAMA SERVICE
# =============================================================================
if (-not $SkipOllama) {
    Log-Phase "PHASE 6: Ollama LLM Service"

    $ollamaRunning = Test-OllamaRunning

    if ($ollamaRunning) {
        Log-Success "Ollama already running at $($startupConfig.ollamaEndpoint)"
    } else {
        Log-Info "Ollama not detected — searching for installation..."
        $ollamaExe = Find-OllamaExe

        if ($ollamaExe) {
            Log-Info "Found Ollama at: $ollamaExe"
            Log-Info "Starting Ollama service..."
            Start-Process -FilePath $ollamaExe -ArgumentList "serve" -WindowStyle Hidden
            Log-Debug "Waiting for Ollama to become ready..."

            $ollamaReady = $false
            for ($i = 0; $i -lt 15; $i++) {
                Start-Sleep -Seconds 1
                if (Test-OllamaRunning) { $ollamaReady = $true; break }
                Log-Debug "Waiting for Ollama... ($($i+1)/15)"
            }

            if ($ollamaReady) {
                Log-Success "Ollama started successfully"
                $ollamaRunning = $true
            } else {
                Log-Warn "Ollama started but not responding after 15 seconds"
                $warnings["Phase6-Ollama"] = "Ollama started but not responding"
            }
        } else {
            Log-Warn "Ollama not installed — AI will use online providers (Anthropic/OpenAI) if configured"
            Log-Info "  Install Ollama from: https://ollama.ai"
            $warnings["Phase6-Ollama"] = "Ollama not installed"
        }
    }

    # Model verification
    if ($ollamaRunning) {
        $targetModel = $startupConfig.ollamaModel
        $models = Get-OllamaModels
        $modelFound = $models | Where-Object { $_ -like "$targetModel*" }

        if ($modelFound) {
            Log-Success "Model ready: $targetModel"
        } else {
            Log-Info "Model '$targetModel' not found — downloading now..."
            Log-Info "This may take several minutes (3-4 GB download)..."

            try {
                $pullBody = "{`"name`":`"$targetModel`"}"
                $pullBytes = [System.Text.Encoding]::UTF8.GetBytes($pullBody)

                $req = [System.Net.HttpWebRequest]::Create("$($startupConfig.ollamaEndpoint)/api/pull")
                $req.Method = "POST"
                $req.ContentType = "application/json"
                $req.ContentLength = $pullBytes.Length
                $req.Timeout = 600000  # 10 minutes

                $stream = $req.GetRequestStream()
                $stream.Write($pullBytes, 0, $pullBytes.Length)
                $stream.Close()

                $resp = $req.GetResponse()
                $reader = New-Object System.IO.StreamReader($resp.GetResponseStream())
                $lastStatus = ""
                while (-not $reader.EndOfStream) {
                    $line = $reader.ReadLine()
                    if ($line) {
                        try {
                            $obj = $line | ConvertFrom-Json
                            $status = $obj.status
                            if ($status -and $status -ne $lastStatus) {
                                if ($obj.completed -and $obj.total) {
                                    $pct = [math]::Round(100.0 * $obj.completed / $obj.total)
                                    Log-Progress "Pulling model: $status" $pct
                                } else {
                                    Log-Info "  $status"
                                }
                                $lastStatus = $status
                            }
                        } catch {}
                    }
                }
                $reader.Close()
                $resp.Close()
                Log-Success "Model '$targetModel' downloaded successfully"
            } catch {
                Log-Warn "Model download failed: $_ — AI will use online providers"
                $warnings["Phase6-Model"] = "Model download failed"
            }
        }
    }
} else {
    Log-Info "Skipping Ollama (--skip-ollama)"
}

# =============================================================================
# PHASE 7: PORT CHECK
# =============================================================================
Log-Phase "PHASE 7: Port Availability ($Port)"

$listeningPid = Get-ListeningPid $Port

if ($listeningPid) {
    $procName = try { (Get-Process -Id $listeningPid -ErrorAction SilentlyContinue).Name } catch { "unknown" }
    Log-Warn "Port $Port is already in use by PID $listeningPid ($procName)"

    if ($ForcKill) {
        Log-Info "Force-killing PID $listeningPid..."
        try {
            Stop-Process -Id $listeningPid -Force
            Start-Sleep -Seconds 2
            $pid2 = Get-ListeningPid $Port
            if ($pid2) {
                Log-ErrorWithRemediation "Port $Port still occupied by PID $pid2 after kill" `
                    "Manually kill the process and retry" `
                    "Stop-Process -Id $pid2 -Force"
                exit 1
            }
            Log-Success "Port $Port freed"
        } catch {
            Log-ErrorWithRemediation "Failed to kill PID $listeningPid: $_" `
                "Run as Administrator or manually kill the process" `
                "Stop-Process -Id $listeningPid -Force"
            exit 1
        }
    } else {
        Log-ErrorWithRemediation "Port $Port is occupied by '$procName' (PID $listeningPid)" `
            "Re-run with --force-kill to auto-kill, or free the port manually" `
            ".\startup.ps1 --force-kill"
        exit 1
    }
} else {
    Log-Success "Port $Port is available"
}

# =============================================================================
# PHASE 8: SERVER STARTUP
# =============================================================================
Log-Phase "PHASE 8: Starting SWARMZ Server"

# LAN IP
$lanIp = Get-LanIp
$localUrl = "http://127.0.0.1:$Port"
$lanUrl   = if ($lanIp) { "http://${lanIp}:$Port" } else { $null }

# Display URLs before launch
Log-Info "Access URLs:"
Write-Host "  LOCAL: $localUrl" -ForegroundColor Green
if ($lanUrl) {
    Write-Host "  LAN:   $lanUrl" -ForegroundColor Green
}
if ($env:OFFLINE_MODE -eq "1") {
    Write-Host "  [OFFLINE MODE enabled]" -ForegroundColor Yellow
}
Write-Host ""

# Start NEXUSMON swarm runner as background process
$swarmRunnerPath = Join-Path $SWARMZ_ROOT "swarm_runner.py"
if (Test-Path $swarmRunnerPath) {
    Log-Info "Starting NEXUSMON mission runner (background daemon)..."
    $runnerProcess = Start-Process -FilePath $venvPy -ArgumentList $swarmRunnerPath `
        -WindowStyle Hidden -PassThru
    Log-Success "NEXUSMON runner started (PID $($runnerProcess.Id))"
} else {
    Log-Warn "swarm_runner.py not found — mission runner not started"
    $warnings["Phase8-Runner"] = "swarm_runner.py not found"
}

# Register Ctrl+C cleanup handler
$runnerPid = if ($runnerProcess) { $runnerProcess.Id } else { $null }
Register-EngineEvent PowerShell.Exiting -Action {
    if ($runnerPid) {
        try { Stop-Process -Id $runnerPid -Force -ErrorAction SilentlyContinue } catch {}
    }
} | Out-Null

# Launch browser in background thread (will poll until server ready)
if (-not $SkipBrowser) {
    $browserJob = Start-Job -ScriptBlock {
        param($url, $healthPath, $timeout)
        $deadline = (Get-Date).AddSeconds($timeout)
        while ((Get-Date) -lt $deadline) {
            try {
                $req = [System.Net.HttpWebRequest]::Create("$url$healthPath")
                $req.Timeout = 1500
                $resp = $req.GetResponse()
                $resp.Close()
                Start-Process $url
                break
            } catch {}
            Start-Sleep -Milliseconds 1000
        }
    } -ArgumentList $localUrl, $startupConfig.healthCheckPath, $startupConfig.serverReadinessTimeout
    Log-Debug "Browser launcher job started (job $($browserJob.Id))"
}

# Print startup report before handing off to server
$totalElapsed = [math]::Round(((Get-Date) - $startTime).TotalSeconds, 1)
Log-Separator
Write-Host "  Setup complete in ${totalElapsed}s — launching server..." -ForegroundColor Cyan
Log-Separator

if ($warnings.Count -gt 0) {
    Write-Host ""
    Write-Host "  Non-fatal warnings:" -ForegroundColor Yellow
    foreach ($w in $warnings.GetEnumerator()) {
        Write-Host "    ⚠  $($w.Key): $($w.Value)" -ForegroundColor Yellow
    }
}
Write-Host ""

# ── Launch server (foreground — blocks until Ctrl+C) ────────────────────────
$runServerPath = Join-Path $SWARMZ_ROOT "run_server.py"
$swarmzServerPath = Join-Path $SWARMZ_ROOT "swarmz_server.py"

if (Test-Path $runServerPath) {
    Log-Success "Starting via run_server.py"
    & $venvPy $runServerPath --host $HostBind --port $Port
    exit $LASTEXITCODE
}

if (Test-Path $swarmzServerPath) {
    Log-Success "Starting via uvicorn swarmz_server:app"
    & $venvPy -m uvicorn swarmz_server:app --host $HostBind --port $Port
    exit $LASTEXITCODE
}

Log-ErrorWithRemediation "Neither run_server.py nor swarmz_server.py found" `
    "Ensure your SWARMZ server entry point exists in the project root" `
    "Expected: run_server.py or swarmz_server.py"
exit 1
