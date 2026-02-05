@echo off
title ZAV Hospital Setup
color 0A

echo.
echo  ============================================
echo   ZAV HOSPITAL SYSTEM - SIMPLE SETUP
echo  ============================================
echo.

:: Check for admin rights
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo [!] Please run as Administrator
    echo     Right-click and select "Run as administrator"
    pause
    exit /b 1
)

:: Create install folder
echo [1/5] Creating install folder...
mkdir "C:\ZavBoss" 2>nul
mkdir "C:\ZavBoss\data" 2>nul

:: Copy files
echo [2/5] Copying files...
copy /Y boss-tui.exe "C:\ZavBoss\" >nul
copy /Y START.bat "C:\ZavBoss\" >nul

:: Check Node.js
echo [3/5] Checking Node.js...
node --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [!] Node.js NOT FOUND
    echo     Please install from: installers\node-v20-setup.msi
    echo     Then run this setup again.
    echo.
    if exist "installers\node-v20-setup.msi" (
        echo     Opening Node.js installer...
        start "" "installers\node-v20-setup.msi"
    )
    pause
    exit /b 1
) else (
    echo     Node.js OK
)

:: Check n8n
echo [4/5] Checking n8n...
call n8n --version >nul 2>&1
if %errorLevel% neq 0 (
    echo.
    echo [!] n8n NOT FOUND - Installing...
    call npm install -g n8n
    if %errorLevel% neq 0 (
        echo [!] n8n install failed. Try manually:
        echo     npm install -g n8n
        pause
    )
) else (
    echo     n8n OK
)

:: Done
echo [5/5] Setup complete!
echo.
echo  ============================================
echo   INSTALLATION COMPLETE
echo  ============================================
echo.
echo   Files installed to: C:\ZavBoss\
echo.
echo   To start the system:
echo     1. Open C:\ZavBoss
echo     2. Double-click START.bat
echo.
echo   Or run from here:
echo     start "" "C:\ZavBoss\START.bat"
echo.
pause
