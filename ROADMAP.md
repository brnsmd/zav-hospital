# ZAV BOSS-TUI ROADMAP 🪓

**Created:** 2026-02-06 by WINDUG
**Purpose:** Features we need but don't have

---

## P0 — MUST HAVE (System breaks without these)

### [F01] Post-Sync Pipeline
**Status:** NOT STARTED
**Why:** After EMR scrape, nothing happens automatically. User must manually trigger Airtable push, VLK pull, CyberIntern enrichment separately.
**Fix:** After scrape completes, auto-chain: push to Airtable → pull VLK from Airtable → enrich from CyberIntern. Single pipeline, fires on every sync.
**Files:** `src/server/routes.rs` (start_sync handler), `src/app.rs` (sync trigger)

### [F02] Stale Data Indicator
**Status:** NOT STARTED
**Why:** Patient safety. User sees patient list but has NO idea if data is 5 minutes or 5 hours old. `DataFreshness` model exists but UI doesn't show it prominently.
**Fix:** Show "Last sync: X min ago" in header bar. Turn red if >60 min. Show "OFFLINE — cached data" when API unreachable.
**Files:** `src/ui/header.rs`, `src/app.rs` (freshness tracking)

---

## P1 — IMPORTANT (System drifts without these)

### [F03] VLK/Airtable Auto-Sync Timer
**Status:** NOT STARTED
**Why:** VLK cache columns exist in DB but nothing populates them. Airtable push is hourly via n8n but if n8n is down, data drifts.
**Fix:** Internal tokio timer: every 30 min, POST to own `/sync/vlk-from-airtable` and `/sync/airtable`. Self-contained, no n8n dependency.
**Files:** `src/app.rs` or `src/server/mod.rs` (spawn timer task)

### [F04] Local SQLite Backup
**Status:** NOT STARTED
**Why:** Single point of failure. `C:\ZavBoss\data\zav.db` dies = all enrichment, VLK cache, notes gone.
**Fix:** On startup + every 6 hours, copy `zav.db` → `zav.db.bak` (timestamped, keep last 3).
**Files:** `src/server/db.rs` (add backup method)

---

## P2 — VALUABLE (Replaces external dependencies)

### [F05] Morning Report in TUI
**Status:** NOT STARTED
**Why:** Doctor opens TUI at 7:30 AM, sees raw data. Morning briefing only goes to Slack via n8n. Doctor must check two places.
**Fix:** On first launch or on-demand, show morning digest: VLK warnings, overstay alerts, today's operations, bed occupancy, new admissions since yesterday.
**Files:** `src/ui/` (new morning report overlay), `src/app.rs`

### [F06] Local Discharge PDF Path (Cut Google Docs)
**Status:** PARTIALLY DONE (PDF gen wired to quick actions)
**Why:** Discharge needs: TUI → n8n → Slack → Google Docs → Airtable. If Slack/n8n/Google down, discharge stalls.
**Fix:** TUI generates 027/о locally via Typst (ALREADY WORKS) → upload PDF directly to Airtable attachment field. Bypasses n8n + Google Docs + Slack entirely.
**Files:** `src/app.rs` (discharge quick action), `src/sync/airtable.rs` (attachment upload)

---

## P3 — NICE TO HAVE (Clinical quality of life)

### [F07] Surgery Checklist View
**Status:** NOT STARTED
**Why:** Pre-op checklist goes to Slack every 30min. TUI has no surgery view. Doctor checks Slack instead of TUI.
**Fix:** Operations tab shows today's surgeries with checkable items: consent (Y/N), labs fresh (Y/N), blood typed (Y/N), fasting confirmed (Y/N).
**Files:** `src/ui/` (operations tab enhancement), `src/models/`

### [F08] Patient Timeline / History
**Status:** NOT STARTED
**Why:** Patient detail view shows current snapshot only. No history: when admitted, when VLK was scheduled, when enriched.
**Fix:** Show chronological event log from date fields: admission → enrichment → VLK warning → VLK done → discharge.
**Files:** `src/ui/` (patient detail enhancement)

### [F09] Batch Discharge
**Status:** NOT STARTED
**Why:** End of week, 5-8 patients discharge at once. Each one is manual select → action → confirm.
**Fix:** Multi-select patients (checkboxes), confirm all at once. Generates all PDFs, triggers all webhooks.
**Files:** `src/app.rs` (batch action mode), `src/ui/patients.rs`

### [F10] Ward Transfer History
**Status:** NOT STARTED
**Why:** Zone transfer modal exists but no log. Patient moves wards, old assignment vanishes. No audit trail for infection control.
**Fix:** New `ward_transfers` table: (patient, from_ward, from_bed, to_ward, to_bed, timestamp, reason). Show in patient detail.
**Files:** `src/server/db.rs` (new table), `src/ui/` (transfer log display)

### [F11] Health Dashboard in TUI
**Status:** NOT STARTED
**Why:** After startup splash, no way to see if n8n/Airtable/CyberIntern are up without leaving TUI.
**Fix:** Status bar or health indicator showing service states. Ping endpoints periodically.
**Files:** `src/app.rs` (health check timer), `src/ui/header.rs` (status icons)

---

## Implementation Order

WINDUG will implement in this order (simplest + highest impact first):
1. F02 — Stale data indicator (UI only, quick win)
2. F04 — Local backup (trivial, prevents data loss)
3. F01 — Post-sync pipeline (chains existing code)
4. F03 — Auto-sync timer (keeps data fresh)
5. F05 — Morning report (replaces Slack dependency)
6. F06 — Local discharge PDF (partially done)
7. F11 — Health dashboard (piggybacks on existing models)
8. F07-F10 — Clinical features (need Grug input on UX)
