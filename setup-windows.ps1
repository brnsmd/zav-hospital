#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Zav Hospital Server - Windows Setup Script
.DESCRIPTION
    Installs all prerequisites and sets up the Zav server environment on Windows.
    Run this script as Administrator in PowerShell.
.NOTES
    Author: Grug & Clug (Barbarian Coders)
    Version: 1.0
#>

param(
    [string]$InstallPath = "C:\Zav",
    [switch]$SkipChoco,
    [switch]$SkipClone,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Stop"

# Colors for output
function Write-Status { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warning { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Error { param($msg) Write-Host "[X] $msg" -ForegroundColor Red }

Write-Host @"

    ╔══════════════════════════════════════════════════════════════╗
    ║  🪓 ZAV HOSPITAL SERVER - WINDOWS SETUP 🪓                   ║
    ║  Barbarian-approved installation script                      ║
    ╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Error "This script must be run as Administrator!"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}

Write-Success "Running as Administrator"
Write-Status "Install path: $InstallPath"

# ============================================================
# STEP 1: Install Chocolatey
# ============================================================
Write-Host "`n=== STEP 1: Chocolatey Package Manager ===" -ForegroundColor Yellow

if (-not $SkipChoco) {
    $chocoPath = "$env:ProgramData\chocolatey\bin\choco.exe"

    if (Test-Path $chocoPath) {
        Write-Success "Chocolatey already installed"
        & $chocoPath --version
    } else {
        Write-Status "Installing Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

        # Refresh environment
        $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

        Write-Success "Chocolatey installed"
    }
}

# ============================================================
# STEP 2: Install Prerequisites
# ============================================================
Write-Host "`n=== STEP 2: Installing Prerequisites ===" -ForegroundColor Yellow

$packages = @(
    @{name="git"; check="git --version"},
    @{name="python311"; check="python --version"},
    @{name="rustup"; check="rustc --version"},
    @{name="nodejs-lts"; check="node --version"}
)

foreach ($pkg in $packages) {
    Write-Status "Checking $($pkg.name)..."

    try {
        $result = Invoke-Expression $pkg.check 2>&1
        Write-Success "$($pkg.name) already installed: $result"
    } catch {
        Write-Status "Installing $($pkg.name)..."
        choco install $pkg.name -y --no-progress
        Write-Success "$($pkg.name) installed"
    }
}

# Refresh environment after installations
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# Install Rust toolchain if rustup was just installed
Write-Status "Ensuring Rust stable toolchain..."
rustup default stable 2>$null

# ============================================================
# STEP 3: Clone Repository
# ============================================================
Write-Host "`n=== STEP 3: Cloning Repository ===" -ForegroundColor Yellow

if (-not $SkipClone) {
    if (Test-Path $InstallPath) {
        Write-Warning "Directory $InstallPath already exists"
        $response = Read-Host "Delete and re-clone? (y/N)"
        if ($response -eq 'y') {
            Remove-Item -Recurse -Force $InstallPath
        } else {
            Write-Status "Skipping clone, using existing directory"
            $SkipClone = $true
        }
    }

    if (-not $SkipClone) {
        Write-Status "Cloning zav-hospital with submodules..."
        git clone --recurse-submodules https://github.com/brnsmd/zav-hospital.git $InstallPath
        Write-Success "Repository cloned to $InstallPath"
    }
}

Set-Location $InstallPath

# ============================================================
# STEP 4: Setup Python Environments
# ============================================================
Write-Host "`n=== STEP 4: Setting up Python Environments ===" -ForegroundColor Yellow

# CyberIntern Boss (Boss API)
Write-Status "Setting up cyberintern-boss..."
Set-Location "$InstallPath\cyberintern-boss"
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
deactivate
Write-Success "cyberintern-boss environment ready"

# CyberIntern App
Write-Status "Setting up cyberintern..."
Set-Location "$InstallPath\cyberintern"
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
if (Test-Path "requirements.txt") {
    pip install -r requirements.txt
} elseif (Test-Path "pyproject.toml") {
    pip install -e .
}
deactivate
Write-Success "cyberintern environment ready"

# CyberIntern MCP
Write-Status "Setting up cyberintern_mcp..."
Set-Location "$InstallPath\cyberintern_mcp"
python -m venv .venv
& .\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
pip install -e .
deactivate
Write-Success "cyberintern_mcp environment ready"

Set-Location $InstallPath

# ============================================================
# STEP 5: Build Rust TUI
# ============================================================
Write-Host "`n=== STEP 5: Building Boss TUI (Rust) ===" -ForegroundColor Yellow

if (-not $SkipBuild) {
    Set-Location "$InstallPath\boss-tui"
    Write-Status "Building boss-tui (this may take a few minutes on first build)..."
    cargo build --release
    Write-Success "boss-tui built successfully"
    Set-Location $InstallPath
}

# ============================================================
# STEP 6: Install n8n
# ============================================================
Write-Host "`n=== STEP 6: Installing n8n ===" -ForegroundColor Yellow

Write-Status "Installing n8n globally via npm..."
npm install -g n8n
Write-Success "n8n installed"

# ============================================================
# STEP 7: Create Configuration Files
# ============================================================
Write-Host "`n=== STEP 7: Creating Configuration Files ===" -ForegroundColor Yellow

# Create secrets template
$secretsPath = "$env:USERPROFILE\.config\zav-secrets.env"
$secretsDir = Split-Path $secretsPath -Parent

if (-not (Test-Path $secretsDir)) {
    New-Item -ItemType Directory -Path $secretsDir -Force | Out-Null
}

if (-not (Test-Path $secretsPath)) {
    Write-Status "Creating secrets template at $secretsPath"
    @"
# Zav Hospital Secrets - FILL IN YOUR VALUES
# Copy this file and fill in the actual values

# Boss API
BOSS_API_URL=http://localhost:8083
BOSS_API_KEY=your_boss_api_key_here

# n8n
N8N_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key_here

# Airtable
AIRTABLE_TOKEN=your_airtable_token_here
AIRTABLE_BASE=appv5BwoWyRhT6Lcr

# CyberIntern
CYBERINTERN_API_URL=http://localhost:8082
CYBERINTERN_USERNAME=admin
CYBERINTERN_PASSWORD=admin123456

# Slack (optional on local server)
SLACK_BOT_TOKEN=your_slack_token_here

# ngrok (if exposing webhooks)
NGROK_AUTHTOKEN=your_ngrok_token_here
"@ | Out-File -FilePath $secretsPath -Encoding utf8
    Write-Warning "IMPORTANT: Edit $secretsPath with your actual secrets!"
} else {
    Write-Success "Secrets file already exists at $secretsPath"
}

# ============================================================
# STEP 8: Create Startup Scripts
# ============================================================
Write-Host "`n=== STEP 8: Creating Startup Scripts ===" -ForegroundColor Yellow

# Create start-zav.bat
$startBat = @"
@echo off
title Zav Hospital Server
echo.
echo  ============================================
echo   ZAV HOSPITAL SERVER - Starting Services
echo  ============================================
echo.

REM Load secrets
for /f "tokens=*" %%a in ('type "%USERPROFILE%\.config\zav-secrets.env" ^| findstr /v "^#"') do set %%a

echo [1/3] Starting CyberIntern App (port 8082)...
start "CyberIntern" cmd /k "cd /d $InstallPath\cyberintern && .venv\Scripts\activate && python -m src.start_web_ui"

timeout /t 3 /nobreak > nul

echo [2/3] Starting Boss API (port 8083)...
start "Boss API" cmd /k "cd /d $InstallPath\cyberintern-boss && .venv\Scripts\activate && python server.py"

timeout /t 3 /nobreak > nul

echo [3/3] Starting n8n (port 5678)...
start "n8n" cmd /k "n8n start"

echo.
echo  All services starting in separate windows!
echo  - CyberIntern: http://localhost:8082
echo  - Boss API:    http://localhost:8083
echo  - n8n:         http://localhost:5678
echo.
pause
"@
$startBat | Out-File -FilePath "$InstallPath\start-zav.bat" -Encoding ascii
Write-Success "Created start-zav.bat"

# Create start-tui.bat
$tuiBat = @"
@echo off
title Boss TUI
cd /d $InstallPath\boss-tui
.\target\release\boss-tui.exe
"@
$tuiBat | Out-File -FilePath "$InstallPath\start-tui.bat" -Encoding ascii
Write-Success "Created start-tui.bat"

# Create stop-zav.bat
$stopBat = @"
@echo off
echo Stopping Zav services...
taskkill /fi "WINDOWTITLE eq CyberIntern*" /f 2>nul
taskkill /fi "WINDOWTITLE eq Boss API*" /f 2>nul
taskkill /fi "WINDOWTITLE eq n8n*" /f 2>nul
echo Done.
pause
"@
$stopBat | Out-File -FilePath "$InstallPath\stop-zav.bat" -Encoding ascii
Write-Success "Created stop-zav.bat"

# ============================================================
# DONE!
# ============================================================
Write-Host @"

    ╔══════════════════════════════════════════════════════════════╗
    ║  🪓 INSTALLATION COMPLETE! FEAST TIME! 🍖                    ║
    ╚══════════════════════════════════════════════════════════════╝

    Installed to: $InstallPath

    NEXT STEPS:
    1. Edit secrets file:
       notepad $secretsPath

    2. Start all services:
       $InstallPath\start-zav.bat

    3. Open Boss TUI:
       $InstallPath\start-tui.bat

    4. Stop services:
       $InstallPath\stop-zav.bat

    SERVICES:
    - CyberIntern App:  http://localhost:8082
    - Boss API:         http://localhost:8083
    - n8n Dashboard:    http://localhost:5678

"@ -ForegroundColor Green

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
