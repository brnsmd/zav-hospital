# Zav Project Status

**Updated:** 2026-02-17
**Status:** ENRICHMENT FIXED — Testing debug build

---

## 2026-02-17: GREAT BOAR HUNT — Enrichment Restored

### What happened

The "simplify" epic (Feb 13-17) successfully removed CyberIntern middleware and BossClient HTTP middleman, replacing both with direct DB access and direct EMR API calls. However, it left enrichment half-migrated: sync (Ctrl+S) worked correctly with doctor credentials, but standalone enrichment (Shift+E) still routed through HTTP to the embedded server, which read credentials from empty env vars. Result: enrichment returned zero data.

### The Hunt: 6 critical bugs fixed + 4 follow-up improvements

**Commit `dec7e5b` — 6 enrichment bugs:**

| # | Bug | Impact | Fix |
|---|-----|--------|-----|
| 1 | `trigger_enrichment()` routed through HTTP, server read empty env vars | Enrichment returned 0 data | Direct call with doctor credentials |
| 2 | Hash saved before enrichment | Failed enrichment = permanently un-enrichable | Hash saved after success |
| 3 | `days_in_hospital` + 5 other fields used `= ?N` not COALESCE | Data destroyed on every sync | All 6 fields now COALESCE |
| 4 | No enrichment result feedback to TUI | User couldn't tell if it worked | Arc<Mutex> result channel + toast |
| 5 | EMR client builder silently fell back to cookieless client | All auth would silently fail | `expect()` instead of fallback |
| 6 | No retry limit on 401/403 in paginated requests | Infinite loop on locked accounts | 3-retry limit |

**Follow-up commits:**

| Commit | Description |
|--------|-------------|
| `d019ee2` | Remove 200 lines dead code (8 unused types, fetch_all_patients, health_check, base_url) |
| `beb5318` | Add warn! logging to 10+ silent error paths in sync and enrichment |
| `265d1a7` | Extract case_type (enables ICU detection) and compute age from birthday |
| `4cd6a6d` | Extract history_number from EMR case detail |
| `0737d86` | Add DEBUG.bat launcher for debug builds |

### Current state

- Debug build compiled and ready at `boss-tui/target/debug/boss-tui.exe`
- `boss-tui/DEBUG.bat` launches with correct env vars
- Testing pending (user in OR)

### Remaining known issues

- **EMRTuiClient stub** — Old api/emr.rs still used by space-menu actions (morning, alerts, diaries). Returns stubs. Needs rewiring to use real emr::EMRClient or DB. Deferred.
- **sicklist_start/end** — Never populated (EnrichmentData doesn't have these fields)
- **blood_type** — Never extracted from EMR
- **Several DB fields not in UI model** — contingent, diagnosis_specified, notes, etc. stored but not displayed

---

## Architecture (Post-Simplify)

```
TUI (app.rs)                    Embedded Server (port 8084)
  |                               |
  +-- Arc<Database> -- SQLite     +-- Same Database (for external clients)
  |   (direct access)             |   (P2P sync, external tools)
  |                               |
  +-- trigger_boss_sync()         +-- EMR import (same function)
  |     perform_emr_import_direct()
  |
  +-- trigger_enrichment()
        perform_emr_enrichment_direct()
```

**Key change:** Both sync AND enrichment now bypass HTTP and call direct functions with doctor credentials. The embedded HTTP server still runs for external API consumers only.

### Data Flow

```
EMR (hospital system)          Boss TUI
  |                              |
  +-- EMR API -----------------> perform_emr_import_direct()
                                   Phase 1: Fetch patient IDs (HTML scraping)
                                   Phase 2: Fetch details, hash comparison
                                   Phase 3: Deep enrichment (only changed patients)
                                     -> 027/o fields, sub-tables
                                     -> Hash saved AFTER success
                                 |
                                 +-- perform_emr_enrichment_direct()
                                       Standalone enrichment for all patients
                                       -> Same fields + sub-tables
                                       -> Results flow back to TUI as toast
```

### Ports
- **8084**: Boss TUI embedded server (Rust axum)
- **8082**: CyberIntern (Python FastAPI — legacy, mostly unused)

---

## Issue Tracking

See `.beads/` for historical issues. Active development tracked via Claude Code tasks.
