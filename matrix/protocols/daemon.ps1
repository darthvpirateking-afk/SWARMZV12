param(
    [string]$Host = "0.0.0.0",
    [int]$Port = 8012,
    [switch]$Register
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$dataDir = Join-Path $Root "data"
if (-not (Test-Path $dataDir)) { New-Item -ItemType Directory -Path $dataDir | Out-Null }
$log = Join-Path $dataDir "daemon.log"

function Write-Log($msg) {
    $stamp = "[{0:yyyy-MM-dd HH:mm:ss}]" -f (Get-Date)
    "$stamp $msg" | Tee-Object -FilePath $log -Append
}

if ($Register) {
    $action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$Root\SWARMZ_DAEMON_UP.ps1`""
    $trigger = New-ScheduledTaskTrigger -AtLogOn
    Register-ScheduledTask -TaskName "SWARMZ_DAEMON" -Action $action -Trigger $trigger -Description "Start SWARMZ daemon at logon" -Force
    Write-Log "Scheduled task SWARMZ_DAEMON registered."
    return
}

# Try to derive host/port from config if present
$configPath = Join-Path $Root "config\runtime.json"
if (Test-Path $configPath) {
    try {
        $cfg = Get-Content $configPath | ConvertFrom-Json
        $apiUrl = $cfg.apiBaseUrl
        if (-not $apiUrl -and $cfg.api_base) { $apiUrl = $cfg.api_base }
        if ($cfg.bind) { $Host = $cfg.bind }
        if ($cfg.port) { $Port = [int]$cfg.port }
        if ($apiUrl) {
            $uri = [uri]$apiUrl
            if ($uri.Port) { $Port = $uri.Port }
            if ($uri.Host) { $Host = $uri.Host }
        }
        if ($cfg.offlineMode) { $env:OFFLINE_MODE = "1" }
    } catch {
        Write-Log "Could not parse runtime.json: $_"
    }
}

Write-Log "Daemon starting (host=$Host port=$Port). Log=$log"

while ($true) {
    Write-Log "Running doctor..."
    try {
        python "$Root\tools\swarmz_doctor.py" >> $log 2>&1
    } catch {
        Write-Log "Doctor failed: $_"
    }

    Write-Log "Launching server..."
    try {
        python "$Root\run_server.py" --port $Port --host $Host >> $log 2>&1
    } catch {
        Write-Log "Server process crashed: $_"
    }

    Write-Log "Process exited with code $LASTEXITCODE. Restarting in 3s..."
    Start-Sleep -Seconds 3
}
