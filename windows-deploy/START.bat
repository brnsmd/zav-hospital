@echo off
title ZAV BOSS - Hospital Server
cd /d "%~dp0"

echo.
echo  ====================================
echo   ZAV BOSS HOSPITAL SERVER
echo  ====================================
echo.
echo  Starting API server on port 8083...
echo  DO NOT CLOSE THIS WINDOW!
echo.

:: Set database path explicitly
set ZAV_DATABASE_PATH=C:\ZavBoss\data\zav.db

boss-tui.exe --headless

echo.
echo  Server stopped.
pause
