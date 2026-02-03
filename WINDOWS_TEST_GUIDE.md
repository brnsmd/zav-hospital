# Windows Testing Guide

**Last Updated:** 2026-02-03 12:15

## Quick Start

1. Transfer these files to Windows machine:
   - `/var/home/htsapenko/Projects/zav-installer/` (entire directory)
   - `/var/home/htsapenko/Projects/Zav/boss-tui/` (entire directory)

2. Install Rust on Windows:
   ```powershell
   # Download and run: https://rustup.rs
   rustup-init.exe
   ```

3. Build boss-tui on Windows:
   ```powershell
   cd boss-tui
   cargo build --release
   # Binary at: target\release\boss-tui.exe
   ```

4. Build installer on Windows:
   ```powershell
   cd zav-installer\installer
   cargo build --release
   # Binary at: target\release\zav-installer.exe
   ```

5. Run installer:
   ```powershell
   .\target\release\zav-installer.exe
   ```

## What to Test

### Boss TUI (All Night Shift Features)

**Tier 1 - Non-Negotiables:**
- [ ] Press `0` - Audit log viewer shows WHO/WHAT/WHEN entries
- [ ] Check header - Data freshness indicators (green <60s, yellow <10m, red >10m)

**Tier 2 - UX Polish:**
- [ ] Footer - Contextual shortcuts change based on state
- [ ] Patients tab - Press `s` to sort, `f` to filter, space to multi-select
- [ ] Table columns - Ctrl+[ and Ctrl+] to resize columns
- [ ] Header - Sparkline shows patient count trend (10 data points)

**Tier 3 - Performance:**
- [ ] Service health badges in header (green/yellow/red)
- [ ] Tab switching - Should feel fast (<50ms) with prefetching
- [ ] Offline mode - Disconnect network, verify cached data still works

**Tier 4 - Visualization:**
- [ ] Wards tab - 2D bed grid with arrow key navigation (h/j/k/l)
- [ ] Select a bed - Details panel shows patient info on right side
- [ ] Bed colors - ICU (red), needs cleaning (yellow), clean (green)

**Tier 5 - VLK Timeline:**
- [ ] VLK tab - Progress bars with color zones (green/yellow/red)
- [ ] Timeline - Shows days remaining until VLK deadline
- [ ] Navigation - Arrow keys sync between timeline and table

**Tier 6 - Medical Features:**
- [ ] Alerts tab - Triage layout (Critical/Warning/Info sections)
- [ ] Quick actions - Press `.` on patient for context menu
- [ ] Generate PDF - Select patient, press `.`, choose "Generate 027/о PDF"
- [ ] Generate Dovidka - Select patient, press `.`, choose "Hospital Certificate"
- [ ] Copy patient info - Press `.`, choose "Copy to Clipboard"

**Auto-Updater:**
- [ ] Press `u` - Check for updates from GitHub
- [ ] If update available - Download and install
- [ ] Windows-specific - Update uses batch script after exit

### Installer (Phase 1 & 2)

**Wizard Screens:**
1. [ ] Welcome screen - Shows system requirements check (pass/warn/fail)
2. [ ] Install directory - Default: `C:\Users\<user>\AppData\Local\Zav`
3. [ ] Airtable config - Enter token and base ID
4. [ ] Slack config - Enter bot token
5. [ ] n8n config - Enter URL (default: http://localhost:5678)
6. [ ] Progress screen - Extraction progress bar

**Installation:**
- [ ] Binary extraction - boss-tui.exe extracted to install dir
- [ ] Config generation - config.toml and .env created with secure API keys
- [ ] Workflows - n8n workflows extracted to workflows/ directory
- [ ] Permissions - Files have correct permissions

**Post-Install:**
- [ ] Run extracted boss-tui.exe - Should start without errors
- [ ] Config validation - Check config.toml has correct values
- [ ] API key - Auto-generated BOSS_API_KEY in .env

## Expected Sizes

- **boss-tui.exe**: ~42MB (stripped release binary)
- **zav-installer.exe**: ~30MB (contains compressed boss-tui + installer code)
- **Installed size**: ~50MB total (boss-tui + configs + workflows)

## Known Issues

None currently. All 73 boss-tui tests and 43 installer tests passing on Linux.

## If Something Fails

1. **Compilation errors**: Check Rust version (rustc --version), should be 1.75+
2. **Missing dependencies**: Windows builds don't need system deps like Linux
3. **Installer can't find boss-tui**: Build boss-tui first, installer looks in ../boss-tui/target/release/
4. **Auto-updater fails**: Normal if GitHub doesn't have newer release yet

## After Testing

Report results in:
- `/var/home/htsapenko/Projects/Zav/WINDOWS_TEST_RESULTS.md`

Include:
- Which features work ✅
- Which features fail ❌
- Any Windows-specific issues
- Screenshots if UI looks different

## Next Steps After Successful Test

1. **Phase 3**: Setup GitHub Actions for automated releases
2. **Phase 4**: Full Rust stack migration (replace Python/FastAPI Boss API)
3. **Distribution**: Publish v1.0.0 release with Windows + Linux binaries
