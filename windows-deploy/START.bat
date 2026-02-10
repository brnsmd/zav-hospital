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

:: Browser mode (true=headless, false=show window)
set BOSS_HEADLESS=true
set RUST_LOG=boss_tui=debug,chromiumoxide=info

:: Store PIDs for targeted cleanup
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
    curl -s http://localhost:5678/healthz > nul 2>&1
    if %errorlevel%==0 (
        echo       n8n: OK
    ) else (
        echo       n8n: Still starting... waiting more
        timeout /t 10 /nobreak > nul
    )
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
echo    Subnet:    %HOSPITAL_SUBNET%
echo.
echo  ====================================
echo  DO NOT CLOSE THIS WINDOW!
echo  ====================================
echo.

ZAV.exe

echo.
echo Stopping services...
:: Kill only our specific processes by window title/port, not all node/python
:: ngrok is safe to kill globally (only one instance)
taskkill /F /IM ngrok.exe > nul 2>&1
:: Kill n8n (node on port 5678) and CyberIntern (python on port 8082)
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5678.*LISTENING" 2^>nul') do taskkill /F /PID %%a > nul 2>&1
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8082.*LISTENING" 2^>nul') do taskkill /F /PID %%a > nul 2>&1
echo Services stopped.
pause
