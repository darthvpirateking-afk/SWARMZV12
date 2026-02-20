@echo off
setlocal
cd /d %~dp0

echo CONNECTING TO MAIN SWARM
python tools\switch_runtime_profile.py render
if %errorlevel% neq 0 exit /b %errorlevel%

start "" "https://swarmzV10-.onrender.com"
echo Opened: https://swarmzV10-.onrender.com
exit /b 0
