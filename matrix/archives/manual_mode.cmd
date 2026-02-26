@echo off
REM SWARMZ_MANUAL.cmd – Start SWARMZ in MANUAL mode (AUTO=0)
setlocal enabledelayedexpansion

echo ============================================
echo   SWARMZ – MANUAL MODE
echo ============================================
echo.

set AUTO=0

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

if not exist "venv" ( %PYTHON_CMD% -m venv venv )

if exist "venv\Scripts\pip.exe" (
    venv\Scripts\pip.exe install -q -r requirements.txt >nul 2>&1
) else (
    pip install -q -r requirements.txt >nul 2>&1
)

set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=%PYTHON_CMD%

echo Starting SWARMZ (AUTO=0 – manual endpoints only)...
%PYTHON_EXE% run_swarmz.py

endlocal
