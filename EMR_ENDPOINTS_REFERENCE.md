# EMR REST API Endpoints - Complete Reference

**Target System:** doc.hospital.mia.software
**Base URL:** `https://doc.hospital.mia.software`
**Date:** 2026-02-13
**Status:** Discovered via CyberIntern source code audit

---

## AUTHENTICATION

### Login Endpoint
```http
POST /login/ HTTP/1.1
Host: doc.hospital.mia.software
Content-Type: application/x-www-form-urlencoded

email=doctor@hospital.ua&password=secure_password
```

**Response:**
- Cookies set: `sessionid`, `csrftoken`
- Redirect to: `/role-choose/{role_id}/?next=...`

### Role Selection
```http
GET /role-choose/{role_id}/?next= HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...; csrftoken=...
```

**Parameters:**
- `role_id`: Department role (e.g., `23622` for Trauma)
- `next`: Redirect URL (optional)

**Response:**
- Redirect to dashboard or specified URL
- Session is now authenticated for that role

---

## CONFIRMED API ENDPOINTS

### 1. Get Patient Information
```http
GET /api/v1/case/{case_id}/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

{
  "id": "25_11636",
  "full_name": "Бурковський О.С.",
  "short_name": "Б.О.С.",
  "number": "25/2024",
  "birthday": "1985-03-15",
  "gender": "M",
  "phone": "+380501234567",
  "address": "вул. Героїв, 10, Кривий Ріг, 50000",
  "workplace": "ЛТД 'Арселор Мітталь'",
  "contingent": "цивільне",
  "social_status": "робітник",
  "bed": "15",
  "division": "Травматологія",
  "ward": "2",
  "admission_date": "2024-11-20",
  "discharge_date": null,
  "trauma_date": "2024-11-18",
  "ehealth_id": "..."
}
```

**Source Code:**
- `/e/zav-hospital/cyberintern/src/services/patient_context_service.py:48`
- Used in: `get_patient_basic_info()`

**Response Fields:**
| Field | Type | Notes |
|-------|------|-------|
| id | string | Unique case ID (format: `25_11636`) |
| full_name | string | Full patient name (ПІБ) |
| number | string | Medical record number |
| birthday | string | YYYY-MM-DD |
| gender | string | M or F |
| workplace | string | Employer name |
| admission_date | string | YYYY-MM-DD |
| discharge_date | string or null | null if still hospitalized |
| trauma_date | string | Injury date |

---

### 2. Get Diaries / Medical Notes
```http
GET /api/v1/case/{case_id}/diary/?page_size=10&show=active HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

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
    }
  ]
}
```

**Source Code:**
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:939`
- Used in: `fetch_diaries()` method

**Query Parameters:**
| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| page_size | int | 10 | Records per page |
| show | string | active | Options: active, all, archived |
| limit | int | - | Alternative to page_size |

**Response Fields:**
| Field | Type | Notes |
|-------|------|-------|
| id | int | Diary ID in EMR |
| inspection_date | string | YYYY-MM-DD |
| inspection_time | string | HH:MM:SS (24-hour) |
| doctor_name | string | Signing doctor |
| doctor_id | int | Doctor's ID |
| description | string | Diary text content (can be HTML or plain text) |
| diary_type | string | diary, lkk, preop, postop, discharge |
| status | string | active, archived, etc |

---

### 3. Submit Diary / Medical Note
```http
POST /api/v1/case/{case_id}/diary/ HTTP/1.1
Host: doc.hospital.mia.software
Content-Type: application/json
X-CSRFToken: {csrf_token}
Cookie: sessionid=...

{
  "description": "Клінічне дослідження: стан задовільний. Пульс 82, АТ 130/85. Рана чиста, без ознак запалення. Осередків больності нема. Рекомендовано продовжити консервативне лікування.",
  "diary_type": "diary",
  "inspection_date": "2024-12-18",
  "inspection_time": "10:30:00",
  "doctor": 5272
}

Response (201 Created):
{
  "id": 55555,
  "success": true,
  "inspection_date": "2024-12-18",
  "inspection_time": "10:30:00",
  "doctor": 5272,
  "description": "..."
}
```

**Source Code:**
- `/e/zav-hospital/cyberintern/src/services/diary_service.py:102`
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:2390`

**Request Headers:**
```
X-CSRFToken: {csrf_token}          # REQUIRED - see CSRF section below
Content-Type: application/json
```

**Request Body Fields:**
| Field | Type | Required | Notes |
|-------|------|----------|-------|
| description | string | yes | Diary text (plain text or HTML) |
| diary_type | string | yes | diary, lkk, preop, postop, discharge |
| inspection_date | string | yes | YYYY-MM-DD format |
| inspection_time | string | yes | HH:MM:SS (24-hour) |
| doctor | int | yes | Doctor ID (must be integer, not string) |

**Response (Success 200/201):**
```json
{
  "id": 55555,
  "success": true,
  "inspection_date": "2024-12-18",
  "inspection_time": "10:30:00"
}
```

**Response (Error 400):**
```json
{
  "error": "Invalid inspection_date format",
  "detail": "..."
}
```

**Response (Error 403):**
```json
{
  "error": "Invalid CSRF token"
}
```

**Diary Types:**
| Type | Usage |
|------|-------|
| diary | Regular daily examination note |
| lkk | Medical commission (ЛКК) |
| preop | Pre-operative assessment |
| postop | Post-operative assessment |
| discharge | Discharge summary |

**CSRF Token Handling:**
See CSRF section below for how to extract and refresh tokens.

---

### 4. Get Surgical Procedures
```http
GET /api/v1/case/{case_id}/procedure/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

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
            {"full_name": "Асистент 1", "id": 9999}
          ],
          "nurses": [
            {"full_name": "Медсестра", "id": 8888}
          ],
          "anesthesia": "epidural",
          "surgery_time": "2024-11-20 14:30:00",
          "duration": "45",
          "anesthesia_duration": "60",
          "complications": [],
          "equipments": []
        }
      ],
      "diagnosis_before_icd10am": {"text": "S06.9"},
      "diagnosis_after_icd10am": {"text": "S06.9"}
    }
  ]
}
```

**Source Code:**
- `/e/zav-hospital/cyberintern/src/services/patient_context_service.py:211`
- Used in: `get_procedures()` method

**Response Fields:**
| Field | Type | Notes |
|-------|------|-------|
| status | string | completed, planned, cancelled |
| surgeries | array | List of surgical procedures |
| surgery_time | string | ISO datetime |
| duration | string | Minutes as string |
| anesthesia | string | Type of anesthesia |
| complications | array | Complication descriptions |
| equipments | array | Equipment used |

---

## INFERRED (NOT YET CONFIRMED) ENDPOINTS

### Get Diagnosis
```http
GET /api/v1/case/{case_id}/diagnosis/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

{
  "diagnosis": "Закрита ЧМТ легкого ступеня",
  "diagnosis_icd10": "S06.9"
}
```

**Source Code Reference:**
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:749-907`
- Currently fetched via page navigation + tab click + JavaScript extraction
- **Not yet tested as direct API call**

---

### Get Prescriptions
```http
GET /api/v1/case/{case_id}/prescription/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

{
  "results": [
    {
      "id": 11111,
      "medication_name": "Аспірин",
      "dosage": "500мг",
      "frequency": "3 times daily",
      "start_date": "2024-11-20",
      "end_date": "2024-12-04",
      "status": "active"
    }
  ]
}
```

**Source Code Reference:**
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:1846-1970`
- Currently fetched via page navigation + tab click + JavaScript extraction
- **Not yet tested as direct API call**

---

### Get Lab Results
```http
GET /api/v1/case/{case_id}/lab/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

{
  "results": [
    {
      "id": 11111,
      "test_name": "Загальний аналіз крові (ЗАК)",
      "test_code": "OBC",
      "date": "2024-12-17",
      "status": "completed",
      "normal": false
    }
  ]
}
```

**Source Code Reference:**
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:1972-2114`
- Currently fetched via page navigation + tab click + JavaScript extraction
- **Not yet tested as direct API call**

---

### Get Consultations
```http
GET /api/v1/case/{case_id}/consultation/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

{
  "results": [
    {
      "id": 33333,
      "specialty": "Ортопедія",
      "doctor_name": "Спеціаліст О.В.",
      "date": "2024-12-15",
      "status": "completed",
      "notes": "..."
    }
  ]
}
```

**Source Code Reference:**
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:2210-2280`
- Currently fetched via page navigation + tab click + JavaScript extraction
- **Not yet tested as direct API call**

---

### Get Medical Conclusions / Sicklists
```http
GET /api/v1/case/{case_id}/conclusion/ HTTP/1.1
Host: doc.hospital.mia.software
Cookie: sessionid=...

{
  "results": [
    {
      "id": 22222,
      "conclusion_number": "ВЛ 450/24",
      "type": "temporary_disability",
      "status": "active",
      "start_date": "2024-11-20",
      "end_date": "2024-12-04",
      "diagnosis": "Закрита ЧМТ легкого ступеня"
    }
  ]
}
```

**Source Code Reference:**
- `/e/zav-hospital/cyberintern/src/services/emr_service_playwright.py:1361-1844`
- Currently fetched via page navigation + tab click + JavaScript extraction
- **Not yet tested as direct API call**

---

## PAGE-BASED NAVIGATION (NOT APIs)

These are web page URLs used for browser automation. They return HTML, not JSON.

### Patient List Pages
```
GET /case/my-patients/hospitalized/
GET /case/my-patients/discharged/
GET /case/all/
```

### Patient Case Page (Hub)
```
GET /case/{case_id}/
GET /case/{case_id}/#/medical-conclusions
GET /case/{case_id}/#/consultations
```

### Search
```
GET /search?q={patient_name}
```

---

## CSRF TOKEN MANAGEMENT

### How CSRF Works
1. **Token Source:** Stored in page DOM or cookies
2. **Token Validity:** 1 hour default
3. **Token Location:** Cookie `csrftoken` + in page HTML meta tag
4. **Token Usage:** Must be sent in `X-CSRFToken` header for POST/PUT/DELETE

### Token Extraction (Current Implementation)
```python
# From csrf_manager.py
csrf_token = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
# OR from form input
csrf_token = document.querySelector('input[name="_csrf_token"]')?.value;
```

**Source Code:**
- `/e/zav-hospital/cyberintern/src/services/csrf_manager.py:153`
- Cache duration: 3600 seconds (1 hour)

### Token Refresh Strategy
If you get `403 Forbidden` with message "Invalid CSRF token":
1. Navigate to any authenticated page (e.g., `/case/{case_id}/`)
2. Wait for page load
3. Extract new CSRF token from page DOM
4. Retry the request with new token

---

## HTTP STATUS CODES

| Code | Meaning | Example |
|------|---------|---------|
| 200 | OK | GET successful, diary retrieved |
| 201 | Created | POST diary succeeded, new diary created |
| 400 | Bad Request | Missing field, invalid format |
| 401 | Unauthorized | Not logged in |
| 403 | Forbidden | Invalid CSRF token, no permission |
| 404 | Not Found | Patient/diary does not exist |
| 500 | Server Error | EMR error |

---

## COMMON RESPONSE PATTERNS

### Success Response (GET)
```json
{
  "id": 123,
  "field1": "value1",
  "field2": "value2"
}
```

### List Response (GET)
```json
{
  "count": 50,
  "next": "?page=2",
  "previous": null,
  "results": [
    {"id": 1, ...},
    {"id": 2, ...}
  ]
}
```

### Success Response (POST)
```json
{
  "id": 123,
  "success": true,
  "message": "Created successfully"
}
```

### Error Response
```json
{
  "error": "Field required: description",
  "detail": "The description field cannot be empty"
}
```

---

## IMPLEMENTATION EXAMPLE (Python requests)

```python
import requests
from datetime import datetime

# 1. Login
session = requests.Session()
session.post(
    'https://doc.hospital.mia.software/login/',
    data={
        'email': 'doctor@hospital.ua',
        'password': 'password123'
    }
)

# Get CSRF token from cookies
csrf_token = session.cookies.get('csrftoken')

# 2. Fetch patient info
response = session.get(
    'https://doc.hospital.mia.software/api/v1/case/25_11636/'
)
patient = response.json()
print(f"Patient: {patient['full_name']}")

# 3. Fetch recent diaries
response = session.get(
    'https://doc.hospital.mia.software/api/v1/case/25_11636/diary/',
    params={'page_size': 5, 'show': 'active'}
)
diaries = response.json()
print(f"Diaries: {diaries['count']}")

# 4. Submit new diary
diary_data = {
    'description': 'Patient stable, continuing treatment',
    'diary_type': 'diary',
    'inspection_date': datetime.now().strftime('%Y-%m-%d'),
    'inspection_time': datetime.now().strftime('%H:%M:%S'),
    'doctor': 5272
}
response = session.post(
    'https://doc.hospital.mia.software/api/v1/case/25_11636/diary/',
    json=diary_data,
    headers={'X-CSRFToken': csrf_token}
)
if response.status_code == 201:
    print(f"Diary created: {response.json()['id']}")
else:
    print(f"Error: {response.text}")
```

---

## KEY IMPLEMENTATION FILES

| File | Purpose | Key Classes |
|------|---------|------------|
| `src/services/emr_service_playwright.py` | Main EMR automation | `EMRPlaywrightService` |
| `src/services/patient_context_service.py` | Patient data aggregation | `PatientContextService` |
| `src/services/diary_service.py` | Diary submission | `DiaryService` |
| `src/services/csrf_manager.py` | CSRF token caching | `CSRFTokenManager` |
| `src/api/routers/emr.py` | API endpoints | EMR sync routes |

---

## NEXT STEPS FOR API INTEGRATION

### Phase 1: Validate Endpoints
- [ ] Test `/api/v1/case/{id}/` (patient info)
- [ ] Test `/api/v1/case/{id}/diary/` GET (list)
- [ ] Test `/api/v1/case/{id}/diary/` POST (create)
- [ ] Test `/api/v1/case/{id}/procedure/` (procedures)
- [ ] Test `/api/v1/case/{id}/diagnosis/` (diagnosis)
- [ ] Test `/api/v1/case/{id}/prescription/` (prescriptions)
- [ ] Test `/api/v1/case/{id}/lab/` (labs)
- [ ] Test `/api/v1/case/{id}/consultation/` (consultations)

### Phase 2: Replace Playwright
Create new `EMRAPIClient` class:
```python
class EMRAPIClient:
    def __init__(self, base_url, email, password):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.post(f"{base_url}/login/", data={"email": email, "password": password})
        self.csrf_token = self.session.cookies.get('csrftoken')

    def get_patient(self, case_id):
        return self.session.get(f"{self.base_url}/api/v1/case/{case_id}/").json()

    def get_diaries(self, case_id, limit=10):
        return self.session.get(
            f"{self.base_url}/api/v1/case/{case_id}/diary/",
            params={'page_size': limit}
        ).json()

    def submit_diary(self, case_id, data):
        return self.session.post(
            f"{self.base_url}/api/v1/case/{case_id}/diary/",
            json=data,
            headers={'X-CSRFToken': self.csrf_token}
        ).json()
```

### Phase 3: Deprecate Playwright
- Remove `EMRPlaywrightService` usage
- Update all imports to use `EMRAPIClient`
- Clean up browser automation code

---

**End of EMR Endpoints Reference**
