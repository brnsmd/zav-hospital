# CyberIntern TUI - Alert & Diary Systems Plan

**Created:** 2026-01-28
**Status:** PLANNING
**Target:** cyberintern-tui (DOC mode - doctor's view)
**Tribe:** Grug & Clug 🪓

---

## Current State (ALREADY EXISTS)

### Models ✅
- `models/alert.rs` - AlertType: SicklistOverdue, LabsOutdated, NeedsDiary, LkkDue, VlkDeadline
- `models/diary.rs` - DiaryType: Daily, Preop, Postop2h, Lkk, DischargeDiary

### DB ✅
- `db/alerts.rs` - get_pending_alerts(), get_patient_alerts(), get_alert_stats()
- `db/diaries.rs` - get_recent_diaries()

### UI ✅
- `ui/alerts.rs` - Alerts tab
- `ui/diaries.rs` - Diaries tab
- `ui/editor.rs` - Diary editor overlay

---

## What's MISSING (TO BUILD)

### 1. Alert Generation Service
**Source:** `cyberintern/src/services/alert_generator.py`
**Target:** `cyberintern-tui/src/services/alert_generator.rs`

Logic to port:
- `check_sicklist_alerts()` - days until expiry: 0, -1, -2, -3+
- `check_labs_alerts()` - days since labs: >5 warning, >14 critical
- `check_preop_alerts()` - op tomorrow, no recent labs
- `check_needs_diary_alerts()` - no diary for today
- `check_lkk_alerts()` - LKK at 30-day marks
- Flexible date parsing (DD.MM.YYYY and YYYY-MM-DD)

### 2. Diary Template Generator
**Source:** `cyberintern/src/ai/template_diary_generator.py` (1486 lines)
**Target:** `cyberintern-tui/src/services/diary_templates.rs`

Components:
- 80+ anatomical location patterns (regex)
- Wound status templates (25+ variants)
- Vitals formatting
- System examination templates
- Diary type builders (daily, preop, postop, lkk, discharge)

### 3. EMR Submission Service
**Source:** `cyberintern/src/services/diary_service.py`
**Target:** `cyberintern-tui/src/emr/diary_submit.rs`

Logic:
- CSRF token management (refresh every ~30 min)
- POST to EMR API `/api/v1/case/{case_id}/diary/`
- Browser automation via chromiumoxide (relay mode required)

### 4. Slack Integration
**Target:** `cyberintern-tui/src/services/slack.rs`

- Send alerts to Slack webhook
- Format with priority emoji (🔴/🟠/🟡)
- Patient name + alert message

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                   CYBERINTERN TUI (DOC Mode)                │
│  ┌─────────┬──────────┬─────────┬─────────┬─────────────┐  │
│  │Patients │ Diaries  │ ALERTS  │Documents│   Stats     │  │
│  │         │(+EDITOR) │(+GENRTR)│         │             │  │
│  └─────────┴──────────┴─────────┴─────────┴─────────────┘  │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│  SQLite DB    │    │  EMR Browser   │    │    Slack     │
│ cyberintern.db│    │ (chromiumoxide)│    │  Webhooks    │
│ - patients    │    │ - diary submit │    │  - alerts    │
│ - alerts      │    │ - CSRF token   │    │              │
│ - diaries     │    │                │    │              │
└───────────────┘    └────────────────┘    └──────────────┘
```

---

## Phase 1: Alert Generation Service

### 1.1 Create services module
**File:** `src/services/mod.rs`

```rust
pub mod alert_generator;
pub mod slack;
```

### 1.2 Alert Generator
**File:** `src/services/alert_generator.rs`

```rust
pub struct AlertGenerator {
    db: Database,
}

impl AlertGenerator {
    pub fn check_all(&self) -> Vec<Alert>;
    fn check_sicklist(&self, patient: &Patient) -> Option<Alert>;
    fn check_labs(&self, patient: &Patient) -> Option<Alert>;
    fn check_needs_diary(&self, patient: &Patient) -> Option<Alert>;
    fn check_lkk(&self, patient: &Patient) -> Option<Alert>;
}
```

### 1.3 Sicklist Logic
| Days Until Expiry | Severity | Message |
|-------------------|----------|---------|
| 0 | High | "Лікарняний закінчується СЬОГОДНІ" |
| -1 | Critical | "Лікарняний ПРОСТРОЧЕНИЙ на 1 день" |
| -2 | Critical | "Лікарняний ПРОСТРОЧЕНИЙ на 2 дні" |
| -3+ | Critical | "Лікарняний ПРОСТРОЧЕНИЙ на N днів" |

### 1.4 Labs Logic
| Days Since Labs | Severity | Message |
|-----------------|----------|---------|
| 5-13 | Medium | "Аналізи застарілі (N днів)" |
| 14+ | High | "Аналізи критично застарілі" |
| PreOp tomorrow + no labs | Critical | "Операція завтра, немає аналізів!" |

---

## Phase 2: DB Extensions

### 2.1 Alert CRUD
**File:** `src/db/alerts.rs` (extend)

Add:
```rust
fn create_alert(&self, alert: &Alert) -> DbResult<i64>;
fn resolve_alert(&self, id: i64) -> DbResult<()>;
fn snooze_alert(&self, id: i64, until: NaiveDateTime) -> DbResult<()>;
fn auto_resolve_stale(&self) -> DbResult<i64>;  // Returns count
```

### 2.2 Sicklist/Labs queries
**File:** `src/db/patients.rs` (extend)

Add:
```rust
fn get_sicklist_data(&self, patient_id: &str) -> DbResult<Option<SicklistData>>;
fn get_latest_labs(&self, patient_id: &str) -> DbResult<Option<LabData>>;
fn get_scheduled_operations(&self, patient_id: &str) -> DbResult<Vec<Operation>>;
```

---

## Phase 3: Slack Integration

### 3.1 Slack Service
**File:** `src/services/slack.rs`

```rust
pub struct SlackService {
    webhook_url: String,
    client: reqwest::Client,
}

impl SlackService {
    pub async fn send_alert(&self, alert: &Alert) -> Result<()>;
}
```

Format:
```
🔴 SICKLIST EXPIRED
Іванов І.І. - Лікарняний ПРОСТРОЧЕНИЙ на 2 дні
```

---

## Phase 4: Diary Template Generator

### 4.1 Template System
**File:** `src/services/diary_templates.rs`

```rust
pub struct TemplateGenerator {
    location_patterns: Vec<LocationPattern>,
    wound_templates: HashMap<WoundType, String>,
}

impl TemplateGenerator {
    pub fn generate(&self, patient: &Patient, diary_type: DiaryType) -> String;
    fn build_daily(&self, patient: &Patient) -> String;
    fn build_preop(&self, patient: &Patient) -> String;
    fn build_lkk(&self, patient: &Patient) -> String;
}
```

### 4.2 Location Patterns
Port 80+ patterns from Python:
```rust
struct LocationPattern {
    regex: Regex,
    body_part: BodyPart,
    templates: WoundTemplates,
}
```

---

## Phase 5: EMR Submission

### 5.1 EMR Client
**File:** `src/emr/mod.rs`

```rust
pub struct EmrClient {
    browser: Browser,
    csrf_token: Option<String>,
    token_time: Option<Instant>,
}

impl EmrClient {
    pub async fn login(&mut self) -> Result<()>;
    pub async fn submit_diary(&self, case_id: &str, content: &str) -> Result<()>;
    async fn refresh_csrf(&mut self) -> Result<()>;
}
```

**Note:** Requires relay mode (Tailscale) for EMR access!

---

## Phase 6: Wire Up UI

### 6.1 Auto-generate alerts on load
**File:** `src/app.rs`

```rust
pub fn load_data(&mut self) -> Result<(), String> {
    // ... existing code ...
    
    // Generate fresh alerts
    let generator = AlertGenerator::new(self.db.as_ref().unwrap());
    let new_alerts = generator.check_all();
    self.db.as_ref().unwrap().upsert_alerts(&new_alerts)?;
    
    // ... load alerts from DB ...
}
```

### 6.2 Diary generation in editor
**File:** `src/ui/editor.rs`

Add 'g' key to generate from template:
```rust
KeyCode::Char('g') => {
    let content = self.template_generator.generate(&self.patient, self.diary_type);
    self.editor.set_content(&content);
}
```

---

## Implementation Order

1. [ ] **Phase 1.1-1.2** - Services module + AlertGenerator skeleton
2. [ ] **Phase 1.3-1.4** - Sicklist + Labs alert logic
3. [ ] **Phase 2** - DB extensions (alert CRUD, sicklist/labs queries)
4. [ ] **Phase 3** - Slack integration
5. [ ] **Phase 6.1** - Wire up alert generation on load
6. [ ] **Phase 4** - Diary template generator (BIG)
7. [ ] **Phase 5** - EMR submission
8. [ ] **Phase 6.2** - Wire up diary generation

---

## Dependencies

```toml
# Already in Cargo.toml:
chrono = "0.4"
rusqlite = "0.31"
tokio = "1"
ratatui = "0.28"

# May need:
regex = "1"  # For anatomical patterns
chromiumoxide = "0.5"  # For EMR browser (if not already)
```

---

## Test Data

CyberIntern database at:
`~/.local/share/cyberintern/cyberintern.db`

Has:
- 18 test patients
- Sicklists
- Labs
- Diaries

---

## Notes

- Relay mode (Tailscale) required for EMR submission
- CSRF token refreshes every ~30 min
- Alerts auto-resolve when condition no longer true
- Templates are pure string manipulation (NO LLM)
- DOC mode filters by `config.doctor_filter` (only your patients)

---

**PLAN READY FOR GRUG APPROVAL!** 🪓
