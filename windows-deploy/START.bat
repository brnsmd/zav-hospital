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
    echo  [!] ERROR: secrets.bat not found!
    echo      Create it with your AIRTABLE_TOKEN, AIRTABLE_BASE, N8N_API_KEY
    echo      System cannot run properly without credentials.
    echo.
    echo  Press any key to continue anyway, or close this window to abort.
    pause > nul
)

:: URLs (these are safe to commit)
set BOSS_API_URL=http://127.0.0.1:8084
set N8N_URL=http://127.0.0.1:5678
set ZAV_DATABASE_PATH=C:\ZavBoss\data\zav.db
set HOSPITAL_SUBNET=192.168.4.
set HOSPITAL_GATEWAY=192.168.4.1

:: EMR direct API (no more CyberIntern)
set EMR_URL=https://doc.hospital.mia.software
set EMR_ROLE_ID=23622
set RUST_LOG=boss_tui=debug

:: n8n and ngrok disabled (deferred — not needed yet)
:: To re-enable: uncomment the n8n and ngrok blocks below
:: start /B cmd /C "n8n start > nul 2>&1"
:: start /B cmd /C "ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev > nul 2>&1"

echo Starting Boss TUI...
echo.
echo  Config:
echo    BOSS API:  %BOSS_API_URL%
echo    EMR:       %EMR_URL%
echo    Subnet:    %HOSPITAL_SUBNET%
echo.
echo  ====================================
echo  DO NOT CLOSE THIS WINDOW!
echo  ====================================
echo.

boss-tui.exe

echo.
echo Stopping services...
:: n8n/ngrok disabled — nothing to clean up
echo Services stopped.
pause
