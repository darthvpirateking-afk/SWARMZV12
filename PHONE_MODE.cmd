@echo off
REM SWARMZ Phone Mode Launcher (Command Prompt)

echo ========================================
echo SWARMZ PHONE MODE
echo ========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    pause
    exit /b 1
)

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
)

echo Activating virtual environment...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

for /f "delims=" %%i in ('python -c "import socket; s=socket.socket(socket.AF_INET, socket.SOCK_DGRAM); s.connect((''8.8.8.8'',80)); print(s.getsockname()[0]); s.close()"') do set LAN_IP=%%i

echo.
echo ========================================
echo PHONE ACCESS READY
echo ========================================
echo Phone URL: http://%LAN_IP%:8012/
echo Health:    http://%LAN_IP%:8012/v1/health
echo AI Chat:   POST http://%LAN_IP%:8012/v1/nexusmon/chat
echo.
echo Use the same Wi-Fi network on phone + PC.
echo.

python run_server.py --host 0.0.0.0 --port 8012

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Server stopped with error code %errorlevel%
    pause
)
