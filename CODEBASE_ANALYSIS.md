# Zav Codebase Analysis & Improvement Plan

**Generated:** 2026-01-24
**Purpose:** Comprehensive analysis for future improvements

---

## Executive Summary

The Zav Hospital Management System is a **production-ready** multi-component platform consisting of:

| Component | Technology | Lines of Code | Status |
|-----------|------------|---------------|--------|
| **Zav Project** | Python/Flask | ~3,500 | Production |
| **Boss TUI** | Rust/Ratatui | ~3,500 | Production |
| **Boss API** | Python/FastAPI | ~2,700 | Production |
| **n8n Workflows** | 12 workflows | N/A | Active |
| **CyberIntern MCP** | Python | ~1,500 | Ready |

**Total:** ~11,000+ lines of production code

---

## Architecture Overview

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      EMR        │────▶│    Boss DB      │────▶│    Airtable     │
│   (Hospital)    │     │   (SQLite)      │     │  (Source Truth) │
└─────────────────┘     └─────────────────┘     └─────────────────┘
    Playwright              FastAPI                  REST API
    (relay mode)            :8083                       │
                               │                        │
                               ▼                        ▼
                    ┌───────────────────────────────────────────┐
                    │                   n8n                     │
                    │              localhost:5678               │
                    │           (12 active workflows)           │
                    └───────────────────────────────────────────┘
                               │
          ┌────────────────────┼────────────────────┐
          ▼                    ▼                    ▼
    ┌──────────┐        ┌──────────┐        ┌──────────┐
    │  SLACK   │        │ Boss TUI │        │ Zav Cloud│
    │ #alerts  │        │  (Rust)  │        │ Railway  │
    │ /patient │        │          │        │          │
    └──────────┘        └──────────┘        └──────────┘
```

---

## Component Analysis

### 1. Zav Project (`/var/home/htsapenko/Projects/Zav`)

**Purpose:** Central coordination, documentation, and web dashboard

**Key Files:**
- `zav_cloud_server.py` (2,298 lines) - Flask/Gunicorn web server
- `cyberintern_mcp/` - MCP server for medical records (10 tools)
- `CLAUDE.md` - Main reference document
- `STATUS.md` - System health tracking

**Strengths:**
- Well-organized documentation
- Clear separation of concerns
- Production deployment on Railway

**Issues:**
- Legacy code still present (`telegram_bot/`, old CLI)
- `brood/` directory (1.6 MB) should be pruned
- Some hardcoded references

---

### 2. Boss TUI (`/var/home/htsapenko/Projects/boss-tui`)

**Purpose:** Terminal dashboard for rapid patient data access

**Key Modules:**
- `main.rs` (270 lines) - Event loop, keyboard handling
- `app.rs` (962 lines) - State machine, business logic
- `api/` - Boss, n8n, Airtable clients
- `ui/` - 12 UI components (header, tabs, popups, etc.)

**Features Implemented:**
- 6-tab interface (Patients, Stats, VLK, n8n, Airtable, Alerts)
- Real-time search with filtering
- VLK tracking (120-day military commission deadline)
- Discharge workflows (Boss API + n8n webhooks)
- Toast notifications, help overlay

**Issues Found & Fixed (2026-01-24):**
- **HTTP timeout missing** - Added 10s timeout, 5s connect timeout (`app.rs`)
- **Tailscale blocking startup** - Removed from `boss()`, created `boss-relay` (`.zshrc`)
- **Airtable not connecting** - Added URL encoding for Cyrillic table names (`api/airtable.rs`)
- **Secrets not loaded** - Added explicit sourcing of `zav-secrets.env` in boss function

**Remaining Issues:**
- No retry logic for failed requests
- Hardcoded Airtable form URL
- UTC+2 timezone hardcoded
- Large monolithic `App` struct

---

### 3. Boss API (`/var/home/htsapenko/Projects/cyberintern-boss`)

**Purpose:** EMR scraper and patient data API

**Key Modules:**
- `src/main.py` (610 lines) - FastAPI + APScheduler
- `src/scraper.py` (845 lines) - Playwright browser automation
- `src/database.py` (523 lines) - SQLite ORM
- `src/airtable_sync.py` (374 lines) - Smart Airtable sync

**API Endpoints:** 14 REST endpoints
**Database:** SQLite with 36 patient fields

**Strengths:**
- Clean async architecture (thread pool for Playwright)
- Smart Airtable sync (only fills empty fields)
- Comprehensive patient enrichment (28+ fields)
- Auto-sync every 30 minutes

**Issues:**
- Only partial type hints
- No test suite
- No request authentication on API
- Raw sqlite3 instead of SQLAlchemy ORM

---

### 4. n8n Workflows

**Active Workflows:** 12

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| VLK Alert System | Daily 7 AM | Track military commissions |
| Daily Morning Report | Hourly | Status briefing |
| Surgery Checklist | Every 30 min | Pre/post-op checklists |
| Operations | Polling | Surgery status updates |
| Boss → Airtable Sync | Scheduled | Data synchronization |
| Patient Discharge Hub | Webhook | Discharge processing |
| Slack: /patient | Slash command | Patient lookup |
| Slack: /ops | Slash command | Today's operations |
| Slack: /beds | Slash command | Ward occupancy |
| Overstay Alert | Daily 9 AM | Flag >30/>60 day stays |
| New Patient Admission | Every 1 min | Intake notifications |
| Operation Plan | Daily 12:00 | Weekly surgery schedule |

**Known Issues:**
- ngrok URL changes on restart (need static domain)
- Webhooks created via API don't register (workaround: save in UI)

---

## Critical Issues (Must Fix)

| Issue | Component | Impact | Priority |
|-------|-----------|--------|----------|
| ~~Boss TUI hangs on startup~~ | boss-tui | **FIXED** (HTTP timeout added) | - |
| ~~HTTP client no timeout~~ | boss-tui | **FIXED** (10s timeout, 5s connect) | - |
| ~~Tailscale blocking boss~~ | zshrc | **FIXED** (moved to boss-relay) | - |
| ~~Airtable not connecting~~ | boss-tui | **FIXED** (URL encoding for Cyrillic) | - |
| ~~ngrok URL instability~~ | n8n/Slack | **DONE** (static domain) | - |
| No API authentication | Boss API | Security risk | HIGH |
| Telegram bot still running | Zav | Duplicate notifications | MEDIUM |

---

## Improvement Opportunities

### High Priority

1. **Persistent ngrok domain** (FREE available)
   - Eliminates URL changes on restart
   - No Slack app reconfiguration needed
   - Effort: Low, Value: High

2. **Add API authentication to Boss API**
   - API key header validation
   - Protect sensitive patient data
   - Effort: Low, Value: High

3. **Shutdown Telegram bot**
   - All functions migrated to Slack
   - Remove maintenance burden
   - Effort: Low, Value: Medium

### Medium Priority

4. **Add retry logic to Boss TUI**
   - Exponential backoff for failed requests
   - Better offline handling
   - Effort: Medium, Value: Medium

5. **Add test suites**
   - Boss API: Unit tests for scraper, database
   - Boss TUI: Integration tests with mock APIs
   - Effort: High, Value: High

6. **Type hints for Boss API**
   - Full type annotations
   - Better IDE support, fewer bugs
   - Effort: Medium, Value: Medium

### Low Priority

7. **Archive `brood/` directory**
   - 1.6 MB of old planning artifacts
   - Move to separate repo or delete
   - Effort: Low, Value: Low

8. **Configurable timezone in Boss TUI**
   - Currently hardcoded UTC+2
   - Effort: Low, Value: Low

9. **Database migrations with Alembic**
   - Replace manual ALTER TABLE
   - Effort: Medium, Value: Low

---

## Shell Commands Reference

```bash
# Start Boss TUI (auto-starts n8n + Boss API, NO Tailscale)
boss

# Start with Tailscale relay (for EMR scraping)
boss-relay

# Disable Tailscale relay only
boss-relay-off

# Check system status
boss-status

# Stop all services
boss-stop

# Start ngrok tunnel (required for Slack commands)
ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev

# Check service health
curl http://localhost:8083/health  # Boss API
curl http://localhost:5678/healthz  # n8n
```

### Boss Commands Summary

| Command | Tailscale | n8n | Boss API | TUI |
|---------|-----------|-----|----------|-----|
| `boss` | No | Start | Start | Launch |
| `boss-relay` | Start | Start | Start | Launch |
| `boss-relay-off` | Stop | - | - | - |
| `boss-stop` | - | Stop | Stop | - |
| `boss-status` | Check | Check | Check | - |

---

## Data Flow Summary

### Patient Data Flow
```
EMR (Hospital)
    → [Playwright scraper, relay mode]
Boss API (SQLite)
    → [REST API, 30-min auto-sync]
Airtable (Source of Truth)
    → [Polling triggers]
n8n Workflows
    → [Webhooks, scheduled triggers]
Slack (#alerts, #operations, /commands)
```

### VLK Tracking Flow
```
Airtable: Дата травми (trauma date)
    → Formula: Дні з травми = TODAY() - trauma_date
    → Formula: ВЛК статус = IF(days >= 120, "🔴", IF(days >= 100, "🟠", "🟢"))
    → n8n: VLK Alert System (daily 7 AM)
    → Slack: #alerts channel
```

---

## Environment Variables

All stored in `~/.config/zav-secrets.env`:

```bash
# Boss API
BOSS_API_URL=http://localhost:8083

# n8n
N8N_URL=http://localhost:5678
N8N_API_KEY=<jwt-token>

# Airtable
AIRTABLE_TOKEN=<token>
AIRTABLE_BASE=appv5BwoWyRhT6Lcr

# Slack
SLACK_BOT_TOKEN=<token>

# ngrok
NGROK_AUTHTOKEN=<token>

# CyberIntern MCP
CYBERINTERN_API_URL=http://localhost:8082
CYBERINTERN_USERNAME=admin
CYBERINTERN_PASSWORD=admin123456
```

---

## Next Steps (Recommended Order)

### Completed
- [x] Set up persistent ngrok domain (kristeen-rootlike-unflirtatiously.ngrok-free.dev)
- [x] Fix Boss TUI HTTP timeouts
- [x] Fix Airtable connection (URL encoding)
- [x] Separate Tailscale from boss startup (boss-relay)

### Remaining
1. [ ] Add API key to Boss API (security)
2. [ ] Shutdown Telegram bot (cleanup)
3. [ ] Add retry logic to Boss TUI HTTP client
4. [ ] Create test suite for Boss API
5. [ ] Add full type hints to Boss API
6. [ ] Archive brood/ directory
7. [ ] Configure timezone in Boss TUI

---

## File Structure Summary

```
Projects/
├── Zav/                        # Main project coordination
│   ├── CLAUDE.md               # Reference doc (213 lines)
│   ├── STATUS.md               # System health
│   ├── CODEBASE_ANALYSIS.md    # THIS FILE
│   ├── cyberintern_mcp/        # MCP server (10 tools)
│   ├── docs/                   # 20 reference docs
│   ├── archive/                # Old sessions, handoffs
│   └── telegram_bot/           # DEPRECATED
│
├── boss-tui/                   # Rust TUI dashboard
│   ├── src/main.rs             # Entry point
│   ├── src/app.rs              # State machine
│   ├── src/api/                # API clients
│   ├── src/ui/                 # UI components
│   └── target/release/boss-tui # Binary
│
└── cyberintern-boss/           # Python FastAPI backend
    ├── src/main.py             # FastAPI + scheduler
    ├── src/scraper.py          # Playwright EMR scraper
    ├── src/database.py         # SQLite operations
    ├── src/airtable_sync.py    # Smart sync
    └── data/boss.db            # SQLite database
```

---

**Document Version:** 1.0
**Last Updated:** 2026-01-24
