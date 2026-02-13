# Zav Project Status

**Updated:** 2026-02-13 10:00
**Status:** BROKEN — SYNC DOES NOT WORK. FULL LINE-BY-LINE AUDIT REQUIRED.

---

## 🔴 2026-02-13: FULL STOP — STARTING FROM ZERO

**What happened:** Multiple sessions of "fix and deploy" failed. Sync button (`s`) does nothing visible. Enrichment data never populates. Debug builds deployed but behavior unchanged. Root cause: we keep guessing instead of reading. Multiple audit teams found 91 issues but fixes were applied without verifying the actual runtime behavior.

**The real problems (unverified — previous session's guesses):**
- Sync trigger (`s` key in TUI) → calls `trigger_boss_sync()` → calls Boss API `POST /sync` → supposed to import from CyberIntern. **NEVER VERIFIED AT RUNTIME.**
- CyberIntern API at localhost:8082 → assumed reachable. **NEVER VERIFIED.**
- Database at `C:\ZavBoss\data\zav.db` → cleared on 2026-02-13. Fresh start.
- The TUI binary at `windows-deploy/boss-tui.exe` → 162MB debug build deployed 2026-02-13 09:53.

**What the next session MUST do:**

### WINDUG MODE (Write It N' Debug)
Every single step must be:
1. Read the actual code line by line
2. Verify with curl/logs what actually happens at runtime
3. Track in beads before AND after
4. Commit after each verified fix

### The audit order:
1. **START.bat → ZAV.exe → boss-tui.exe launch chain** — verify env vars arrive
2. **`s` key press** → trace through main.rs event loop → api/boss.rs → server route → actual HTTP call
3. **CyberIntern API** — curl it directly, verify it returns patients
4. **Sync route** — read every line of perform_ci_import(), verify each step
5. **DB writes** — verify data actually lands in SQLite after sync
6. **UI refresh** — verify TUI re-fetches after sync completes
7. **Maxun** — evaluate as EMR API replacement for cleaner data source

### Previous changes (may or may not be working):
- boss-tui commit `1e2eb3a`: 12 files changed, sync pipeline rewrite
- Concurrent sync guard, direct CI ID enrichment, status in upsert
- COALESCE for doctor/ward/bed, hospitalized_only=false
- surgical_treatment included, instrumental_tests fixed
- Help popup corrected, popup 1-6 keys, UTF-8 safe truncation

---

## 🔧 PREVIOUS: 4-Team Opus Audit Sprint (2026-02-12)

**4 Opus Investigation Teams** deployed in parallel:
- **Team Alpha (Bugs)**: Found 16 bugs (2 P0, 3 P1, 4 P2, 7 P3)
- **Team Bravo (UX)**: Found 46 UX issues (2 CRITICAL, 8 MEDIUM)
- **Team Charlie (UI)**: Found 22 UI issues (3 HIGH, 7 MEDIUM)
- **Team Delta (Data Flow)**: Found 9 data integrity + 8 security issues

**Fixed in this sprint:**

### Sync Pipeline (was completely broken):
- Concurrent sync guard (reject if already running)
- sync_running flag properly toggled (was never set)
- Health check timeout (5s, was infinite)
- CI client: auth optional, page_size=100 pagination
- Direct CI ID enrichment (eliminated failing re-search)
- Status field in INSERT/UPDATE (discharged patients now tracked)
- COALESCE for doctor/ward/bed (prevents NULL overwrites on re-sync)
- fetch_patients uses hospitalized_only=false (TUI gets all patients)
- Discharge invalidates all caches

### Data Flow (enrichment was incomplete):
- surgical_treatment now included in treatment (was dropped)
- instrumental_tests now maps xray+additional_methods (was duplicate of analyses)
- workplace + discharge_date added to TUI model (was lost at API boundary)
- Certificate PDF now gets workplace from patient data
- All 12 enrichment fields displayed in CyberIntern popup tab

### UX/UI:
- Popup sub-tab keys 1-6 wired in ZAV mode
- Help popup corrected (wrong tab numbers, removed dead N8N section)
- Shortcuts hint "1-4" -> "1-6"
- Empty state for discharged tab
- UTF-8 safe truncation (prevents panic on Ukrainian text)
- G key for jump-to-bottom in popup

### Known Issues (not yet fixed):
- SEC-01: No API key validation on server routes
- SEC-03: Passwords stored plaintext in SQLite
- DATA-02: 027/o PDF still missing 8 clinical narrative fields
- UX-22: `d` key force-discharges without confirmation
- UI-03: highlight_symbol column overflow
- UI-17: Operations table not selectable

---

## 🚀 Night Shift Complete (2026-02-03)

**22 Opus Agents** deployed across 5 waves:
- ✅ **ZAV Smart Installer** - Phase 1 & 2 complete (66 tests passing)
- ✅ **Boss TUI Enhancements** - 6 tiers implemented (73 tests passing)
- ✅ **Binaries Ready** - Linux builds tested, Windows pending
- 📄 **Documentation** - Full guides in NIGHT_SHIFT_SUMMARY.md, BUILD_SUMMARY.md

**New Capabilities:**
- Audit trail logging (WHO/WHAT/WHEN)
- Smart tables (sort/filter/multi-select)
- Triage-style alerts (Critical/Warning/Info)
- PDF generation (027/о, Довідка)
- Ward 2D grid with arrow navigation
- VLK timeline with progress bars
- Auto-updater from GitHub
- Graceful degradation with health tracking
- Background prefetching for <50ms tab switches

**See:** `WINDOWS_TEST_GUIDE.md` for testing checklist

---

## 📍 Current State

### Rust Migration: COMPLETE 🦀

**Boss System** (100% Rust):
- ✅ Rust API server embedded in boss-tui (port 8083)
- ✅ Rust chromiumoxide scraper (~1100 lines)
- ✅ EMR diary submission with CSRF management
- ✅ All 15 API endpoints operational
- ✅ Binary: 7.0MB (TUI + API + SQLite + scraper)

**CyberIntern TUI** (Alert system complete):
- ✅ Alert Generator (sicklist + labs)
- ✅ Alert CRUD (create/resolve/dismiss)
- ✅ EMR scraper (shared from boss-tui)
- ⚠️ Diary templates (in progress)

### Architecture

```
Boss TUI (Rust) = TUI + API + Scraper
├── Port 8083 (API endpoints)
├── chromiumoxide (browser automation)
└── SQLite (boss.db)

CyberIntern API (Python FastAPI)
└── Port 8082 (enrichment for 027/о forms)
```

---

## 🎯 Issue Tracking

**Using Beads** - AI-native issue tracking in `.beads/`

```bash
# View all issues
bd list

# View specific issue
bd show <issue-id>

# Create new issue
bd create "Task description"

# Update status
bd update <issue-id> --status in_progress
bd update <issue-id> --status closed
```

**Historical Epics** (closed):
- Zav-xy5: Rust Scraper Migration
- Zav-b3f: MEGALITH Fixes
- Zav-owy: Sync Hunt
- Zav-ako: VLK Features
- Zav-6sr: Great Vypyska Hunt
- Zav-bl1: Data Purification Hunt
- Zav-wfx: Boss TUI Polish
- Zav-294: Boss TUI Masterplan
- Zav-ixa: Rust Sync Migration
- Zav-snh: Nurse TUI
- Zav-sze: CyberIntern TUI Alerts
- Zav-ue1: EMR Diary Submission

**Active Tasks**:
- Zav-zaz: Test VLK reverse sync endpoint (P1)
- Zav-4u8: Boss TUI Tier 5 - Developer Experience (P2, deferred)
- Zav-ww5: Phase 4 - Full Rust Stack Migration (P2, future)
- Zav-jvk: Installer Phase 3 - CI/CD Pipeline (P2, pending Windows test)

---

## 🏥 System Health

| Component | Status | URL |
|-----------|--------|-----|
| Airtable | ✅ Active | appv5BwoWyRhT6Lcr |
| n8n | ✅ Active | localhost:5678 |
| ngrok | ✅ Active | kristeen-rootlike-unflirtatiously.ngrok-free.dev |
| Slack | ✅ Active | Zav Hospital workspace |
| Boss API | ✅ Active | localhost:8083 |
| CyberIntern API | ⚠️ Needs Start | localhost:8082 (enrichment data) |
| Boss TUI | ✅ Active | ~/Projects/boss-tui |
| Zav Cloud | ✅ Active | zav-production.up.railway.app |

---

## 🔄 Active Workflows (n8n)

| Workflow | ID | Trigger |
|----------|-----|---------|
| **Combined Morning Briefing** | dfVgfARoNS9XXMIq | Daily 7 AM |
| Operation plan | T2fTND8RQcNrx6jZc05Wh | Daily 12:00 |
| Surgery Checklist | sF3jem3G4RztR9su | Every 30 min |
| Operations | xBlSfRngiWvEyCFetoHjs | Airtable poll |
| Boss → Airtable Sync | 7wV_aGUYTN8q_qJHSs-gy | Hourly |
| Patient Discharge Hub | h3XuUfInGUY3DDgu | Webhook |
| **Slack: /patient** | SuPFqfszZvm7NrLs | Command |
| **Slack: /ops** | fVibWFfEsLG4lpg1 | Command |
| **Slack: /beds** | qWJ9XBL9nQlTzHjo | Command |
| **Slack: /vlk** | vRsj4uEe15uIlWaK | Command |
| **Slack: /stats** | e3l4J3KI9tgBSiid | Command |
| **Slack: /surgery** | LTkL7j7i99btWwSu | Command |
| **MEGALITH 6: Interactive Handler** | y2vWK35PLkwj8zDr | Button clicks (51 nodes, 9 routes) |
| **Dovidka Cleanup (Daily)** | ZRbqEpbzkSWNRRM6 | Daily 2 AM |
| New Patient Admission | SuSKrbIFqFtNx3qO | Every 1 min |

---

## ⚡ Quick Commands

```bash
# Start Boss TUI (auto-starts n8n + Boss API)
boss

# Start with Tailscale relay (for EMR scraping)
boss-relay

# Check system status
boss-status

# Stop all services
boss-stop

# Start ngrok (required for Slack commands)
ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev

# Reconnect MCPs
/mcp
```

---

## 📚 Documentation

See `CLAUDE.md` for:
- Working guidelines (Barbarian/Grug mode)
- Architecture details
- n8n webhook debugging
- Slack integration
- MCP usage
- Environment variables

See `.beads/` for:
- Issue tracking
- Historical epic details
- Task dependencies
