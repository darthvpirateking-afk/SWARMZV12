#!/usr/bin/env pwsh
# run_weaver.ps1 – Create venv, install deps, run Weaver + VerificationRunner
# Usage: .\run_weaver.ps1 [-Loop] [-Interval 30]

param(
    [switch]$Loop,
    [int]$Interval = 30
)

Set-Location $PSScriptRoot

if (-not (Test-Path ".venv")) {
    Write-Host "Creating virtual environment..."
    python -m venv .venv
}

Write-Host "Installing dependencies..."
& .venv/Scripts/pip install -q -r requirements.txt

Write-Host ""
Write-Host "Starting Layer-Weaver..."
Write-Host ""

# Start verification runner in background
$verifyJob = Start-Job -ScriptBlock {
    Set-Location $using:PSScriptRoot
    & .venv/Scripts/python -m control_plane.layer_weaver.verification_runner --loop --interval 5
}

# Build args for weaver
$weaverArgs = @()
if ($Loop) {
    $weaverArgs += "--loop"
    $weaverArgs += "--interval"
    $weaverArgs += $Interval.ToString()
}

try {
    & .venv/Scripts/python -m control_plane.layer_weaver.weaver_service @weaverArgs
}
finally {
    Stop-Job $verifyJob -ErrorAction SilentlyContinue
    Remove-Job $verifyJob -ErrorAction SilentlyContinue
}
