# Zav Project Status

**Updated:** 2026-02-02
**Status:** ✅ PRODUCTION READY

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
- Zav-8r1: Test CyberIntern enrichment endpoint (P1)
- Zav-bf4: Test Airtable sync endpoint (P1) ✅ COMPLETE
- Zav-bup: Test EMR sync endpoint (P2, in progress)

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
