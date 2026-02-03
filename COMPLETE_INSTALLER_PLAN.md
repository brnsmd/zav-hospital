# COMPLETE BINGO-BONGO INSTALLER - Implementation Plan

**Goal:** Single-click installer that detects, installs, and configures EVERYTHING needed for Zav Hospital on Windows.

**Status:** Planning → Implementation
**Assignee:** Claude (Continuous work until complete)
**Created:** 2026-02-03

---

## 🎯 Feature Requirements

### 1. Existing Installation Detection
- [ ] Check for existing `.zav` directory
- [ ] Check for existing boss-tui process running
- [ ] Show found installations with paths
- [ ] Offer options:
  - Delete old installation (clean install)
  - Upgrade in place (keep configs)
  - Install to different location
  - Cancel installation

### 2. Node.js Detection & Installation
- [ ] Check if `node.exe` in PATH
- [ ] Verify version (need v18+)
- [ ] If missing or old:
  - Check if `winget` available
  - Run: `winget install OpenJS.NodeJS.LTS --silent`
  - Verify installation succeeded
  - Refresh PATH environment

### 3. n8n Detection & Installation
- [ ] Check if `n8n` in PATH
- [ ] Run: `npm list -g n8n` to verify
- [ ] If missing:
  - Run: `npm install -g n8n`
  - Verify installation succeeded
  - Show n8n version installed

### 4. Windows Terminal Detection & Installation
- [ ] Check if Windows Terminal installed
  - Windows 11: Usually pre-installed
  - Windows 10: Check `wt.exe` exists
- [ ] If missing:
  - Run: `winget install Microsoft.WindowsTerminal --silent`
  - Verify installation
- [ ] Get settings.json path: `%LOCALAPPDATA%\Packages\Microsoft.WindowsTerminal_8wekyb3d8bbwe\LocalState\settings.json`

### 5. Boss-TUI Installation
- [ ] Extract boss-tui.exe to install directory
- [ ] Verify SHA256 checksum
- [ ] Set executable permissions
- [ ] Create data directory structure:
  ```
  %USERPROFILE%\.zav\
  ├── boss-tui.exe
  ├── config.toml
  ├── data\
  ├── logs\
  └── workflows\
  ```

### 6. Configuration Setup
- [ ] Generate config.toml with wizard inputs
- [ ] Create .env file with secrets
- [ ] Set up logging configuration
- [ ] Create initial database (if needed)

### 7. Shortcuts Creation
- [ ] Desktop shortcut: `Boss-TUI.lnk`
  - Target: `wt.exe -p "Boss-TUI"`
  - Icon: Extract from boss-tui.exe or use default
  - Working directory: `%USERPROFILE%\.zav`
- [ ] Start Menu entry: `%APPDATA%\Microsoft\Windows\Start Menu\Programs\Boss-TUI.lnk`
- [ ] Quick Launch (optional)

### 8. Windows Terminal Profile
- [ ] Read existing settings.json
- [ ] Add Boss-TUI profile:
  ```json
  {
    "name": "Boss-TUI",
    "commandline": "%USERPROFILE%\\.zav\\boss-tui.exe",
    "startingDirectory": "%USERPROFILE%\\.zav",
    "icon": "%USERPROFILE%\\.zav\\boss-tui.exe",
    "colorScheme": "One Half Dark",
    "font": {
      "face": "Cascadia Code",
      "size": 11
    }
  }
  ```
- [ ] Write updated settings.json
- [ ] Validate JSON syntax

### 9. Optional Features (Ask User)
- [ ] Add boss-tui to PATH
  - Modify user PATH environment variable
  - Allow running `boss-tui` from any directory
- [ ] Auto-start on login
  - Create registry entry: `HKCU\Software\Microsoft\Windows\CurrentVersion\Run`
  - Or create shortcut in Startup folder
- [ ] n8n auto-start service
  - Create batch script to start n8n
  - Add to startup

### 10. Post-Installation
- [ ] Show completion screen with:
  - Installation summary
  - Installed components versions
  - Shortcuts created
  - Next steps (how to launch)
- [ ] Offer to launch Boss-TUI immediately
- [ ] Create uninstaller script

---

## 📐 Architecture Changes

### New Modules to Create

```
installer/src/
├── windows/
│   ├── mod.rs           # Windows-specific utilities
│   ├── winget.rs        # winget command wrapper
│   ├── npm.rs           # npm command wrapper
│   ├── shortcuts.rs     # .lnk file creation
│   ├── terminal.rs      # Windows Terminal config
│   ├── registry.rs      # Windows registry operations
│   └── existing.rs      # Detect existing installations
├── install/
│   ├── mod.rs           # Installation orchestrator
│   ├── node.rs          # Node.js installation
│   ├── n8n.rs           # n8n installation
│   ├── terminal.rs      # Windows Terminal installation
│   └── bosstui.rs       # Boss-TUI extraction
└── wizard.rs (update)   # Add new wizard steps
```

### New Wizard Steps

```
1. Welcome + System Check (existing)
2. **Existing Installation Detection** (NEW)
3. Installation Directory (existing)
4. Airtable Config (existing)
5. Slack Config (existing)
6. n8n Config (existing)
7. **Optional Features** (NEW)
   - Add to PATH?
   - Auto-start on login?
   - Install n8n as service?
8. **Component Installation** (NEW)
   - Node.js check/install
   - n8n check/install
   - Windows Terminal check/install
9. Progress (update to show component progress)
10. **Completion** (NEW)
    - Summary
    - Launch now?
```

---

## 🔧 Implementation Steps

### Phase 1: Detection & Cleanup (Week 1, Day 1-2)

**Day 1: Existing Installation Detection**
- [ ] Create `windows/existing.rs`
- [ ] Scan for `.zav` directories
- [ ] Check running processes for `boss-tui.exe`
- [ ] Find Windows Terminal profiles
- [ ] Collect registry entries
- [ ] Create `ExistingInstallation` struct with paths
- [ ] Add wizard step to show findings
- [ ] Implement delete/upgrade/cancel logic

**Day 2: Winget & npm Detection**
- [ ] Create `windows/winget.rs`
- [ ] Function: `check_winget_available() -> bool`
- [ ] Function: `run_winget(args: &[&str]) -> Result<Output>`
- [ ] Create `windows/npm.rs`
- [ ] Function: `check_npm_available() -> bool`
- [ ] Function: `check_package_installed(name: &str) -> bool`
- [ ] Function: `install_package(name: &str) -> Result<()>`

### Phase 2: Component Installation (Week 1, Day 3-4)

**Day 3: Node.js & n8n Installation**
- [ ] Create `install/node.rs`
- [ ] Detect Node.js version
- [ ] Compare against minimum version (v18)
- [ ] Install via winget if missing/old
- [ ] Refresh environment PATH
- [ ] Verify installation
- [ ] Create `install/n8n.rs`
- [ ] Check n8n installation
- [ ] Install via npm if missing
- [ ] Verify n8n command works
- [ ] Return installed version

**Day 4: Windows Terminal Installation**
- [ ] Create `install/terminal.rs`
- [ ] Detect Windows version (10 vs 11)
- [ ] Check if Windows Terminal installed
- [ ] Install via winget if missing
- [ ] Locate settings.json path
- [ ] Read/parse existing settings
- [ ] Add Boss-TUI profile
- [ ] Write updated settings
- [ ] Validate JSON

### Phase 3: Shortcuts & Integration (Week 1, Day 5)

**Day 5: Shortcuts & Registry**
- [ ] Create `windows/shortcuts.rs`
- [ ] Use `windows-rs` crate for IShellLink
- [ ] Function: `create_desktop_shortcut()`
- [ ] Function: `create_start_menu_shortcut()`
- [ ] Extract icon from boss-tui.exe
- [ ] Create `windows/registry.rs`
- [ ] Function: `add_to_path()`
- [ ] Function: `add_to_startup()`
- [ ] Function: `remove_from_path()`
- [ ] Function: `remove_from_startup()`

### Phase 4: Wizard Updates (Week 1, Day 6)

**Day 6: Wizard Integration**
- [ ] Update `wizard.rs` with new steps
- [ ] Add `ExistingInstallationStep`
- [ ] Add `OptionalFeaturesStep`
- [ ] Add `ComponentInstallationStep`
- [ ] Add `CompletionStep`
- [ ] Update progress screen to show components
- [ ] Add component installation UI
- [ ] Show real-time output from winget/npm
- [ ] Handle installation failures gracefully

### Phase 5: Testing & Polish (Week 1, Day 7)

**Day 7: Testing & Documentation**
- [ ] Test on clean Windows 11 VM
- [ ] Test on clean Windows 10 VM
- [ ] Test upgrade from existing installation
- [ ] Test with Node.js already installed
- [ ] Test with n8n already installed
- [ ] Test with Windows Terminal already installed
- [ ] Test all optional features
- [ ] Create uninstaller script
- [ ] Update README with new features
- [ ] Record demo video

---

## 📦 Dependencies to Add

```toml
[dependencies]
# Existing
anyhow = "1.0"
thiserror = "1.0"
ratatui = "0.29"
crossterm = "0.28"
arboard = "3.4"
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# NEW for Windows features
[target.'cfg(windows)'.dependencies]
windows = { version = "0.58", features = [
    "Win32_System_Com",           # For IShellLink (shortcuts)
    "Win32_UI_Shell",             # For shell operations
    "Win32_System_Registry",      # For registry access
    "Win32_Foundation",
    "Win32_System_Environment",   # For PATH manipulation
] }
winreg = "0.52"                   # Easier registry access
```

---

## 🎨 UI Mockups

### Existing Installation Detection Screen

```
╔══════════════════════════════════════════════════════════╗
║  Existing Installation Detected                          ║
╚══════════════════════════════════════════════════════════╝

Found Boss-TUI installation at:
  C:\Users\YourName\.zav\

Components found:
  ✓ boss-tui.exe (v0.9.5)
  ✓ config.toml
  ✓ Windows Terminal profile
  ✓ Desktop shortcut

What would you like to do?

  ○ Clean Install (delete old installation)
  ● Upgrade (keep configs, replace binaries)
  ○ Install to different location
  ○ Cancel

[Enter] Continue  [↑↓] Select  [Esc] Cancel
```

### Component Installation Screen

```
╔══════════════════════════════════════════════════════════╗
║  Installing Components                                   ║
╚══════════════════════════════════════════════════════════╝

[✓] Node.js v20.11.0
    Already installed

[~] n8n
    Installing via npm...
    ████████████████░░░░░░░░░░ 65%

[░] Windows Terminal
    Waiting...

[░] Boss-TUI
    Waiting...

[░] Shortcuts
    Waiting...
```

### Completion Screen

```
╔══════════════════════════════════════════════════════════╗
║  Installation Complete! 🎉                               ║
╚══════════════════════════════════════════════════════════╝

Installed Components:
  ✓ Node.js v20.11.0
  ✓ n8n v1.23.0
  ✓ Windows Terminal (profile added)
  ✓ Boss-TUI v1.0.0
  ✓ Desktop shortcut created
  ✓ Start Menu entry created

Installation Directory:
  C:\Users\YourName\.zav\

How to Launch:
  • Double-click "Boss-TUI" on Desktop
  • Or press Windows+R, type "boss-tui"
  • Or open Windows Terminal → Select "Boss-TUI"

Launch Boss-TUI now? [Y/n]
```

---

## 🧪 Test Plan

### Manual Tests

1. **Fresh Install (No existing software)**
   - Windows 10 VM (clean)
   - Windows 11 VM (clean)
   - Verify all components install
   - Verify shortcuts work
   - Verify Windows Terminal profile works

2. **Partial Install (Some components exist)**
   - Node.js installed, n8n missing
   - n8n installed, Node.js missing
   - Windows Terminal missing
   - Verify installer detects and fills gaps

3. **Upgrade Scenario**
   - Old Boss-TUI v0.9 installed
   - Upgrade to v1.0
   - Verify configs preserved
   - Verify shortcuts updated

4. **Optional Features**
   - Test PATH addition
   - Test auto-start on login
   - Test uninstall

### Automated Tests

```rust
#[cfg(test)]
mod tests {
    #[test]
    fn test_detect_nodejs() { }

    #[test]
    fn test_parse_npm_version() { }

    #[test]
    fn test_detect_existing_installation() { }

    #[test]
    fn test_create_shortcut_metadata() { }

    #[test]
    fn test_windows_terminal_profile_json() { }
}
```

---

## 📝 File Checklist

**New Files to Create:**
- [ ] `installer/src/windows/mod.rs`
- [ ] `installer/src/windows/winget.rs`
- [ ] `installer/src/windows/npm.rs`
- [ ] `installer/src/windows/shortcuts.rs`
- [ ] `installer/src/windows/terminal.rs`
- [ ] `installer/src/windows/registry.rs`
- [ ] `installer/src/windows/existing.rs`
- [ ] `installer/src/install/mod.rs`
- [ ] `installer/src/install/node.rs`
- [ ] `installer/src/install/n8n.rs`
- [ ] `installer/src/install/terminal.rs`
- [ ] `installer/src/install/bosstui.rs`

**Files to Update:**
- [ ] `installer/Cargo.toml` (add windows dependencies)
- [ ] `installer/src/wizard.rs` (add new steps)
- [ ] `installer/src/extract.rs` (integrate with install module)
- [ ] `installer/build.rs` (ensure Windows build works)

**Files to Create (Post-Install):**
- [ ] `uninstall.bat` (generated during install)
- [ ] `start-n8n.bat` (if n8n service requested)

---

## 🚀 Success Criteria

**Installer passes if:**
- [ ] Detects existing installations correctly
- [ ] Installs Node.js if missing (verified with `node --version`)
- [ ] Installs n8n if missing (verified with `n8n --version`)
- [ ] Installs Windows Terminal if missing (verified with `wt.exe`)
- [ ] Extracts boss-tui.exe successfully
- [ ] Creates desktop shortcut that launches Boss-TUI
- [ ] Creates Start Menu entry
- [ ] Adds Windows Terminal profile
- [ ] Boss-TUI launches successfully from shortcut
- [ ] Windows Terminal profile works
- [ ] Optional features work (PATH, auto-start)
- [ ] Uninstaller removes everything cleanly

---

## 📊 Progress Tracking

**Status Codes:**
- ✅ Complete
- 🔄 In Progress
- ⏸️ Blocked
- ❌ Failed
- ⏭️ Skipped

### Phase 1: Detection & Cleanup
- ✅ Existing installation detection
- ✅ Winget wrapper
- ✅ npm wrapper

### Phase 2: Component Installation
- ✅ Node.js installation
- ✅ n8n installation
- ✅ Windows Terminal installation

### Phase 3: Shortcuts & Integration
- ✅ Shortcut creation
- ✅ Windows Terminal profile
- ✅ Registry operations

### Phase 4: Wizard Updates
- ✅ New wizard steps
- ✅ Progress UI
- ⏸️ Error handling (integration pending)

### Phase 5: Testing & Polish
- ⏸️ VM testing
- ⏸️ Documentation
- ⏸️ Demo video

---

## 🎯 Next Action

**When you return from /clear:**

1. Read this plan
2. Start with Phase 1, Day 1: Existing Installation Detection
3. Create `installer/src/windows/existing.rs`
4. Implement detection logic
5. Continue until complete

**No stopping. No asking. Just build until EVERYTHING works.**

---

**Built by:** Claude & Grug
**Target:** Windows 10/11
**Installer Size:** ~40MB (includes all embedded assets)
**Install Time:** 2-5 minutes (depending on components to install)
