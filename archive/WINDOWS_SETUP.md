# Zav Hospital Server - Windows Setup Guide

## Quick Start

### One-Command Install

1. **Open PowerShell as Administrator**
   - Press `Win + X`, select "Windows Terminal (Admin)" or "PowerShell (Admin)"

2. **Run the setup script:**
   ```powershell
   # Allow script execution (one-time)
   Set-ExecutionPolicy Bypass -Scope Process -Force

   # Download and run setup
   irm https://raw.githubusercontent.com/brnsmd/zav-hospital/main/setup-windows.ps1 | iex
   ```

   Or if you already cloned the repo:
   ```powershell
   cd C:\path\to\zav-hospital
   .\setup-windows.ps1
   ```

### What Gets Installed

| Component | Version | Purpose |
|-----------|---------|---------|
| Chocolatey | Latest | Package manager |
| Git | Latest | Version control |
| Python | 3.11 | Backend services |
| Rust | Stable | Boss TUI |
| Node.js | LTS | n8n automation |
| n8n | Latest | Workflow automation |

### Directory Structure

```
C:\Zav\
├── boss-tui\           Rust TUI dashboard
├── cyberintern\        Medical records app (port 8082)
├── cyberintern-boss\   Boss API server (port 8083)
├── cyberintern_mcp\    MCP server for Claude
├── discharge_generator\ Document generator
├── start-zav.bat       Start all services
├── start-tui.bat       Start TUI only
└── stop-zav.bat        Stop all services
```

## Usage

### Start Services
```batch
C:\Zav\start-zav.bat
```
This opens 3 windows:
- CyberIntern App (port 8082)
- Boss API (port 8083)
- n8n (port 5678)

### Start TUI Dashboard
```batch
C:\Zav\start-tui.bat
```

### Stop Services
```batch
C:\Zav\stop-zav.bat
```

## Configuration

### Secrets File
Located at: `%USERPROFILE%\.config\zav-secrets.env`

```env
# Required
BOSS_API_URL=http://localhost:8083
AIRTABLE_TOKEN=your_token_here
AIRTABLE_BASE=appv5BwoWyRhT6Lcr

# CyberIntern
CYBERINTERN_API_URL=http://localhost:8082
CYBERINTERN_USERNAME=admin
CYBERINTERN_PASSWORD=admin123456

# n8n (get from n8n settings)
N8N_URL=http://localhost:5678
N8N_API_KEY=your_n8n_api_key

# Optional (for Slack integration)
SLACK_BOT_TOKEN=xoxb-...
NGROK_AUTHTOKEN=...
```

## Troubleshooting

### "Script cannot be loaded because running scripts is disabled"
```powershell
Set-ExecutionPolicy Bypass -Scope Process -Force
```

### Python not found after install
Close and reopen PowerShell to refresh PATH.

### Rust build fails
```powershell
rustup update
rustup default stable
```

### Port already in use
```powershell
# Find what's using port 8082
netstat -ano | findstr :8082

# Kill by PID
taskkill /PID <pid> /F
```

## Manual Installation

If the script fails, install manually:

```powershell
# 1. Install Chocolatey
Set-ExecutionPolicy Bypass -Scope Process -Force
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 2. Install packages
choco install git python311 rustup nodejs-lts -y

# 3. Restart PowerShell, then:
rustup default stable
npm install -g n8n

# 4. Clone repo
git clone --recurse-submodules https://github.com/brnsmd/zav-hospital.git C:\Zav

# 5. Setup Python environments (for each folder with requirements.txt)
cd C:\Zav\cyberintern-boss
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# 6. Build TUI
cd C:\Zav\boss-tui
cargo build --release
```

## Updating

```powershell
cd C:\Zav
git pull
git submodule update --remote --merge
```

---
*Setup script by Grug & Clug - Barbarian Coders 🪓*
