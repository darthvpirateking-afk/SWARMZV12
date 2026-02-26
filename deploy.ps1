#!/usr/bin/env pwsh
# NEXUSMON One-Click Deploy Script

Write-Host "🚀 NEXUSMON Deployment Script" -ForegroundColor Cyan

# Test local build first
Write-Host "📦 Testing frontend build..." -ForegroundColor Yellow
Set-Location frontend
npm run build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Frontend build failed!" -ForegroundColor Red
    exit 1
}

Write-Host "✅ Frontend build successful!" -ForegroundColor Green

# Check if backend works
Set-Location ..
Write-Host "🔍 Testing backend..." -ForegroundColor Yellow
$response = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue

if ($response.status -eq "ok") {
    Write-Host "✅ Backend is running!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Backend not running. Start with: python swarmz_server.py" -ForegroundColor Yellow
}

# Deploy options
Write-Host "`n🌍 Deployment Options:" -ForegroundColor Cyan
Write-Host "1. Deploy frontend to Vercel (recommended)"
Write-Host "2. Deploy backend to Render.com"
Write-Host "3. Both (full stack)"

$choice = Read-Host "Choose option (1-3)"

switch ($choice) {
    "1" {
        Write-Host "🚀 Deploying to Vercel..." -ForegroundColor Cyan
        Set-Location frontend
        If (Get-Command vercel -ErrorAction SilentlyContinue) {
            vercel --prod
        } Else {
            Write-Host "📦 Installing Vercel CLI..." -ForegroundColor Yellow
            npm install -g vercel
            vercel --prod
        }
    }
    "2" {
        Write-Host "📋 Backend deploy instructions:" -ForegroundColor Cyan
        Write-Host "1. Go to render.com and connect GitHub repo"
        Write-Host "2. Create Web Service"
        Write-Host "3. Build: pip install -r requirements.txt"
        Write-Host "4. Start: python swarmz_server.py"
        Write-Host "5. Port: 8000"
    }
    "3" {
        Write-Host "🌟 Full stack deploy!" -ForegroundColor Cyan
        Write-Host "Frontend: Deploying to Vercel..."
        Set-Location frontend
        If (Get-Command vercel -ErrorAction SilentlyContinue) {
            vercel --prod
        } Else {
            npm install -g vercel
            vercel --prod
        }
        Write-Host "Backend: Follow Render.com instructions above"
    }
}

Write-Host "`n✨ Deployment complete! Your NEXUSMON is ready." -ForegroundColor Green