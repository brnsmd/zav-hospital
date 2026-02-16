# Boss-TUI Architecture Audit

**Date:** 2026-02-10
**Language:** Rust (29,732 lines across 71 .rs files)
**Port:** 8084 (embedded REST API)
**Binary:** ~50 MB release

---

## Architecture

```
boss-tui/
├── src/
│   ├── main.rs              (1,517 lines) - Unified launcher: ZAV + Doctor modes
│   ├── lib.rs               (28 lines)    - Library exports
│   ├── app.rs               (3,100 lines) - GOD MODULE: 172 fields, all business logic
│   ├── config.rs            (156 lines)   - Config, NetworkMode, NodeIdentity
│   ├── error.rs             (150 lines)   - miette error handling
│   ├── helpers.rs           (4 KB)        - Utilities
│   ├── theme.rs             (28 KB)       - MedicalTheme semantic colors
│   ├── audit.rs             (12 KB)       - Audit logging
│   │
│   ├── api/                 (21 KB) - HTTP Client Wrappers
│   │   ├── boss.rs          <- BossClient for self-API
│   │   └── n8n.rs           <- N8nClient for workflow control
│   │
│   ├── models/              (140 KB) - Data Models
│   │   ├── patient.rs       <- Patient (52 fields) + stats
│   │   ├── alert.rs         <- SmartAlert + AlertSeverity (Tier 6.1)
│   │   ├── vlk.rs           <- VlkTimeline + VlkStatistics (Tier 4.2)
│   │   ├── ward.rs          <- WardBed + InfectionZone (Tier 4.1)
│   │   ├── sync.rs          <- SyncState
│   │   ├── n8n.rs           <- Workflow + Execution models
│   │   ├── freshness.rs     <- DataFreshness (Tier 1.2)
│   │   ├── trends.rs        <- TrendData + ApiLatencyTracker
│   │   ├── health.rs        <- ServiceHealth
│   │   ├── toast.rs         <- Toast notifications
│   │   └── validation.rs    <- ValidationSummary
│   │
│   ├── server/              (152 KB) - EMBEDDED REST API
│   │   ├── mod.rs           <- Server startup & health
│   │   ├── routes.rs        <- (1,539 lines) 30+ endpoints
│   │   ├── db.rs            <- (1,576 lines) SQLite layer
│   │   ├── cache.rs         <- In-memory cache (5 min TTL)
│   │   └── auth.rs          <- Doctor session auth (Phase 4)
│   │
│   ├── ui/                  (358 KB) - TUI RENDERING
│   │   ├── mod.rs           <- Main dispatcher
│   │   ├── patients.rs      <- Patient list (Tab 1)
│   │   ├── stats.rs         <- Statistics (Tab 2)
│   │   ├── vlk.rs           <- VLK timeline (Tab 3)
│   │   ├── alerts.rs        <- Smart alerts (Tab 4)
│   │   ├── sync.rs          <- Sync status (Tab 5)
│   │   ├── operations.rs    <- Surgery schedule (Tab 6)
│   │   ├── wards.rs         <- (36 KB) Ward grid (Tab 7)
│   │   ├── popup.rs         <- (22 KB) Patient detail (6 tabs)
│   │   ├── doctor_dashboard.rs <- (85 KB) Doctor mode (7 tabs)
│   │   ├── table.rs         <- (23 KB) SmartTable component
│   │   ├── quick_actions.rs <- Quick actions menu (Tier 6.2)
│   │   ├── login.rs         <- Doctor login (PIN entry)
│   │   ├── morning_report.rs <- Daily briefing (F05)
│   │   ├── health_dashboard.rs <- Service health (F11)
│   │   ├── header.rs        <- Status bar + P2P display
│   │   ├── shortcuts.rs     <- Dynamic keyboard guide
│   │   ├── toast.rs         <- Toast notifications
│   │   ├── confirm.rs       <- Confirmation dialogs
│   │   ├── error_detail.rs  <- Error popup
│   │   ├── help.rs          <- Help page
│   │   ├── selector.rs      <- ZAV/Doctor mode selector
│   │   ├── freshness.rs     <- Staleness indicators
│   │   └── splash.rs        <- Startup animation
│   │
│   ├── scraper/             (76 KB) - EMR BROWSER SCRAPER [DEAD CODE]
│   │   ├── browser.rs       <- Chromium automation (chromiumoxide)
│   │   ├── patients.rs      <- Patient list scraping
│   │   ├── enrichment.rs    <- Detail page enrichment
│   │   ├── diary_submit.rs  <- Diary form submission
│   │   └── types.rs         <- ScrapedPatient types
│   │
│   ├── sync/                (53 KB) - External Integrations
│   │   ├── cyberintern.rs   <- CyberIntern API client (027/o, labs, docs)
│   │   └── validator.rs     <- Data validation rules
│   │
│   ├── p2p/                 (41 KB) - Peer-to-Peer Sync
│   │   ├── discovery.rs     <- mDNS peer discovery
│   │   ├── sync.rs          <- Delta sync engine
│   │   ├── tls.rs           <- TLS for P2P comms
│   │   └── types.rs         <- P2pStatus, PeerInfo, SyncEvent
│   │
│   ├── pdf/                 (29 KB) - PDF Generation
│   │   ├── generator.rs     <- Typst-based PDF
│   │   └── templates.rs     <- 027 + Dovidka templates
│   │
│   ├── analytics/           (36 KB) - Polars Data Analytics
│   │   ├── reports.rs       <- Daily report (F05)
│   │   └── trends.rs        <- Trend analysis
│   │
│   └── updater/             (84 KB) - Auto-Update System
│       ├── github.rs        <- GitHub release fetching
│       ├── download.rs      <- Binary download + checksum
│       ├── apply.rs         <- Update logic
│       └── ui.rs            <- Update popup display
│
├── Cargo.toml              (30+ dependencies)
└── Cargo.lock
```

---

## Entry Points

**main.rs** starts with:
1. Parse CLI args (`--headless`, `--server`)
2. Find/backup database
3. Start embedded server (port 8084, fallback 8085/8086)
4. Start P2P discovery in background
5. Show master selector: **ZAV** (1) | **Doctor** (2) | **Quit** (Q)

| Mode | Lines | Purpose |
|------|-------|---------|
| ZAV | 264-728 | Full hospital management TUI (7 tabs) |
| Doctor | 735-1291 | CyberIntern medical assistant (7 tabs) |
| Headless | - | Server-only, no UI |

---

## API Endpoints (30+)

### Core

| Route | Method | Purpose |
|-------|--------|---------|
| `/` | GET | Root info |
| `/health` | GET | Health check |
| `/stats` | GET | DB statistics |
| `/api/cache/stats` | GET | Cache stats |

### Patients

| Route | Method | Purpose |
|-------|--------|---------|
| `/patients` | GET | All/hospitalized (cached) |
| `/patients/{case}` | GET | Single patient (cached) |
| `/patients/{case}` | PATCH | Update fields |
| `/patients/{case}/discharge` | POST | Discharge patient |
| `/patients/by-doctor/{name}` | GET | Filter by doctor |
| `/patients/by-ward/{ward}` | GET | Filter by ward |
| `/patients/search` | GET | Search (for Slack) |
| `/patients/{case}/vlk` | PATCH | Update VLK (MEGALITH 6) |

### Sync

| Route | Method | Purpose |
|-------|--------|---------|
| `/sync` | POST | Start EMR sync |
| `/sync/status` | GET | Sync status |
| `/sync/enrich` | POST | Trigger enrichment |
| `/sync/enrich-cyberintern` | POST | CyberIntern enrichment |
| `/validate` | GET | Validation summary |

### Operations

| Route | Method | Purpose |
|-------|--------|---------|
| `/operations` | GET | All operations |
| `/operations` | POST | Create operation |
| `/operations/today` | GET | Today's surgeries |
| `/operations/{id}` | GET/PATCH/DELETE | CRUD |

### Wards

| Route | Method | Purpose |
|-------|--------|---------|
| `/wards/occupancy` | GET | Ward status (Slack /beds) |
| `/ward-transfers` | POST | Record transfer (F10) |
| `/ward-transfers/{name}` | GET | Transfer history |

### P2P

| Route | Method | Purpose |
|-------|--------|---------|
| `/p2p/changes` | GET | Delta sync changes |
| `/p2p/apply` | POST | Apply peer changes |
| `/p2p/status` | GET | Node status |
| `/p2p/peers` | GET | Connected peers |

### Auth

| Route | Method | Purpose |
|-------|--------|---------|
| `/auth/login` | POST | Doctor login |
| `/auth/register` | POST | Create doctor |

### Other

| Route | Method | Purpose |
|-------|--------|---------|
| `/pdfs/{filename}` | GET | Serve generated PDFs (F06) |
| `/vlk/summary` | GET | VLK status (Slack /vlk) |

---

## Database Schema

**File:** `~/.local/share/zav/zav.db` (SQLite, WAL mode)

### patients (56 columns)

| Category | Fields |
|----------|--------|
| **EMR basic** | case_number (UNIQUE), case_id, case_url, history_number, pib, case_date, admission_date, case_type, age, sex, diagnosis_general, reanimation, doctor, ward, bed, days_in_hospital |
| **Enrichment** | hospital_card_number, ehealth_id, bed_type, institution, case_created_by, admission_department, current_division, division, case_created_datetime, full_diagnosis |
| **Metadata** | birth_date, trauma_date, blood_type, address, workplace, marital_status, contingent, preferential_category, personal_signs, social_status, identity_document_type |
| **VLK** | vlk_date, vlk_decision, extension_days |
| **Manual** | diagnosis_specified, notes |
| **027/o form** | discharge_date, complaints, disease_anamnesis, life_anamnesis, objective_status, lab_tests, instrumental_tests, consultations, treatment, treatment_result, recommendations, sicklist_start, sicklist_end, physical_history_number |
| **System** | status, created_at, updated_at, last_enriched_at |

**Indexes:** case_number, pib, ward, doctor, status (+ 2 more)

### Other Tables

| Table | Columns | Purpose |
|-------|---------|---------|
| sync_history | 8 | EMR sync tracking |
| ward_transfers | 6 | Zone transfer history (F10) |
| change_log | 8 | P2P delta sync |
| operations | 14 | Surgery schedule |
| doctors | 5 | Auth (username, password_hash, role) |
| settings | 2 | Key-value config |

---

## TUI Tabs

### ZAV Mode (7 tabs)

| Tab | Key | Module | Size |
|-----|-----|--------|------|
| Patients | 1 | patients.rs | 7.9 KB |
| Stats | 2 | stats.rs | 15 KB |
| VLK | 3 | vlk.rs | 16 KB |
| Alerts | 4 | alerts.rs | 15 KB |
| Sync | 5 | sync.rs | 7.9 KB |
| Operations | 6 | operations.rs | 7.3 KB |
| Wards | 7 | wards.rs | 36 KB |

### Doctor Mode (7 tabs)

| Tab | Module | Purpose |
|-----|--------|---------|
| Dashboard | doctor_dashboard.rs | Patient list + diary queue |
| Alerts | (shared) | Health monitoring |
| Diaries | (inline) | Generation + batch writer |
| Labs | (inline) | Lab results |
| Documents | (inline) | Vypyska, Dovidka, EMR fetch |
| EMRSync | (inline) | Status polling |
| PatientDetail | (inline) | Scrollable patient view |

### Popups/Modals

- Patient detail (6 sub-tabs: Boss, CyberIntern, Labs, Trauma, VLK, Notes)
- Morning report (F05 overlay)
- Health dashboard (F11 overlay)
- Help page
- Confirmation dialog
- Error detail
- Quick actions menu (Tier 6.2)
- Update notification
- Toast queue

---

## Key Subsystems

| System | Location | Size | Status |
|--------|----------|------|--------|
| **Embedded REST API** | server/ | 152 KB | Active, 30+ endpoints |
| **EMR Scraper** | scraper/ | 76 KB | DEAD CODE (allow(dead_code)) |
| **CyberIntern Client** | sync/cyberintern.rs | 53 KB | Active, 027/o integration |
| **P2P Sync** | p2p/ | 41 KB | Active, mDNS + delta sync |
| **PDF Generation** | pdf/ | 29 KB | Active, Typst-based |
| **Analytics** | analytics/ | 36 KB | Active, Polars dataframes |
| **Auto-Updater** | updater/ | 84 KB | Active, GitHub releases |

---

## Issues Found

### CRITICAL

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | **GOD MODULE: app.rs** (3,100 lines, 172 fields) | `src/app.rs` | Unmaintainable, untestable |
| 2 | **main.rs mixed concerns** (1,517 lines, 2 mode loops) | `src/main.rs` | Business logic in entry point |

### HIGH

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 3 | **routes.rs monolith** (1,539 lines, 30+ handlers) | `server/routes.rs` | No validation layer, duplicated error handling |
| 4 | **Scraper module: 76 KB dead code** | `scraper/` | Binary bloat (~50 MB from chromiumoxide) |
| 5 | **doctor_dashboard.rs: 85 KB single component** | `ui/doctor_dashboard.rs` | 7 tabs + 3 state machines in one file |
| 6 | **P2P startup fails silently** | `main.rs:90-118` | User sees 0 peers with no explanation |
| 7 | **Database lock issues on Windows** | `server/db.rs` | After crash, port/file may stay locked |

### MEDIUM

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 8 | Dual error handling (miette + anyhow) | Throughout | Inconsistent error messages |
| 9 | Cache invalidation manual in routes | `routes.rs` | New endpoints may forget to invalidate |
| 10 | 16+ `#[allow(dead_code)]` annotations | Throughout | Unclear what's intentional |
| 11 | No structured logging (uses eprintln!) | Throughout | No log filtering |

### LOW

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 12 | No test coverage | - | Untested critical paths |
| 13 | No API documentation/OpenAPI | Routes | Client devs must read source |
| 14 | Verbose startup logging | main.rs | Not structured |

---

## Dependency Highlights

| Crate | Purpose | Concern |
|-------|---------|---------|
| ratatui 0.30 | TUI | Stable |
| tokio 1.* | Async | Essential |
| axum 0.8 | Web | Young but active |
| rusqlite 0.33 | SQLite | Bundled, stable |
| **chromiumoxide 0.7** | Browser | **76 KB DEAD CODE, ~50 MB bloat** |
| polars 0.45 | Analytics | Heavy but used (F05, F11) |
| typst 0.14 | PDF | Used for F06 |
| mdns-sd 0.11 | P2P | P2P feature |

---

## Feature Completeness

All 11 roadmap features (F01-F11) implemented.
All 11 tier enhancements (1.2, 2.1-2.4, 3.2-3.3, 4.1-4.2, 6.1-6.2) implemented.
4 development phases completed.

---

## Scorecard

| Category | Score | Notes |
|----------|-------|-------|
| Module Organization | 5/10 | God modules need refactoring |
| API Design | 8/10 | Good routes, needs validation layer |
| Database Schema | 9/10 | Complete, well-indexed |
| Error Handling | 6/10 | Dual approach, needs completion |
| Testing | 2/10 | None |
| Documentation | 4/10 | API not documented |
| Dependencies | 6/10 | 76 KB unused scraper |
| Performance | 7/10 | Good cache, P2P needs work |
| Feature Completeness | 10/10 | All 11 features + 11 tiers |
| **OVERALL** | **6.3/10** | **Functional but needs refactoring** |

---

## Priority Actions

1. **Remove chromiumoxide** if scraper stays unused (-50 MB binary)
2. **Split app.rs** into domain models (PatientManager, SyncManager, AlertManager)
3. **Split routes.rs** into route modules (patients, sync, operations, p2p)
4. **Split main.rs** into ZavMode + DoctorMode launchers
5. **Add integration tests** for critical paths
6. **Make P2P failure visible** in UI header
7. **Complete miette migration** (or commit to anyhow)
