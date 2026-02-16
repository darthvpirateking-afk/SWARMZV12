@echo off
REM SWARMZ_UP.cmd – Start SWARMZ in AUTO mode (AUTO=1)
setlocal enabledelayedexpansion

echo ============================================
echo   SWARMZ – AUTO MODE STARTUP
echo ============================================
echo.

set AUTO=1
set TICK_INTERVAL=30
if "%OFFLINE_MODE%"=="" set OFFLINE_MODE=0
set HOST=0.0.0.0
set PORT=8012
set BASE_URL=http://localhost:8012

REM Locate Python
set PYTHON_CMD=
for %%p in (python3 python) do (
    %%p --version >nul 2>&1
    if !errorlevel! equ 0 (
        set PYTHON_CMD=%%p
        goto :found
    )
)
echo [ERROR] Python 3 not found. & exit /b 1
:found

REM Create venv if missing
if not exist "venv" (
    echo Creating virtual environment...
    %PYTHON_CMD% -m venv venv
)

set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=%PYTHON_CMD%

REM Install deps
if exist "venv\Scripts\pip.exe" (
    venv\Scripts\pip.exe install -q -r requirements.txt >nul 2>&1
) else (
    pip install -q -r requirements.txt >nul 2>&1
)

echo Running self_check...
%PYTHON_EXE% tools\self_check.py
if errorlevel 1 (
    echo [WARN] self_check reported issues. Continuing...
)

if exist "config\runtime.json" (
    for /f "usebackq tokens=1,2,3" %%a in (`powershell -NoProfile -Command "$cfg=Get-Content -Raw 'config/runtime.json' | ConvertFrom-Json; if($cfg){$h=$cfg.bind; if(-not $h){$h='0.0.0.0'}; $p=$cfg.port; if(-not $p){$p=8012}; $api=$cfg.apiBaseUrl; if(-not $api){$local=($h -eq '0.0.0.0') ? '127.0.0.1' : $h; $api='http://'+$local+':' + $p}; Write-Output \"$h $p $api\"}"`) do (
        set HOST=%%a
        set PORT=%%b
        set BASE_URL=%%c
    )
)

echo Opening UI...
start "" %BASE_URL%/app

echo Starting SWARMZ (AUTO=1, TICK_INTERVAL=%TICK_INTERVAL%)...
%PYTHON_EXE% run_server.py --host %HOST% --port %PORT%

endlocal
