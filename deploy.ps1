#!/usr/bin/env pwsh
# NEXUSMON One-Click Deploy Script -- Render Edition

param(
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Write-Host "============================================" -ForegroundColor Cyan
Write-Host "  NEXUSMON Render Deploy" -ForegroundColor Cyan
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
    git add render.yaml requirements.txt swarmz_server.py
    git commit -m "chore: update Render deploy config" --allow-empty
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

# -- Render deploy instructions -----------------------------------
Write-Host "`n[4/4] Render Setup" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Your repo is ready for Render. Connect it now:" -ForegroundColor White
Write-Host ""
Write-Host "  1. Go to  https://dashboard.render.com" -ForegroundColor White
Write-Host "  2. Click  New + and choose Blueprint" -ForegroundColor White
Write-Host "  3. Select  darthvpirateking-afk/NEXUSMON" -ForegroundColor White
Write-Host "  4. Render auto-detects render.yaml" -ForegroundColor White
Write-Host "  5. Confirm service settings and deploy" -ForegroundColor White
Write-Host "  6. (Optional) Add ANTHROPIC_API_KEY in Environment" -ForegroundColor White
Write-Host ""
Write-Host "  Health check:  /v1/health" -ForegroundColor White
Write-Host "  Cockpit:       /nexusmon_cockpit.html" -ForegroundColor White
Write-Host "  API docs:      /docs" -ForegroundColor White
Write-Host ""

# -- Open Render dashboard ----------------------------------------
$open = Read-Host "Open Render dashboard now? (y/n)"
if ($open -eq 'y') {
    Start-Process "https://dashboard.render.com"
}

Pop-Location
Write-Host ""
Write-Host "Done. Render auto-deploys on every push." -ForegroundColor Green