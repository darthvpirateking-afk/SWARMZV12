@echo off
setlocal enabledelayedexpansion

REM Find project root from script location
pushd "%~dp0"
cd ..\..\..\
set "ROOT=%CD%"
popd
cd /d "%ROOT%"

REM Verify we landed in the right place
if not exist "%ROOT%\requirements.txt" (
    echo [FAIL] Could not find project root. Expected requirements.txt in %ROOT%
    echo        Try running from the swarmz folder instead.
    pause
    exit /b 1
)

echo.
echo  SWARMZ ONE-BUTTON STARTUP
echo  ==========================
echo.

REM ── Startup mode ─────────────────────────────────────────────────────────
set "FAST_START=1"
if /I "%SWARMZ_FULL_BOOT%"=="1" set "FAST_START=0"
if /I "%~1"=="--full" set "FAST_START=0"

if "!FAST_START!"=="1" (
    echo [OK] Fast startup mode
) else (
    echo [OK] Full startup mode
)

REM ── Phase 1: Check Python ──────────────────────────────────────────────────
echo [..] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found. Install from https://python.org
    pause
    exit /b 1
)
echo [OK] Python found

REM ── Phase 1b: Check Node ───────────────────────────────────────────────────
echo [..] Checking Node.js...
set "SKIP_FRONTEND=0"
node --version >nul 2>&1
if errorlevel 1 (
    echo [WARN] Node.js not found - skipping frontend build
    set "SKIP_FRONTEND=1"
) else (
    echo [OK] Node.js found
)

REM ── Phase 2: Virtual environment ───────────────────────────────────────────
echo.
echo [..] Setting up virtual environment...
if not exist "%ROOT%\venv\Scripts\python.exe" (
    python -m venv "%ROOT%\venv"
    if errorlevel 1 (
        echo [FAIL] Could not create venv
        pause
        exit /b 1
    )
    echo [OK] Created venv
) else (
    echo [OK] venv already exists
)
set "PY=%ROOT%\venv\Scripts\python.exe"

REM ── Phase 2b: Bootstrap flags ─────────────────────────────────────────────
if not exist "%ROOT%\data" mkdir "%ROOT%\data"
set "BOOTSTRAP_FILE=%ROOT%\data\.swarmz_bootstrap_done"
set "DO_BOOTSTRAP=0"
if "!FAST_START!"=="0" set "DO_BOOTSTRAP=1"
if not exist "!BOOTSTRAP_FILE!" set "DO_BOOTSTRAP=1"
if /I "%SWARMZ_DRY_RUN%"=="1" set "DO_BOOTSTRAP=0"

if "!DO_BOOTSTRAP!"=="1" (
    echo [..] Bootstrap required
) else (
    echo [OK] Bootstrap already complete
)

REM ── Phase 3: Python deps ───────────────────────────────────────────────────
echo.
if "!DO_BOOTSTRAP!"=="1" (
    echo [..] Installing Python dependencies...
    "%PY%" -m pip install --upgrade pip --quiet 2>nul
    "%PY%" -m pip install -r "%ROOT%\requirements.txt" --quiet
    if errorlevel 1 (
        echo [FAIL] pip install failed
        pause
        exit /b 1
    )
    echo [OK] Python dependencies installed
) else (
    echo [OK] Skipping Python dependency install (fast mode)
)

REM ── Phase 4: Frontend build ────────────────────────────────────────────────
if "!SKIP_FRONTEND!"=="1" goto :after_frontend
if not exist "%ROOT%\frontend\package.json" goto :after_frontend

if "!DO_BOOTSTRAP!"=="1" (
    echo.
    echo [..] Building frontend...
    pushd "%ROOT%\frontend"
    call npm install --legacy-peer-deps
    if errorlevel 1 (
        popd
        echo [WARN] npm install failed - continuing without frontend
        goto :after_frontend
    )
    call npm run build
    if errorlevel 1 (
        popd
        echo [WARN] Frontend build failed - continuing anyway
        goto :after_frontend
    )
    popd
    echo [OK] Frontend built
) else (
    echo [OK] Skipping frontend install/build (fast mode)
)

:after_frontend

if "!DO_BOOTSTRAP!"=="1" (
    > "!BOOTSTRAP_FILE!" echo bootstrap_complete=1
)

REM ── Phase 5: Ollama ────────────────────────────────────────────────────────
echo.
echo [..] Checking Ollama...
curl -s -o nul -w "" http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    echo [..] Ollama not running, trying to start...
    where ollama >nul 2>&1
    if errorlevel 1 (
        echo [WARN] Ollama not found - skipping. Install from https://ollama.ai
        goto :after_ollama
    )
    start "" /B ollama serve
    echo [..] Waiting for Ollama...
    timeout /t 5 /nobreak >nul
)
echo [OK] Ollama checked
if "!DO_BOOTSTRAP!"=="1" (
    curl -s http://localhost:11434/api/tags 2>nul | findstr /i "llama3.1" >nul 2>&1
    if errorlevel 1 (
        echo [..] Pulling llama3.1:8b-instruct-q5_K_M - this may take a while...
        ollama pull llama3.1:8b-instruct-q5_K_M
    )
) else (
    echo [OK] Skipping Ollama model pull (fast mode)
)

:after_ollama

REM ── Phase 6: Kill port if busy ─────────────────────────────────────────────
echo.
if /I "%KILL_PORT%"=="1" (
    for /f "tokens=5" %%p in ('netstat -ano 2^>nul ^| findstr ":8012 " ^| findstr "LISTENING"') do (
        echo [..] Port 8012 busy - killing PID %%p...
        taskkill /PID %%p /F >nul 2>&1
        timeout /t 1 /nobreak >nul
    )
) else (
    echo [OK] Port cleanup skipped
)

if /I "%SWARMZ_DRY_RUN%"=="1" goto :dry_run_done

REM ── Phase 7: Start everything ──────────────────────────────────────────────
echo.
echo  ============================================
echo   LOCAL: http://127.0.0.1:8012
echo  ============================================
echo.

if exist "%ROOT%\swarm_runner.py" (
    echo [OK] Starting mission runner...
    start "" /B "%PY%" "%ROOT%\swarm_runner.py"
)

echo [OK] Opening browser...
start "" http://127.0.0.1:8012

echo [OK] Starting server...
echo.
if exist "%ROOT%\run_server.py" (
    "%PY%" "%ROOT%\run_server.py" --host 0.0.0.0 --port 8012
) else (
    "%PY%" -m uvicorn swarmz_server:app --host 0.0.0.0 --port 8012
)

pause
exit /b 0

:dry_run_done
echo [OK] Dry run complete - startup checks passed
exit /b 0
