@echo off
REM Remove SWARMZ Windows Service using NSSM
set SERVICE_NAME=SWARMZ_Service

nssm stop %SERVICE_NAME%
nssm remove %SERVICE_NAME% confirm
echo Service %SERVICE_NAME% removed.