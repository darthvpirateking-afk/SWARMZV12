#!/usr/bin/env pwsh
# NEXUSMON One-Click Deploy Script -- Railway Edition

param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NEXUSMON Railway Deploy" -ForegroundColor Cyan
Write-Host "============================================" -ForegroundColor Cyan

# -- Pre-flight checks --------------------------------------------
if (-not $SkipTests) {
    Write-Host "`n[1/4] Health-checking backend..." -ForegroundColor Yellow
    try {
        $r = Invoke-RestMethod -Uri "http://localhost:8000/v1/health" -TimeoutSec 3 -ErrorAction Stop
        Write-Host "  Backend OK ($($r.status))" -ForegroundColor Green
    } catch {
        Write-Host "  Backend not running locally (fine for remote deploy)" -ForegroundColor DarkYellow
    }
}

# -- Git status ---------------------------------------------------
Write-Host "`n[2/4] Checking git status..." -ForegroundColor Yellow
Push-Location $root
$dirty = git status --porcelain
if ($dirty) {
    Write-Host "  Uncommitted changes found -- committing..." -ForegroundColor DarkYellow
    git add railway.json nixpacks.toml Procfile requirements.txt swarmz_server.py
    git commit -m "chore: update Railway deploy config" --allow-empty
}
$branch = git rev-parse --abbrev-ref HEAD
Write-Host "  Branch: $branch" -ForegroundColor Green

# -- Push to GitHub -----------------------------------------------
Write-Host "`n[3/4] Pushing to GitHub..." -ForegroundColor Yellow
git push origin $branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "  git push failed!" -ForegroundColor Red
    Pop-Location
    exit 1
}
Write-Host "  Pushed." -ForegroundColor Green

# -- Railway deploy instructions ----------------------------------
Write-Host "`n[4/4] Railway Setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Your repo is ready for Railway. Connect it now:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Go to  https://railway.app/new" -ForegroundColor White
Write-Host "  2. Click  Deploy from GitHub Repo" -ForegroundColor White
Write-Host "  3. Select  darthvpirateking-afk/NEXUSMON" -ForegroundColor White
Write-Host "  4. Railway auto-detects railway.json" -ForegroundColor White
Write-Host "  5. PORT is set automatically" -ForegroundColor White
Write-Host "  6. (Optional) Add ANTHROPIC_API_KEY in Variables tab" -ForegroundColor White
Write-Host ""
Write-Host "  Health check:  /v1/health" -ForegroundColor White
Write-Host "  Cockpit:       /web/index.html" -ForegroundColor White
Write-Host "  API docs:      /docs" -ForegroundColor White
Write-Host ""

# -- Open Railway dashboard ---------------------------------------
$open = Read-Host "Open Railway dashboard now? (y/n)"
if ($open -eq 'y') {
    Start-Process "https://railway.app/new"
}

Pop-Location
Write-Host ""
Write-Host "Done. Railway auto-deploys on every push." -ForegroundColor Green