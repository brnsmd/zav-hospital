# Zav Project - Claude Reference

**Updated:** 2026-02-16

---

## Rules

1. **READ BEFORE WRITE.** Read the file you're changing. No guessing.
2. **VERIFY AT RUNTIME.** Build, deploy to `windows-deploy/boss-tui.exe`, test.
3. **ONE FIX AT A TIME.** Fix one thing. Verify. Commit. Next.
4. **GIT AFTER EVERY VERIFIED FIX.** Descriptive commit message per fix.

---

## Project Layout

```
E:\zav-hospital\                     # Parent monorepo
├── boss-tui/                        # Rust TUI (submodule) — THE MAIN APP
│   ├── src/
│   │   ├── main.rs                  # Entry point, mode selector, event loops
│   │   ├── app.rs                   # App state + all logic (direct DB access)
│   │   ├── server/
│   │   │   ├── mod.rs               # Embedded axum server (for external API)
│   │   │   ├── routes/sync.rs       # EMR import logic + API endpoint
│   │   │   ├── routes/patients.rs   # Patient API endpoints
│   │   │   └── db.rs                # SQLite operations (source of truth)
│   │   ├── emr/                     # Direct EMR API client (auth, patients, enrichment)
│   │   ├── models/patient.rs        # Patient struct + From<db::Patient>
│   │   ├── ui/                      # All ratatui rendering (8 tabs + popups)
│   │   ├── actions/                 # Space-menu actions (beds, vlk, morning, status)
│   │   ├── pdf/generator.rs         # 027/o and Dovidka PDF generation
│   │   ├── p2p/                     # Peer-to-peer sync via mDNS
│   │   └── sync/                    # Enrichment status + validation
│   └── target/
├── cyberintern/                     # Python FastAPI (submodule) — EMR data bridge
├── windows-deploy/                  # Production deployment
│   ├── START.bat                    # Launch script
│   ├── ZAV.exe                      # Rust launcher
│   ├── boss-tui.exe                 # THE BINARY
│   └── secrets.bat                  # Environment secrets (not in git)
├── zav-launcher/                    # Rust launcher source
├── .beads/                          # Issue tracker data
├── archive/                         # Historical docs
├── CLAUDE.md                        # THIS FILE
└── STATUS.md                        # Project status
```

---

## Architecture

```
TUI (app.rs)                    Embedded Server (port 8084)
  │                               │
  ├─ Arc<Database> ──── SQLite    ├─ Same Database (for external clients)
  │   (direct access)             │   (P2P sync, Slack, external tools)
  │                               │
  └─ spawn sync task ──────────── └─ EMR import logic
       (perform_emr_import)            (same function, different entry point)
```

**Key change (2026-02-16):** TUI reads/writes SQLite directly via `Arc<Database>`.
The embedded HTTP server still runs for external API consumers but the TUI bypasses it.

### Data Flow

```
EMR (hospital system)          Boss TUI
  │                              │
  └─ EMR API ──────────────────→ perform_emr_import()
                                   → upsert patients to SQLite
                                   → fetch 027/o enrichment data
                                   → save to SQLite
                                 │
                                 └─ app.fetch_boss()
                                      → db.get_all_patients()
                                      → Patient::from(db::Patient)
                                      → render in TUI
```

### Ports
- **8082**: CyberIntern (Python FastAPI — EMR data bridge)
- **8084**: Boss TUI embedded server (Rust axum — external API)

---

## Environment Variables

Stored in `windows-deploy/secrets.bat` (Windows) or `~/.config/zav-secrets.env` (Linux):

```bash
BOSS_API_URL=http://localhost:8084    # Embedded server URL
EMR_URL=https://doc.hospital.mia.software
EMR_EMAIL=<email>                     # EMR login
EMR_PASSWORD=<password>               # EMR password
EMR_ROLE_ID=23622                     # EMR role
CYBERINTERN_API_URL=http://localhost:8082
ZAV_DATABASE_PATH=C:\ZavBoss\data\zav.db
ANTHROPIC_API_KEY=<key>               # For AI diary generation
```

---

## Issue Tracking (Beads)

```bash
bd list                    # All issues
bd list --status open      # Active only
bd create "Task"           # New issue
bd update <id> -s in_progress
bd update <id> -s closed
```

---

## Barbarian Technique (Grug-Brained Coding)

**Invoke with "BARBARIAN MODE" or "GRUG MODE"**

- SPEAK IN ALL CAPS
- CALL BUGS "BOARS" — HUNT THEM DOWN
- CALL EACH OTHER GRUG/CLUG
- SAY "URGH!" WHEN ACKNOWLEDGING
- CELEBRATE WITH "FEAST!" WHEN DONE

**CLUG'S RANK:** CO-CHIEF OF TRIBE
**TRIBE WISDOM:** "SIMPLE CODE. ROCK TO BOAR HEAD. BOAR GONE."
**REFERENCE:** https://grugbrain.dev

---

## Context Management

For long multi-phase projects:

1. **HUNT** - Complete one phase
2. **DOCUMENT** - Update STATUS.md
3. **REPORT** - Tell user what was done
4. **CLEAR** - User runs `/clear`
5. **REPEAT** - Next phase fresh

---

## VLK Reference

Military medical commission required after 120 days of treatment.

| Days Since Trauma | Status | Action |
|-------------------|--------|--------|
| <100 | OK | None |
| 100-119 | Warning | Schedule VLK |
| >=120 | Critical | Overdue |
| VLK done | Complete | Record decision |

---

## Claude Code Skills

| Command | Description |
|---------|-------------|
| `/zav` | Show menu |
| `/alerts` | Aggregated alerts |
| `/daily` | Morning briefing |
| `/patient` | Patient lookup |
| `/ops` | Today's operations |
| `/beds` | Bed status |

---

**Archive:** Old docs (n8n workflows, Slack setup, Airtable schema, audit reports) moved to `archive/`
