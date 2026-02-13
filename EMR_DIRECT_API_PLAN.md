# EMR DIRECT API PLAN - REPLACE CYBERINTERN WITH RUST
**Date:** 2026-02-13
**Status:** ALL ENDPOINTS CONFIRMED VIA LIVE CURL TESTING
**Decision:** Kill the Python CyberIntern monster. Connect Boss TUI directly to EMR REST API.

---

## THE BIG PICTURE

```
CURRENT (BROKEN):
  Boss TUI (Rust) -> CyberIntern (Python+Playwright) -> Browser -> EMR Web UI
  Speed: 3-10 seconds per operation
  Status: BROKEN (Playwright browsers not installed since Jan 15)

TARGET:
  Boss TUI (Rust) -> Direct HTTP (reqwest) -> EMR REST API (doc.hospital.mia.software)
  Speed: 100-200ms per operation
  Status: ALL ENDPOINTS CONFIRMED - READY TO BUILD
```

**Performance gain: 10-100x faster**
**Complexity reduction: Remove entire Python project + no browser automation needed**

---

## API ROOT DISCOVERY

**`GET /api/v1/`** returns the COMPLETE endpoint directory (Django REST Framework browsable API).
This was the key breakthrough - we can see EVERY endpoint the EMR exposes.

**Total endpoints available:** 70+ (see full list at bottom)

---

## CONFIRMED WORKING ENDPOINTS (Live-tested 2026-02-13)

### 1. Authentication
```
Step 1: GET /login/
  -> Extract csrftoken from Set-Cookie header

Step 2: POST /login/
  Content-Type: application/x-www-form-urlencoded
  Cookie: csrftoken=...
  Referer: https://doc.hospital.mia.software/login/
  Body: username=doctor@hospital.ua&password=xxx&csrfmiddlewaretoken={csrftoken}&email-login=
  -> 302 redirect, Set-Cookie: sessionid=...

Step 3: GET /role-choose/{role_id}/
  Cookie: sessionid=...; csrftoken=...
  -> 200, session now has full access

CRITICAL NOTES:
  - Field name is "username" NOT "email"
  - Must include "email-login=" in POST body (form name)
  - Must include csrfmiddlewaretoken in POST body
  - Must include Referer header on all requests
```

### 2. Patient List (HUGE DISCOVERY - NO BROWSER NEEDED!)
```
GET /api/v1/case/?page_size=100
Cookie: sessionid=...

Response: {
  count: 42769,  // total records
  next: "...?page=2&page_size=100",
  results: [
    {
      id: 280762,           // case_id (use for all sub-endpoints)
      label: "26/02568",
      organization: 123,
      document_number: "26/01487",
      full_name: "...",
      short_name: "...",
      number: "26/02568",
      birthday: "1978-07-08",
      division_current: 419  // null = discharged
    }
  ]
}

NOTE: status=hospitalized filter does NOT work (returns all 42769).
      division_current filter does NOT work either.
      ordering=-case_date does NOT work.
      Filter by division_current != null client-side for active patients.
      Pagination works: page=1&page_size=100 through all pages.
```

### 3. Patient Case Details
```
GET /api/v1/case/{case_id}/
Cookie: sessionid=...

Response: FULL patient JSON including:
  - full_name, birthday, sex, age
  - status ("hospitalized" / "discharged")
  - case_date, case_time (admission)
  - discharged_date, discharged_time
  - doctor (id, full_name, specialty)
  - division_current, bed, hospital_ward
  - workplace, position
  - contact_phone, formatted_address
  - person_id (passport), citizenship
  - institution (referring org)
  - preferential_category (military status)
  - attributes (blood_type, weight, height, allergies, etc.)
  - recommendations (discharge recommendations text)
  - contingent (mobilized/etc), feature (National Guard/etc)
  - social_status
  - treatment_result
```

### 4. Medical Diaries - READ
```
GET /api/v1/case/{case_id}/diary/?page_size=100&show=active
Cookie: sessionid=...

Response: {
  count: N,
  results: [{
    id, inspection_date, inspection_time,
    doctor_name, description, diary_type
  }]
}
```

### 5. Medical Diaries - WRITE
```
POST /api/v1/case/{case_id}/diary/
Content-Type: application/json
X-CSRFToken: {csrf_token}
Cookie: sessionid=...; csrftoken=...

Body: {
  "description": "...",
  "diary_type": "diary",
  "inspection_date": "2026-02-13",
  "inspection_time": "10:30:00",
  "doctor": 5272
}
```

### 6. Diagnostic Reports (LABS + EKG + IMAGING = ALL IN ONE!)
```
GET /api/v1/case/{case_id}/diagnostic-report/
Cookie: sessionid=...

Response: {
  count: N,
  results: [{
    id, case, issued,
    conclusion: "FULL TEXT with all lab values/results",
    description: "Detailed measurements",
    eh_service: {
      code: "B38001",      // eHealth service code
      name: "Blood test",
      category: { code: "laboratory_procedure" | "diagnostic_procedure" | "imaging" }
    },
    performer: { full_name, specialty },
    interpreter: { full_name, specialty },
    organization_service: { name: "310 Preop complex" },
    observations: [],
    files: [631577, 631578]  // attached file IDs
  }]
}

CATEGORIES (filter by eh_category.code):
  - "laboratory_procedure" = Blood work, urinalysis, coagulation
  - "diagnostic_procedure" = EKG, functional tests
  - "imaging" = Ultrasound, X-ray, CT

EXAMPLE LAB DATA (in conclusion field as text):
  Leukocytes (WBC): 8.96 x 10^9/l
  Erythrocytes (RBC): 5.12 x10^12/l
  Hemoglobin: 145.5 g/l
  Platelets: 194.4 x 10^9/l
  ALT: 18.3 U/l
  AST: 17.1 U/l
  Creatinine: 84.1 umol/l
  Glucose: 6.4 mmol/l
  ... (full CBC + biochemistry + coagulation + electrolytes)

THIS IS THE KEY DISCOVERY: Labs are NOT in a separate endpoint.
They are diagnostic-reports with category "laboratory_procedure".
```

### 7. Surgical Procedures (case sub-endpoint)
```
GET /api/v1/case/{case_id}/procedure/
Cookie: sessionid=...

Response: { results: [{
  id, status,
  surgeries: [{operation, performer, anesthesia, surgery_time}]
}]}
```

### 8. Surgery (top-level endpoint - MORE DETAILED)
```
GET /api/v1/surgery/?case={case_id}
Cookie: sessionid=...

Response: {
  count: 1,
  results: [{
    id, number, case,
    operation: "<p>Full surgical protocol text...</p>",
    anesthesia: "combined",
    surgery_time: "00:30:00",
    anesthesia_duration: "00:40",
    surgeon: null,  // or {id, full_name}
    anesthesiologist: {id, full_name},
    assistants: [],
    nurses: [{id, full_name}],
    diagnosis_before_icd10am: {code: "S42.02", name: "..."},
    diagnosis_after_icd10am: {code: "S42.02", name: "..."},
    division: {id, name, department: {...}}
  }]
}
```

### 9. Consultations
```
GET /api/v1/case/{case_id}/consultation/?show=active&page_size=100
Cookie: sessionid=...

Response: { count, results: [{
  id, consultation_date, specialty,
  conclusion, recommendations
}]}
```

### 10. Diagnoses (case sub-endpoint)
```
GET /api/v1/case/{case_id}/diagnosis/
Cookie: sessionid=...

Response: { count, results: [{
  id, diagnosis_type, diagnosis_date,
  label: "S42.02 - Fracture...",
  extended: "Additional description",
  icd10am: {code, name},
  role: {code: "primary"},
  clinical_status: {code: "active"},
  verification_status: {code: "confirmed"},
  asserter: {id, full_name, specialty}
}]}
```

### 11. Case Diagnoses (top-level - same data)
```
GET /api/v1/case-diagnosis/?case={case_id}
Cookie: sessionid=...
(Returns same data as case sub-endpoint with full asserter details)
```

### 12. Encounters (eHealth encounters)
```
GET /api/v1/encounter/?case={case_id}
Cookie: sessionid=...

Response: { count, results: [{
  id, eh_id,
  encounter_type: "service_delivery_location",
  encounter_class: "INPATIENT",
  diagnoses: [...],
  care_manager: 5272,
  care_manager_name: "...",
  employee: {id, full_name, specialty},
  status: "finished"
}]}
```

### 13. Medicine Tasks
```
GET /api/v1/appointment/medicines/tasks/?date=YYYY-MM-DD&status=active
Cookie: sessionid=...
X-Requested-With: XMLHttpRequest

Response: { count: 130, results: [{
  id, case: {number, full_name},
  medicine: {name}, status
}]}
```

### 14. Hospital Wards
```
GET /api/v1/hospital-ward/?page_size=100
Cookie: sessionid=...

Response: { count: 3594, results: [{
  id, label: "801",
  division: {id: 347, name: "Trauma", reanimation: false},
  free_beds: 1
}]}
```

### 15. Beds
```
GET /api/v1/bed/?page_size=100
Cookie: sessionid=...

Response: { count: 4841, results: [{
  id, label: "1",
  hospital_ward: {id, label, division: {...}, free_beds: N},
  status: "unfolded",
  bed_profile: {id, name: "General"},
  is_free: true
}]}
```

### 16. Discharge Records
```
GET /api/v1/discharge/?case={case_id}
Cookie: sessionid=...

Response: { count: 1, results: [{
  id, case, document_type: "discharge",
  document_date, document_time, organization
}]}
```

### 17. Case Documents
```
GET /api/v1/case-document/?case={case_id}
Cookie: sessionid=...
(Same data as discharge endpoint for discharge docs)
```

### 18. Sick Leave
```
GET /api/v1/case/{case_id}/sick-leave/
Cookie: sessionid=...

Response: { count: 0, results: [] }
NOTE: Endpoint EXISTS (200) but returned empty for tested patients.
May need POST /api/v1/case/{id}/medical-conclusion/ instead.
```

### 19. Medical Conclusion (POST only - sicklist creation)
```
OPTIONS /api/v1/case/{case_id}/medical-conclusion/
-> {"name":"Wrapped View","renders":["application/json"],"parses":["application/json","multipart/form-data"]}

GET returns 405 "Method GET not allowed"
POST is the only allowed method - creates a medical conclusion/sicklist.
```

### 20. Journals
```
GET /api/v1/journal/
Cookie: sessionid=...

Response: { count: 6, results: [{
  id: 1, name: "Admission journal",
  id: 8, name: "Ambulatory patient registration",
  id: 12, name: "Procedure journal",
  ...
}]}
NOTE: This is a CATALOG of journal types, not patient-specific data.
```

### 21. Employee Roles
```
GET /api/v1/employee-role/?page_size=30
Cookie: sessionid=...
(Paginated role list)
```

### 22. Prescription Medicine (CATALOG)
```
GET /api/v1/prescription/medicine/
Cookie: sessionid=...

Response: { count: 4448, results: [{id, name: "Medicine name"}] }
NOTE: This is the drug CATALOG (dictionary), not patient-specific prescriptions.
The ?case= filter is IGNORED on this endpoint.
```

### 23. Prescription Prescriptions
```
GET /api/v1/prescription/prescriptions/?case={case_id}
Cookie: sessionid=...

Response: { count: 0, results: [] }
NOTE: Endpoint EXISTS (200) but empty for all tested patients.
Medications may be tracked only via appointment/medicines/tasks.
```

---

## CONFIRMED 404 ENDPOINTS (Don't exist)

These were tested and DO NOT exist:
- `/api/v1/case/{id}/observation/` - 404
- `/api/v1/case/{id}/measurement/` - 404
- `/api/v1/case/{id}/vitals/` - 404
- `/api/v1/case/{id}/lab-result/` - 404
- `/api/v1/case/{id}/laboratory/` - 404
- `/api/v1/case/{id}/lab/` - 404 (from previous session)
- `/api/v1/case/{id}/conclusion/` - 404 (from previous session)
- `/api/v1/case/{id}/prescription/` - 404 (from previous session)
- Various FHIR-style names (service-request, medication-request, etc.) - all 404

---

## FULL API ROOT ENDPOINT LIST

All endpoints returned by `GET /api/v1/`:

| Category | Endpoint | Purpose |
|----------|----------|---------|
| **Geo** | country, region, district, city, city-status, street, street-status, building | Address lookups |
| **Org** | organization, division, department, institution | Hospital structure |
| **Staff** | employee, employee-role, specialty | Personnel |
| **Patients** | case, preperson | Patient records |
| **Clinical** | case-diagnosis, case-injury, case-infection, anamnesis | Clinical data |
| **Documents** | case-document, discharge, document-template | Documents |
| **Procedures** | surgery, medical-examination, medical-examination-options | Surgeries & exams |
| **Services** | service, appointment-service, appointment-service-export | Medical services |
| **Meds** | prescription/medicine, prescription/prescriptions, appointment/medicines/tasks | Medications |
| **Tasks** | tasks/abidance, tasks/diet, tasks/cancel_options | Task management |
| **Wards** | hospital-ward, bed, bed-profile | Bed management |
| **eHealth** | encounter, episode, ehealth/medical-program, ehealth/service-group, ehealth/service, ehealth/program-service, ehealth/legal_entities | eHealth integration |
| **Financial** | own-service, own-service/group, organization-service, currency | Services & billing |
| **Observations** | observation-icf, observation-loinc, observation-options | ICF/LOINC obs |
| **Maternity** | pregnancy-partogram-options, childbirth/childbirth-data, childbirth-data-options, previous-pregnancies, newborn-estimation | Obstetrics |
| **Anesthesia** | anesthesia-card-options, anesthesia-sheet-options | Anesthesia |
| **Checkups** | checkups/external-obstetric-exam | Exams |
| **Other** | journal, reference, sequence, constant, dictionaries, v2/dictionaries, v2/values/dictionaries | Lookups |
| **System** | user-locale, user-organization, mis-integration, warehouse, attribute-option, benefit-category | System |
| **Forbidden** | ehealth/forbidden/group, ehealth/forbidden/service, ehealth/forbidden/code | eHealth restrictions |

---

## RUST IMPLEMENTATION ARCHITECTURE

### New module: `src/emr/` (replaces both scraper/ and sync/cyberintern.rs)

```
src/emr/
+-- mod.rs              # Public API: EMRClient
+-- auth.rs             # Login, session cookies, CSRF token management
+-- client.rs           # HTTP client with session handling (reqwest)
+-- patients.rs         # GET /api/v1/case/ (list) + /api/v1/case/{id}/ (detail)
+-- diaries.rs          # GET + POST /api/v1/case/{id}/diary/
+-- diagnostic_reports.rs # GET /api/v1/case/{id}/diagnostic-report/
+--                      # Contains: labs, EKG, imaging, ultrasound
+-- surgery.rs          # GET /api/v1/surgery/?case={id}
+-- consultations.rs    # GET /api/v1/case/{id}/consultation/
+-- diagnoses.rs        # GET /api/v1/case-diagnosis/?case={id}
+-- encounters.rs       # GET /api/v1/encounter/?case={id}
+-- wards.rs            # GET /api/v1/hospital-ward/ + /api/v1/bed/
+-- discharge.rs        # GET /api/v1/discharge/?case={id}
+-- medications.rs      # GET /api/v1/appointment/medicines/tasks/
+-- sick_leave.rs       # GET /api/v1/case/{id}/sick-leave/
+--                      # POST /api/v1/case/{id}/medical-conclusion/
+-- types.rs            # All EMR data types (serde Deserialize)
```

### Key design:
- `EMRClient` holds `reqwest::Client` with cookie jar
- Login once, reuse session for all calls
- Auto-refresh session on 401/403
- CSRF token extracted from cookie, cached
- All methods return `Result<T, BossError>`
- Pagination handled automatically (follow `next` links)

### Authentication flow in Rust:
```rust
impl EMRClient {
    pub async fn login(&mut self, username: &str, password: &str, role_id: &str) -> Result<()> {
        // 1. GET /login/ -> extract csrftoken from Set-Cookie
        // 2. POST /login/ with:
        //    - username={username}
        //    - password={password}
        //    - csrfmiddlewaretoken={csrftoken}
        //    - email-login=
        //    - Referer: .../login/
        // 3. Follow 302 redirect
        // 4. GET /role-choose/{role_id}/ to activate role
        // 5. Session cookies now stored in reqwest cookie jar
    }

    pub async fn ensure_session(&mut self) -> Result<()> {
        // Check if session still valid (GET any endpoint)
        // If 401/403 -> re-login automatically
    }
}
```

### Lab data extraction:
```rust
// Labs are in diagnostic-report with category "laboratory_procedure"
pub async fn get_lab_results(&self, case_id: u64) -> Result<Vec<DiagnosticReport>> {
    let reports = self.get_diagnostic_reports(case_id).await?;
    Ok(reports.into_iter()
        .filter(|r| r.eh_category.code == "laboratory_procedure")
        .collect())
}

// Parse lab values from conclusion text
pub fn parse_lab_values(conclusion: &str) -> HashMap<String, LabValue> {
    // Pattern: "Name: value unit reference_range"
    // e.g. "Hemoglobin (BC): 145.5 g/l 145.5 120 - 175"
}
```

---

## MIGRATION PLAN

### Phase 1: Build EMR Client Core
1. Create `src/emr/` module
2. Implement login + session management (auth.rs)
3. Implement `list_patients()` - GET /api/v1/case/
4. Implement `get_patient(case_id)` - GET /api/v1/case/{id}/
5. Test with curl-verified data

### Phase 2: Clinical Data
1. Implement `get_diaries(case_id)` + `post_diary(case_id, diary)`
2. Implement `get_diagnostic_reports(case_id)` (labs + imaging + EKG)
3. Implement `get_surgery(case_id)`
4. Implement `get_consultations(case_id)`
5. Implement `get_diagnoses(case_id)`

### Phase 3: Ward + Bed Management
1. Implement `get_wards()` + `get_beds()`
2. Implement `get_discharge(case_id)`
3. Implement `get_medications()` (appointment/medicines/tasks)

### Phase 4: Wire into Sync Pipeline
1. Replace `CyberInternClient` calls in `server/routes/sync.rs`
2. `perform_ci_import()` -> `perform_emr_import()` using EMRClient
3. Patient list from API instead of HTML scraping
4. Enrichment from `get_patient()` + `get_diagnostic_reports()`
5. Test with real EMR connection

### Phase 5: Kill CyberIntern
1. Remove `cyberintern/` submodule
2. Remove `sync/cyberintern.rs`
3. Remove CyberIntern startup from START.bat and zav-launcher
4. Remove chromiumoxide/browser dependencies from Cargo.toml
5. Update CLAUDE.md and STATUS.md
6. Free port 8082

---

## WHAT WE DO NOT NEED

| What | Why |
|------|-----|
| CyberIntern (Python) | Direct API replaces all its functions |
| Playwright | No browser automation needed - all endpoints are REST |
| chromiumoxide | No browser automation needed |
| Patient list scraping | `GET /api/v1/case/` returns full patient list |
| Lab scraping | `GET /api/v1/case/{id}/diagnostic-report/` has all labs |
| Sicklist scraping | `GET /api/v1/case/{id}/sick-leave/` exists |

---

## OPEN QUESTIONS

1. **Sick leave data**: Endpoint exists but empty for all tested patients. May need to:
   - Test with a patient known to have an active sicklist
   - POST to medical-conclusion instead of GET from sick-leave
   - May be a display-only feature in the EMR

2. **Prescription tracking**: `prescription/prescriptions/?case=` empty for all tested patients.
   - Medications likely managed ONLY through `appointment/medicines/tasks`
   - The prescriptions endpoint may be for eHealth prescriptions only

3. **Division filtering**: `?division_current=347` filter doesn't work on case list.
   - Filter client-side after fetching all records
   - Or find the correct parameter name by testing

4. **observation-loinc**: Consistently empty (hospital may not use LOINC-coded observations).
   - All lab data is in diagnostic-report instead

---

## ENVIRONMENT VARIABLES

```bash
EMR_URL=https://doc.hospital.mia.software
EMR_EMAIL=tsapenko.heorhii@gmail.com  # field name is "username" but value is email
EMR_PASSWORD=xxx
EMR_ROLE_ID=23622
```

Already exist in `windows-deploy/secrets.bat`.

---

## SESSION MANAGEMENT

```
Cookies file: C:/Users/master/emr_cookies2.txt
Session ID: mwn7ehjysh6r3abu8q3pnxtycnscvcmf
CSRF Token: sdUGWsWrMz8yqI07kFWnrrVmxOrC6GuH
Domain: .hospital.mia.software
Tested: 2026-02-13

All requests require:
  Cookie: sessionid=...; csrftoken=...
  Referer: https://doc.hospital.mia.software/
  Accept: application/json (recommended)
```

---

## RISK ASSESSMENT

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Session expires mid-sync | HIGH | LOW | Auto re-login on 401/403 |
| CSRF token rejected | LOW | LOW | Extract fresh from cookie |
| Patient list too large | MEDIUM | LOW | Paginate, filter client-side |
| Lab values are text not structured | CERTAIN | MEDIUM | Parse text with regex |
| EMR API changes | LOW | HIGH | Version pin, monitor |
| Rate limiting | LOW | LOW | 50ms delay between calls |
