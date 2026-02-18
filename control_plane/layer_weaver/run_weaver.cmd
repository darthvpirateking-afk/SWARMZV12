@echo off
REM run_weaver.cmd – Create venv, install deps, run Weaver + VerificationRunner
REM Usage: run_weaver.cmd [--loop]

setlocal
cd /d "%~dp0"

if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing dependencies...
.venv\Scripts\pip install -q -r requirements.txt

echo.
echo Starting Layer-Weaver...
echo.

REM Start verification runner in background
start "VerificationRunner" /b .venv\Scripts\python -m control_plane.layer_weaver.verification_runner --loop --interval 5

REM Start weaver service
.venv\Scripts\python -m control_plane.layer_weaver.weaver_service %*

endlocal
