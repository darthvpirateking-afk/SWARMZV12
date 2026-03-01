@echo off
setlocal
cd /d "%~dp0"

echo SWARMZ ONE-BUTTON STARTUP
echo ==========================
echo.

set KILL_PORT=1
call matrix\protocols\startup\startup.cmd
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo [FAIL] Startup exited with code %EXIT_CODE%
    pause
)

exit /b %EXIT_CODE%
