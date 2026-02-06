@echo off
chcp 65001 >nul 2>&1
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
set BOSS_API_URL=http://127.0.0.1:8084
set N8N_URL=http://127.0.0.1:5678
set ZAV_DATABASE_PATH=C:\ZavBoss\data\zav.db
set HOSPITAL_SUBNET=192.168.4.
set HOSPITAL_GATEWAY=192.168.4.1

:: Browser mode (true=headless, false=show window)
set BOSS_HEADLESS=true
set RUST_LOG=boss_tui=debug,chromiumoxide=info

echo [1/4] Starting n8n in background...
start /B cmd /C "n8n start > nul 2>&1"
timeout /t 5 /nobreak > nul

echo        Checking n8n...
curl -s http://localhost:5678/healthz > nul 2>&1
if %errorlevel%==0 (
    echo       n8n: OK
) else (
    echo       n8n: Starting... please wait
    timeout /t 10 /nobreak > nul
)

echo [2/4] Starting ngrok tunnel in background...
start /B cmd /C "ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev > nul 2>&1"
echo       ngrok: Started

echo [3/4] Starting CyberIntern in background...
set CYBERINTERN_DIR=%~dp0..\cyberintern
start /B cmd /C "cd /d %CYBERINTERN_DIR% && python -m uvicorn main:app --host 0.0.0.0 --port 8082 > nul 2>&1"
echo       CyberIntern: Started (port 8082)

echo [4/4] Starting Boss TUI...
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
echo Stopping services...
taskkill /F /IM node.exe > nul 2>&1
taskkill /F /IM ngrok.exe > nul 2>&1
taskkill /F /IM python.exe > nul 2>&1
echo Services stopped.
pause
