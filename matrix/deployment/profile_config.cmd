@echo off
setlocal
cd /d %~dp0

if "%~1"=="" (
  echo Usage: SWARMZ_PROFILE.cmd ^<local^|render^>
  python tools\switch_runtime_profile.py --show
  exit /b 1
)

python tools\switch_runtime_profile.py %~1
exit /b %ERRORLEVEL%
