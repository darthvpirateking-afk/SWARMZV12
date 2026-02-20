@echo off
setlocal
cd /d %~dp0\mobile\app_store_wrapper

echo SWARMZ APP STORE WRAPPER SETUP

npm install
if %errorlevel% neq 0 exit /b %errorlevel%

npx cap add android
if %errorlevel% neq 0 exit /b %errorlevel%

npx cap sync
if %errorlevel% neq 0 exit /b %errorlevel%

npx cap open android
exit /b %errorlevel%
