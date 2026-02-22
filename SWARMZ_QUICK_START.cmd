@echo off
echo 🚀 SWARMZ Quick Start
echo ==================

:: Kill existing processes
echo 🔧 Cleaning port 8012...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8012.*LISTENING"') do (
    if not "%%p"=="" (
        taskkill /F /PID %%p >nul 2>&1
        echo    ✓ Killed process %%p
    )
)

:: Wait and start
timeout /t 2 /nobreak >nul
echo 🚀 Starting Enhanced SWARMZ...
echo    📡 Interface: http://localhost:8012
echo    🤖 Enhanced AI: ACTIVE
echo.

set PORT=8012
cd /d "%~dp0"
.venv\Scripts\python.exe run_server.py

pause