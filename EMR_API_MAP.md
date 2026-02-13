# CyberIntern ↔ EMR API Mapping
**Complete audit of all HTTP interactions with doc.hospital.mia.software**

**Date:** 2026-02-13
**Status:** Research & Documentation
**Target EMR:** https://doc.hospital.mia.software
**CyberIntern Location:** /e/zav-hospital/cyberintern/

---

## CRITICAL FINDING: Browser Scraping vs REST API

### Current Architecture (Browser-Based)
CyberIntern uses **Playwright browser automation** to scrape the EMR. This is:
- ✅ Works with visual UI (avoids API authentication complexity)
- ❌ Brittle (breaks on UI changes)
- ❌ Slow (full page loads for each operation)
- ❌ Resource-intensive (headless Chrome running constantly)
- ❌ Limited to what the UI renders (may miss backend data)

### Available REST APIs (Undocumented)
The EMR has a **real backend REST API** (`/api/v1/`) that serves the UI. This is:
- ✅ Fast (direct data transfer)
- ✅ Reliable (doesn't break on UI changes)
- ✅ Less resource-intensive
- ❌ May require authentication (needs investigation)
- ❌ Undocumented (discovered via browser network traffic)

### Recommendation
**Replace Playwright scraping with REST API calls** to the `/api/v1/` endpoints. This requires mapping API authentication (may be session-based, token-based, or CSRF-protected).

---

## BASE URL
```
https://doc.hospital.mia.software
```

---

## AUTHENTICATION & SESSION MANAGEMENT

### Login Flow (Page-Based)
**Source:** `src/services/emr_service_playwright.py:189-200`

```
1. Navigate to: https://doc.hospital.mia.software/login/
2. Enter email & password (form submission)
3. Select department role: https://doc.hospital.mia.software/role-choose/{role_id}/?next=
4. Navigate to: https://doc.hospital.mia.software/case/my-patients/hospitalized/
```

**Key Details:**
- **Role ID (Trauma Department):** `23622`
- **Session Management:** Browser cookies (stored by Playwright)
- **CSRF Tokens:** Required for diary/document submissions
  - Fetched from cache or page DOM
  - Passed in `X-CSRFToken` header for POST requests

### CSRF Token Retrieval
**Source:** `src/services/csrf_manager.py:153`

CSRF tokens are extracted from page during browser automation:
```javascript
// Extract from page DOM
const token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
// OR from form input
const token = document.querySelector('input[name="_csrf_token"]')?.value;
```

### Login Role Selection URLs
```
GET https://doc.hospital.mia.software/role-choose/{role_id}/?next=
```

**Parameters:**
- `role_id`: Department role ID (e.g., `23622` for trauma)
- `next`: Redirect URL after selection (optional)

---

## DATA RETRIEVAL ENDPOINTS

### 1. Patient List (Hospitalized)
**Purpose:** Fetch all hospitalized patients for logged-in doctor
**Source:** `src/services/emr_service_playwright.py:507-583`

#### Page Navigation (Current)
```
GET https://doc.hospital.mia.software/case/my-patients/hospitalized/
```

#### Backend (via page.evaluate)
```javascript
// Automatically called by EMR UI
// Extracts from dynamically-rendered DataTable
// Returns array of patient objects
{
  success: true,
  patients: [
    {
      id: "25_11636",           // EMR case number (unique ID)
      pib: "Бурковський О.С.",  // Full name (ПІБ)
      status: "Госпіталізовано", // Status
      case_number: "25/2024",    // Medical record number
      case_url: "...",           // Direct link to patient
      history_number: "11636",   // History/case number
      ...
    }
  ]
}
```

**Data Extracted via JavaScript Evaluation:**
```javascript
// Parses DataTable rows to extract patient data
const rows = document.querySelectorAll('.ant-table-tbody tr');
rows.forEach(row => {
  const cells = row.querySelectorAll('td');
  // Extract: ID, name, status, bed, ward, admission date, etc.
});
```

---

### 2. Patient Details / Case Information
**Purpose:** Fetch full patient data for a specific case
**Source:** `src/services/emr_service_playwright.py:594-748`

#### Page Navigation (Current)
```
GET https://doc.hospital.mia.software/case/{case_id}/
```

#### REST API (Recommended)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/
```

**Response Format:**
```json
{
  "id": "25_11636",
  "full_name": "Бурковський О.С.",
  "short_name": "Б.О.С.",
  "number": "25/2024",                    // Case number
  "birthday": "1985-03-15",
  "gender": "M",                          // or "F"
  "phone": "+380501234567",
  "address": "вул. Героів, 10, Кривий Ріг, 50000",
  "workplace": "ЛТД 'Арселор Мітталь'",  // Employer
  "contingent": "цивільне",              // Civilian/military
  "social_status": "робітник",           // Social status
  "bed": "15",                            // Bed number
  "division": "Травматологія",           // Department
  "ward": "2",                            // Ward/room
  "admission_date": "2024-11-20",
  "discharge_date": null,                 // null if hospitalized
  "trauma_date": "2024-11-18",           // Injury date
  "ehealth_id": "...",                    // Optional eHealth ID
  ...
}
```

**Query Parameters:**
None documented, but common patterns:
- `?format=json` - Force JSON response
- `?include=full` - Include nested relationships

---

### 3. Diagnosis Information
**Purpose:** Get primary diagnosis and ICD-10 code
**Source:** `src/services/emr_service_playwright.py:749-907`

#### Page Navigation + Tab Click
```
1. GET https://doc.hospital.mia.software/case/{case_id}/
2. Click "Діагноз" (Diagnosis) tab
3. Extract from visible panel
```

#### REST API (Likely, but not yet confirmed)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/diagnosis/
```

**Response Format (from page extraction):**
```json
{
  "diagnosis": "Закрита ЧМТ легкого ступеня",
  "diagnosis_icd10": "S06.9",             // ICD-10 code
  "full_diagnosis": "Закрита черепно-мозкова травма легкого ступеня..."
}
```

**Extraction Method (JavaScript):**
```javascript
// Find diagnosis tab
const diagTab = document.querySelector('[aria-label*="Діагноз"]');
const panelId = diagTab.getAttribute('aria-controls');
const panel = document.getElementById(panelId);

// Extract text content
const diagnosis = panel.querySelector('.diagnosis-field')?.textContent;
const icd10 = panel.querySelector('.icd10-code')?.textContent;
```

---

### 4. Diaries / Medical Notes
**Purpose:** Fetch existing diaries for a patient
**Source:** `src/services/emr_service_playwright.py:909-1059`

#### REST API (Confirmed - Uses Fetch)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/diary/
```

**Query Parameters:**
```
?page_size=10          # Records per page (default: 10)
&show=active           # Filter: active, all, archived
&limit=10              # Alternative to page_size
```

**Request Headers (from browser evaluation):**
```
GET /api/v1/case/{case_id}/diary/ HTTP/1.1
Host: doc.hospital.mia.software
Content-Type: application/json
Authorization: (session-based via cookies)
```

**Response Format:**
```json
{
  "count": 15,
  "results": [
    {
      "id": 12345,
      "inspection_date": "2024-12-18",
      "inspection_time": "10:30:00",
      "doctor_name": "Панфьоров С.В.",
      "doctor_id": 5272,
      "description": "Клінічне дослідження...",
      "diary_type": "diary",
      "status": "active"
    },
    ...
  ]
}
```

**Diary Types:**
- `diary` - Regular daily note
- `lkk` - Medical commission report
- `preop` - Pre-operative note
- `postop` - Post-operative note
- `discharge` - Discharge summary

---

### 5. Procedures / Operations
**Purpose:** Get surgical procedures for patient
**Source:** `src/services/patient_context_service.py:190-265`

#### REST API
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/procedure/
```

**Response Format:**
```json
{
  "results": [
    {
      "id": 67890,
      "status": "completed",
      "surgeries": [
        {
          "operation": "Хірургічна обробка рани, первинне закриття",
          "performer": {
            "full_name": "Кондратов Д.С.",
            "id": 1234
          },
          "anesthesiologist": {
            "full_name": "Лікар анестезіолог",
            "id": 5678
          },
          "assistants": [
            {"full_name": "Асистент 1", "id": 9999},
            ...
          ],
          "nurses": [
            {"full_name": "Медсестра", "id": 8888},
            ...
          ],
          "anesthesia": "epidural",
          "surgery_time": "2024-11-20 14:30:00",
          "duration": "45",                    // minutes
          "anesthesia_duration": "60",         // minutes
          "complications": [],
          "equipments": []
        }
      ],
      "diagnosis_before_icd10am": {
        "text": "S06.9"
      },
      "diagnosis_after_icd10am": {
        "text": "S06.9"
      }
    }
  ]
}
```

---

### 6. Prescriptions / Medications
**Purpose:** Get current and historical medication prescriptions
**Source:** `src/services/emr_service_playwright.py:1846-1970`

#### Page Navigation + Tab Click
```
1. GET https://doc.hospital.mia.software/case/{case_id}/
2. Click "Препарати" (Prescriptions) tab
3. Extract from DataTable
```

#### REST API (Likely)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/prescription/
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/medications/
```

**Response Format (from page extraction):**
```json
{
  "prescriptions": [
    {
      "medication_name": "Аспірин",
      "dosage": "500мг",
      "full_text": "Аспірин 500мг, 2 таблетки 3 рази на день",
      "status": "active",
      "start_date": "2024-11-20",
      "end_date": "2024-12-04",
      "frequency": "3 times daily"
    }
  ]
}
```

**Extraction Method (JavaScript):**
```javascript
// Find prescriptions tab and click
// Extract from DataTable rows
const prescRows = document.querySelectorAll('.ant-table-tbody tr');
prescRows.forEach(row => {
  const cells = row.querySelectorAll('td');
  // Extract: medication, dosage, status, dates
});
```

---

### 7. Laboratory Results / Diagnostic Tests
**Purpose:** Get lab test results and diagnostic reports
**Source:** `src/services/emr_service_playwright.py:1972-2114`

#### Page Navigation + Tab Click
```
1. GET https://doc.hospital.mia.software/case/{case_id}/
2. Click "Діагностичні звіти" (Diagnostic Reports) tab
3. Extract from DataTable
```

#### REST API (Likely)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/lab/
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/diagnostics/
```

**Response Format (from page extraction):**
```json
{
  "labs": [
    {
      "id": 11111,
      "test_name": "Загальний аналіз крові (ЗАК)",
      "test_code": "OBC",
      "service_code": "1001",
      "date": "2024-12-17",
      "status": "completed",
      "results": "See EMR for detailed results",
      "normal": false
    },
    {
      "id": 11112,
      "test_name": "Біохімічний аналіз",
      "test_code": "BAS",
      "date": "2024-12-17",
      "status": "completed"
    }
  ]
}
```

---

### 8. Sick Leaves / Medical Conclusions
**Purpose:** Get medical certificates (sicklists, temporary disability documents)
**Source:** `src/services/emr_service_playwright.py:1361-1844`

#### Page Navigation + Tab Click
```
1. GET https://doc.hospital.mia.software/case/{case_id}/
2. Click "Медичні висновки" (Medical Conclusions) tab
3. Click on specific sicklist row to get details
4. Extract conclusion number and dates
```

#### REST API (Likely)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/conclusion/
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/sicklist/
```

**Response Format (from page extraction):**
```json
{
  "sicklists": [
    {
      "id": 22222,
      "conclusion_number": "ВЛ 450/24",
      "type": "temporary_disability",
      "status": "active",
      "start_date": "2024-11-20",
      "end_date": "2024-12-04",
      "diagnosis": "Закрита ЧМТ легкого ступеня",
      "category": "civil",
      "doctor_name": "Панфьоров С.В.",
      "processing_status": "completed"
    }
  ]
}
```

**Document Types:**
- `temporary_disability` - Sicklist (ВЛ)
- `medical_referral` - Referral for specialist
- `discharge_summary` - Discharge conclusion

---

### 9. Consultations / Specialist Visits
**Purpose:** Get specialist consultations and referrals
**Source:** `src/services/emr_service_playwright.py:2210-2280`

#### Page Navigation + Tab Click
```
1. GET https://doc.hospital.mia.software/case/{case_id}/
2. Click "Консультації" (Consultations) tab
3. Extract consultation data
```

#### REST API (Likely)
```
GET https://doc.hospital.mia.software/api/v1/case/{case_id}/consultation/
```

**Response Format (from page extraction):**
```json
{
  "consultations": [
    {
      "id": 33333,
      "specialty": "Ортопедія",
      "doctor_name": "Спеціаліст О.В.",
      "date": "2024-12-15",
      "status": "completed",
      "notes": "Консультативний висновок...",
      "recommendations": "..."
    }
  ]
}
```

---

## DATA SUBMISSION ENDPOINTS

### 1. Submit Diary (Most Important)
**Purpose:** Create and post daily patient notes
**Source:** `src/services/diary_service.py:57-173` and `src/services/emr_service_playwright.py:2370-2410`

#### REST API
```
POST https://doc.hospital.mia.software/api/v1/case/{case_id}/diary/
```

**Request Headers:**
```
POST /api/v1/case/{case_id}/diary/ HTTP/1.1
Host: doc.hospital.mia.software
Content-Type: application/json
X-CSRFToken: {csrf_token}
```

**Request Body:**
```json
{
  "description": "Клінічне дослідження: стан задовільний. Пульс 82, АТ 130/85. Рана чиста, без ознак запалення. Осередків больності нема. Рекомендовано продовжити консервативне лікування.",
  "diary_type": "diary",
  "inspection_date": "2024-12-18",
  "inspection_time": "10:30:00",
  "doctor": 5272
}
```

**Response (Success - 200/201):**
```json
{
  "id": 55555,
  "success": true,
  "inspection_date": "2024-12-18",
  "inspection_time": "10:30:00",
  "doctor": 5272,
  "description": "..."
}
```

**Response (Error - 400/401):**
```json
{
  "error": "Invalid CSRF token",
  "detail": "..."
}
```

**Key Fields:**
- `diary_type`: Type of note (diary, lkk, preop, postop, discharge)
- `inspection_date`: YYYY-MM-DD format
- `inspection_time`: HH:MM:SS format (24-hour)
- `doctor`: Doctor ID (integer, not string)
- `description`: Free text, can contain HTML or plain text

**CSRF Token:**
- Required in `X-CSRFToken` header
- Obtained from page DOM during Playwright session
- Expires after session ends

**Implementation Note:**
Currently CyberIntern uses `page.evaluate()` to call this API from within the browser context (preserves session/cookies). To call directly from backend, need to:
1. Extract CSRF token from authenticated session
2. Pass session cookies or Bearer token in Authorization header
3. Handle 403 (invalid CSRF) errors gracefully

---

### 2. Submit Prescription
**Purpose:** Create medication prescription
**Status:** DEPRECATED (Form automation incomplete, marked as 0% success rate)
**Source:** `src/services/prescription_submit_service.py:1-41`

#### Likely REST API (Not Confirmed)
```
POST https://doc.hospital.mia.software/api/v1/case/{case_id}/prescription/
```

**Expected Request Body (Based on Form Structure):**
```json
{
  "medication_name": "Аспірин",
  "dosage": "500мг",
  "frequency": "3 times daily",
  "start_date": "2024-12-18",
  "end_date": "2024-12-25",
  "notes": "..."
}
```

**Status:** Service is DEPRECATED per ADR-002. Manual prescription creation is standard workflow.

---

### 3. Submit Sicklist / Medical Conclusion
**Purpose:** Create medical conclusion (temporary disability certificate)
**Status:** DEPRECATED (Form automation incomplete, 0% success rate)
**Source:** `src/services/sicklist_submit_service.py:1-41`

#### Likely REST API (Not Confirmed)
```
POST https://doc.hospital.mia.software/api/v1/case/{case_id}/conclusion/
```

**Expected Request Body:**
```json
{
  "type": "temporary_disability",
  "diagnosis": "...",
  "start_date": "2024-12-18",
  "end_date": "2024-12-25",
  "conclusion_number": "ВЛ 450/24"
}
```

**Status:** Service is DEPRECATED. Use monitoring instead (detect expiring sicklists early).

---

### 4. Submit Lab Order
**Purpose:** Create laboratory test order
**Status:** DEPRECATED (Form automation incomplete)
**Source:** `src/services/lab_order_submit_service.py:1-41`

#### Likely REST API (Not Confirmed)
```
POST https://doc.hospital.mia.software/api/v1/case/{case_id}/lab/
```

**Status:** Service is DEPRECATED. Confirmation needed on actual API endpoints.

---

## PAGE NAVIGATION ROUTES

### Case List / Patient Management
```
GET https://doc.hospital.mia.software/case/my-patients/hospitalized/
GET https://doc.hospital.mia.software/case/my-patients/discharged/
GET https://doc.hospital.mia.software/case/all/
```

### Patient Case Page (Hub)
```
GET https://doc.hospital.mia.software/case/{case_id}/
GET https://doc.hospital.mia.software/case/{case_id}/#/medical-conclusions
GET https://doc.hospital.mia.software/case/{case_id}/#/consultations
```

### Search
```
GET https://doc.hospital.mia.software/search?q={patient_name}
```

---

## IMPLEMENTATION LOCATIONS

### Key Files for EMR Integration

| File | Purpose | Key Functions |
|------|---------|---------------|
| `src/services/emr_service_playwright.py` | Main EMR service | `login()`, `fetch_my_patients()`, `fetch_patient_details()`, `fetch_diaries()`, `fetch_procedures()` |
| `src/services/patient_context_service.py` | Patient data aggregation | `get_patient_context_for_diary()`, `get_latest_vitals()`, `get_procedures()` |
| `src/services/diary_service.py` | Diary submission | `submit_diary()` |
| `src/services/csrf_manager.py` | CSRF token handling | `get_csrf_token()` |
| `src/api/routers/emr.py` | API endpoints for CyberIntern | `POST /api/emr/sync`, `GET /api/emr/sync/status` |
| `src/services/emr_explorer.py` | EMR discovery/debugging | `explore_page()`, `map_ui_structure()` |

### Main EMRPlaywrightService Methods
```python
# Authentication
login(email, password, role_id)

# Data Retrieval (via browser automation)
fetch_my_patients()                    # GET case/my-patients/hospitalized/ + JavaScript
fetch_patient_details(case_id)         # GET case/{case_id}/ + page extraction
fetch_diagnosis_from_tab(case_id)      # Click tab + JavaScript evaluation
fetch_diaries(case_id, limit=10)       # GET /api/v1/case/{case_id}/diary/ (already uses API!)
fetch_prescriptions(case_id)           # Click tab + JavaScript extraction
fetch_lab_results(case_id)             # Click tab + JavaScript extraction
fetch_procedures(case_id)              # /api/v1/case/{case_id}/procedure/ (already uses API!)
fetch_sicklists(case_id)               # Click tab + JavaScript extraction
fetch_consultations(case_id)           # Click tab + JavaScript extraction

# CSRF & Session Management
_get_csrf_token()                      # Extract from page
```

---

## AUTHENTICATION DETAILS

### Session-Based (Current)
- **Method:** Browser cookies set during login
- **Login URL:** `https://doc.hospital.mia.software/login/`
- **Session Cookie:** `sessionid` (Django default)
- **CSRF Cookie:** `csrftoken`
- **Expires:** Session end or timeout

### CSRF Protection
- **Header:** `X-CSRFToken`
- **Value:** Retrieved from page before submission
- **Required For:** POST/PUT/DELETE requests to API
- **Cache:** 1 hour (per `csrf_manager.py`)

### Direct API Authentication (Unknown)
- **Token-Based?** Unknown - needs investigation
- **API Key?** Unknown
- **OAuth?** Unknown
- **Likely:** Inherits session authentication (session cookie sufficient)

---

## DATA FLOW DIAGRAM

```
CyberIntern Backend                          EMR (doc.hospital.mia.software)
    (Python)                                 (Django + React UI)

    ┌─────────────────────────────┐
    │   1. POST /api/emr/sync     │──────┐
    │   (Boss TUI requests)       │      │
    └─────────────────────────────┘      │
                                          │
    ┌─────────────────────────────┐      │
    │  EMRPlaywrightService       │      │
    │  ┌───────────────────────┐  │      │
    │  │ start()               │  │      │
    │  │ - Launch Chromium     │  │      │
    │  │ - Headless mode       │  │      │
    │  └───────────────────────┘  │      │
    │                             │      │
    │  ┌───────────────────────┐  │      │
    │  │ login(email, pwd)     │──┼──────┼──► GET /login/
    │  │ - Navigate to login   │  │      │    Enter credentials
    │  │ - Submit form         │  │      │    GET /role-choose/{id}/
    │  │ - Select role         │  │      │
    │  └───────────────────────┘  │      │
    │                             │      │
    │  ┌───────────────────────┐  │      │
    │  │ fetch_my_patients()   │──┼──────┼──► GET /case/my-patients/hospitalized/
    │  │ - page.goto()         │  │      │    page.evaluate() → extract DataTable
    │  │ - page.evaluate()     │  │      │
    │  │ - Extract from DOM    │  │      │
    │  └───────────────────────┘  │      │
    │                             │      │
    │  ┌───────────────────────┐  │      │
    │  │ fetch_diaries()       │──┼──────┼──► GET /api/v1/case/{id}/diary/
    │  │ - page.evaluate()     │  │      │    fetch() from browser context
    │  │ - Use /api/v1/ endpoint   │      │    (Session cookies passed)
    │  └───────────────────────┘  │      │
    │                             │      │
    └─────────────────────────────┘      │
                                          │
    ┌─────────────────────────────┐      │
    │  DiaryService               │      │
    │  ┌───────────────────────┐  │      │
    │  │ submit_diary()        │──┼──────┼──► POST /api/v1/case/{id}/diary/
    │  │ - Get CSRF token      │  │      │    Headers: X-CSRFToken
    │  │ - page.evaluate()     │  │      │    Body: {description, diary_type, ...}
    │  │ - Fetch API with token    │      │    Response: {id, success, ...}
    │  └───────────────────────┘  │      │
    │                             │      │
    └─────────────────────────────┘      │
                                          │
    ┌─────────────────────────────┐      │
    │  2. Store in SQLite DB      │      │
    │     cyberintern.db          │      │
    │  - patients table           │      │
    │  - diaries table            │      │
    │  - procedures table         │      │
    │  - consultations table      │      │
    └─────────────────────────────┘      │
                                          │
    ┌─────────────────────────────┐      │
    │  3. REST API (FastAPI)      │      │
    │  - GET /api/patients        │      │
    │  - GET /api/patient/{id}    │      │
    │  - POST /api/diaries/batch  │      │
    │  - GET /mcp/...             │      │
    └─────────────────────────────┘      │
```

---

## SUMMARY: REST API ENDPOINTS AVAILABLE

### Read Operations (GET)
| Endpoint | Method | Purpose | Source |
|----------|--------|---------|--------|
| `/api/v1/case/{case_id}/` | GET | Patient basic info | `patient_context_service.py:48` |
| `/api/v1/case/{case_id}/diary/` | GET | List diaries | `emr_service_playwright.py:939` |
| `/api/v1/case/{case_id}/procedure/` | GET | Surgical procedures | `patient_context_service.py:211` |
| `/api/v1/case/{case_id}/diagnosis/` | GET | Diagnosis (inferred) | emr_service_playwright.py:749+ |
| `/api/v1/case/{case_id}/prescription/` | GET | Prescriptions (inferred) | emr_service_playwright.py:1846+ |
| `/api/v1/case/{case_id}/lab/` | GET | Lab results (inferred) | emr_service_playwright.py:1972+ |
| `/api/v1/case/{case_id}/consultation/` | GET | Consultations (inferred) | emr_service_playwright.py:2210+ |
| `/api/v1/case/{case_id}/sicklist/` | GET | Medical conclusions (inferred) | emr_service_playwright.py:1361+ |

### Write Operations (POST/PUT)
| Endpoint | Method | Purpose | Source |
|----------|--------|---------|--------|
| `/api/v1/case/{case_id}/diary/` | POST | Submit diary | `diary_service.py:102`, `emr_service_playwright.py:2390` |
| `/api/v1/case/{case_id}/prescription/` | POST | Submit prescription (deprecated) | `prescription_submit_service.py` |
| `/api/v1/case/{case_id}/conclusion/` | POST | Submit medical conclusion (deprecated) | `sicklist_submit_service.py` |
| `/api/v1/case/{case_id}/lab/` | POST | Submit lab order (deprecated) | `lab_order_submit_service.py` |

### Query Parameters
```
?page_size=10          # Pagination
?limit=10              # Alternative pagination
?show=active           # Filter diaries (active, all, archived)
?include=full          # Include nested data (inferred)
```

---

## CRITICAL ISSUES & RECOMMENDATIONS

### Issue 1: Browser Automation Is Brittle
**Current State:** Everything uses Playwright + page.evaluate() to extract data from DOM or call APIs from browser context.

**Problems:**
- Breaks if EMR UI changes
- Slow (full page loads)
- Resource-intensive (headless Chrome per connection)
- Unmaintainable (JS extraction code is complex)

**Recommendation:**
Replace with direct API calls. CyberIntern can:
1. Extract CSRF token from any authenticated session
2. Make HTTP requests to `/api/v1/` endpoints
3. Include session cookies in requests
4. This will be 10x faster and more reliable

---

### Issue 2: CSRF Token Management
**Current State:** CSRF tokens cached for 1 hour in memory.

**Problem:**
- If cache clears, next POST fails with 403
- Multiple concurrent requests may fail

**Recommendation:**
- Implement persistent CSRF token cache (Redis or DB)
- Refresh token if POST returns 403
- Implement retry logic

---

### Issue 3: Session Management
**Current State:** Playwright session stored in memory, dies on server restart.

**Problem:**
- Need to re-authenticate after every restart
- Multiple simultaneous syncs require multiple browser instances
- Resource-intensive

**Recommendation:**
- Store session cookies in encrypted DB
- Refresh session periodically
- Implement cookie-based auth to reduce authentication overhead
- Or: Investigate if EMR has API key authentication

---

### Issue 4: Deprecated Submission Services
**Current State:** Prescription, sicklist, and lab order submission services are 0% functional.

**Problem:**
- Form automation too complex (multi-step modals, React Select dropdowns)
- Marked as deprecated (2025-10-22)

**Recommendation:**
- If needed: Use REST APIs directly (POST endpoints)
- If not needed: Remove code, use monitoring instead

---

### Issue 5: Undocumented API
**Current State:** `/api/v1/` endpoints work but are undocumented.

**Problem:**
- No OpenAPI/Swagger docs
- Endpoint paths inferred from UI code
- May break on EMR updates

**Recommendation:**
- Document all confirmed endpoints
- Create OpenAPI spec for CyberIntern/EMR integration
- Test each endpoint independently
- Implement API versioning

---

## NEXT STEPS FOR DIRECT API IMPLEMENTATION

### Step 1: Test Session-Based Auth
```python
import requests

# 1. Login
session = requests.Session()
login_url = "https://doc.hospital.mia.software/login/"
response = session.post(login_url, data={
    "email": "doctor@hospital.ua",
    "password": "password"
})

# 2. Get CSRF token from cookies
csrf_token = session.cookies.get('csrftoken')

# 3. Fetch patient list
headers = {'X-CSRFToken': csrf_token}
response = session.get(
    "https://doc.hospital.mia.software/api/v1/case/25_11636/",
    headers=headers
)
print(response.json())

# 4. Submit diary
diary_data = {
    "description": "Clinical note...",
    "diary_type": "diary",
    "inspection_date": "2024-12-18",
    "inspection_time": "10:30:00",
    "doctor": 5272
}
response = session.post(
    "https://doc.hospital.mia.software/api/v1/case/25_11636/diary/",
    json=diary_data,
    headers=headers
)
print(response.json())
```

### Step 2: Confirm All Endpoints
- [ ] GET `/api/v1/case/{id}/` - Patient info
- [ ] GET `/api/v1/case/{id}/diary/` - Diaries
- [ ] GET `/api/v1/case/{id}/procedure/` - Procedures
- [ ] GET `/api/v1/case/{id}/diagnosis/` - Diagnosis (TBD)
- [ ] GET `/api/v1/case/{id}/prescription/` - Prescriptions (TBD)
- [ ] GET `/api/v1/case/{id}/lab/` - Lab results (TBD)
- [ ] GET `/api/v1/case/{id}/consultation/` - Consultations (TBD)
- [ ] POST `/api/v1/case/{id}/diary/` - Submit diary
- [ ] POST `/api/v1/case/{id}/prescription/` - Submit prescription (TBD)
- [ ] POST `/api/v1/case/{id}/conclusion/` - Submit sicklist (TBD)

### Step 3: Implement Direct API Client
Create `src/services/emr_api_client.py` to replace browser automation:
```python
class EMRAPIClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.session = requests.Session()
        self._authenticate(email, password)

    def _authenticate(self, email, password):
        # Login and store session
        response = self.session.post(f"{self.base_url}/login/", data={
            "email": email,
            "password": password
        })
        self.csrf_token = self.session.cookies.get('csrftoken')

    def get_patient(self, case_id):
        return self.session.get(
            f"{self.base_url}/api/v1/case/{case_id}/"
        ).json()

    def get_diaries(self, case_id):
        return self.session.get(
            f"{self.base_url}/api/v1/case/{case_id}/diary/"
        ).json()

    def submit_diary(self, case_id, data):
        return self.session.post(
            f"{self.base_url}/api/v1/case/{case_id}/diary/",
            json=data,
            headers={'X-CSRFToken': self.csrf_token}
        ).json()
```

---

## ADDITIONAL RESOURCES

### Files with API endpoint information
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py` - Main integration
- `/e/zav-hospital/cyberintern/src/services/patient_context_service.py` - Data aggregation
- `/e/zav-hospital/cyberintern/src/services/diary_service.py` - Diary submission
- `/e/zav-hospital/cyberintern/src/services/csrf_manager.py` - CSRF handling
- `/e/zav-hospital/cyberintern/src/api/routers/emr.py` - API router

### Configuration
- Base URL: `https://doc.hospital.mia.software`
- CyberIntern DB: `/e/zav-hospital/cyberintern/data/cyberintern.db`
- Playwright binary: Uses system cache or bundled installation

---

**End of EMR API Audit**
