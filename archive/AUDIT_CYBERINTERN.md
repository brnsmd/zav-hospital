# CyberIntern Structure Audit

**Date:** 2026-02-10
**Files:** 609 Python files + React 18 frontend
**Port:** 8082 (FastAPI) / 8080 (Flask legacy)

---

## Architecture

```
cyberintern/
├── main.py                    <- Entry point (202 lines)
├── src/
│   ├── api/                   <- FastAPI server (port 8082)
│   │   ├── main.py            <- FastAPI app (340 lines)
│   │   ├── routers/           <- 13 routers, 50+ endpoints
│   │   │   ├── diaries.py     <- 174KB (LARGEST file)
│   │   │   ├── emr.py         <- 80KB
│   │   │   ├── documents.py   <- 54KB
│   │   │   ├── workflows.py   <- 37KB
│   │   │   ├── broodmother.py <- 33KB (AI agent)
│   │   │   ├── patients.py    <- 51KB
│   │   │   ├── alerts.py      <- 32KB
│   │   │   ├── websockets.py  <- 25KB
│   │   │   ├── devtools.py    <- 26KB
│   │   │   ├── settings.py    <- 23KB
│   │   │   ├── auth.py        <- 12KB
│   │   │   ├── setup.py
│   │   │   └── health.py
│   │   ├── middleware/        <- Request ID, logging, audit, errors
│   │   ├── services/         <- Business logic
│   │   ├── models/           <- Pydantic schemas
│   │   ├── auth/             <- Authentication modules
│   │   ├── config.py         <- Settings
│   │   ├── database.py       <- DB init
│   │   ├── dependencies.py   <- DI
│   │   └── validators.py     <- Input validation
│   ├── mcp/                   <- MCP AI server (10 tools)
│   │   ├── mcp_server.py      <- 40KB, direct SQLite access
│   │   ├── mcp_router.py      <- 76KB, HTTP endpoints
│   │   ├── cyberintern_client.py <- 15KB
│   │   ├── credential_manager.py
│   │   ├── emr_actions.py
│   │   ├── emr_error_handlers.py
│   │   ├── emr_selectors.py
│   │   ├── emr_session.py
│   │   └── session_manager.py
│   ├── data/                  <- Repository pattern (8 repos)
│   │   ├── patient_repository.py
│   │   ├── diary_repository.py
│   │   ├── lab_results_repository.py
│   │   ├── prescription_repository.py
│   │   ├── sicklist_repository.py
│   │   ├── procedure_repository.py
│   │   ├── alert_repository.py
│   │   └── operation_repository.py
│   ├── database/migrations/   <- Alembic seed scripts
│   ├── services/              <- Business logic layer
│   ├── ai/                    <- AI templates & prompts
│   ├── utils/                 <- Helpers
│   ├── web_ui_react/          <- React 18 + Vite + Blueprint.js
│   │   ├── src/
│   │   │   ├── main.jsx
│   │   │   ├── ProductionApp.jsx
│   │   │   ├── components/    <- alerts/, patients/, diary/, forms/, common/
│   │   │   ├── features/      <- alerts/, patients/, diary/, dashboard/, emr-sync/
│   │   │   ├── hooks/
│   │   │   ├── shared/
│   │   │   └── theme/
│   │   ├── dist/              <- Production build
│   │   ├── vite.config.ts
│   │   └── package.json
│   ├── http_server.py         <- Flask server (LEGACY, port 8080)
│   ├── start_web_ui.py        <- Web UI launcher (imports legacy code)
│   ├── db_models.py           <- 12 SQLAlchemy tables (244 lines)
│   ├── config_paths.py        <- Platform-specific paths (269 lines)
│   ├── connection_pool.py     <- DB connection pooling
│   ├── data_handler.py        <- Legacy data handling (34KB)
│   └── data_manager.py        <- Data layer abstraction (35KB)
├── config/
│   ├── settings.yaml.template
│   ├── production.env
│   ├── skills/                <- Claude Code skills
│   ├── workflows/
│   └── mode_state.yaml
├── data/
│   ├── templates/             <- Document templates
│   ├── training/              <- ML training data
│   └── update_manifest.json
├── alembic/                   <- DB migrations (3 versions)
│   ├── versions/
│   │   ├── 001_initial_schema.py
│   │   ├── 002_add_auth_tables.py
│   │   └── 003_add_sync_logs.py
│   └── alembic.ini
├── broodmother/               <- AI Agent System
├── archive/                   <- ~500+ DEAD files (PySide6 legacy)
├── windows/                   <- Installer scripts
├── tests/                     <- Test suite
├── requirements.txt           <- 40+ deps (now version-pinned)
└── CLAUDE.md
```

---

## Entry Points

| Entry | File | Port | Framework | Status |
|-------|------|------|-----------|--------|
| Main | `main.py` -> `src/start_web_ui.py` | 8080 | Flask | LEGACY |
| FastAPI | `src/api/main.py` | 8082 | FastAPI | CURRENT |
| MCP | `src/mcp/mcp_server.py` | 8082/mcp/ | MCP | CURRENT |

---

## API Endpoints (50+)

### FastAPI Routers (src/api/routers/)

**patients.py** - Patient CRUD
- `GET /api/patients` - List with pagination/search/sort
- `GET /api/patients/<id>` - Full patient record
- `POST /api/patients` - Create patient
- `PUT /api/patients/<id>` - Update patient
- `DELETE /api/patients/<id>` - Soft delete
- `GET /api/patients/<id>/vitals|labs|prescriptions|diaries`

**diaries.py** (174KB) - Diary management
- `GET /api/diaries` - List
- `POST /api/diaries` - Create
- `PUT /api/diaries/<id>` - Update
- `DELETE /api/diaries/<id>` - Delete
- `POST /api/diaries/batch-generate` - Batch creation
- `POST /api/diaries/post-to-emr` - Publish to EMR

**emr.py** (80KB) - EMR integration
- `POST /api/emr/sync` - Sync EMR data
- `GET /api/emr/patients` - EMR patient list
- `POST /api/emr/import` - Import patients
- `POST /api/emr/documents/fetch` - Fetch Form 027

**documents.py** (54KB) - Document generation
- `POST /api/documents/generate` - Generate DOCX
- `POST /api/documents/fetch-emr` - Fetch EMR data

**alerts.py** (32KB) - Alerts
- `GET /api/alerts` - List (filterable)
- `POST /api/alerts/<id>/handle` - Mark handled

**workflows.py** (37KB) - Automation
- CRUD for workflow definitions

**auth.py** - Authentication
- `POST /api/auth/login|logout|refresh`
- `GET /api/auth/me`

**settings.py** - Configuration
- `GET/PUT /api/settings`
- `GET/POST /api/settings/doctor`

**broodmother.py** (33KB) - AI Agent
- `POST /api/broodmother/query`
- `GET /api/broodmother/status`

**websockets.py** (25KB) - Real-time
- `WebSocket /ws`

### MCP Endpoints (src/mcp/mcp_router.py)

- `GET /mcp/context/doctor` - Doctor profile + EMR creds
- `GET /mcp/patient/<id>/full` - Complete patient data (ONE request)
- `GET /mcp/patient/<id>/diaries` - All diaries with text
- `GET /mcp/search?q=X&type=Y` - Full-text search
- `GET /mcp/alerts?severity=X` - Filtered alerts
- `GET /mcp/workflow/patient-list` - Patients with diary status
- `POST /mcp/generate/diary` - Diary generation
- `POST /mcp/generate/document` - Vypyska/dovidka generation
- `POST /mcp/call?tool_name=X` - Direct MCP tool call

### MCP Tools (10)

1. get_alerts
2. get_patient_record
3. analyze_patient_data
4. get_patient_prescriptions
5. get_lab_results
6. get_doctor_info
7. get_doctor_diaries
8. search_cyberintern
9. create_diary_entry
10. create_prescription

---

## Database Schema (12 tables)

| Table | Key Fields |
|-------|------------|
| patients | pib, diagnosis, admission_date, bed, ward, emr_case_number |
| diaries | patient_id, diary_date, content, submitted_to_emr |
| prescriptions | patient_id, prescription_text, status |
| sicklists | patient_id, start_date, end_date, certificate_number |
| lab_results | patient_id, test_type, result_value, reference_range |
| alerts | patient_id, alert_type, priority, status |
| operation_schedule | patient_id, operation_name, scheduled_date |
| consultations | patient_id, specialty, doctor_name, status |
| users | username, email, hashed_password, role |
| sessions | user_id, refresh_token, expires_at |
| audit_logs | user_id, action, details |
| emr_diaries | patient_id, diary_date, content, source |

---

## Issues Found

### CRITICAL

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 1 | Legacy PySide6 imports in startup path | `src/start_web_ui.py:19-20` | Import errors if PySide6 not installed |
| 2 | Two competing HTTP servers (Flask + FastAPI) | `http_server.py` vs `api/main.py` | Confusion, maintenance burden |

### HIGH

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 3 | Hardcoded creds in MCP config (`admin123456`) | `src/mcp/config.py` | Security risk |
| 4 | No transaction management in data layer | `data_handler.py`, `data_manager.py` | Data inconsistency |
| 5 | Ward migration runs every startup | `api/main.py:66-90` | Wasted time, should be Alembic migration |
| 6 | ~500+ dead files in archive/ | `archive/` | +50MB bloat in PyInstaller builds |
| 7 | MCP uses direct SQLite, no connection pool | `mcp/mcp_server.py` | Connection exhaustion under load |

### MEDIUM

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 8 | Single-instance lock race condition (30s window) | `main.py:139-178` | Duplicate instances possible |
| 9 | `diaries.py` is 174KB god file | `api/routers/diaries.py` | Unmaintainable |
| 10 | Alembic migrations not used at startup | `api/main.py` does inline DDL | Schema drift |
| 11 | No API versioning | All routers use `/api/*` | Breaking changes affect all clients |
| 12 | Playwright browser not closed on error | `mcp/emr_session.py` | Memory leak |

### LOW

| # | Issue | Location | Impact |
|---|-------|----------|--------|
| 13 | No rate limiting on API | All routers | Abuse potential |
| 14 | Deprecated `template_type` column in schema | `db_models.py:114` | Confusion |
| 15 | Inconsistent error responses across routers | All routers | Poor DX |
| 16 | No input sanitization for LIKE queries | `patients.py:132` | Low SQL risk |

---

## Quick Wins (Effort vs Impact)

1. **Delete `archive/`** - removes 500+ dead files, shrinks build by ~50MB
2. **Remove Flask** (`http_server.py`, `start_web_ui.py` legacy imports) - one server
3. **Fix MCP hardcoded creds** - read from env vars
4. **Move ward migration to Alembic** - stop running on every startup
5. **Pin dependencies** - DONE (requirements.txt updated)

---

## Frontend (React 18 + Vite)

- **Framework:** React 18 + Blueprint.js + Zustand
- **Build:** Vite (dev:5173, prod: served by FastAPI)
- **Structure:** Feature-based (alerts/, patients/, diary/, dashboard/)
- **Tests:** Playwright E2E (test-results/ present but no CI)
- **Output:** `dist/` served as static files
