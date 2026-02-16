@echo off
REM SWARMZ_UP.cmd – Start SWARMZ in AUTO mode (AUTO=1)
setlocal enabledelayedexpansion

echo ============================================
echo   SWARMZ – AUTO MODE STARTUP
echo ============================================
echo.

set AUTO=1
set TICK_INTERVAL=30

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

REM Install deps
if exist "venv\Scripts\pip.exe" (
    venv\Scripts\pip.exe install -q -r requirements.txt >nul 2>&1
) else (
    pip install -q -r requirements.txt >nul 2>&1
)

REM Determine python exe
set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=%PYTHON_CMD%

echo Starting SWARMZ (AUTO=1, TICK_INTERVAL=%TICK_INTERVAL%)...
%PYTHON_EXE% run_swarmz.py

endlocal
