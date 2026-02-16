@echo off
setlocal enabledelayedexpansion
set ROOT=%~dp0
cd /d "%ROOT%"
if not exist "%ROOT%data" mkdir "%ROOT%data"
set LOG=%ROOT%data\daemon.log
set HOST=0.0.0.0
set PORT=8012
if exist "%ROOT%config\runtime.json" (
  for /f "usebackq tokens=1,2" %%h in (`powershell -NoProfile -Command "$cfg=Get-Content -Raw 'config/runtime.json' | ConvertFrom-Json; if($cfg){$u=[uri]$cfg.api_base; Write-Output \"$($u.Host) $($u.Port)\"}"`) do (
    set HOST=%%h
    set PORT=%%i
  )
)
:loop
echo [%date% %time%] running doctor >> "%LOG%"
python tools\swarmz_doctor.py >> "%LOG%" 2>&1
echo [%date% %time%] starting server host=%HOST% port=%PORT% >> "%LOG%"
python run_server.py --port %PORT% --host %HOST% >> "%LOG%" 2>&1
echo [%date% %time%] server exited (%errorlevel%), restarting in 3s >> "%LOG%"
timeout /t 3 >nul
goto loop
