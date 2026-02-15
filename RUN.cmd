@echo off
REM SWARMZ - One-Command Startup Script (Windows Batch)
REM Usage: RUN.cmd [test|demo|api|help]

setlocal enabledelayedexpansion

echo ============================================
echo   SWARMZ - Operator-Sovereign System
echo ============================================
echo.

REM Parse arguments
set MODE=interactive
if "%1"=="test" set MODE=test
if "%1"=="demo" set MODE=demo
if "%1"=="api" set MODE=api
if "%1"=="help" goto :show_help
if "%1"=="--test" set MODE=test
if "%1"=="--demo" set MODE=demo
if "%1"=="--api" set MODE=api
if "%1"=="--help" goto :show_help
if "%1"=="/?" goto :show_help

goto :main

:show_help
echo Usage: RUN.cmd [options]
echo.
echo Options:
echo   (no args)   Start interactive CLI mode
echo   test        Run test suite
echo   demo        Run demo examples
echo   api         Start API server (requires FastAPI)
echo   help        Show this help message
echo.
exit /b 0

:main

REM Check Python installation
echo [1/5] Checking Python installation...
set PYTHON_CMD=
for %%p in (python3 python) do (
    %%p --version >nul 2>&1
    if !errorlevel! equ 0 (
        for /f "tokens=*" %%v in ('%%p --version 2^>^&1') do (
            echo %%v | findstr /r "Python 3\.[6-9] Python 3\.[1-9][0-9]" >nul
            if !errorlevel! equ 0 (
                set PYTHON_CMD=%%p
                echo   [OK] Found: %%v
                goto :python_found
            )
        )
    )
)

echo   [ERROR] Python 3.6+ not found
echo   Please install Python from https://www.python.org/
exit /b 1

:python_found

REM Check/create virtual environment
echo [2/5] Setting up virtual environment...
if not exist "venv" (
    echo   Creating new virtual environment...
    %PYTHON_CMD% -m venv venv
    if !errorlevel! neq 0 (
        echo   [ERROR] Failed to create virtual environment
        exit /b 1
    )
    echo   [OK] Virtual environment created
) else (
    echo   [OK] Virtual environment exists
)

REM Activate virtual environment
echo [3/5] Activating virtual environment...
if exist "venv\Scripts\activate.bat" (
    call venv\Scripts\activate.bat
    echo   [OK] Virtual environment activated
) else (
    echo   [WARNING] Activation script not found, continuing...
)

REM Install dependencies
echo [4/5] Installing dependencies...
if exist "requirements.txt" (
    if exist "venv\Scripts\pip.exe" (
        venv\Scripts\pip.exe install -q -r requirements.txt >nul 2>&1
    ) else (
        pip install -q -r requirements.txt >nul 2>&1
    )
    if !errorlevel! equ 0 (
        echo   [OK] Dependencies installed
    ) else (
        echo   [WARNING] Some dependencies may have failed (optional packages)
    )
) else (
    echo   [WARNING] requirements.txt not found, skipping...
)

REM Determine Python executable
set PYTHON_EXE=venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" (
    set PYTHON_EXE=%PYTHON_CMD%
)

REM Run appropriate command
echo [5/5] Starting SWARMZ...
echo.

if "%MODE%"=="test" (
    echo Running test suite...
    echo ============================================
    %PYTHON_EXE% test_swarmz.py
) else if "%MODE%"=="demo" (
    echo Running demo examples...
    echo ============================================
    %PYTHON_EXE% examples.py
) else if "%MODE%"=="api" (
    echo Starting API server...
    echo ============================================
    if exist "swarmz_api.py" (
        echo API will be available at: http://127.0.0.1:8000
        echo API docs at: http://127.0.0.1:8000/docs
        echo.
        %PYTHON_EXE% -m uvicorn swarmz_api:app --host 127.0.0.1 --port 8000
    ) else (
        echo   [ERROR] swarmz_api.py not found
        echo   Run installer.py to create API components
        exit /b 1
    )
) else (
    echo Starting interactive CLI...
    echo ============================================
    echo Available commands:
    echo   list          - List all capabilities
    echo   task ^<name^>   - Execute a task
    echo   audit         - View audit log
    echo   exit          - Exit interactive mode
    echo.
    echo Quick start:
    echo   swarmz^> list
    echo   swarmz^> task echo {"message": "Hello!"}
    echo.
    echo ============================================
    echo.
    %PYTHON_EXE% swarmz_cli.py --interactive
)

echo.
echo ============================================
echo   SWARMZ session ended
echo ============================================

endlocal
