# RUST SYNC MASTERPLAN - THE GREAT PURIFICATION

**Created:** 2026-01-29
**Status:** PLANNING
**Goal:** Replace ALL Python sync/enrichment with pure Rust

---

## THE VISION

```
BEFORE (MESSY):                          AFTER (CLEAN):
================                         ==============

┌──────────────┐                        ┌──────────────┐
│  Rust TUI    │                        │  Rust TUI    │
│  (boss-tui)  │                        │  (boss-tui)  │
└──────┬───────┘                        │              │
       │ subprocess                     │  EVERYTHING  │
       ▼                                │  BUILT IN!   │
┌──────────────┐                        │              │
│  Python API  │                        │  - Airtable  │
│  (8083)      │                        │  - CyberInt  │
│              │                        │  - Validate  │
│  airtable.py │                        │  - VLK sync  │
│  enrichment  │                        │              │
│  validator   │                        └──────────────┘
└──────────────┘
                                        ONE BINARY!
TWO LANGUAGES!                          cargo install boss-tui
pip + cargo!                            DONE!
```

---

## WHAT WE'RE REPLACING

| Python File | Lines | Rust Module | Purpose |
|-------------|-------|-------------|---------|
| `airtable_sync.py` | 525 | `src/sync/airtable.rs` | Airtable CRUD |
| `cyberintern_enrichment.py` | 438 | `src/sync/cyberintern.rs` | 027/о enrichment |
| `data_validator.py` | ~200 | `src/sync/validator.rs` | Data validation |

**Total Python to replace:** ~1163 lines
**Estimated Rust:** ~800-1000 lines (Rust is more concise for this)

---

## PHASE 1: AIRTABLE CLIENT (Day 1)

### 1.1 Create Airtable HTTP Client

**File:** `boss-tui/src/sync/airtable.rs`

```rust
pub struct AirtableClient {
    client: reqwest::Client,
    api_key: String,
    base_id: String,
    table_name: String,
}

impl AirtableClient {
    // Core CRUD operations
    pub async fn list_records(&self) -> Result<Vec<AirtableRecord>>;
    pub async fn get_record(&self, record_id: &str) -> Result<AirtableRecord>;
    pub async fn create_record(&self, fields: HashMap<String, Value>) -> Result<AirtableRecord>;
    pub async fn update_record(&self, record_id: &str, fields: HashMap<String, Value>) -> Result<AirtableRecord>;
    pub async fn find_by_formula(&self, formula: &str) -> Result<Vec<AirtableRecord>>;
}
```

**Airtable API is simple REST:**
- Base URL: `https://api.airtable.com/v0/{base_id}/{table_name}`
- Auth: `Authorization: Bearer {api_key}`
- List: `GET /`
- Create: `POST /` with `{"fields": {...}}`
- Update: `PATCH /{record_id}` with `{"fields": {...}}`
- Search: `GET /?filterByFormula={formula}`

### 1.2 Field Mapping

```rust
/// Map Boss DB fields to Airtable field names
fn map_patient_to_airtable(patient: &Patient) -> HashMap<String, Value> {
    let mut fields = HashMap::new();

    // Basic fields
    if let Some(ref pib) = patient.pib { fields.insert("ПІБ".into(), json!(pib)); }
    if let Some(ref doctor) = patient.doctor { fields.insert("Хірург".into(), json!(doctor)); }
    // ... 40+ field mappings

    fields
}
```

### 1.3 Smart Sync Logic

```rust
/// Sync patient to Airtable (only fill empty fields)
pub async fn sync_patient(&self, patient: &Patient) -> Result<SyncResult> {
    let case_number = patient.case_number.as_ref().ok_or("No case number")?;

    // Find existing record
    let formula = format!("{{№ запису}} = '{}'", case_number);
    let existing = self.find_by_formula(&formula).await?;

    if let Some(record) = existing.first() {
        // Smart update: only fill empty fields
        let update_fields = self.get_empty_fields_to_fill(record, patient);
        if !update_fields.is_empty() {
            self.update_record(&record.id, update_fields).await?;
            Ok(SyncResult::Updated)
        } else {
            Ok(SyncResult::Unchanged)
        }
    } else {
        // Create new
        let fields = map_patient_to_airtable(patient);
        self.create_record(fields).await?;
        Ok(SyncResult::Created)
    }
}
```

---

## PHASE 2: DATA VALIDATOR (Day 1)

### 2.1 Validation Rules

**File:** `boss-tui/src/sync/validator.rs`

```rust
pub struct ValidationResult {
    pub is_valid: bool,
    pub errors: Vec<String>,
    pub warnings: Vec<String>,
    pub cleaned_fields: Vec<String>,
    pub patient_data: Patient,  // Cleaned version
}

pub fn validate_patient(patient: &Patient) -> ValidationResult {
    let mut result = ValidationResult::new(patient.clone());

    // Required fields (block if missing)
    if patient.case_number.is_none() {
        result.add_error("Missing case_number");
    }
    if patient.pib.is_empty() {
        result.add_error("Missing pib (name)");
    }
    if patient.admission_date.is_none() {
        result.add_error("Missing admission_date");
    }
    if patient.birth_date.is_none() {
        result.add_error("Missing birth_date");
    }

    // Warnings (sync but flag)
    if patient.doctor.is_none() {
        result.add_warning("Missing doctor");
    }

    // Data cleaning
    if let Some(ref inst) = patient.institution {
        if inst.chars().all(|c| c.is_uppercase() || !c.is_alphabetic()) {
            result.patient_data.institution = Some(to_title_case_ukrainian(inst));
            result.cleaned_fields.push("institution".into());
        }
    }

    result.is_valid = result.errors.is_empty();
    result
}
```

### 2.2 Title Case Conversion (Ukrainian-aware)

```rust
/// Convert "ВІЙСЬКОВА ЧАСТИНА А1234" to "Військова Частина А1234"
/// Preserves: ДУ, ТМО, МВС, НГУ, СБУ
fn to_title_case_ukrainian(s: &str) -> String {
    let preserved = ["ДУ", "ТМО", "МВС", "НГУ", "СБУ", "ЗСУ"];

    s.split_whitespace()
        .map(|word| {
            if preserved.contains(&word) {
                word.to_string()
            } else {
                let mut chars = word.chars();
                match chars.next() {
                    Some(first) => first.to_uppercase().chain(chars.flat_map(|c| c.to_lowercase())).collect(),
                    None => String::new(),
                }
            }
        })
        .collect::<Vec<_>>()
        .join(" ")
}
```

---

## PHASE 3: CYBERINTERN CLIENT (Day 2)

### 3.1 HTTP Client with JWT Auth

**File:** `boss-tui/src/sync/cyberintern.rs`

```rust
pub struct CyberInternClient {
    client: reqwest::Client,
    base_url: String,
    access_token: Option<String>,
}

impl CyberInternClient {
    pub async fn authenticate(&mut self, username: &str, password: &str) -> Result<()> {
        let resp = self.client
            .post(format!("{}/api/auth/login", self.base_url))
            .json(&json!({"username": username, "password": password}))
            .send().await?;

        let data: AuthResponse = resp.json().await?;
        self.access_token = Some(data.access_token);
        Ok(())
    }

    async fn get<T: DeserializeOwned>(&self, endpoint: &str) -> Result<T> {
        let token = self.access_token.as_ref().ok_or("Not authenticated")?;
        let resp = self.client
            .get(format!("{}{}", self.base_url, endpoint))
            .bearer_auth(token)
            .send().await?;
        Ok(resp.json().await?)
    }
}
```

### 3.2 Patient Matching

```rust
/// Find patient in CyberIntern by case_number, history_number, or name
pub async fn find_patient(&self,
    case_number: Option<&str>,
    history_number: Option<&str>,
    pib: Option<&str>
) -> Result<Option<CIPatient>> {
    // Try case_number first (most reliable)
    if let Some(cn) = case_number {
        let patients: PatientList = self.get(&format!("/api/patients?search={}", cn)).await?;
        if let Some(p) = patients.items.iter().find(|p| p.emr_case_number.as_deref() == Some(cn)) {
            return Ok(Some(p.clone()));
        }
    }

    // Try history_number
    if let Some(hn) = history_number {
        let patients: PatientList = self.get(&format!("/api/patients?search={}", hn)).await?;
        if let Some(p) = patients.items.iter().find(|p| p.history_number.as_deref() == Some(hn)) {
            return Ok(Some(p.clone()));
        }
    }

    // Try name search (least reliable)
    if let Some(name) = pib {
        let patients: PatientList = self.get(&format!("/api/search/patients?q={}", name)).await?;
        return Ok(patients.items.into_iter().next());
    }

    Ok(None)
}
```

### 3.3 Data Fetching & Parsing

```rust
pub async fn enrich_patient(&self, patient: &Patient) -> Result<EnrichmentData> {
    let ci_patient = self.find_patient(
        patient.case_number.as_deref(),
        patient.history_number.as_deref(),
        Some(&patient.pib)
    ).await?.ok_or("Patient not found in CyberIntern")?;

    let patient_id = ci_patient.id;

    // Fetch all data in parallel
    let (diaries, labs, prescriptions) = tokio::join!(
        self.get_diaries(patient_id),
        self.get_labs(patient_id),
        self.get_prescriptions(patient_id)
    );

    // Parse and format
    Ok(EnrichmentData {
        complaints: parse_complaints(&diaries?),
        disease_anamnesis: parse_disease_anamnesis(&diaries?),
        life_anamnesis: parse_life_anamnesis(&diaries?),
        objective_status: parse_objective_status(&diaries?),
        lab_tests: format_labs(&labs?),
        treatment: format_prescriptions(&prescriptions?),
    })
}
```

### 3.4 Text Parsing (Regex)

```rust
/// Extract complaints from latest diary
fn parse_complaints(diaries: &[Diary]) -> Option<String> {
    diaries.iter()
        .filter(|d| d.complaints.is_some())
        .max_by_key(|d| &d.diary_date)
        .and_then(|d| d.complaints.clone())
        .filter(|c| !c.is_empty() && c.to_lowercase() != "не пред'являє")
}

/// Extract anamnesis from admission diary content
fn parse_disease_anamnesis(diaries: &[Diary]) -> Option<String> {
    let re = Regex::new(r"Анамнез захворювання[:\s]*(.+?)(?:Анамнез життя|Об'єктивно|$)").unwrap();

    diaries.iter()
        .min_by_key(|d| &d.diary_date)  // Earliest = admission
        .and_then(|d| d.content.as_ref())
        .and_then(|content| re.captures(content))
        .map(|cap| cap[1].trim().to_string())
}
```

---

## PHASE 4: WIRE UP ROUTES (Day 2-3)

### 4.1 Update routes.rs

**File:** `boss-tui/src/server/routes.rs`

```rust
use crate::sync::{AirtableClient, CyberInternClient, validate_patient};

/// Sync to Airtable - NOW ACTUALLY WORKS!
async fn sync_to_airtable(
    State(state): State<Arc<AppState>>,
) -> Result<impl IntoResponse, ...> {
    let api_key = env::var("AIRTABLE_API_KEY")?;
    let base_id = env::var("AIRTABLE_BASE_ID").unwrap_or("appv5BwoWyRhT6Lcr".into());

    let client = AirtableClient::new(&api_key, &base_id, "Пацієнти");
    let patients = state.db.get_hospitalized_patients()?;

    let mut counts = SyncCounts::default();

    for patient in patients {
        // Validate first
        let validation = validate_patient(&patient);
        if !validation.is_valid {
            counts.blocked += 1;
            continue;
        }

        // Sync to Airtable
        match client.sync_patient(&validation.patient_data).await {
            Ok(SyncResult::Created) => counts.created += 1,
            Ok(SyncResult::Updated) => counts.updated += 1,
            Ok(SyncResult::Unchanged) => counts.unchanged += 1,
            Err(_) => counts.failed += 1,
        }
    }

    Ok(Json(counts))
}

/// CyberIntern enrichment - NOW ACTUALLY WORKS!
async fn enrich_cyberintern(
    State(state): State<Arc<AppState>>,
    Query(params): Query<EnrichQuery>,
) -> Result<impl IntoResponse, ...> {
    let api_url = env::var("CYBERINTERN_API_URL")?;
    let username = env::var("CYBERINTERN_USERNAME").unwrap_or("admin".into());
    let password = env::var("CYBERINTERN_PASSWORD").unwrap_or("admin123456".into());

    let mut client = CyberInternClient::new(&api_url);
    client.authenticate(&username, &password).await?;

    let patients = state.db.get_hospitalized_patients()?;
    let max = params.max_patients.unwrap_or(50) as usize;

    let mut enriched = 0;
    for patient in patients.into_iter().take(max) {
        if let Ok(data) = client.enrich_patient(&patient).await {
            state.db.update_enrichment(&patient.case_number.unwrap(), &data)?;
            enriched += 1;
        }
    }

    Ok(Json(json!({"enriched": enriched})))
}
```

---

## PHASE 5: VLK REVERSE SYNC (Day 3)

### 5.1 Airtable → Boss DB

```rust
/// Reverse sync VLK fields from Airtable to Boss DB
pub async fn reverse_sync_vlk(&self, db: &Database) -> Result<ReverseSyncResult> {
    let records = self.list_records().await?;
    let mut counts = ReverseSyncResult::default();

    for record in records {
        let fields = &record.fields;
        let case_number = match fields.get("№ запису").and_then(|v| v.as_str()) {
            Some(cn) => cn,
            None => { counts.skipped += 1; continue; }
        };

        // Get VLK fields from Airtable
        let trauma_date = fields.get("Дата травми").and_then(|v| v.as_str());
        let vlk_date = fields.get("Дата ВЛК").and_then(|v| v.as_str());
        let vlk_decision = fields.get("Рішення ВЛК").and_then(|v| v.as_str());
        let extension_days = fields.get("Дні продовження").and_then(|v| v.as_i64());

        // Update Boss DB
        if trauma_date.is_some() || vlk_date.is_some() {
            db.update_vlk_fields(case_number, trauma_date, vlk_date, vlk_decision, extension_days)?;
            counts.updated += 1;
        } else {
            counts.skipped += 1;
        }
    }

    Ok(counts)
}
```

---

## FILE STRUCTURE

```
boss-tui/src/
├── main.rs
├── app.rs
├── server/
│   ├── mod.rs
│   ├── routes.rs      # Updated with real implementations
│   └── db.rs          # Add update_enrichment(), update_vlk_fields()
├── sync/              # NEW MODULE
│   ├── mod.rs
│   ├── airtable.rs    # Airtable REST client
│   ├── cyberintern.rs # CyberIntern API client
│   └── validator.rs   # Data validation
└── ...
```

---

## DEPENDENCIES TO ADD

```toml
# Cargo.toml additions
[dependencies]
regex = "1"  # For text parsing (if not already)
# reqwest already included
# serde already included
# tokio already included
```

---

## TESTING PLAN

### Unit Tests
```rust
#[cfg(test)]
mod tests {
    #[test]
    fn test_title_case_ukrainian() {
        assert_eq!(to_title_case_ukrainian("ВІЙСЬКОВА ЧАСТИНА"), "Військова Частина");
        assert_eq!(to_title_case_ukrainian("ДУ ЛІКАРНЯ"), "ДУ Лікарня");
    }

    #[test]
    fn test_validation_required_fields() {
        let patient = Patient { pib: "".into(), ..Default::default() };
        let result = validate_patient(&patient);
        assert!(!result.is_valid);
        assert!(result.errors.contains(&"Missing pib (name)".to_string()));
    }
}
```

### Integration Tests
```bash
# Test Airtable sync
curl -X POST http://localhost:8083/sync/airtable

# Test CyberIntern enrichment
curl -X POST http://localhost:8083/sync/enrich-cyberintern

# Test VLK reverse sync
curl -X POST http://localhost:8083/sync/vlk-from-airtable
```

---

## TIMELINE

| Day | Phase | Deliverable |
|-----|-------|-------------|
| **Day 1 AM** | Phase 1 | Airtable client (CRUD operations) |
| **Day 1 PM** | Phase 2 | Data validator (validation + cleaning) |
| **Day 2 AM** | Phase 3 | CyberIntern client (auth + fetching) |
| **Day 2 PM** | Phase 3 | Text parsing (complaints, anamnesis) |
| **Day 3 AM** | Phase 4 | Wire up routes.rs |
| **Day 3 PM** | Phase 5 | VLK reverse sync + testing |

---

## SUCCESS CRITERIA

- [ ] `cargo build --release` produces single binary
- [ ] No Python dependency
- [ ] All 4 sync endpoints actually work:
  - [ ] `POST /sync/airtable` syncs to Airtable
  - [ ] `POST /sync/enrich-cyberintern` enriches 027/о data
  - [ ] `POST /sync/vlk-from-airtable` reverse syncs VLK
  - [ ] `POST /sync` saves scraped patients to DB
- [ ] Data validation blocks invalid patients
- [ ] Smart sync only fills empty Airtable fields
- [ ] Ukrainian text handling (Title Case) works

---

## ROLLBACK PLAN

If Rust implementation has issues:
1. Python API still exists at `cyberintern-boss/`
2. Can run Python API on 8083, Rust TUI on 8084
3. Gradual migration: one endpoint at a time

---

**GRUG APPROVED?** 🪓
