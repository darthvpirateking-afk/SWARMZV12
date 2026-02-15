@echo off
REM SWARMZ Windows Launcher (Command Prompt)
REM Creates virtual environment, installs dependencies, and starts the server

echo ========================================
echo SWARMZ - Windows Setup and Launch
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.6+ from python.org
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)
echo.

REM Start the server
echo ========================================
echo Starting SWARMZ Server...
echo ========================================
echo.
python swarmz_server.py

REM Keep window open if there's an error
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Server stopped with error code %errorlevel%
    pause
)
