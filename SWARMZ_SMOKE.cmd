@echo off
setlocal

set BASE=http://127.0.0.1:8012

curl -s %BASE%/health >nul
if errorlevel 1 goto :fail

curl -s -H "Content-Type: application/json" -d "{\"intent\":\"smoke\",\"scope\":{\"test\":\"ok\"}}" %BASE%/v1/sovereign/dispatch >nul
if errorlevel 1 goto :fail

curl -s %BASE%/v1/system/log?tail=5 >nul
if errorlevel 1 goto :fail

echo SMOKE PASSED
exit /b 0

:fail
echo SMOKE FAILED
exit /b 1
