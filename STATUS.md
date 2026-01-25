# Zav Project Status

**Updated:** 2026-01-25
**Status:** ✅ PRODUCTION READY

---

## System Health

| Component | Status | URL |
|-----------|--------|-----|
| Airtable | ✅ Active | appv5BwoWyRhT6Lcr |
| n8n | ✅ Active | localhost:5678 |
| ngrok | ✅ Active | kristeen-rootlike-unflirtatiously.ngrok-free.dev |
| Slack | ✅ Active | Zav Hospital workspace |
| Boss API | ✅ Active | localhost:8083 (now with API key auth) |
| Boss TUI | ✅ Active | ~/Projects/boss-tui |
| Zav Cloud | ✅ Active | zav-production.up.railway.app |

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
