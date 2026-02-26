@echo off
setlocal ENABLEDELAYEDEXPANSION
echo SWARMZ_SMOKE

if "%BASE_URL%"=="" (set BASE=http://127.0.0.1:8012) else (set BASE=%BASE_URL%)
set TMP=%TEMP%\swarmz_smoke.txt

rem 1. /health
curl -s "%BASE%/health" >"%TMP%" 2>nul
findstr /i "\"status\":\"ok\"" "%TMP%" >nul || (echo 1/3 Health FAIL & type "%TMP%" & exit /b 1)
echo 1/3 Health OK

rem 2. /v1/ui/state
curl -s "%BASE%/v1/ui/state" >"%TMP%" 2>nul
findstr /i "\"ok\":true" "%TMP%" >nul || (echo 2/3 UI State FAIL & type "%TMP%" & exit /b 1)
echo 2/3 UI State OK

rem 3. /v1/missions/list
curl -s "%BASE%/v1/missions/list" >"%TMP%" 2>nul
findstr /i "\"ok\":true" "%TMP%" >nul || (echo 3/3 Missions List FAIL & type "%TMP%" & exit /b 1)
echo 3/3 Missions List OK

del "%TMP%" >nul 2>nul
echo ALL SMOKE TESTS PASSED
exit /b 0
endlocal
