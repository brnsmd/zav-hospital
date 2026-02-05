@echo off
title ZAV BOSS - Hospital Server
cd /d "%~dp0"

echo.
echo  ====================================
echo   ZAV BOSS HOSPITAL SERVER
echo  ====================================
echo.

:: ============================================
:: CONFIGURE YOUR TOKENS HERE:
:: ============================================
set BOSS_API_URL=http://localhost:8083
set N8N_URL=http://localhost:5678

:: Airtable - get from: https://airtable.com/create/tokens
set AIRTABLE_TOKEN=YOUR_AIRTABLE_TOKEN_HERE
set AIRTABLE_BASE=appv5BwoWyRhT6Lcr

:: n8n - generate in: n8n Settings > API > Create API Key
set N8N_API_KEY=YOUR_N8N_API_KEY_HERE

:: Database path
set ZAV_DATABASE_PATH=C:\ZavBoss\data\zav.db
:: ============================================

echo  Config loaded:
echo    BOSS API: %BOSS_API_URL%
echo    N8N:      %N8N_URL%
echo    Airtable: %AIRTABLE_BASE%
echo.
echo  Starting...
echo  DO NOT CLOSE THIS WINDOW!
echo.

boss-tui.exe

echo.
echo  Server stopped.
pause
