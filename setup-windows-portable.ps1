#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Zav Hospital Server - FULLY PORTABLE Windows Setup
.DESCRIPTION
    Installs ALL tools to E: drive. No C: drive usage!
    Downloads portable/embeddable versions of everything.
.NOTES
    Author: Grug & Clug (Barbarian Coders)
    Version: 3.0 - FULL PORTABLE
#>

param(
    [string]$BasePath = "E:\Zav",
    [switch]$SkipDownloads,
    [switch]$SkipClone,
    [switch]$SkipBuild
)

$ErrorActionPreference = "Continue"

# Paths
$ToolsPath = "$BasePath\Tools"
$RepoPath = "$BasePath\Hospital"
$GitPath = "$ToolsPath\Git"
$PythonPath = "$ToolsPath\Python"
$NodePath = "$ToolsPath\Node"
$RustPath = "$ToolsPath\Rust"
$CargoPath = "$ToolsPath\Cargo"
$NpmPath = "$ToolsPath\npm-global"

# Download URLs (latest stable versions)
$GitUrl = "https://github.com/git-for-windows/git/releases/download/v2.43.0.windows.1/PortableGit-2.43.0-64-bit.7z.exe"
$PythonUrl = "https://www.python.org/ftp/python/3.11.7/python-3.11.7-embed-amd64.zip"
$PythonPipUrl = "https://bootstrap.pypa.io/get-pip.py"
$NodeUrl = "https://nodejs.org/dist/v20.11.0/node-v20.11.0-win-x64.zip"
$RustupUrl = "https://win.rustup.rs/x86_64"

function Write-Status { param($msg) Write-Host "[*] $msg" -ForegroundColor Cyan }
function Write-Success { param($msg) Write-Host "[+] $msg" -ForegroundColor Green }
function Write-Warn { param($msg) Write-Host "[!] $msg" -ForegroundColor Yellow }
function Write-Err { param($msg) Write-Host "[X] $msg" -ForegroundColor Red }

Write-Host @"

    ╔══════════════════════════════════════════════════════════════╗
    ║  🪓 ZAV HOSPITAL - FULL PORTABLE INSTALL v3.0 🪓             ║
    ║  EVERYTHING ON E: DRIVE - NO C: NEEDED!                      ║
    ╚══════════════════════════════════════════════════════════════╝

"@ -ForegroundColor Magenta

# ============================================================
# PRE-FLIGHT CHECKS
# ============================================================
Write-Host "=== PRE-FLIGHT CHECKS ===" -ForegroundColor Yellow

# Check admin
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")
if (-not $isAdmin) {
    Write-Err "Must run as Administrator!"
    exit 1
}
Write-Success "Running as Administrator"

# Check E: drive
$drive = Get-PSDrive -Name "E" -ErrorAction SilentlyContinue
if (-not $drive) {
    Write-Err "E: drive not found!"
    exit 1
}

$freeGB = [math]::Round($drive.Free / 1GB, 2)
Write-Status "E: drive has $freeGB GB free"

if ($freeGB -lt 5) {
    Write-Err "Need at least 5GB free on E:"
    exit 1
}
Write-Success "Sufficient disk space"

# Create directories
Write-Status "Creating directory structure..."
$dirs = @($BasePath, $ToolsPath, $RepoPath, $GitPath, $PythonPath, $NodePath, $RustPath, $CargoPath, $NpmPath)
foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}
Write-Success "Directories created"

Write-Host @"

    Install locations:
    - Tools:    $ToolsPath
    - Repo:     $RepoPath
    - Git:      $GitPath
    - Python:   $PythonPath
    - Node.js:  $NodePath
    - Rust:     $RustPath

"@ -ForegroundColor Gray

# ============================================================
# STEP 1: Download and Extract Git Portable
# ============================================================
Write-Host "`n=== STEP 1: Git Portable ===" -ForegroundColor Yellow

$gitExe = "$GitPath\bin\git.exe"
if (Test-Path $gitExe) {
    Write-Success "Git already installed"
} elseif (-not $SkipDownloads) {
    Write-Status "Downloading Git Portable..."
    $gitArchive = "$env:TEMP\PortableGit.7z.exe"

    # Download
    [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
    Invoke-WebRequest -Uri $GitUrl -OutFile $gitArchive -UseBasicParsing

    Write-Status "Extracting Git (this may take a minute)..."
    # PortableGit is a self-extracting archive
    Start-Process -FilePath $gitArchive -ArgumentList "-o`"$GitPath`" -y" -Wait -NoNewWindow

    Remove-Item $gitArchive -Force -ErrorAction SilentlyContinue

    if (Test-Path $gitExe) {
        Write-Success "Git installed to $GitPath"
    } else {
        Write-Err "Git extraction failed!"
    }
}

# ============================================================
# STEP 2: Download and Setup Python Embeddable
# ============================================================
Write-Host "`n=== STEP 2: Python Embeddable ===" -ForegroundColor Yellow

$pythonExe = "$PythonPath\python.exe"
if (Test-Path $pythonExe) {
    Write-Success "Python already installed"
} elseif (-not $SkipDownloads) {
    Write-Status "Downloading Python embeddable..."
    $pythonZip = "$env:TEMP\python-embed.zip"

    Invoke-WebRequest -Uri $PythonUrl -OutFile $pythonZip -UseBasicParsing

    Write-Status "Extracting Python..."
    Expand-Archive -Path $pythonZip -DestinationPath $PythonPath -Force
    Remove-Item $pythonZip -Force

    # Enable pip in embeddable Python
    Write-Status "Enabling pip support..."
    $pthFile = Get-ChildItem "$PythonPath\python*._pth" | Select-Object -First 1
    if ($pthFile) {
        $content = Get-Content $pthFile.FullName
        $content = $content -replace '#import site', 'import site'
        $content | Set-Content $pthFile.FullName
    }

    # Download and install pip
    Write-Status "Installing pip..."
    $getPip = "$env:TEMP\get-pip.py"
    Invoke-WebRequest -Uri $PythonPipUrl -OutFile $getPip -UseBasicParsing
    & $pythonExe $getPip --no-warn-script-location
    Remove-Item $getPip -Force

    # Create Scripts directory if not exists
    $scriptsDir = "$PythonPath\Scripts"
    if (-not (Test-Path $scriptsDir)) {
        New-Item -ItemType Directory -Path $scriptsDir -Force | Out-Null
    }

    if (Test-Path $pythonExe) {
        Write-Success "Python installed to $PythonPath"
    } else {
        Write-Err "Python installation failed!"
    }
}

# ============================================================
# STEP 3: Download and Extract Node.js
# ============================================================
Write-Host "`n=== STEP 3: Node.js Portable ===" -ForegroundColor Yellow

$nodeExe = "$NodePath\node.exe"
if (Test-Path $nodeExe) {
    Write-Success "Node.js already installed"
} elseif (-not $SkipDownloads) {
    Write-Status "Downloading Node.js..."
    $nodeZip = "$env:TEMP\node.zip"

    Invoke-WebRequest -Uri $NodeUrl -OutFile $nodeZip -UseBasicParsing

    Write-Status "Extracting Node.js..."
    Expand-Archive -Path $nodeZip -DestinationPath "$env:TEMP\node-extract" -Force

    # Move from nested folder
    $nodeExtracted = Get-ChildItem "$env:TEMP\node-extract\node-*" | Select-Object -First 1
    if ($nodeExtracted) {
        Get-ChildItem $nodeExtracted.FullName | Move-Item -Destination $NodePath -Force
    }

    Remove-Item $nodeZip -Force -ErrorAction SilentlyContinue
    Remove-Item "$env:TEMP\node-extract" -Recurse -Force -ErrorAction SilentlyContinue

    # Configure npm to use E: drive for global packages
    Write-Status "Configuring npm for E: drive..."
    $npmrc = "$env:USERPROFILE\.npmrc"
    @"
prefix=$($NpmPath -replace '\\', '/')
cache=$($ToolsPath -replace '\\', '/')/npm-cache
"@ | Out-File -FilePath $npmrc -Encoding ascii

    if (Test-Path $nodeExe) {
        Write-Success "Node.js installed to $NodePath"
    } else {
        Write-Err "Node.js installation failed!"
    }
}

# ============================================================
# STEP 4: Download and Setup Rust (to E: drive)
# ============================================================
Write-Host "`n=== STEP 4: Rust (to E: drive) ===" -ForegroundColor Yellow

$cargoExe = "$CargoPath\bin\cargo.exe"
if (Test-Path $cargoExe) {
    Write-Success "Rust already installed"
} elseif (-not $SkipDownloads) {
    Write-Status "Downloading Rust installer..."
    $rustupInit = "$env:TEMP\rustup-init.exe"

    Invoke-WebRequest -Uri $RustupUrl -OutFile $rustupInit -UseBasicParsing

    Write-Status "Installing Rust to E: drive..."
    # Set environment variables BEFORE running rustup
    $env:RUSTUP_HOME = $RustPath
    $env:CARGO_HOME = $CargoPath

    # Run rustup with default options
    Start-Process -FilePath $rustupInit -ArgumentList "-y --default-toolchain stable --no-modify-path" -Wait -NoNewWindow

    Remove-Item $rustupInit -Force -ErrorAction SilentlyContinue

    if (Test-Path $cargoExe) {
        Write-Success "Rust installed to $RustPath"
    } else {
        Write-Err "Rust installation failed - may need manual setup"
    }
}

# ============================================================
# STEP 5: Setup Environment Variables
# ============================================================
Write-Host "`n=== STEP 5: Environment Variables ===" -ForegroundColor Yellow

Write-Status "Setting system environment variables..."

# Set RUSTUP_HOME and CARGO_HOME permanently
[Environment]::SetEnvironmentVariable("RUSTUP_HOME", $RustPath, "User")
[Environment]::SetEnvironmentVariable("CARGO_HOME", $CargoPath, "User")

# Build PATH additions
$pathAdditions = @(
    "$GitPath\bin",
    "$GitPath\cmd",
    $PythonPath,
    "$PythonPath\Scripts",
    $NodePath,
    $NpmPath,
    "$CargoPath\bin"
)

# Get current user PATH
$currentPath = [Environment]::GetEnvironmentVariable("Path", "User")
$pathParts = $currentPath -split ';' | Where-Object { $_ -ne '' }

# Add new paths if not already present
foreach ($addition in $pathAdditions) {
    if ($pathParts -notcontains $addition) {
        $pathParts += $addition
    }
}

# Set new PATH
$newPath = $pathParts -join ';'
[Environment]::SetEnvironmentVariable("Path", $newPath, "User")

# Also set for current session
$env:RUSTUP_HOME = $RustPath
$env:CARGO_HOME = $CargoPath
$env:Path = $newPath + ";" + $env:Path

Write-Success "Environment variables configured"

# ============================================================
# STEP 6: Clone Repository
# ============================================================
Write-Host "`n=== STEP 6: Clone Repository ===" -ForegroundColor Yellow

if (-not $SkipClone) {
    if (Test-Path "$RepoPath\.git") {
        Write-Success "Repository already cloned"
    } else {
        Write-Status "Cloning zav-hospital..."

        # Use our portable git
        & "$GitPath\bin\git.exe" clone --recurse-submodules https://github.com/brnsmd/zav-hospital.git $RepoPath

        if (Test-Path "$RepoPath\.git") {
            Write-Success "Repository cloned to $RepoPath"
        } else {
            Write-Err "Clone failed!"
        }
    }
}

# ============================================================
# STEP 7: Setup Python Virtual Environments
# ============================================================
Write-Host "`n=== STEP 7: Python Virtual Environments ===" -ForegroundColor Yellow

# Helper function to setup venv
function Setup-PythonVenv {
    param($ProjectPath, $ProjectName)

    if (-not (Test-Path $ProjectPath)) {
        Write-Warn "$ProjectName not found at $ProjectPath"
        return
    }

    Write-Status "Setting up $ProjectName..."
    Set-Location $ProjectPath

    # Create venv
    & $pythonExe -m venv .venv

    # Install requirements
    $pipExe = ".\.venv\Scripts\pip.exe"
    & $pipExe install --upgrade pip

    if (Test-Path "requirements.txt") {
        & $pipExe install -r requirements.txt
    }
    if (Test-Path "pyproject.toml") {
        & $pipExe install -e .
    }
    if (Test-Path "setup.py") {
        & $pipExe install -e .
    }

    Write-Success "$ProjectName environment ready"
}

Setup-PythonVenv -ProjectPath "$RepoPath\cyberintern-boss" -ProjectName "cyberintern-boss"
Setup-PythonVenv -ProjectPath "$RepoPath\cyberintern" -ProjectName "cyberintern"
Setup-PythonVenv -ProjectPath "$RepoPath\cyberintern_mcp" -ProjectName "cyberintern_mcp"

Set-Location $RepoPath

# ============================================================
# STEP 8: Build Rust TUI
# ============================================================
Write-Host "`n=== STEP 8: Build Boss TUI ===" -ForegroundColor Yellow

if (-not $SkipBuild) {
    if (Test-Path "$RepoPath\boss-tui") {
        Set-Location "$RepoPath\boss-tui"

        if (Test-Path $cargoExe) {
            Write-Status "Building boss-tui (this takes a few minutes)..."
            & $cargoExe build --release

            if (Test-Path ".\target\release\boss-tui.exe") {
                Write-Success "boss-tui built successfully"
            } else {
                Write-Warn "Build may have had issues"
            }
        } else {
            Write-Warn "Cargo not found - skipping TUI build"
        }

        Set-Location $RepoPath
    }
}

# ============================================================
# STEP 9: Install n8n
# ============================================================
Write-Host "`n=== STEP 9: Install n8n ===" -ForegroundColor Yellow

$npmExe = "$NodePath\npm.cmd"
if (Test-Path $npmExe) {
    Write-Status "Installing n8n..."
    & $npmExe install -g n8n
    Write-Success "n8n installed"
} else {
    Write-Warn "npm not found - install n8n manually later"
}

# ============================================================
# STEP 10: Create Startup Scripts
# ============================================================
Write-Host "`n=== STEP 10: Create Startup Scripts ===" -ForegroundColor Yellow

# Create secrets template
$secretsPath = "$BasePath\secrets.env"
if (-not (Test-Path $secretsPath)) {
    @"
# Zav Hospital Secrets
# Edit this file with your actual values

# Airtable
AIRTABLE_TOKEN=your_token_here
AIRTABLE_BASE=appv5BwoWyRhT6Lcr

# n8n
N8N_URL=http://localhost:5678
N8N_API_KEY=your_n8n_key_here

# Boss API
BOSS_API_URL=http://localhost:8083

# CyberIntern
CYBERINTERN_API_URL=http://localhost:8082
CYBERINTERN_USERNAME=admin
CYBERINTERN_PASSWORD=admin123456

# Slack
SLACK_BOT_TOKEN=your_slack_token

# ngrok
NGROK_AUTHTOKEN=your_ngrok_token
"@ | Out-File -FilePath $secretsPath -Encoding ascii
    Write-Status "Created secrets template at $secretsPath"
}

# Create environment setup script
$envSetup = @"
@echo off
REM Zav Environment Setup - Run this first!

set RUSTUP_HOME=$RustPath
set CARGO_HOME=$CargoPath
set PATH=$GitPath\bin;$PythonPath;$PythonPath\Scripts;$NodePath;$NpmPath;$CargoPath\bin;%PATH%

REM Load secrets
for /f "tokens=*" %%a in ('type "$secretsPath" ^| findstr /v "^#"') do set %%a

echo Environment configured!
echo.
"@
$envSetup | Out-File -FilePath "$BasePath\setup-env.bat" -Encoding ascii

# Create start-zav.bat
$startBat = @"
@echo off
title Zav Hospital Server
call "$BasePath\setup-env.bat"

echo.
echo  ============================================
echo   ZAV HOSPITAL SERVER - Starting Services
echo  ============================================
echo.

echo [1/3] Starting CyberIntern App (port 8082)...
start "CyberIntern" cmd /k "call $BasePath\setup-env.bat && cd /d $RepoPath\cyberintern && .venv\Scripts\activate && python -m src.start_web_ui"

timeout /t 3 /nobreak > nul

echo [2/3] Starting Boss API (port 8083)...
start "Boss API" cmd /k "call $BasePath\setup-env.bat && cd /d $RepoPath\cyberintern-boss && .venv\Scripts\activate && python server.py"

timeout /t 3 /nobreak > nul

echo [3/3] Starting n8n (port 5678)...
start "n8n" cmd /k "call $BasePath\setup-env.bat && n8n start"

echo.
echo  All services starting!
echo  - CyberIntern: http://localhost:8082
echo  - Boss API:    http://localhost:8083
echo  - n8n:         http://localhost:5678
echo.
pause
"@
$startBat | Out-File -FilePath "$BasePath\start-zav.bat" -Encoding ascii
Write-Success "Created start-zav.bat"

# Create start-tui.bat
$tuiBat = @"
@echo off
title Boss TUI
call "$BasePath\setup-env.bat"
cd /d $RepoPath\boss-tui
if exist ".\target\release\boss-tui.exe" (
    .\target\release\boss-tui.exe
) else (
    echo boss-tui.exe not found!
    echo Run: cargo build --release
    pause
)
"@
$tuiBat | Out-File -FilePath "$BasePath\start-tui.bat" -Encoding ascii
Write-Success "Created start-tui.bat"

# Create stop script
$stopBat = @"
@echo off
echo Stopping Zav services...
taskkill /fi "WINDOWTITLE eq CyberIntern*" /f 2>nul
taskkill /fi "WINDOWTITLE eq Boss API*" /f 2>nul
taskkill /fi "WINDOWTITLE eq n8n*" /f 2>nul
echo Done.
pause
"@
$stopBat | Out-File -FilePath "$BasePath\stop-zav.bat" -Encoding ascii
Write-Success "Created stop-zav.bat"

# Create shell shortcut
$shellBat = @"
@echo off
title Zav Shell
call "$BasePath\setup-env.bat"
cd /d $RepoPath
cmd /k
"@
$shellBat | Out-File -FilePath "$BasePath\zav-shell.bat" -Encoding ascii
Write-Success "Created zav-shell.bat (opens shell with tools in PATH)"

# ============================================================
# DONE!
# ============================================================
Write-Host @"

    ╔══════════════════════════════════════════════════════════════╗
    ║  🪓 INSTALLATION COMPLETE! FEAST TIME! 🍖                    ║
    ╚══════════════════════════════════════════════════════════════╝

    EVERYTHING INSTALLED TO E: DRIVE!

    Structure:
    $BasePath\
    ├── Tools\          All portable tools (Git, Python, Node, Rust)
    ├── Hospital\       The Zav repository
    ├── secrets.env     Your API keys (EDIT THIS!)
    ├── start-zav.bat   Start all services
    ├── start-tui.bat   Start TUI dashboard
    ├── stop-zav.bat    Stop all services
    └── zav-shell.bat   Open shell with tools in PATH

    NEXT STEPS:
    1. Edit secrets:     notepad $secretsPath
    2. Start services:   $BasePath\start-zav.bat
    3. Open TUI:         $BasePath\start-tui.bat

    NO REBOOT NEEDED! Tools are portable!

"@ -ForegroundColor Green

Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
