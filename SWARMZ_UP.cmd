@echo off
setlocal ENABLEDELAYEDEXPANSION
cd /d %~dp0

echo SWARMZ_UP

set HOSTBIND=0.0.0.0
if "%PORT%"=="" (set PORT=8012)

rem ---------- port check ----------
set EXISTPID=
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT% " ^| findstr LISTENING 2^>nul') do (
  set EXISTPID=%%p
  goto :foundpid
)
:foundpid
if defined EXISTPID (
  if "%KILL_PORT%"=="1" (
    echo KILL_PORT=1 — killing PID %EXISTPID% ...
    taskkill /PID %EXISTPID% /F >nul 2>nul
    timeout /t 1 >nul
  ) else (
    call :lanip
    echo Server already running.
    echo LOCAL: http://127.0.0.1:%PORT%/
    if not "%LANIP%"=="" echo LAN:   http://%LANIP%:%PORT%/
    echo PHONE: open LAN URL on same Wi-Fi
    exit /b 0
  )
)

rem ---------- LAN IP ----------
call :lanip
echo LOCAL: http://127.0.0.1:%PORT%/
if not "%LANIP%"=="" echo LAN:   http://%LANIP%:%PORT%/
echo PHONE: open LAN URL on same Wi-Fi

rem ---------- python ----------
set PY=%~dp0venv\Scripts\python.exe
if not exist "%PY%" set PY=python

rem ---------- venv ----------
set VENV=%~dp0venv\Scripts\python.exe
if not exist "%VENV%" (
  echo Creating virtual environment...
  python -m venv %~dp0venv
)
if not exist "%VENV%" (
  echo [ERROR] Virtual environment creation failed.
  exit /b 1
)

rem ---------- install dependencies ----------
if exist "%~dp0requirements.txt" (
  echo Installing dependencies...
  "%VENV%" -m pip install -U pip >nul 2>nul
  "%VENV%" -m pip install -r "%~dp0requirements.txt" >nul 2>nul
)

rem ---------- start ----------
if exist "%~dp0run_server.py" (
  echo Starting run_server.py on %HOSTBIND%:%PORT%
  "%PY%" run_server.py --host %HOSTBIND% --port %PORT%
  exit /b %ERRORLEVEL%
)
if exist "%~dp0server.py" (
  echo Starting uvicorn server:app on %HOSTBIND%:%PORT%
  "%PY%" -m uvicorn server:app --host %HOSTBIND% --port %PORT%
  exit /b %ERRORLEVEL%
)
echo [ERROR] No server.py or run_server.py found.
exit /b 1

:lanip
set LANIP=
for /f "tokens=2 delims=:" %%i in ('ipconfig ^| findstr /i "IPv4" ^| findstr /v "127.0.0.1" ^| findstr /v "169.254"') do (
  set TMP=%%i
  set TMP=!TMP: =!
  set LANIP=!TMP!
  goto :eof
)
goto :eof
endlocal
