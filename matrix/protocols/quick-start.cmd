@echo off
setlocal
cd /d %~dp0

echo SWARMZ ONE-BUTTON START

rem Always use local profile for one-button desktop/phone-on-LAN usage
python tools\switch_runtime_profile.py local >nul 2>nul

rem Auto-free default port if blocked
set KILL_PORT=1

call startup\startup.cmd
exit /b %ERRORLEVEL%
