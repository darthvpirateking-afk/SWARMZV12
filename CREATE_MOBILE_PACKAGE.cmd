@echo off
:: SWARMZ Mobile Package Creator
:: Creates a minimal package for phone installation

echo =========================================
echo SWARMZ Mobile Package Creator  
echo =========================================
echo.

:: Create mobile package directory
if not exist "SWARMZ_MOBILE_PACKAGE" mkdir SWARMZ_MOBILE_PACKAGE

echo Copying essential files for mobile...

:: Copy core Python files
copy "mobile_server.py" "SWARMZ_MOBILE_PACKAGE\"
copy "run_server.py" "SWARMZ_MOBILE_PACKAGE\"
copy "swarmz.py" "SWARMZ_MOBILE_PACKAGE\"
copy "phone_install.sh" "SWARMZ_MOBILE_PACKAGE\"

:: Copy requirements
copy "requirements.txt" "SWARMZ_MOBILE_PACKAGE\"

:: Copy companion system
if exist "core" (
    xcopy "core" "SWARMZ_MOBILE_PACKAGE\core" /E /I /H /Y > nul
    echo ✅ Copied AI companion system
)

:: Copy API system
if exist "addons" (
    xcopy "addons" "SWARMZ_MOBILE_PACKAGE\addons" /E /I /H /Y > nul
    echo ✅ Copied API system
)

:: Copy static files (UI)
if exist "static" (
    xcopy "static" "SWARMZ_MOBILE_PACKAGE\static" /E /I /H /Y > nul
    echo ✅ Copied cybernetic interface
)

:: Copy essential data
if exist "data" (
    xcopy "data" "SWARMZ_MOBILE_PACKAGE\data" /E /I /H /Y > nul
    echo ✅ Copied mission data
)

:: Create mobile launch script
echo #!/data/data/com.termux/files/usr/bin/bash > "SWARMZ_MOBILE_PACKAGE\start_swarmz.sh"
echo echo "🤖 Starting SWARMZ Mobile..." >> "SWARMZ_MOBILE_PACKAGE\start_swarmz.sh"
echo python mobile_server.py >> "SWARMZ_MOBILE_PACKAGE\start_swarmz.sh"

:: Create installation instructions
echo # 📱 SWARMZ Mobile Installation > "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo. >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo ## Quick Setup: >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 1. Install Termux from F-Droid >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 2. Copy this SWARMZ_MOBILE_PACKAGE folder to phone >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 3. In Termux: `cp -r /sdcard/SWARMZ_MOBILE_PACKAGE ~/swarmz` >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 4. `cd ~/swarmz` >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 5. `chmod +x phone_install.sh` >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md" 
echo 6. `./phone_install.sh` >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 7. `python mobile_server.py` >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"
echo 8. Open browser: `http://localhost:8012` >> "SWARMZ_MOBILE_PACKAGE\README_MOBILE.md"

echo.
echo ✅ Mobile package created in: SWARMZ_MOBILE_PACKAGE\
echo.
echo 📱 To install on phone:
echo    1. Copy SWARMZ_MOBILE_PACKAGE folder to phone storage
echo    2. Follow instructions in README_MOBILE.md
echo.
echo 🤖 SWARMZ will run 100%% offline on your phone!
echo.
pause