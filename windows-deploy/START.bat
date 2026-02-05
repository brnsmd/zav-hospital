@echo off
title ZAV BOSS - Hospital Server
cd /d "%~dp0"

echo.
echo  ====================================
echo   ZAV BOSS HOSPITAL SERVER
echo  ====================================
echo.

:: Load secrets from secrets.bat (not committed to git)
if exist secrets.bat (
    call secrets.bat
    echo  [OK] Secrets loaded from secrets.bat
) else (
    echo  [!] WARNING: secrets.bat not found!
    echo      Create it with your AIRTABLE_TOKEN, AIRTABLE_BASE, N8N_API_KEY
    echo.
)

:: URLs (these are safe to commit)
set BOSS_API_URL=http://localhost:8083
set N8N_URL=http://localhost:5678
set ZAV_DATABASE_PATH=C:\ZavBoss\data\zav.db
set HOSPITAL_SUBNET=192.168.4.
set HOSPITAL_GATEWAY=192.168.4.1

echo [1/3] Starting n8n in background...
start /B cmd /C "n8n start > nul 2>&1"
timeout /t 5 /nobreak > nul

echo [2/3] Checking n8n...
curl -s http://localhost:5678/healthz > nul 2>&1
if %errorlevel%==0 (
    echo       n8n: OK
) else (
    echo       n8n: Starting... please wait
    timeout /t 10 /nobreak > nul
)

echo [3/3] Starting Boss TUI...
echo.
echo  Config:
echo    BOSS API:  %BOSS_API_URL%
echo    N8N:       %N8N_URL%
echo    Airtable:  %AIRTABLE_BASE%
echo    Subnet:    %HOSPITAL_SUBNET%
echo.
echo  ====================================
echo  DO NOT CLOSE THIS WINDOW!
echo  ====================================
echo.

boss-tui.exe

echo.
echo Stopping n8n...
taskkill /F /IM node.exe > nul 2>&1
echo Server stopped.
pause
