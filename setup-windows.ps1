#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Zav Hospital Server - Windows Setup Script
.DESCRIPTION
    Installs all prerequisites and sets up the Zav server environment on Windows.
    Run this script as Administrator in PowerShell.
.PARAMETER InstallPath
    Where to install Zav (default: E:\Zav-Hospital)
.EXAMPLE
    .\setup-windows.ps1
    .\setup-windows.ps1 -InstallPath "D:\MyZav"
.NOTES
    Author: Grug & Clug (Barbarian Coders)
    Version: 2.0
#>

param(
    [string]$InstallPath = "E:\Zav-Hospital",
    [switch]$SkipChoco,
    [switch]$SkipClone,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Continue"  # Don't stop on every error

# Colors for output
function Write-Status { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[X] $msg" -ForegroundColor Red }

function Refresh-Path {
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")
    # Also add common install locations
    $env:Path += ";$env:ProgramFiles\Git\cmd"
    $env:Path += ";$env:ProgramFiles\Python311"
    $env:Path += ";$env:ProgramFiles\Python311\Scripts"
    $env:Path += ";$env:USERPROFILE\.cargo\bin"
    $env:Path += ";$env:ProgramFiles\nodejs"
    $env:Path += ";$env:APPDATA\npm"
}

Write-Host @"

    ╔══════════════════════════════════════════════════════════════╗
    ║  🪓 ZAV HOSPITAL SERVER - WINDOWS SETUP v2.0 🪓              ║
    ║  Barbarian-approved installation script                      ║
    ╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# ============================================================
# PRE-FLIGHT CHECKS
# ============================================================
Write-Host "=== PRE-FLIGHT CHECKS ===" -ForegroundColor Yellow

# Check if running as admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Err "This script must be run as Administrator!"
    Write-Host "Right-click PowerShell and select 'Run as Administrator'"
    exit 1
}
Write-Success "Running as Administrator"

# Check disk space on target drive
$driveLetter = (Split-Path $InstallPath -Qualifier).TrimEnd(':')
$drive = Get-PSDrive -Name $driveLetter -ErrorAction SilentlyContinue

if ($drive) {
    $freeGB = [math]::Round($drive.Free / 1GB, 2)
    Write-Status "Drive $driveLetter`: has $freeGB GB free"

    if ($freeGB -lt 5) {
        Write-Err "NOT ENOUGH SPACE! Need at least 5GB free on drive $driveLetter`:"
        Write-Host "Free up space and try again."
        exit 1
    }
    Write-Success "Sufficient disk space available"
} else {
    Write-Warn "Could not check drive $driveLetter - make sure it exists!"
}

Write-Status "Install path: $InstallPath"

# ============================================================
# STEP 1: Install/Fix Chocolatey
# ============================================================
Write-Host "`n=== STEP 1: Chocolatey Package Manager ===" -ForegroundColor Yellow

if (-not $SkipChoco) {
    $chocoPath = "$env:ProgramData\chocolatey\bin\choco.exe"

    if (Test-Path $chocoPath) {
        Write-Success "Chocolatey already installed"
        & $chocoPath --version

        # Clean up any corrupted packages
        Write-Status "Cleaning up any corrupted packages..."
        $corruptedPkgs = @("python311", "rustup", "nodejs-lts", "git")
        foreach ($pkg in $corruptedPkgs) {
            $nupkgPath = "C:\ProgramData\chocolatey\lib\$pkg\$pkg.nupkg"
            if (Test-Path $nupkgPath) {
                $fileSize = (Get-Item $nupkgPath).Length
                if ($fileSize -eq 0) {
                    Write-Warn "Found corrupted package: $pkg - removing..."
                    Remove-Item "C:\ProgramData\chocolatey\lib\$pkg" -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
        }
    } else {
        Write-Status "Installing Chocolatey..."
        Set-ExecutionPolicy Bypass -Scope Process -Force
        [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
        Invoke-Expression ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
        Write-Success "Chocolatey installed"
    }

    Refresh-Path
}

# ============================================================
# STEP 2: Install Prerequisites (One by One)
# ============================================================
Write-Host "`n=== STEP 2: Installing Prerequisites ===" -ForegroundColor Yellow

# Function to install package with retry
function Install-ChocoPackage {
    param($PackageName, $TestCommand)

    Write-Status "Checking $PackageName..."

    # Try the test command
    try {
        $result = Invoke-Expression "$TestCommand 2>&1" -ErrorAction Stop
        if ($LASTEXITCODE -eq 0 -or $result -match '\d+\.\d+') {
            Write-Success "$PackageName already installed: $result"
            return $true
        }
    } catch {}

    # Not installed, try to install
    Write-Status "Installing $PackageName..."

    # Remove corrupted package if exists
    $libPath = "C:\ProgramData\chocolatey\lib\$PackageName"
    if (Test-Path $libPath) {
        Remove-Item $libPath -Recurse -Force -ErrorAction SilentlyContinue
    }

    # Install
    $chocoResult = choco install $PackageName -y --no-progress 2>&1

    if ($LASTEXITCODE -ne 0) {
        Write-Warn "Chocolatey install had issues, checking if it worked anyway..."
    }

    # Refresh PATH and test again
    Refresh-Path

    try {
        $result = Invoke-Expression "$TestCommand 2>&1" -ErrorAction Stop
        if ($result -match '\d+\.\d+' -or $LASTEXITCODE -eq 0) {
            Write-Success "$PackageName installed successfully"
            return $true
        }
    } catch {}

    Write-Err "Failed to install $PackageName"
    return $false
}

# Install Git
$gitOk = Install-ChocoPackage -PackageName "git" -TestCommand "git --version"

# Install Python 3.11
$pythonOk = Install-ChocoPackage -PackageName "python311" -TestCommand "python --version"

# If python311 failed, try python3
if (-not $pythonOk) {
    Write-Status "Trying alternative: python3..."
    $pythonOk = Install-ChocoPackage -PackageName "python3" -TestCommand "python --version"
}

# Install Rust via rustup
Write-Status "Checking Rust..."
Refresh-Path

$rustupExists = Get-Command rustup -ErrorAction SilentlyContinue
if (-not $rustupExists) {
    Write-Status "Installing Rust via rustup..."

    # Download and run rustup-init directly (more reliable than choco)
    $rustupInit = "$env:TEMP\rustup-init.exe"
    Invoke-WebRequest -Uri "https://win.rustup.rs/x86_64" -OutFile $rustupInit

    # Run rustup-init with default options
    Start-Process -FilePath $rustupInit -ArgumentList "-y" -Wait -NoNewWindow

    Refresh-Path
}

# Verify/setup Rust toolchain
Write-Status "Ensuring Rust stable toolchain..."
Refresh-Path
$rustupPath = "$env:USERPROFILE\.cargo\bin\rustup.exe"
if (Test-Path $rustupPath) {
    & $rustupPath default stable
    Write-Success "Rust toolchain ready"
} else {
    # Try from PATH
    try {
        rustup default stable
        Write-Success "Rust toolchain ready"
    } catch {
        Write-Warn "Could not setup Rust toolchain - may need manual setup"
    }
}

# Install Node.js
$nodeOk = Install-ChocoPackage -PackageName "nodejs-lts" -TestCommand "node --version"

Refresh-Path

# ============================================================
# STEP 3: Clone Repository
# ============================================================
Write-Host "`n=== STEP 3: Cloning Repository ===" -ForegroundColor Yellow

if (-not $SkipClone) {
    # Ensure parent directory exists
    $parentDir = Split-Path $InstallPath -Parent
    if (-not (Test-Path $parentDir)) {
        New-Item -ItemType Directory -Path $parentDir -Force | Out-Null
    }

    if (Test-Path $InstallPath) {
        Write-Warn "Directory $InstallPath already exists"
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

        if ($LASTEXITCODE -eq 0) {
            Write-Success "Repository cloned to $InstallPath"
        } else {
            Write-Err "Git clone failed!"
            exit 1
        }
    }
}

Set-Location $InstallPath

# ============================================================
# STEP 4: Setup Python Environments
# ============================================================
Write-Host "`n=== STEP 4: Setting up Python Environments ===" -ForegroundColor Yellow

Refresh-Path

# Find Python executable
$pythonExe = Get-Command python -ErrorAction SilentlyContinue
if (-not $pythonExe) {
    $pythonExe = Get-Command python3 -ErrorAction SilentlyContinue
}
if (-not $pythonExe) {
    # Try common locations
    $possiblePaths = @(
        "$env:ProgramFiles\Python311\python.exe",
        "$env:ProgramFiles\Python312\python.exe",
        "$env:LocalAppData\Programs\Python\Python311\python.exe"
    )
    foreach ($p in $possiblePaths) {
        if (Test-Path $p) {
            $pythonExe = $p
            break
        }
    }
}

if (-not $pythonExe) {
    Write-Err "Python not found! Please install Python manually and rerun with -SkipChoco"
    exit 1
}

Write-Status "Using Python: $pythonExe"

# CyberIntern Boss (Boss API)
if (Test-Path "$InstallPath\cyberintern-boss") {
    Write-Status "Setting up cyberintern-boss..."
    Set-Location "$InstallPath\cyberintern-boss"
    & $pythonExe -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    & .\.venv\Scripts\pip.exe install -r requirements.txt
    Write-Success "cyberintern-boss environment ready"
}

# CyberIntern App
if (Test-Path "$InstallPath\cyberintern") {
    Write-Status "Setting up cyberintern..."
    Set-Location "$InstallPath\cyberintern"
    & $pythonExe -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        & .\.venv\Scripts\pip.exe install -r requirements.txt
    } elseif (Test-Path "pyproject.toml") {
        & .\.venv\Scripts\pip.exe install -e .
    }
    Write-Success "cyberintern environment ready"
}

# CyberIntern MCP
if (Test-Path "$InstallPath\cyberintern_mcp") {
    Write-Status "Setting up cyberintern_mcp..."
    Set-Location "$InstallPath\cyberintern_mcp"
    & $pythonExe -m venv .venv
    & .\.venv\Scripts\python.exe -m pip install --upgrade pip
    if (Test-Path "requirements.txt") {
        & .\.venv\Scripts\pip.exe install -r requirements.txt
    }
    if (Test-Path "setup.py") {
        & .\.venv\Scripts\pip.exe install -e .
    }
    Write-Success "cyberintern_mcp environment ready"
}

Set-Location $InstallPath

# ============================================================
# STEP 5: Build Rust TUI
# ============================================================
Write-Host "`n=== STEP 5: Building Boss TUI (Rust) ===" -ForegroundColor Yellow

if (-not $SkipBuild) {
    if (Test-Path "$InstallPath\boss-tui") {
        Set-Location "$InstallPath\boss-tui"

        Refresh-Path
        $cargoExe = "$env:USERPROFILE\.cargo\bin\cargo.exe"

        if (Test-Path $cargoExe) {
            Write-Status "Building boss-tui (this may take a few minutes on first build)..."
            & $cargoExe build --release

            if ($LASTEXITCODE -eq 0) {
                Write-Success "boss-tui built successfully"
            } else {
                Write-Warn "boss-tui build had issues - may need manual build later"
            }
        } else {
            Write-Warn "Cargo not found - skipping TUI build. Run 'cargo build --release' manually in boss-tui folder"
        }

        Set-Location $InstallPath
    }
}

# ============================================================
# STEP 6: Install n8n
# ============================================================
Write-Host "`n=== STEP 6: Installing n8n ===" -ForegroundColor Yellow

Refresh-Path
$npmExe = Get-Command npm -ErrorAction SilentlyContinue

if ($npmExe) {
    Write-Status "Installing n8n globally via npm..."
    npm install -g n8n

    if ($LASTEXITCODE -eq 0) {
        Write-Success "n8n installed"
    } else {
        Write-Warn "n8n install had issues - try 'npm install -g n8n' manually"
    }
} else {
    Write-Warn "npm not found - install Node.js and run 'npm install -g n8n' manually"
}

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
    Write-Warn "IMPORTANT: Edit $secretsPath with your actual secrets!"
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
if exist ".\target\release\boss-tui.exe" (
    .\target\release\boss-tui.exe
) else (
    echo boss-tui.exe not found! Run 'cargo build --release' in boss-tui folder first.
    pause
)
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
    1. REBOOT YOUR COMPUTER (required for PATH changes)

    2. Edit secrets file:
       notepad $secretsPath

    3. Start all services:
       $InstallPath\start-zav.bat

    4. Open Boss TUI:
       $InstallPath\start-tui.bat

    5. Stop services:
       $InstallPath\stop-zav.bat

    SERVICES:
    - CyberIntern App:  http://localhost:8082
    - Boss API:         http://localhost:8083
    - n8n Dashboard:    http://localhost:5678

"@ -ForegroundColor Green

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
