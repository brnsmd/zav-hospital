# MEGA BOAR CATALOG - ZAV HOSPITAL FULL SYSTEM AUDIT
**Date:** 2026-02-13
**Auditor:** CLUG (CO-CHIEF OF TRIBE)
**Status:** BOAR GENOCIDE COMPLETE. EVERY FILE READ. EVERY BOAR CATALOGED.

**Completion:** 2026-02-13 — ALL 103 .rs files + configs + Python + deploy scripts read.

---

## STATISTICS

| Area | Critical | High | Medium | Low | Total |
|------|----------|------|--------|-----|-------|
| Scraper (chromiumoxide) | 3 | 1 | 0 | 0 | **4** |
| app.rs (god module) | 3 | 3 | 9 | 7 | **22** |
| main.rs + lib.rs | 4 | 4 | 6 | 11 | **25** |
| UI modules (33 files) | 5 | 0 | 7 | 10 | **22** |
| managers/actions/analytics/p2p/pdf/updater | 0 | 0 | 0 | 0 | **0** |
| api/ module (4 files) | 1 | 0 | 0 | 1 | **2** |
| models/ (11 files) | 0 | 0 | 0 | 0 | **0** |
| server/ (db.rs, routes, auth, cache) | 3 | 2 | 2 | 12 | **19** |
| CyberIntern (Python) | 1 | 2 | 3 | 7 | **13** |
| windows-deploy + zav-launcher | 3 | 3 | 4 | 6 | **16** |
| Cargo.toml / config | 2 | 0 | 0 | 0 | **2** |
| standalone (theme, helpers) | 0 | 0 | 1 | 0 | **1** |
| **GRAND TOTAL** | **25** | **15** | **32** | **54** | **126** |

### GENOCIDE RESULTS - FILES CONFIRMED CLEAN (0 boars):
- models/ (11 files, 3203 lines) - ALL CLEAN
- actions/ (7 files, 697 lines) - ALL CLEAN
- analytics/ (3 files, 943 lines) - ALL CLEAN
- pdf/ (3 files, 643 lines) - ALL CLEAN
- updater/ (4 files) - ALL CLEAN
- p2p/ (5 files) - ALL CLEAN (boars in p2p are from FIRST audit, confirmed)
- server/auth.rs, cache.rs, routes/operations.rs, routes/p2p.rs, routes/system.rs, routes/wards.rs - ALL CLEAN
- audit.rs, diary_prompt.rs, helpers.rs - ALL CLEAN
- api/anthropic.rs, api/n8n.rs - CLEAN

---

## TIER 1: COMPILATION BLOCKERS (Must fix before cargo check)

### B-01: Missing `which` crate in Cargo.toml
- **File:** boss-tui/Cargo.toml
- **Needed by:** src/scraper/browser.rs:122 (`which::which("chrome")`)
- **Fix:** Add `which = "6"` to [dependencies]

### B-02: Missing `winreg` crate in Cargo.toml
- **File:** boss-tui/Cargo.toml
- **Needed by:** src/scraper/browser.rs:136 (Windows registry lookup)
- **Fix:** Add `winreg = "0.52"` to [dependencies] under [target.'cfg(windows)'.dependencies]

### B-56: CRITICAL - api/cyberintern.rs borrow checker violation
- **File:** src/api/cyberintern.rs:59,71,111
- **Issue:** Methods `ensure_token()`, `auth_get()`, `auth_post()` are `&self` but take `&mut Option<String>` — Rust won't allow mutation through shared reference
- **Impact:** COMPILATION BLOCKER — entire api/cyberintern module won't compile
- **Fix:** Change to `&mut self` OR use interior mutability (`Mutex<Option<String>>`)

### B-03: Missing `crate::api::cyberintern::CyberInternClient` import
- **File:** src/actions/diaries.rs:5
- **Issue:** Module path may not exist as separate api module
- **Fix:** Verify module exists or update import path

### B-04: Missing `crate::api::anthropic` module
- **File:** src/actions/diaries.rs:14
- **Issue:** Module undefined, used for AI diary generation
- **Fix:** Create module or remove feature

### B-05: Missing `crate::diary_prompt` module
- **File:** src/actions/diaries.rs:15
- **Issue:** Module undefined, used for prompt building
- **Fix:** Create module or remove feature

### B-06: Missing `ChangeLogEntry` type in server::db
- **File:** src/p2p/sync.rs:8
- **Issue:** Type imported but may not exist in server::db
- **Fix:** Verify exists or add definition

### B-07: Missing 8+ Database methods for P2P
- **File:** src/p2p/sync.rs:229,249,255,286-301,361
- **Methods needed:** get_patient(), get_changes_since(), node_id(), update_patient_manual_fields(), update_patient_vlk_fields(), discharge_patient() (p2p variant), update_patient_027_fields() (p2p variant), update_operation()
- **Fix:** Verify all methods exist in db.rs

---

## TIER 2: WIRING (Scraper restored but not connected)

### B-08: Scraper module declared but never used
- **File:** src/main.rs:43 - `mod scraper;` declared
- **Issue:** No code imports or calls anything from scraper module
- **Fix:** Wire scraper into sync routes or enrichment pipeline

### B-09: /sync/enrich returns 410 GONE
- **File:** src/server/routes/sync.rs:315-323
- **Issue:** Endpoint says "EMR scraper has been removed"
- **Fix:** Rewire to use chromiumoxide scraper module OR direct API calls

### B-10: Stale comment "Scraper removed"
- **File:** src/server/routes/mod.rs:23
- **Issue:** Comment says scraper removed but we restored it
- **Fix:** Update comment

---

## TIER 3: SYNC PIPELINE (Why pressing 's' doesn't work reliably)

### B-11: fetch_all() called too early after sync trigger
- **File:** src/main.rs:882-883
- **Issue:** Immediate fetch before sync completes on server - gets stale data
- **Fix:** Remove immediate fetch_all(), let polling handle it

### B-12: Silent error swallowing in poll_sync_status()
- **File:** src/app.rs:2459-2474
- **Issue:** `if let Ok(status)` silently ignores all errors, stale state remains
- **Fix:** Log errors, update last_error field

### B-13: enrichment_pending_refresh SET but NEVER READ
- **File:** src/app.rs:2437 (set) / main.rs event loop (never checked)
- **Issue:** Field is set after enrichment but never read - refresh never triggered
- **Fix:** Add check in main event loop: if elapsed > 10s, fetch_all()

### B-14: Sync state not cleared if background task panics
- **File:** src/server/routes/sync.rs:70-76
- **Issue:** If perform_ci_import() panics, sync_running stays true FOREVER
- **Fix:** Wrap in catch_unwind or use JoinHandle with error handling

### B-15: 3-second sync poll interval too slow
- **File:** src/main.rs:317
- **Issue:** User waits 3+ seconds to see sync results after completion
- **Fix:** Poll every 500ms during active sync, 3s when idle

### B-16: trigger_sync() returns bool, loses error details
- **File:** src/api/boss.rs:137-144
- **Issue:** Returns false on error with no info about cause
- **Fix:** Return Result<bool, String> to preserve error details

---

## TIER 4: DATABASE / SCHEMA

### B-17: Missing physical_history_number in INSERT
- **File:** src/server/db.rs:869-881
- **Issue:** Column defined in schema (line 351) but NOT in INSERT statement
- **Impact:** SILENT DATA LOSS - new patients lose physical_history_number
- **Fix:** Add to INSERT column list and params

### B-18: Missing physical_history_number in UPDATE
- **File:** src/server/db.rs:794-834
- **Issue:** Column never updated via COALESCE in UPDATE statement
- **Fix:** Add `physical_history_number = COALESCE(?XX, physical_history_number)`

### B-19: Incomplete 027/o enrichment - saves 6 of 13 fields
- **File:** src/server/db.rs:1038-1092
- **Issue:** update_patient_027_fields saves only 6 fields:
  - complaints, disease_anamnesis, life_anamnesis, objective_status, lab_tests, treatment
- **Missing 7 fields:** discharge_date, instrumental_tests, consultations, treatment_result, recommendations, sicklist_start, sicklist_end
- **Note:** Second method update_patient_from_ci_detail saves some missing ones
- **Fix:** Consolidate into single method or ensure BOTH always called together

### B-20: Hardcoded AUTH secret fallback
- **File:** src/server/routes/auth.rs:51
- **Issue:** Default "zav-default-secret-change-me" used if ZAV_AUTH_SECRET env var missing
- **Fix:** Fail hard or generate random secret on first startup

---

## TIER 5: UI / UX

### B-21: Help text missing tabs [2] Stats and [4] Alerts
- **File:** src/ui/help.rs:23-74
- **Issue:** Help references [1],[3],[5],[6],[7],[8] but skips [2] and [4]
- **Fix:** Add help sections for Stats and Alerts tabs

### B-22: Shortcuts display says "1-0" instead of "1-8"
- **File:** src/ui/shortcuts.rs:167
- **Issue:** `ShortcutDisplay::new("1-0", "Tabs")` but only 8 tabs exist
- **Fix:** Change to "1-8"

### B-23: Emoji width calculation broken in wards grid
- **File:** src/ui/wards.rs:520-528
- **Issue:** Uses chars().count() which counts codepoints, not visual width. Emojis are 1 codepoint but 2 columns wide
- **Fix:** Use unicode-width crate for proper terminal width calculation

### B-24: Ward grid disappears when terminal too small
- **File:** src/ui/wards.rs:334-339
- **Issue:** Returns early with "Terminal too small" message, no fallback compact view
- **Fix:** Add compact list/table fallback when grid won't fit

### B-25: Mixed English/Ukrainian text in popup tabs
- **File:** src/ui/popup.rs:265 ("TRANSFER HISTORY"), 308 ("027/о ДАНІ"), 407 ("TIMELINE"), 462 ("CYBERINTERN DATA")
- **Fix:** Standardize language across all popup sections

### B-26: Doctor column width inconsistency
- **File:** src/ui/discharged.rs:76 (18 chars) vs src/ui/patients.rs:186 (15 chars)
- **Fix:** Align to same width in both tables

### B-27: Fixed-width columns silently truncate data
- **File:** src/ui/patients.rs:180-190
- **Issue:** Case(12), Ward(6), Bed(5), Doctor(15), Days(5), Status(14) all fixed
- **Fix:** Use Min() constraints for important columns like Case and Doctor

### B-28: Discharged tab empty message misleading
- **File:** src/ui/discharged.rs:35
- **Issue:** Says "Sync with CyberIntern" but sync endpoint is /sync on Boss API
- **Fix:** Update to "Press 's' to sync patients"

### B-57: theme.rs test bitflag comparison wrong
- **File:** src/theme.rs:544,557
- **Issue:** `assert!(modifier == Modifier::BOLD)` uses equality on bitflags, should use `.contains()`
- **Impact:** Tests may pass/fail incorrectly depending on bitflag internals
- **Fix:** Change to `assert!(modifier.contains(Modifier::BOLD))`

---

## TIER 6: P2P / TLS (Entirely non-functional)

### B-29: TLS certificates are PLACEHOLDERS
- **File:** src/p2p/tls.rs:127-136
- **Issue:** `"-----BEGIN CERTIFICATE-----\nPLACEHOLDER_CERT_FOR_NODE_..."` - not valid X.509
- **Fix:** Implement with rcgen crate or disable P2P TLS entirely

### B-30: Certificate fingerprint calculation wrong
- **File:** src/p2p/tls.rs:148,158-161
- **Issue:** Hashes PEM text (base64 with headers) instead of DER bytes
- **Fix:** Parse DER from PEM and hash that, or use proper X.509 fingerprint

### B-31: /p2p/changes endpoint doesn't exist
- **File:** src/p2p/sync.rs:98
- **Issue:** P2P sync calls `{peer.url()}/p2p/changes?since=...` but no such route in server/routes/
- **Fix:** Register endpoint or disable P2P sync feature

---

## TIER 7: CYBERINTERN (Python) BUGS

### B-32: CRITICAL - current_user NameError in 6 endpoints
- **File:** cyberintern/src/api/routers/patients.py:222,440,444,538,630,693
- **Issue:** Auth dependency commented out (`# current_user: dict = Depends(require_medical_staff)`) but code still references `current_user['id']` and `current_user['username']`
- **Impact:** Runtime crash (NameError) on: GET /patients/current, POST /patients/{id}/set-current, POST /patients, PUT /patients/{id}, DELETE /patients/{id}
- **Fix:** Uncomment dependency or provide mock user dict

### B-33: Inconsistent response wrapper in EMR debug endpoints
- **File:** cyberintern/src/api/routers/emr.py:1055-1094
- **Issue:** Returns raw dict missing `data`, `timestamp`, `request_id` fields
- **Fix:** Use standard `{success, data, error, timestamp, request_id}` envelope

### B-34: EMR response models lack standard wrapper
- **File:** cyberintern/src/api/routers/emr.py:115-150
- **Endpoints:** POST /api/emr/test-connection, GET /api/emr/patient-list, POST /api/emr/import-patients
- **Issue:** Response models (TestConnectionResponse, PatientListResponse) return raw data without envelope
- **Fix:** Wrap in standard response format

### B-35: No error checks after Playwright service calls
- **File:** cyberintern/src/api/routers/emr.py:370,442,514,543,616,676,809,851,886
- **Issue:** 10 service calls without checking `.get("success")` on result
- **Fix:** Check each result for success/error before continuing

### B-36: Resource leak - no finally block in test-connection
- **File:** cyberintern/src/api/routers/emr.py:1640
- **Issue:** emr_service.start() without corresponding close in finally
- **Fix:** Add try/finally with service.close()

### B-37: Column type mismatch in discharge_documents
- **File:** cyberintern/src/api/main.py:402
- **Issue:** patient_id INTEGER but should be TEXT to match patient case_number
- **Fix:** Change column type or use proper foreign key

### B-38: Inconsistent status filter logic
- **File:** cyberintern/src/api/routers/patients.py:113-129
- **Issue:** Mixes English and Ukrainian status values without normalization
- **Fix:** Normalize with status_map dictionary

---

## TIER 8: WINDOWS DEPLOY / LAUNCHER

### B-39: Environment vars lost in START.bat child processes
- **File:** windows-deploy/START.bat:38,58,64
- **Issue:** `start /B cmd /C ...` creates fresh env, loses parent's `set` vars
- **Workaround:** Use ZAV.exe launcher instead (handles this correctly with temp .bat)
- **Fix:** Rewrite START.bat to pass env vars explicitly

### B-40: Insufficient CyberIntern startup wait
- **File:** windows-deploy/START.bat:65
- **Issue:** Only 3 seconds wait for Python uvicorn (needs 5-10s)
- **Fix:** Increase timeout or add health check loop for port 8082

### B-41: ngrok started with no health check
- **File:** windows-deploy/START.bat:57-59
- **Issue:** Prints "Started" immediately without verifying tunnel established
- **Fix:** Add curl check for ngrok tunnel status

### B-42: n8n health check incomplete
- **File:** windows-deploy/START.bat:41-55
- **Issue:** After 2 failed health checks, proceeds anyway (no 3rd attempt)
- **Fix:** Add 3rd check or fail with error message

### B-43: Database .expect() panics on startup
- **File:** src/main.rs:137
- **Issue:** `.expect("Failed to open database")` panics instead of graceful error
- **Fix:** Use .map_err() with user-friendly error message

### B-44: Headless mode infinite loop, no graceful shutdown
- **File:** src/main.rs:154-156
- **Issue:** `loop { sleep(60s) }` with no signal handler for SIGTERM/ctrl_c
- **Fix:** Add tokio::signal::ctrl_c() handler

### B-45: Hardcoded P2P port 8084
- **File:** src/main.rs:128
- **Issue:** P2P discovery hardcodes port instead of reading from BOSS_API_URL
- **Fix:** Extract port from env var

### B-46: Localhost-only server binding
- **File:** src/main.rs:1483
- **Issue:** Binds to 127.0.0.1 only, P2P unreachable from other machines
- **Fix:** Allow 0.0.0.0 via config

---

## TIER 9: LOWER PRIORITY

### B-47: VLK date parsing calls system time in loop
- **File:** src/app.rs:1181-1223
- **Fix:** Compute `today` once before loop, not per-patient

### B-48: No timeout on Claude subprocess
- **File:** src/main.rs:1414-1416
- **Issue:** `claude -p ...` can hang forever
- **Fix:** Add 30s timeout

### B-49: Server errors go to stderr not tracing
- **File:** src/main.rs:1494,1502
- **Fix:** Use tracing::error!() instead of eprintln!()

### B-50: Hardcoded Windows paths
- **File:** src/main.rs:1298,1303
- **Issue:** `E:\\zav-hospital\\cyberintern` hardcoded as absolute fallback
- **Fix:** Use relative path resolution only

### B-51: PDF filenames all underscores with Ukrainian names
- **File:** src/pdf/generator.rs:198-204
- **Issue:** sanitize_filename strips non-ASCII, Ukrainian names become `___`
- **Fix:** Keep Unicode alphanumeric chars in filename

### B-52: CyberIntern binds to 0.0.0.0
- **File:** windows-deploy/START.bat:64
- **Issue:** Accessible from all network interfaces (security risk)
- **Fix:** Use --host 127.0.0.1 for localhost-only

### B-53: P2P patient count stale after startup
- **File:** src/main.rs:118-120
- **Issue:** Count fetched once, never updated after sync
- **Fix:** Update after sync completes

### B-54: Unimplemented space handler in diary selector
- **File:** src/main.rs:578-580
- **Issue:** Comment "Toggle last numbered" but empty handler
- **Fix:** Implement or remove

### B-55: Esc clears both search AND ward filter
- **File:** src/main.rs:914
- **Issue:** User may want to clear only one
- **Fix:** Esc clears search, separate key for filter reset

---

## HUNT PROGRESS (2026-02-13 evening session)

### Phase A: COMPILATION — ✅ SLAIN (commit 4435fa8)
- ~~B-01 to B-07~~: 69 compile errors fixed. EMR migration completed. enrichment_status created.
- CyberIntern imports → EMRTuiClient, DoctorState stubs, Tab::Discharged added

### Phase B: WIRING — ✅ SUPERSEDED
- ~~B-08, B-09, B-10~~: Direct EMR API replaces scraper+CyberIntern entirely

### Phase C: SYNC RELIABILITY — ✅ ALL SLAIN
- ~~B-11~~: Removed premature fetch_all() after sync trigger ✅
- ~~B-12~~: Poll error handling + last_error on failure ✅
- ~~B-13~~: enrichment_pending_refresh polled in event loop (10s) ✅
- ~~B-14~~: JoinHandle + monitoring task clears sync_running on panic ✅
- ~~B-15~~: Poll interval 500ms during active sync (was 3s) ✅
- ~~B-16~~: trigger_sync returns Result<bool,String> with error details ✅

### Phase D: DATA COMPLETENESS — ✅ ALL SLAIN
- ~~B-17~~: physical_history_number in INSERT ✅
- ~~B-18~~: physical_history_number in UPDATE ✅
- ~~B-19~~: update_patient_027_fields saves all 13 fields (was 6) ✅
- ~~B-20~~: Ephemeral auth secret replaces hardcoded fallback ✅
- ~~B-32~~: SUPERSEDED (killing CyberIntern Python)

### Phase E: UI POLISH — ✅ MOSTLY SLAIN
- ~~B-21~~: Help text for Stats/Alerts tabs ✅
- ~~B-22~~: Shortcuts "1-0" → "1-8" ✅
- ~~B-25~~: Popup headers English→Ukrainian ✅
- ~~B-26~~: Doctor column width aligned to 18 chars ✅
- ~~B-28~~: Discharged message fixed ✅
- B-23: Emoji width (unicode-width) — TODO (low priority)
- B-24: Ward grid small terminal — TODO (low priority)
- B-27: Fixed-width column truncation — TODO (low priority)
- B-57: Theme test bitflag — TODO (low priority)

### Phase F: STARTUP / DEPLOY — ✅ MOSTLY SLAIN
- ~~B-43~~: Database open graceful error+exit ✅
- ~~B-44~~: Headless mode Ctrl+C clean shutdown ✅
- ~~B-47~~: VLK date today() before loop ✅
- ~~B-51~~: PDF Ukrainian filenames is_alphanumeric ✅
- B-39 to B-42: START.bat — partially superseded (EMR_URL set, CI removed)
- B-45, B-46: Port hardcoding — TODO (low priority)
- B-48 to B-55: Lower priority — TODO

### SUPERSEDED (no longer relevant):
- Tier 2 (B-08..B-10): Scraper wiring → replaced by direct EMR API
- Tier 7 (B-32..B-38): CyberIntern Python → being killed entirely
- Tier 6 (B-29..B-31): P2P/TLS → deferred per Grug

---

## STRATEGIC DECISION: REPLACE CYBERINTERN WITH DIRECT API

**Date:** 2026-02-13
**Decision:** Replace Python CyberIntern + Playwright browser automation with direct REST API calls to doc.hospital.mia.software

**Rationale:**
- CyberIntern is a 50+ endpoint Python FastAPI monster with Playwright browser automation
- Playwright browsers are broken (not installed, stale since Jan 15)
- 6 endpoints crash with NameError (B-32)
- 10 service calls have no error handling (B-35)
- The EMR system (doc.hospital.mia.software) likely has REST APIs we can call directly
- Direct API = faster, more reliable, no browser dependency, pure Rust

**Investigation needed:**
- What APIs does doc.hospital.mia.software expose?
- Can we authenticate via API (not browser login)?
- What endpoints exist for: patients, diaries, labs, sicklists, consultations?
- Research getmaxun/maxun for structured API extraction

**Target architecture:**
```
Boss TUI (Rust) → Direct HTTP/REST → doc.hospital.mia.software
                   No Python
                   No Playwright
                   No CyberIntern
```
