#!/bin/bash
# Copy ZAV Installer to USB Flash Drive
# Run this script to copy everything needed for Windows installation

set -e  # Exit on error

echo "🚀 ZAV Installer - USB Copy Script"
echo "=================================="
echo

# Check if USB is mounted
USB_MOUNT="/mnt/usb"
if [ ! -d "$USB_MOUNT" ]; then
    echo "📌 Mounting USB drive..."
    sudo mkdir -p "$USB_MOUNT"
    sudo mount /dev/sda1 "$USB_MOUNT"
    echo "✅ USB mounted at $USB_MOUNT"
else
    if ! mountpoint -q "$USB_MOUNT"; then
        echo "📌 Mounting USB drive..."
        sudo mount /dev/sda1 "$USB_MOUNT"
        echo "✅ USB mounted at $USB_MOUNT"
    else
        echo "✅ USB already mounted at $USB_MOUNT"
    fi
fi

echo
echo "📦 Available space on USB:"
df -h "$USB_MOUNT" | tail -1
echo

# Create ZAV directory on USB
ZAV_DIR="$USB_MOUNT/ZAV"
echo "📁 Creating directory structure..."
sudo mkdir -p "$ZAV_DIR/zav-installer"
sudo mkdir -p "$ZAV_DIR/boss-tui"
echo "✅ Directories created"

echo
echo "📋 Copying files..."
echo

# Copy zav-installer project
echo "  ➜ Copying zav-installer source code..."
sudo rsync -a --info=progress2 \
    --exclude='target' \
    --exclude='.git' \
    /var/home/htsapenko/Projects/zav-installer/ \
    "$ZAV_DIR/zav-installer/"
echo "  ✅ zav-installer copied"

# Copy boss-tui project
echo "  ➜ Copying boss-tui source code..."
sudo rsync -a --info=progress2 \
    --exclude='target' \
    --exclude='.git' \
    /var/home/htsapenko/Projects/Zav/boss-tui/ \
    "$ZAV_DIR/boss-tui/"
echo "  ✅ boss-tui copied"

# Copy pre-built Linux binaries (for reference)
echo "  ➜ Copying pre-built Linux binaries..."
sudo mkdir -p "$ZAV_DIR/linux-binaries"
sudo cp /var/home/htsapenko/Projects/Zav/boss-tui/target/release/boss-tui \
    "$ZAV_DIR/linux-binaries/boss-tui"
sudo cp /var/home/htsapenko/Projects/zav-installer/target/release/zav-installer \
    "$ZAV_DIR/linux-binaries/zav-installer"
echo "  ✅ Linux binaries copied"

# Copy installation instructions
echo "  ➜ Copying installation instructions..."
cat > /tmp/INSTALL_WINDOWS.txt << 'EOF'
========================================
ZAV INSTALLER - WINDOWS INSTALLATION
========================================

STEP 1: Install Rust
----------------------
1. Open web browser and go to: https://rustup.rs
2. Download: rustup-init.exe
3. Run rustup-init.exe
4. Follow prompts (choose default installation)
5. Restart PowerShell/Command Prompt after installation

Verify:
  Open PowerShell and run:
    rustc --version
    cargo --version


STEP 2: Copy Files to Windows
-------------------------------
Copy these two folders from the USB drive to your Windows machine:

  USB:\ZAV\zav-installer\  →  C:\Dev\zav-installer\
  USB:\ZAV\boss-tui\       →  C:\Dev\boss-tui\

(You can use any location, just keep the folder structure)


STEP 3: Build Boss TUI
-----------------------
Open PowerShell and run:

  cd C:\Dev\boss-tui
  cargo build --release

This will take 3-5 minutes (first build compiles 200+ dependencies).

Binary will be at: C:\Dev\boss-tui\target\release\boss-tui.exe (~42MB)

Verify:
  .\target\release\boss-tui.exe --version


STEP 4: Build Installer
-------------------------
In PowerShell, run:

  cd C:\Dev\zav-installer\installer
  cargo build --release

This will take 15-20 seconds.

Binary will be at: C:\Dev\zav-installer\installer\target\release\zav-installer.exe (~30MB)

Verify:
  .\target\release\zav-installer.exe --version
  (Should show: Zav Installer v1.0.0)


STEP 5: Run Installer
-----------------------
  .\target\release\zav-installer.exe

This opens a 6-screen wizard:
  1. Welcome - Shows system check
  2. Install Directory - Choose location (default: C:\Users\<You>\AppData\Local\Zav)
  3. Airtable Config - Enter your token and base ID
  4. Slack Config - Enter bot token
  5. n8n Config - Enter URL (default: http://localhost:5678)
  6. Progress - Watch installation

After installation, boss-tui.exe will be in the install directory.


STEP 6: Run Boss TUI
---------------------
  cd C:\Users\<You>\AppData\Local\Zav
  .\boss-tui.exe

Test new features:
  Press 0      → Audit log
  Press t      → Transfer patient between infection zones (in Wards tab)
  Press .      → Quick actions menu
  Press u      → Check for updates
  Arrow keys   → Navigate (Wards tab shows infection zones)


INFECTION CONTROL ZONES (NEW!)
================================
The Wards tab now shows patients grouped by infection risk:

  🟢 Clean Zone    - ORIF (ОРІВ), closed wounds (закриті рани)
  🟡 Medium Zone   - Open wounds, not infected (відкриті рани)
  🔴 Infected Zone - Infected wounds (інфіковані рани)

Features:
  • Press 't' on a patient to mark for zone transfer
  • Misplaced patients show ⚠️ warning
  • Zone counts shown in header
  • Color-coded by infection risk


TROUBLESHOOTING
================

Build fails - Missing MSVC:
  Download "Build Tools for Visual Studio 2022":
  https://visualstudio.microsoft.com/downloads/

  Install:
    ✓ Desktop development with C++
    ✓ Windows 10/11 SDK

Build crashes - Out of memory:
  cargo build --release -j 2

Slow compilation:
  First build: 5-10 minutes (normal)
  Later builds: ~20 seconds


WHAT'S INCLUDED
================
✅ Boss TUI with ALL enhancements:
   - Audit trail logging
   - Smart tables (sort/filter/multi-select)
   - Triage alerts (Critical/Warning/Info)
   - PDF generation (027/о, Довідка)
   - Infection control zones (NEW!)
   - Zone transfer feature (NEW!)
   - Ward infection tracking (NEW!)
   - Auto-updater
   - 2D ward grid
   - VLK timeline
   - Quick actions menu
   - Service health tracking
   - Background prefetching

✅ ZAV Installer:
   - Single-file installer (30MB)
   - TUI wizard (6 screens)
   - Auto-generated secure keys
   - System requirements check


TESTS
======
Run tests to verify everything works:

Boss TUI:
  cd C:\Dev\boss-tui
  cargo test --lib
  Expected: 80+ tests passing

Installer:
  cd C:\Dev\zav-installer\installer
  cargo test
  Expected: 43 tests passing


SUPPORT
========
If you encounter issues:
  1. Check error message
  2. Verify Rust version: rustc --version (should be 1.75+)
  3. Check disk space (need ~5GB for build)
  4. Try clean rebuild: cargo clean && cargo build --release

========================================
Generated: 2026-02-03
ZAV Hospital Management System
========================================
EOF

sudo cp /tmp/INSTALL_WINDOWS.txt "$ZAV_DIR/INSTALL_WINDOWS.txt"
echo "  ✅ Installation instructions copied"

# Create quick reference card
cat > /tmp/QUICK_REFERENCE.txt << 'EOF'
ZAV BOSS TUI - QUICK REFERENCE CARD
=====================================

KEYBOARD SHORTCUTS
------------------
Tab Numbers:
  1-9       Switch tabs
  0         Audit log viewer

General:
  q         Quit
  r         Refresh data
  h         Help
  Esc       Back/Cancel

Tables:
  s         Sort
  f         Filter
  Space     Multi-select
  Enter     Details
  Ctrl+[    Decrease column width
  Ctrl+]    Increase column width

Patient Actions:
  .         Quick actions menu
  d         Discharge (requires confirmation)
  t         Transfer zone (Wards tab only)

Wards Tab (Infection Zones):
  Arrow↑↓   Navigate patients
  t         Mark patient for zone transfer
  Enter     View details

Updates:
  u         Check for updates


INFECTION ZONES
----------------
🟢 Clean    ORIF, closed wounds
🟡 Medium   Open wounds (not infected)
🔴 Infected Infected wounds

Warning Signs:
  ⚠️ Patient in wrong zone
  🔄 Transfer pending


QUICK ACTIONS MENU (.)
-----------------------
1. Schedule VLK
2. Extend Treatment
3. Mark for Discharge
4. Add Note
5. Copy to Clipboard
6. Open in Browser
7. Open in n8n
8. Generate 027/о PDF
9. Generate Dovіdka


DATA FRESHNESS
---------------
🟢 Green   < 60 seconds (real-time)
🟡 Yellow  1-10 minutes (cached)
🔴 Red     > 10 minutes (stale)


AUDIT TRAIL
------------
Press 0 to view:
  • WHO performed action
  • WHAT was done
  • WHEN it happened
  • Color-coded by action type


SERVICE HEALTH
---------------
Header badges show:
  ✅ Healthy
  ⚠️  Degraded (using cache)
  ❌ Unavailable
  💀 Failed

Boss TUI works offline with cached data!


ALERTS TAB
-----------
Sections:
  🔴 CRITICAL  Urgent attention needed
  🟡 WARNING   Attention needed soon
  🟢 INFO      For your information

Actions:
  Space  Acknowledge alert
  a      Acknowledge all in section
  s      Snooze alert (24 hours)


STATS TAB
----------
Shows:
  • Daily report (Polars analytics)
  • Ward occupancy
  • Doctor patient counts
  • Average stay duration
  • VLK statistics


WINDOWS-SPECIFIC
-----------------
Auto-updater:
  • Download happens in background
  • Batch script applies update after exit
  • Old binary backed up automatically

Installation:
  Default: C:\Users\<You>\AppData\Local\Zav
  Config:  C:\Users\<You>\AppData\Local\Zav\config.toml
  Logs:    C:\Users\<You>\AppData\Local\Zav\audit.log


BUILD INFO
-----------
Boss TUI: 42MB (80+ tests passing)
Installer: 30MB (43 tests passing)
Features: 22 Opus agents × 5 waves
Version: Built 2026-02-03

=====================================
EOF

sudo cp /tmp/QUICK_REFERENCE.txt "$ZAV_DIR/QUICK_REFERENCE.txt"
echo "  ✅ Quick reference card copied"

# Fix permissions (make readable on Windows)
echo
echo "🔐 Setting permissions..."
sudo chmod -R a+rw "$ZAV_DIR"
echo "✅ Permissions set"

# Show summary
echo
echo "✨ COPY COMPLETE!"
echo "=================="
echo
echo "📁 Files copied to USB:"
echo "  $ZAV_DIR/"
echo "  ├── zav-installer/       (source code)"
echo "  ├── boss-tui/            (source code)"
echo "  ├── linux-binaries/      (pre-built for reference)"
echo "  ├── INSTALL_WINDOWS.txt  (installation guide)"
echo "  └── QUICK_REFERENCE.txt  (keyboard shortcuts)"
echo
echo "📊 Disk usage:"
du -sh "$ZAV_DIR"
echo
echo "🎯 Next steps:"
echo "  1. Safely eject USB drive"
echo "  2. Plug into Windows machine"
echo "  3. Read INSTALL_WINDOWS.txt"
echo "  4. Follow installation steps"
echo
echo "🦞 The hunt is ready for Windows!"
