@echo off
REM SWARMZ_SMOKE_TEST.cmd – Full-flow smoke test for SWARMZ ecosystem
REM Assumes server is already running on localhost:8012 (with swarm runner)
setlocal enabledelayedexpansion

set BASE=http://localhost:8012
set PASS=0
set FAIL=0
set MISSION_ID=

echo ============================================
echo   SWARMZ SMOKE TEST
echo ============================================
echo.

REM 1) GET /v1/health
echo [1/7] GET /v1/health
curl -sf %BASE%/v1/health >nul 2>&1
if !errorlevel! equ 0 (
    echo   PASS
    set /a PASS+=1
) else (
    echo   FAIL - /v1/health not reachable
    set /a FAIL+=1
)

REM 2) GET /v1/swarm/status
echo [2/7] GET /v1/swarm/status
curl -sf %BASE%/v1/swarm/status -o _smoke_status.json 2>nul
if !errorlevel! equ 0 (
    findstr /C:"\"up\"" _smoke_status.json >nul 2>&1
    if !errorlevel! equ 0 (
        echo   PASS - runner is up
        set /a PASS+=1
    ) else (
        echo   FAIL - runner not up
        set /a FAIL+=1
    )
) else (
    echo   FAIL - could not reach /v1/swarm/status
    set /a FAIL+=1
)

REM 3) POST /v1/mode -> BUILD
echo [3/7] POST /v1/mode -^> BUILD
curl -sf -X POST %BASE%/v1/mode -H "Content-Type: application/json" -d "{\"mode\":\"BUILD\"}" -o _smoke_mode.json 2>nul
if !errorlevel! equ 0 (
    findstr /C:"\"BUILD\"" _smoke_mode.json >nul 2>&1
    if !errorlevel! equ 0 (
        echo   PASS
        set /a PASS+=1
    ) else (
        echo   FAIL - mode not BUILD
        set /a FAIL+=1
    )
) else (
    echo   FAIL - could not switch mode
    set /a FAIL+=1
)

REM 4) POST /v1/build/dispatch (intent=smoke)
echo [4/7] POST /v1/build/dispatch (intent=smoke)
curl -sf -X POST %BASE%/v1/build/dispatch -H "Content-Type: application/json" -d "{\"intent\":\"smoke\",\"spec\":{}}" -o _smoke_dispatch.json 2>nul
if !errorlevel! equ 0 (
    echo   PASS - dispatched
    set /a PASS+=1
    REM Extract mission_id (rough parse)
    for /f "tokens=2 delims=:," %%A in ('findstr /C:"mission_id" _smoke_dispatch.json') do (
        set MISSION_ID=%%~A
        set MISSION_ID=!MISSION_ID:"=!
        set MISSION_ID=!MISSION_ID: =!
    )
) else (
    echo   FAIL - could not dispatch
    set /a FAIL+=1
)

REM 5) Wait for runner
echo [5/7] Waiting 3 seconds for runner...
timeout /t 3 /nobreak >nul

REM 6) GET /v1/missions/list — confirm SUCCESS
echo [6/7] GET /v1/missions/list (confirm SUCCESS)
curl -sf %BASE%/v1/missions/list -o _smoke_missions.json 2>nul
if !errorlevel! equ 0 (
    findstr /C:"SUCCESS" _smoke_missions.json >nul 2>&1
    if !errorlevel! equ 0 (
        echo   PASS - found SUCCESS mission
        set /a PASS+=1
    ) else (
        echo   FAIL - no SUCCESS mission found
        set /a FAIL+=1
    )
) else (
    echo   FAIL - could not list missions
    set /a FAIL+=1
)

REM 7) Confirm packs result.json
echo [7/7] Check packs result.json
if defined MISSION_ID (
    if exist "packs\!MISSION_ID!\result.json" (
        echo   PASS
        set /a PASS+=1
    ) else (
        echo   FAIL - packs\!MISSION_ID!\result.json not found
        set /a FAIL+=1
    )
) else (
    echo   FAIL - no mission_id to check
    set /a FAIL+=1
)

REM Cleanup temp files
del /q _smoke_status.json _smoke_mode.json _smoke_dispatch.json _smoke_missions.json 2>nul

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
