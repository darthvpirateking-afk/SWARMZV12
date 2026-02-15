@echo off
REM SWARMZ_SMOKE_TEST.cmd – Smoke test for SWARMZ ecosystem
REM Assumes server is already running on localhost:8012
REM Or starts it, runs checks, then stops.
setlocal enabledelayedexpansion

set BASE=http://localhost:8012
set PASS=0
set FAIL=0

echo ============================================
echo   SWARMZ SMOKE TEST
echo ============================================
echo.

REM 1) Check /openapi.json
echo [1/6] GET /openapi.json
curl -sf %BASE%/openapi.json >nul 2>&1
if !errorlevel! equ 0 (
    echo   PASS
    set /a PASS+=1
) else (
    echo   FAIL – /openapi.json not reachable
    set /a FAIL+=1
)

REM 2) Check /v1/health
echo [2/6] GET /v1/health
curl -sf %BASE%/v1/health >nul 2>&1
if !errorlevel! equ 0 (
    echo   PASS
    set /a PASS+=1
) else (
    echo   FAIL – /v1/health not reachable
    set /a FAIL+=1
)

REM 3) Start AUTO loop
echo [3/6] POST /v1/ecosystem/auto/start (tick_interval=5)
curl -sf -X POST %BASE%/v1/ecosystem/auto/start -H "Content-Type: application/json" -d "{\"tick_interval\":5}" >nul 2>&1
if !errorlevel! equ 0 (
    echo   PASS
    set /a PASS+=1
) else (
    echo   FAIL – could not start auto loop
    set /a FAIL+=1
)

REM 4) Wait for 2 ticks (~12s)
echo [4/6] Waiting 12 seconds for 2 ticks...
timeout /t 12 /nobreak >nul

REM 5) Confirm audit.jsonl grew
echo [5/6] Checking audit.jsonl growth
for %%F in (data\audit.jsonl) do set SIZE=%%~zF
if !SIZE! GTR 0 (
    echo   PASS – audit.jsonl has !SIZE! bytes
    set /a PASS+=1
) else (
    echo   FAIL – audit.jsonl is empty
    set /a FAIL+=1
)

REM 6) Stop AUTO loop
echo [6/6] POST /v1/ecosystem/auto/stop
curl -sf -X POST %BASE%/v1/ecosystem/auto/stop >nul 2>&1
if !errorlevel! equ 0 (
    echo   PASS
    set /a PASS+=1
) else (
    echo   FAIL – could not stop auto loop
    set /a FAIL+=1
)

echo.
echo ============================================
echo   Results: !PASS! passed, !FAIL! failed
echo ============================================

if !FAIL! GTR 0 (
    echo   STATUS: FAIL
    exit /b 1
) else (
    echo   STATUS: ALL PASSED
    exit /b 0
)

endlocal
