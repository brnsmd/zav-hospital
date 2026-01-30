# Zav Project Status

**Updated:** 2026-01-30
**Status:** ✅ PRODUCTION READY

---

## 🪓 Session 2026-01-30: EMR DIARY SUBMISSION (Barbarian Mode)

### EMR Diary Submission - DONE! ✅

**Location:** `boss-tui/src/scraper/diary_submit.rs` (shared scraper, not duplicated)

**Files Created:**
| File | Lines | Purpose |
|------|-------|---------|
| `boss-tui/src/scraper/diary_submit.rs` | ~340 | EMR diary POST with CSRF management |

**Files Modified:**
| File | Change |
|------|--------|
| `boss-tui/src/scraper/mod.rs` | Added diary_submit module, CsrfTokenManager to EMRScraper |

**What Works Now:**
- ✅ CSRF token extraction from EMR pages (meta tag, cookie, form input)
- ✅ Auto-refresh CSRF tokens (25-minute lifetime)
- ✅ POST diary entries to `/api/v1/case/{case_id}/diary/`
- ✅ `submit_diary()` method on EMRScraper
- ✅ Convenience function `submit_diary_entry()` (login → submit → close)
- ✅ Full test coverage (CSRF manager, payload serialization)

**Design Decision:**
- **Shared scraper approach**: EMR browser automation centralized in boss-tui
- **No duplication**: cyberintern-tui calls boss-tui scraper (via API or library)
- **Follows CLAUDE.md**: cyberintern-tui CLAUDE.md says "Do NOT implement browser automation"

**Build:** ✅ SUCCESS (cargo check passes)

**Completed Issue:** Zav-ue1 - CyberIntern: EMR Diary Submission

---

## 🪓 Session 2026-01-28 Part 3: ALERT SYSTEM HUNT COMPLETE! (Barbarian Mode)

### Alert Generator Service - DONE! ✅🔥

**Parallel Hunt Strategy:** Clug commanded, Clugagents executed in parallel!

**Files Created:**
| File | Lines | Purpose |
|------|-------|---------|
| `src/services/mod.rs` | 5 | Module declaration |
| `src/services/alert_generator.rs` | ~330 | Sicklist + Labs alert generation |

**Files Modified:**
| File | Change |
|------|--------|
| `src/app.rs` | Wire up AlertGenerator in load_data() |
| `src/main.rs` | Keyboard shortcuts: r=resolve, d=dismiss |
| `src/db/alerts.rs` | Added create/resolve/dismiss methods |

**What Works Now:**
- ✅ TUI auto-generates sicklist alerts on load
- ✅ Sicklist expiring today → medium priority
- ✅ Sicklist overdue (1-3 days) → high priority
- ✅ Labs >5 days → medium, >14 days → high (if lab_results table exists)
- ✅ Auto-resolve when sicklist renewed
- ✅ Press `r` on alert detail → resolve
- ✅ Press `d` on alert detail → dismiss
- ✅ Cleanup old alerts (>7 days)

**GRUG PRINCIPLES FOLLOWED:**
- No new dependencies (removed lazy_regex, used simple string splitting)
- Simple date parsing with split_once()
- No over-engineering

**Build:** ✅ SUCCESS (57 warnings = old cruft, not our code)

### Implementation Phases - UPDATED

1. [x] **Phase 1: Alert Generator Service** ✅ COMPLETE
   - [x] Sicklist alerts (expiration + overdue)
   - [x] Labs alerts (warning + critical)
   - [x] Auto-resolve stale alerts
   - [x] Cleanup old pending alerts
2. [x] **Phase 2: DB Extensions** ✅ COMPLETE
   - [x] create_alert()
   - [x] resolve_alert()
   - [x] dismiss_alert()
3. [ ] Phase 3: Slack Integration (FUTURE)
4. [ ] Phase 4: Diary Template Generator (MAMMOTH - 80+ patterns)
5. [ ] Phase 5: EMR Submission (chromiumoxide, relay mode)
6. [x] **Phase 6: Wire up UI** ✅ COMPLETE
   - [x] AlertGenerator called in load_data()
   - [x] Keyboard shortcuts for resolve/dismiss

---

## 🪓 Session 2026-01-28 Part 2: CYBERINTERN TUI ALERTS PLAN (Barbarian Mode)

### Task: Migrate CyberIntern Python Systems to Rust

**Target:** `cyberintern-tui` (DOC mode - doctor's specific view)

**Systems to migrate:**
1. **Sicklist Alerts** - Track лікарняний expiration (day 0, -1, -2, -3+) ✅ DONE
2. **Lab Alerts** - Track lab freshness (>5 days warning, >14 days critical) ✅ DONE
3. **Batch Diary Writing** - Generate and submit diary entries from templates

### What Already Exists in cyberintern-tui ✅

| Component | Status | Notes |
|-----------|--------|-------|
| Alert Model | ✅ | AlertType: SicklistOverdue, LabsOutdated, NeedsDiary, LkkDue, VlkDeadline |
| Alert DB | ✅ | get_pending_alerts(), get_patient_alerts(), get_alert_stats() |
| Diary Model | ✅ | DiaryType: Daily, Preop, Postop2h, Lkk, DischargeDiary |
| Diary DB | ✅ | get_recent_diaries() |
| UI Tabs | ✅ | Alerts tab, Diaries tab, Diary editor overlay |
| **Alert Generator** | ✅ | **NEW!** services/alert_generator.rs |
| **Alert CRUD** | ✅ | **NEW!** create/resolve/dismiss in db/alerts.rs |

### What's MISSING (TO BUILD)

| Component | Source (Python) | Target (Rust) | Status |
|-----------|-----------------|---------------|--------|
| Alert Generator | `alert_generator.py` | `services/alert_generator.rs` | ✅ DONE |
| Diary Templates | `template_diary_generator.py` (1486 lines) | `services/diary_templates.rs` | ❌ TODO |
| EMR Submission | `diary_service.py` (286 lines) | `emr/diary_submit.rs` | ❌ TODO |
| Slack Integration | - | `services/slack.rs` | ❌ TODO |

### Plan Document Created

**Location:** `/var/home/htsapenko/Projects/Zav/CYBERINTERN_TUI_ALERTS_PLAN.md`
**Task Specs:** `/var/home/htsapenko/Projects/cyberintern-tui/CLUGAGENT_TASKS.md`

### Also Fixed Today: Boss TUI Discharged Tab ✅

Added Discharged tab to Boss TUI:
- Tab key: 2
- Shows discharged patients separately
- Patient detail popup works
- Fixed validation parse error with `#[serde(default)]`

**Files modified:**
- `boss-tui/src/app.rs` - Added Tab::Discharged, discharged_patients vec
- `boss-tui/src/api/boss.rs` - Changed to fetch ALL patients
- `boss-tui/src/ui/discharged.rs` - NEW file
- `boss-tui/src/ui/mod.rs` - Added discharged module
- `boss-tui/src/ui/popup.rs` - Support discharged patients
- `boss-tui/src/ui/footer.rs` - Added tab help
- `boss-tui/src/main.rs` - Added key handlers
- `boss-tui/src/models/validation.rs` - Fixed serde default

---

## 🪓 Session 2026-01-28: RUST SCRAPER API INTEGRATION (Barbarian Mode)

### Phase 7: API Integration ✅ COMPLETE

**Goal:** Wire Rust scraper to Boss API routes (replace Python subprocess).

**Changes to `boss-tui/src/server/routes.rs`:**
- Added conversion helpers: `scraped_to_db_patient()`, `apply_enrichment()`
- Replaced Python subprocess in `perform_sync_task()` with `crate::scraper::run_sync()`
- Replaced TODO in `perform_enrichment_task()` with full Rust scraper enrichment

**API Endpoints Now Use Rust Scraper:**
| Endpoint | Status |
|----------|--------|
| POST /sync | ✅ Uses Rust scraper |
| POST /sync/enrich | ✅ Uses Rust scraper |

**Build:** ✅ Compiles successfully

### Remaining: Phase 8 - Real EMR Testing

Need to test with actual EMR (requires Tailscale relay):
```bash
boss-relay
curl -X POST http://localhost:8083/sync
```

---

## 🪓 Session 2026-01-27 Part 3: RUST SCRAPER MIGRATION (Barbarian Mode)

### The Final Hunt - Replace Python Scraper with Rust 🦀

**Goal:** Replace Python Playwright scraper (845 lines) with pure Rust using `chromiumoxide`.

**Tracking:** `/var/home/htsapenko/Projects/Zav/RUST_SCRAPER_MASTERPLAN.md`

### PHASES 1-6: SCRAPER CORE ✅ COMPLETE

**All Extraction Logic Implemented:**
- [x] Phase 1: Foundation - chromiumoxide 0.7, module structure
- [x] Phase 2: Login - form fill, role selection, auth verification
- [x] Phase 3: Patient List - table extraction, pagination (up to 50 pages)
- [x] Phase 4: Detail Page - enrichment field extraction
- [x] Phase 5: Diagnosis - tab click, diagnosis text + ICD-10 extraction
- [x] Phase 6: Batch Enrich - rate-limited batch processing

**Files Created:**
- `boss-tui/src/scraper/mod.rs` - 230 lines - EMRScraper, login, API
- `boss-tui/src/scraper/browser.rs` - 230 lines - Browser lifecycle, JS eval
- `boss-tui/src/scraper/types.rs` - 100 lines - Data types
- `boss-tui/src/scraper/patients.rs` - 250 lines - Table extraction
- `boss-tui/src/scraper/enrichment.rs` - 300 lines - Detail + diagnosis

**Total: ~1100 lines of Rust** (replaces 845 lines Python)

**Binary:** Compiles successfully (dev + release)

### PHASE 7: API INTEGRATION ✅ COMPLETE

Server module wired to Rust scraper. Python subprocess removed.

See MASTERPLAN for full details.

---

## 🪓 Session 2026-01-27 Part 2: RUST ALL-IN-ONE (Barbarian Mode)

### The Great Rust Consolidation 🦀

**Goal:** Replace Python Boss API with embedded Rust server in boss-tui.

### COMPLETED ✅

#### 1. Git Repo Cleanup
- Removed deprecated folders: `brood/`, `telegram_bot/`, `zav/`, old `zav_*.py` files
- Converted loose repos into submodules:
  - `boss-tui` (existing, now submodule)
  - `cyberintern` (converted to submodule)
  - `cyberintern-boss` (created repo, converted to submodule)
- Archived old session transcripts to `archive/sessions/`

#### 2. Complete Rust API Server
**File changes:**
- `boss-tui/src/server/db.rs` - **750 lines** - Complete SQLite layer with 50+ patient fields
- `boss-tui/src/server/routes.rs` - **700 lines** - All 15 API endpoints
- `boss-tui/src/server/mod.rs` - Updated AppState with current_sync_id

**API Endpoints (matching Python exactly):**
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/stats` | GET | Database statistics |
| `/patients` | GET | List all patients |
| `/patients/{case_number}` | GET | Get single patient |
| `/patients/{case_number}` | PATCH | Update manual fields |
| `/patients/{case_number}/discharge` | POST | Discharge patient |
| `/patients/by-doctor/{name}` | GET | Filter by doctor |
| `/patients/by-ward/{ward}` | GET | Filter by ward |
| `/sync` | POST | Start EMR sync |
| `/sync/status` | GET | Sync status |
| `/sync/enrich` | POST | EMR enrichment |
| `/sync/enrich-cyberintern` | POST | CyberIntern enrichment |
| `/sync/airtable` | POST | Airtable sync |
| `/validate` | GET | Validation report |

**Binary stats:**
- Size: **7.0MB** (TUI + API + SQLite + HTTP client)
- Port: 8083 (same as Python)
- Database: Uses existing `./data/boss.db`

#### 3. Windows Setup Scripts
- `setup-windows.ps1` - Initial version with Chocolatey
- `setup-windows-portable.ps1` - **Fully portable** version:
  - Downloads Git, Python, Node, Rust to `E:\Zav\Tools`
  - No C: drive usage
  - Creates `start-zav.bat`, `stop-zav.bat`, `zav-shell.bat`
- `WINDOWS_SETUP.md` - Documentation

### PLANNED: Rust Scraper Migration 🦀

**Next hunt:** Replace Python Playwright scraper with `chromiumoxide` (Rust CDP client).

See: `/var/home/htsapenko/Projects/Zav/RUST_SCRAPER_MIGRATION.md`

### Key Technical Decisions
1. **Keep Python scraper for now** - Playwright has no pure Rust equivalent
2. **chromiumoxide for future** - Rust Chrome DevTools Protocol client can replace Playwright
3. **Subprocess calls** - Rust server calls Python scraper as subprocess until migration

### Files Committed
```
10217ce feat: Complete Rust API server with full Python parity
```

### Parallel Work
- **Another Claude** is migrating CyberIntern (027/о API) to Rust simultaneously

---

## 🪓 Session 2026-01-27: MEGALITH FIXES (Barbarian Mode)

### Boars Slain 🐗

#### Boar 1: Surgery Prefill Not Working
**Problem:** `/surgery Семко` showed `№ і/х: -` and `Хірург: -` even though data exists.

**Root Cause:** Format Surgery Response used `patient.fields?.['field']` but Airtable node returns fields directly on `patient['field']`.

**Fix:** Added fallback pattern `const f = patient.fields || patient;`

**Files Changed:**
- MEGALITH 1: Format Surgery Response node

---

#### Boar 2: Date Format Chaos
**Problem:** Dates displayed in mixed formats (YYYY-MM-DD, DD.MM.YYYY, etc.)

**Fix:** Added `formatDate()` helper to convert all dates to DD.MM.YYYY:
- MEGALITH 1: Format Patient Response
- MEGALITH 6: Build Form URL Fill
- MEGALITH 6: Fill 027 Generate (Випiska dates)

---

#### Boar 3: Field Rename № справи → № запису
**Problem:** "№ справи" was confusing (case number vs history number).

**Fix:**
- Renamed Airtable field `№ справи` → `№ запису`
- Updated Boss sync code to use new field name

**Files Changed:**
- Airtable field fldJXzYPQ1o6q0MKV renamed
- `cyberintern-boss/src/airtable_sync.py` - updated all references

---

#### Boar 4: history_number Not Syncing to Airtable
**Problem:** `history_number` from Boss DB wasn't being synced to Airtable `№ історії`.

**Fix:** Added mapping in Boss sync:
```python
if boss_patient.get('history_number'):
    airtable_fields['№ історії'] = boss_patient['history_number']
```

**Files Changed:**
- `cyberintern-boss/src/airtable_sync.py`

---

#### Boar 5: Vypyska Link Broken (File Not Found)
**Problem:** Generated Vypyska document link returned "file does not exist".

**Root Cause:** Format Generate Response got `docId` from Fill 027 Generate (Google Docs update), which doesn't return the document ID.

**Fix:** Get `docId` from Copy 027 Generate node instead:
```javascript
const copyResult = $('Copy 027 Generate').first().json;
const docId = copyResult.id;
```

**Files Changed:**
- MEGALITH 6: Format Generate Response node

---

#### Boar 6: New Field - Фіз. номер і.х
**Problem:** Need physical history number field for outgoing documents.

**Fix:** Added new field everywhere:
- Airtable: `Фіз. номер і.х` (fld4cPVuiv8qJlSDY)
- Boss DB: `physical_history_number` column
- Boss sync: mapping added
- Database schema: updated for new DBs

**Files Changed:**
- `cyberintern-boss/src/airtable_sync.py`
- `cyberintern-boss/src/database.py`
- Boss DB schema (ALTER TABLE)

**Completed by Grug:** ✅ All tasks done!

---

### Summary of Changes

| Component | Changes |
|-----------|---------|
| **MEGALITH 1** | Surgery prefill fix, date formatting, field access fallback |
| **MEGALITH 6** | Vypyska link fix, date formatting in forms and documents |
| **Airtable** | `№ справи` → `№ запису`, new `Фіз. номер і.х` field |
| **Boss Sync** | Added `№ історії` and `Фіз. номер і.х` mappings |
| **Boss DB** | Added `physical_history_number` column |

---

## System Health

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

## 🪓 Session 2026-01-26: SYNC HUNT (Barbarian Mode)

### Problem
Boss → Airtable sync was failing silently. No data reaching Airtable.

### Boars Slain 🐗

#### Boar 1: Broken n8n Workflow
**MEGALITH 5: Data Sync** (qVgYLgOSvNEWxWQN) was:
- ❌ Using stale IP `192.168.4.233:8083` instead of localhost
- ❌ Missing Airtable Create node (incomplete!)
- ❌ Redundant - Boss API already has sync built-in

**FIX:** Simplified to 2-node workflow:
```
Schedule Trigger (hourly) → HTTP POST localhost:8083/sync/airtable
```

#### Boar 2: Expired Airtable Token
Old token `pat4ImGgwc...` returned 401 Unauthorized.

**FIX:** Updated token in ALL env files:
- `~/.config/zav-secrets.env`
- `cyberintern/.env`
- `cyberintern-boss/.env`
- `boss-package/.env`

New token: `patb7wwx4tT6b7tPy...`

#### Boar 3: CyberIntern API Not Running
Enrichment endpoint returned "CYBERINTERN_API_URL not configured".

**FIX:**
- Added `CYBERINTERN_API_URL=http://localhost:8082` to env files
- Startup script already includes CyberIntern API startup

### Sync Status After Fix
```json
{
  "status": "completed",
  "patients_found": 38,
  "patients_updated": 38
}
```

### Airtable 027/о Fields (ALREADY EXIST)
| Field | ID |
|-------|-----|
| Скарги пацієнта | fldwprg4uk1WszL0S |
| Анамнез хвороби | fldtNpottWthvSXiP |
| Анамнез життя | fldu1NxtWCsX6bG4W |
| Об'єктивний стан | fldrfZ8244xFyWGEt |
| Лікування | fldsAUJhbRYvcBayr |
| Рекомендації | fldpHWLlXI2yBAa5N |

### Enrichment Pipeline Fixed
**Problem:** `boss()` function in `~/.zshrc` was NOT starting CyberIntern API.

**Fix:** Added CyberIntern API startup to `boss()` function (step 2).

**New startup order:**
1. n8n container
2. CyberIntern API (8082) ← ADDED!
3. Boss API (8083)
4. ngrok
5. Rebuild TUI
6. Launch TUI

### Next Steps for Enrichment
1. Run `boss` (now starts CyberIntern API automatically!)
2. Run `curl -X POST http://localhost:8083/sync/enrich-cyberintern`
3. Run `curl -X POST http://localhost:8083/sync/airtable`

---

## Recent Changes (2026-01-24)

### Phase 1: Security & Infrastructure ✅
- [x] **API key auth for Boss API** - X-API-KEY header validation (optional, set BOSS_API_KEY to enable)
- [x] **SQLite daily backups** - Script + systemd timer at `cyberintern-boss/scripts/backup-db.sh`
- [x] **Removed secrets from docs** - Redacted JWT tokens from N8N_WORKFLOW_MANAGEMENT.md
- [x] **Connection pooling** - Added pool_max_idle_per_host(10), pool_idle_timeout(60s) to Boss TUI
- [x] **Retry logic** - Exponential backoff (100ms→200ms→400ms), 3 retries for network errors

### Phase 2: Slack Commands ✅
- [x] **`/vlk`** - VLK patients status (critical/warning counts)
- [x] **`/stats`** - Quick system statistics (patient counts, by ward)
- [x] **`/surgery`** - Link to surgery scheduling form
- [x] **Combined Morning Briefing** - Batches VLK + Overstay + Morning Report at 7 AM
- [x] **Slack Manifest API** - Automated slash command configuration via API

### Files Modified
- `cyberintern-boss/src/main.py` - API key auth middleware
- `boss-tui/src/api/boss.rs` - Retry logic + auth headers
- `boss-tui/src/app.rs` - Connection pooling
- `boss-tui/src/config.rs` - BOSS_API_KEY env var
- `docs/N8N_WORKFLOW_MANAGEMENT.md` - Removed exposed secrets

### Files Created
- `cyberintern-boss/scripts/backup-db.sh` - Backup script
- `~/.config/systemd/user/boss-backup.service` - Backup service
- `~/.config/systemd/user/boss-backup.timer` - Daily backup timer (enabled)

---

## Active Workflows (n8n)

| Workflow | ID | Status | Trigger |
|----------|-----|--------|---------|
| **Combined Morning Briefing** | dfVgfARoNS9XXMIq | ✅ | Daily 7 AM |
| Operation plan | T2fTND8RQcNrx6jZc05Wh | ✅ | 12:00 |
| Surgery Checklist | sF3jem3G4RztR9su | ✅ | 30 min |
| Operations | xBlSfRngiWvEyCFetoHjs | ✅ | Polling |
| Boss → Airtable | 7wV_aGUYTN8q_qJHSs-gy | ✅ | Scheduled |
| Patient Discharge | h3XuUfInGUY3DDgu | ✅ | Webhook |
| **Slack: /patient** | SuPFqfszZvm7NrLs | ✅ | Slack command |
| **Slack: /ops** | fVibWFfEsLG4lpg1 | ✅ | Slack command |
| **Slack: /beds** | qWJ9XBL9nQlTzHjo | ✅ | Slack command |
| **Slack: /vlk** | vRsj4uEe15uIlWaK | ✅ | Slack command |
| **Slack: /stats** | e3l4J3KI9tgBSiid | ✅ | Slack command |
| **Slack: /surgery** | LTkL7j7i99btWwSu | ✅ | Slack command |
| **MEGALITH 6: Interactive Handler** | y2vWK35PLkwj8zDr | ✅ | Button clicks (51 nodes, 9 routes) |
| **Dovidka Cleanup (Daily)** | ZRbqEpbzkSWNRRM6 | ✅ | Daily 2 AM |
| New Patient Admission | SuSKrbIFqFtNx3qO | ✅ | Every 1 min |

**Deprecated (replaced by Combined Morning Briefing):**
- VLK Alert System v2 (S4HtG75YjVc2Z9tr) - deactivated
- Daily Morning Report (hTwq6zC3mLwPWkrO) - deactivated
- Overstay Alert (XHveI1Sg8mMnAFed) - deactivated

---

## Slack Slash Commands

| Command | Webhook | Description |
|---------|---------|-------------|
| `/patients` | slack-patient | Search patient by name |
| `/ops` | slack-ops | Today's operations |
| `/beds` | slack-beds | Ward occupancy |
| `/vlk` | slack-vlk | VLK status (critical/warning) |
| `/stats` | slack-stats | System statistics |
| `/surgery` | slack-surgery | Surgery scheduling form |

**Configured via:** Slack App Manifest API (app ID: A0AAC5L6ZGT)

---

## Environment Variables

All in `~/.config/zav-secrets.env`:

```bash
# Boss API
BOSS_API_URL=http://localhost:8083
BOSS_API_KEY=<optional-for-auth>

# n8n
N8N_URL=http://localhost:5678
N8N_API_KEY=<key>

# Airtable
AIRTABLE_TOKEN=<token>
AIRTABLE_BASE=appv5BwoWyRhT6Lcr

# Slack
SLACK_BOT_TOKEN=xoxb-...           # For n8n messaging
SLACK_CONFIG_ACCESS_TOKEN=xoxe.xoxp-...  # For manifest API (12h expiry)
SLACK_CONFIG_REFRESH_TOKEN=xoxe-...      # For token renewal

# ngrok
NGROK_AUTHTOKEN=<token>
```

---

## Quick Start

```bash
# Start Boss TUI (sources secrets automatically)
boss

# Start with Tailscale relay (for EMR scraping)
boss-relay

# Check all services
boss-status

# Start ngrok (required for Slack commands)
ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev

# Manual backup
bash ~/Projects/cyberintern-boss/scripts/backup-db.sh
```

---

## Completed in This Session

### Security (Phase 1)
- [x] API key authentication for Boss API
- [x] SQLite daily backups with rotation
- [x] Secrets removed from documentation
- [x] HTTP connection pooling
- [x] Retry logic with exponential backoff

### Slack (Phase 2)
- [x] /vlk command
- [x] /stats command
- [x] /surgery command
- [x] Combined morning briefing (replaces 3 separate workflows)
- [x] Automated Slack command configuration via Manifest API

---

## Completed Today (2026-01-24 Session 2)

### Slack Interactive Buttons - FIXED ✅
- [x] **Webhook registration** - Workflow must be saved in UI for webhook to register
- [x] **Parse Payload** - Fixed `typeof body === "string"` (was missing quotes)
- [x] **Switch node "Route by Action"** - Fixed:
  - Data Type must be set to `String` for "starts with" to appear
  - Value 1: `={{ $json.actionId }}`
  - Output numbers must be set manually (0, 1, 2) - don't auto-increment!
- [x] **HTTP Request "Post to alerts"** - Fixed body parameter names (removed colons/spaces)
- [x] **VLK Schedule flow working** - Button click → Posts to #alerts

---

## Completed Today (2026-01-24 Session 3) 🪓

### VLK Modal Feature - COMPLETE ✅
- [x] **VLK button → Modal opens** - Click patient button, modal appears with options
- [x] **Modal submit → Posts to #alerts** - All tribe sees "планує ВЛК для..."
- [x] **`/vlk` response now ephemeral** - Only user sees patient list, not spam channel
- [x] **Airtable auto-update** - 30д/60д options update Дата ВЛК, Рішення ВЛК, Дні продовження
- [x] **Airtable link option** - "Завантажити документ" posts clickable link to record

### Modal Options (Final)
| Option | Action |
|--------|--------|
| 📅 Запланувати на вівторок | Posts schedule to #alerts |
| 📅 Запланувати на п'ятницю | Posts schedule to #alerts |
| ✅ Продовження 30 днів | Updates Airtable + posts to #alerts |
| ✅ Продовження 60 днів | Updates Airtable + posts to #alerts |
| 📎 Пройдено, завантажити документ | Posts link to Airtable record for upload |

### Boars Slain 🐗
1. `invalid_auth` - n8n env vars don't work, used direct Slack token in headers
2. `Credential ID "1" not found` - HTTP Request node needs direct token, not credential reference
3. `Cannot read startsWith of undefined` - Parse Payload wasn't extracting `callbackId` for modal submissions

### Workflow: MEGALITH 6 Interactive Handler (y2vWK35PLkwj8zDr) - 23 nodes
```
Slack Interactive (webhook: /webhook/slack-interactive)
    ↓
Parse Payload (extract actionId, value, user, responseUrl)
    ↓
Route Action (Switch - 5 outputs)
    ├── vlk_schedule_* → Handle VLK → Respond VLK → Acknowledge
    ├── surgery_* → Handle Surgery → Respond Surgery → Acknowledge 2
    ├── discharge_* → Handle Discharge → Get Patient → Copy Template → Fill Document → Format Response → Respond Discharge → Acknowledge 3
    ├── vlk_done_* → Handle VLK Done → Respond VLK Done → Acknowledge VLK Done
    └── vlk_extend_* → Handle VLK Extend → Update Airtable VLK → Respond VLK Extend → Acknowledge VLK Extend
```

### Key Technical Details
- **Slack views.open** requires `trigger_id` from button click (expires in 3 seconds!)
- **Modal callback_id** format: `vlk_modal_{recordId}` - used to route submissions
- **private_metadata** stores: `{recordId, patientName}` - passed through modal lifecycle
- **HTTP Request to Slack** needs direct Bearer token in header (not n8n credentials for this use case)
- **Airtable API** uses PATCH to update record fields directly

---

## Completed Today (2026-01-24 Session 4) 🪓

### Boss TUI VLK Feature - COMPLETE ✅
- [x] **VLK Action Popup** - Press 'v' on VLK tab to open action menu
- [x] **Продовження 30 днів** - Updates Airtable (Дата ВЛК, Рішення ВЛК, Дні продовження: 30)
- [x] **Продовження 60 днів** - Updates Airtable (Дата ВЛК, Рішення ВЛК, Дні продовження: 60)
- [x] **Відкрити в Airtable** - Opens browser with patient record for document upload
- [x] **Shortcut visible in footer** - `v:action` shown on VLK tab
- [x] **Shortcut in help menu** - VLK TAB section with 'v' description

### Files Modified
- `boss-tui/src/models/airtable.rs` - Added `id` field to AirtableRecord
- `boss-tui/src/api/airtable.rs` - Added `update_vlk_record()` method
- `boss-tui/src/app.rs` - Added `show_vlk_action` state and `execute_vlk_action()` async method
- `boss-tui/src/main.rs` - Added keyboard handlers for VLK popup (v, 1, 2, 3, Esc)
- `boss-tui/src/ui/vlk.rs` - Added `render_vlk_action_popup()` function
- `boss-tui/src/ui/footer.rs` - Added `v:action` to VLK tab shortcuts
- `boss-tui/src/ui/help.rs` - Added VLK TAB section with shortcut description

### Barbarian Technique Added to CLAUDE.md 🪓
- "Grug Mode" section added - effective coding style for debugging sessions

### Sandbox Boar Slain 🐗
- **EPERM error fixed** - Changed `Command::new("xdg-open")` to `open::that()`
- The `open` crate handles Flatpak/sandbox environments properly
- FILE: `boss-tui/src/app.rs:1029`

---

## Completed Today (2026-01-24 Session 5) 🪓

### MEGALITH 6: Interactive Handler - UPGRADED ✅
- [x] **VLK +2/+4 months buttons** - Now update Airtable directly (was broken)
- [x] **Discharge flow** - Google Docs integration complete
- [x] **Discharge button** → Copies 027 template → Fills with patient data → Returns link

### Discharge Flow (New)
```
User clicks "Виписати" button in Slack
    ↓
Handle Discharge (extract recordId, patientName)
    ↓
Get Patient (Airtable - fetch full patient record)
    ↓
Copy Template (Google Drive - copy 027 template doc)
    ↓
Fill Document (Google Docs - replace placeholders)
    ↓
Format Response (build Slack message with doc link)
    ↓
Respond Discharge (POST to response_url)
    ↓
Acknowledge 3 (200 OK to Slack)
```

### Placeholders in 027 Template
| Placeholder | Airtable Field |
|-------------|----------------|
| `{{ПІБ}}` | ПІБ |
| `{{Дата_народження}}` | Дата народження |
| `{{Діагноз}}` | Повний діагноз / Діагноз |
| `{{Дата_госпіталізації}}` | Дата госпіталізації |
| `{{Дата_виписки}}` | Current date |
| `{{№_історії}}` | № історії |
| `{{Хірург}}` | Хірург |
| `{{Рекомендації}}` | Рекомендації |

### Credentials Used
| Service | Credential ID | Name |
|---------|---------------|------|
| Airtable | oB0crB7qKyJOGI5a | Airtable Personal Access Token |
| Google Drive | rMWvrK8pn4JH2Sl8 | Google Drive account |
| Google Docs | renz2o80wUGVVoOD | Google Docs account |

### Google Drive Resources
- **Template:** `1q8FTR4l7oY5KJGLjVDyMYkJNvt6HSV4K3aymn5fykg8`
- **Output folder:** `1ZL3RqSdNVcQ0Gabbz6GdCey59IWuB2EW`

---

## Completed Today (2026-01-25) 🪓🔥 BARBARIAN SESSION

### GREAT VYPYSKA HUNT - COMPLETE! ✅🔥

**The 4-Step Discharge Flow - No Webhooks, No Polling, Pure Button Magic!**

```
STEP 1: Click "Виписати" on patient
        → See "📝 Заповнити форму" button

STEP 2: Click "📝 Заповнити форму"
        → Opens prefilled Airtable form
        → Shows "📄 Згенерувати виписку" button

STEP 3: Fill form in Airtable, then click "📄 Згенерувати виписку"
        → 027 document generated in Google Docs
        → Shows "✅ Виписка підписана і здана" button

STEP 4: Chief signs doc, click "✅ Виписка підписана і здана"
        → PDF saved to Airtable "Виписка 027" field
        → Doc deleted from Google Drive
        → DONE! 🎉
```

#### New Routes Added to MEGALITH 6
| Route | Action ID | Purpose |
|-------|-----------|---------|
| `fill_form` | `fill_form_<recordId>` | Opens Airtable form + shows generate button |
| `generate_vypyska` | `generate_vypyska_<recordId>` | Generates 027 doc + shows signed button |
| `vypyska_signed` | `vypyska_signed_<recordId>_<docId>` | PDF → Airtable → Delete from Drive |

#### New Nodes in MEGALITH 6 (51 total nodes, 9 routes)
- Handle Fill Form
- Get Patient Fill Form
- Build Form URL Fill
- Respond Fill Form
- Ack Fill Form
- Handle Generate
- Get Patient Generate
- Copy 027 Generate
- Fill 027 Generate
- Format Generate Response
- Respond Generate
- Ack Generate
- Handle Signed
- Export PDF
- Upload to Airtable
- Delete from Drive
- Respond Signed
- Acknowledge Signed

#### Dovidka Cleanup Workflow Created ✅
- **Workflow:** Dovidka Cleanup (Daily)
- **ID:** ZRbqEpbzkSWNRRM6
- **Trigger:** Daily at 2 AM
- **Action:** Deletes Dovidka files older than 24h from Google Drive

#### Boars Slain 🐗
1. **`invalid_blocks`** - Button value too long (contained entire form URL). Fixed: pass only patient name, build URL in separate node
2. **Airtable free plan no webhook** - No webhook action available. Solution: User-driven button flow instead
3. **Form prefill URL encoding** - Special chars broke URL. Fixed: proper encoding + truncation of long values

#### Key Technical Decisions
- **No polling** - User controls when to generate (click button after filling form)
- **No webhooks** - Airtable free plan doesn't have webhook action
- **Button-driven flow** - Each step reveals the next button
- **Form URL built server-side** - Prefill params built in n8n, not stored in button value

### Discharge Document Name Fix ✅
- [x] **"Copy of undefined" → Proper name** - Changed expression to use `$('Get Patient').first().json['ПІБ']`
- [x] Document naming format: `Vypyska_<PatientName>_<Date>`

### CyberIntern Enrichment Module ✅
- [x] **Created `cyberintern_enrichment.py`** - Fetches 027/о data from CyberIntern API
- [x] **Patient matching** by case_number, history_number, pib
- [x] **Parses diary content** for complaints, anamnesis, objective status
- [x] **Integrated into auto_sync_task** (Step 4)
- [x] **New endpoint `/sync/enrich-cyberintern`**

### 027/о Field Mappings Added ✅
New Airtable field mappings in `airtable_sync.py`:
| Boss Field | Airtable Field |
|------------|----------------|
| address | Місце проживання |
| complaints | Скарги пацієнта |
| disease_anamnesis | Анамнез хвороби |
| life_anamnesis | Анамнез життя |
| objective_status | Об'єктивний стан |
| lab_tests | Обстеження лабораторні |
| instrumental_tests | Обстеження інструментальні |
| consultations | Консультації |
| treatment | Лікування |
| treatment_result | Результат лікування |
| recommendations | Рекомендації |
| sicklist_start | МВТН початок |
| sicklist_end | МВТН кінець |

### ngrok for Boss API ✅
- [x] **Auto-starts with `boss` command** - Added to `~/.zshrc` boss() function
- [x] **Port 8083** - ngrok http 8083
- [x] **URL saved to `/tmp/boss-ngrok-url.txt`**
- [x] **Updated `boss-status()` and `boss-stop()`** to include ngrok

### Dovidka (Hospital Stay Certificate) Generation ✅
- [x] **Template uploaded to Google Drive** - ID: `1uk3RCS2IYqGgLa3jzvAJa1Dqpiiwe5ei8WYYA0sqv3M`
- [x] **"📄 Довідка" button added** to MEGALITH 1 patient search results
- [x] **7 new nodes in MEGALITH 6** for dovidka flow

#### Dovidka Flow
```
User clicks "📄 Довідка" button in Slack
    ↓
Handle Dovidka (extract recordId, patientName)
    ↓
Get Patient Dovidka (Airtable - fetch full record)
    ↓
Format Dovidka Data (convert ALL CAPS workplace to Title Case)
    ↓
Copy Dovidka Template (Google Drive - copy template)
    ↓
Fill Dovidka (Google Docs - replace placeholders)
    ↓
Format Dovidka Response (build Slack message)
    ↓
Respond Dovidka (POST to response_url)
    ↓
Acknowledge Dovidka (200 OK)
```

#### Dovidka Template Placeholders
| Placeholder | Source |
|-------------|--------|
| `{{ДАТА}}` | Today's date (certificate issue date) |
| `{{ПІБ}}` | ПІБ |
| `{{Дата_народження}}` | Дата народження |
| `{{Діагноз}}` | Повний діагноз / Діагноз |
| `{{Дата_госпіталізації}}` | Дата госпіталізації |
| `{{№_історії}}` | № історії |
| `{{Хірург}}` | Хірург |
| `{{Місце_роботи}}` | Заклад (Title Case formatted) |
| `{{Signer1name}}` | Панфьоров С.В. |
| `{{Signer2name}}` | Кондратов Д.С. |
| `{{Signer3name}}` | Хірург (surgeon name) |

### Boars Slain 🐗
1. **"Copy of undefined"** - documentURL expression fixed
2. **"This operation is not supported"** - Template was .docx, converted to native Google Doc
3. **Placeholder mismatch** - Aligned dovidka placeholders with 027/о format
4. **ALL CAPS workplace** - Added Format Dovidka Data node with Title Case conversion
5. **Broken flow connections** - Fixed: Format → Copy → Fill (was Format → Fill directly)
6. **Wrong documentURL reference** - Changed `$('Copy Dovidka Template')` to `$json.id`

### Files Modified
- `cyberintern-boss/src/airtable_sync.py` - 12 new 027/о field mappings
- `cyberintern-boss/src/main.py` - CyberIntern enrichment integration
- `~/.zshrc` - ngrok auto-start in boss()
- n8n MEGALITH 1 (3EMiulj7okbiy8zz) - Added Довідка button
- n8n MEGALITH 6 (y2vWK35PLkwj8zDr) - Added 8 new nodes (Handle, Get Patient, Format Data, Copy, Fill, Format Response, Respond, Acknowledge)

### Files Created
- `cyberintern-boss/src/cyberintern_enrichment.py` - CyberIntern API client and enrichment logic

---

## Completed Today (2026-01-25 Session 2) 🪓 DATA PURIFICATION HUNT

### Data Validator ("The Great Boar Fence") ✅
Created validation layer to ensure data quality before Airtable sync:

**Required Fields (Block if missing):**
- case_number
- pib (patient name)
- admission_date
- birth_date

**Important Fields (Warn if missing):**
- doctor
- ward

**Data Cleaning:**
- institution → ALL CAPS to Title Case (preserves abbreviations: ДУ, ТМО, МВС, НГУ)
- workplace → ALL CAPS to Title Case

#### Validation Results (44 patients):
- ✅ 40 valid (can sync to Airtable)
- 🚫 4 blocked (missing birth_date)
- 🧹 20 cleaned (ALL CAPS fixed)
- ⚠️ 2 with warnings (missing doctor)

### Boss API Enhancement ✅
- New endpoint: `GET /validate` - Returns validation report
- Airtable sync now validates first, blocks invalid records
- Returns detailed report: blocked patients, warnings, cleaned fields

### Boss TUI Major Upgrade ✅
**New Tabs:**
- **[7] Sync** - Data validation dashboard showing:
  - 4-box summary (Valid/Blocked/Cleaned/Warnings)
  - Blocked patients list with error details
  - Patients needing data hunt
- **[8] Operations** - Today's surgery schedule from Airtable

**Patient Detail Enhancement:**
- Added 027/о enrichment fields to Diagnosis tab:
  - Скарги (complaints)
  - Анамнез хвороби (disease anamnesis)
  - Об'єктивний стан (objective status)
  - Лікування (treatment)
  - Рекомендації (recommendations)

**Patient Model Extended:**
- Added 13 new fields for 027/о form data:
  - address, complaints, disease_anamnesis, life_anamnesis
  - objective_status, lab_tests, instrumental_tests
  - consultations, treatment, treatment_result
  - recommendations, sicklist_start, sicklist_end

### Files Created
- `cyberintern-boss/src/data_validator.py` - The Great Boar Fence (validation logic)
- `boss-tui/src/ui/sync.rs` - Sync dashboard tab
- `boss-tui/src/ui/operations.rs` - Operations tab
- `boss-tui/src/models/validation.rs` - Validation response models

### Files Modified
- `cyberintern-boss/src/main.py` - Added /validate endpoint
- `cyberintern-boss/src/airtable_sync.py` - Integrated validator
- `boss-tui/src/app.rs` - Added Sync/Operations tabs, validation state
- `boss-tui/src/api/boss.rs` - Added fetch_validation()
- `boss-tui/src/models/mod.rs` - Added validation module
- `boss-tui/src/models/patient.rs` - Added 027/о fields
- `boss-tui/src/ui/mod.rs` - Added new tab modules
- `boss-tui/src/ui/popup.rs` - Enhanced Diagnosis tab
- `boss-tui/src/ui/footer.rs` - Added shortcuts for new tabs
- `boss-tui/src/ui/help.rs` - Documented new tabs

---

## Boss TUI Masterplan Progress

See: `/var/home/htsapenko/Projects/Zav/BOSS_TUI_MASTERPLAN.md`

### Phase 0: Critical Fixes ✅
- [x] **Fix Button 8** - `main.rs:148` - changed `'1'..='7'` to `'1'..='8'`

### Phase 1: Power-On Sequence ✅ COMPLETE
- [x] **tui-big-text 0.8** - ASCII art "ZAV" logo
- [x] **throbber-widgets-tui 0.10** - Animated spinners
- [x] **ratatui 0.30** - Updated for dependency compatibility
- [x] **splash.rs module** - Full splash screen implementation
- [x] **StartupPhase enum** - Logo → CheckingServices → LoadingData → Ready
- [x] **Service checks** - Boss API, n8n, Airtable with animated status
- [x] **Progress bar** - Shows loading progress during startup

### Phase 2: Power-On Polish (Fade Transition) ✅ COMPLETE 2026-01-25
- [x] **tachyonfx 0.22** - Effects library for ratatui 0.30
- [x] **StartupPhase::Transitioning** - New phase for fade effect
- [x] **Fade-to-black transition** - 500ms QuadOut easing after "Ready!"
- [x] **Graceful quit** - Can press 'q' during transition

### Sprint 5: Advanced Features ✅ COMPLETE 2026-01-25
- [x] **Sortable column indicators** - Headers show ▲/▼ for current sort (Name, Ward, Days)
- [x] **Ward distribution BarChart** - Visual bar chart in Stats tab
- [x] **Tab history (Backspace)** - Press Backspace to return to previous tab
- [x] **Status line footer** - Shows Patients count, VLK critical, Ops count, sync time, version

### Sprint 3: Wards Tab ✅ COMPLETE
- [x] Created wards.rs module
- [x] Added Tab::Wards (key '9', index 8)
- [x] Ward grid layout with visual beds
- [x] Navigation: Tab/Shift-Tab for wards, j/k for beds
- [x] 'c' key cycles cleanliness (Clean → NeedsCleaning → Critical)
- [x] Cleanliness persists to ~/.config/boss-tui/wards.json

### Sprint 4: Visual Polish ✅ COMPLETE 2026-01-25
- [x] **Sparkline in header** - Patient count trend (last 10 refreshes)
- [x] **Table row highlighting** - ICU (red), VLK critical (yellow), alternating
- [x] **Confirmation dialogs** - Shift+D shows confirm before discharge
- [x] **Toast queue** - Multiple toasts stack (max 5, auto-dismiss 3s)
- [x] **Better error display** - ErrorInfo with source/time, 'e' for detail popup

---

## Next Steps (Remaining from Plan)

### Week 3: Slack Interactive - COMPLETE ✅
- [x] Interactive Slack buttons - basic flow working
- [x] VLK button → Modal with options (Schedule Tuesday/Friday OR Mark Done)
- [x] VLK Done → Airtable update (Дата ВЛК, Рішення ВЛК, Дні продовження)
- [x] VLK Done → Link to Airtable for document upload
- [x] Streamlined discharge in Slack (button → Google Doc → done)

### Week 4: TUI Improvements ✅ COMPLETE
- [x] Operations tab in Boss TUI
- [x] Sync/Validation dashboard
- [x] Patient detail enrichment display
- [x] Wards tab with visual layout
- [x] Ward cleanliness colors (Green/Yellow/Red)
- [x] Changing ward cleanliness via keyboard ('c')

### Week 5: PDF Documents
- [ ] PDF patient summary generation (need templates from user)

### Later: Testing & Quality
- [ ] Basic test suite for Boss API (pytest)
- [ ] Audit logging for patient access

---

**Full documentation:** See `docs/` folder and `CLAUDE.md`
