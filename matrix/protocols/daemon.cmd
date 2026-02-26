@echo off
setlocal enabledelayedexpansion
set ROOT=%~dp0
cd /d "%ROOT%"
if not exist "%ROOT%data" mkdir "%ROOT%data"
set LOG=%ROOT%data\daemon.log
set HOST=0.0.0.0
set PORT=8012
set BASE=http://localhost:8012
if exist "%ROOT%config\runtime.json" (
  for /f "usebackq tokens=1,2,3" %%h in (`powershell -NoProfile -Command "$cfg=Get-Content -Raw 'config/runtime.json' | ConvertFrom-Json; if($cfg){$host=$cfg.bind; if(-not $host){$host='0.0.0.0'}; $port=$cfg.port; if(-not $port){$port=8012}; $api=$cfg.apiBaseUrl; if(-not $api -and $cfg.api_base){$api=$cfg.api_base}; if(-not $api){$local=($host -eq '0.0.0.0') ? '127.0.0.1' : $host; $api='http://'+$local+':' + $port}; if($cfg.offlineMode){Write-Output 'OFFLINE_MODE 1'}; Write-Output \"$host $port $api\"}"`) do (
    if /i "%%h"=="OFFLINE_MODE" (
      set OFFLINE_MODE=%%i
    ) else (
      set HOST=%%h
      set PORT=%%i
      set BASE=%%j
    )
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
