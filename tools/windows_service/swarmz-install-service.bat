@echo off
REM Install SWARMZ as a Windows Service using NSSM
set SERVICE_NAME=SWARMZ_Service
set SERVICE_PATH="%~dp0..\..\run_server.py"
set LOG_PATH="%~dp0..\..\logs\swarmz_service.log"

nssm install %SERVICE_NAME% python "%SERVICE_PATH%"
nssm set %SERVICE_NAME% AppStdout "%LOG_PATH%"
nssm set %SERVICE_NAME% AppStderr "%LOG_PATH%"
nssm start %SERVICE_NAME%

echo Service %SERVICE_NAME% installed and started.