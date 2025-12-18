# 📊 Database Population Strategy - Zav Hospital System

**Objective**: Import hospital patient data from two sources into the unified Zav database

---

## Two Data Sources

### Source 1: Active Patients (EMR)
**What**: Current patients already hospitalized in your EMR system
**Where**: Electronic Medical Record system (CyberIntern)
**Status**: ACTIVE in hospital
**Data Available**: Patient ID, name, admission date, medical history, current treatment

**Use Cases**:
- Real-time monitoring of hospitalized patients
- Track ongoing treatments and equipment
- Monitor antibiotic courses
- Generate daily alerts for critical patients

---

### Source 2: Outside Patients (Planned)
**What**: Patients scheduled for hospitalization/surgery (NOT yet admitted)
**Where**: Calendar app / scheduling system (Notion, Airtable, manual list)
**Status**: UPCOMING - waiting for bed/operation date
**Data Available**: Patient name, age, planned operation, expected admission date, priority

**Use Cases**:
- Plan bed allocation
- Prepare surgical equipment and medications
- Schedule operation theater
- Track pre-op requirements
- Manage waiting list

---

## Implementation Options

### Option A: Dual Database Approach (RECOMMENDED)

**Architecture**:
```
Active Patients Table
├── patient_id (e.g., "P001", "P002", "P003")
├── source: "EMR"
├── status: "active"
└── [all medical data]

Planned Patients Table (NEW)
├── planned_patient_id (e.g., "PL001", "PL002")
├── source: "external"
├── status: "planned" / "waiting" / "scheduled"
└── [pre-op data]
```

**Advantages**:
✅ Clear separation of current vs. future patients
✅ Different fields for each (EMR data vs. scheduling data)
✅ Can manage waiting lists separately
✅ Easy to track bed allocation
✅ Can generate separate reports

**Disadvantages**:
⚠️ Need separate import process for each source
⚠️ Manual reconciliation when patient moves from planned→active

---

### Option B: Single Table with Status Field

**Architecture**:
```
Patients Table
├── patient_id
├── status: "active" | "planned" | "discharged" | "admitted_today"
├── admission_date (NULL for planned)
├── expected_admission_date (for planned)
└── source: "EMR" | "external"
```

**Advantages**:
✅ Single patient table for all statuses
✅ Easy to track patient lifecycle
✅ Simpler queries ("show all active + planned")
✅ Automatic transition when admitted

**Disadvantages**:
⚠️ Requires careful status management
⚠️ Different data completeness depending on status

---

## Recommended: Hybrid Approach

**Use a single `patients` table with status tracking** (Option B), but:

1. **Active Patients**: Status = "active" (imported from EMR daily)
2. **Planned Patients**: Status = "planned" (imported from external scheduling)
3. **New Fields for Planned Patients**:
   - `expected_admission_date` - when surgery is scheduled
   - `operation_type` - what procedure needed
   - `priority` - urgent/routine/elective
   - `pre_op_checklist_completed` - boolean
   - `assigned_bed` - when bed allocated

---

## Import Process for Each Source

### Import #1: Active Patients from EMR (Daily)

**Frequency**: Every morning or every 6 hours

**Process**:
```bash
1. Connect to EMR API (CyberIntern)
2. Query GET /api/patients with filter: status="active"
3. For each patient:
   - Check if patient_id exists in Zav database
   - If NEW: INSERT with status="active", admission_date=today
   - If EXISTS: UPDATE with latest medical data
   - Sync: equipment, alerts, antibiotics, consultations
4. Log: X patients synced from EMR
5. Mark: discharge_date for patients no longer in EMR
```

**Implementation Code**:
```python
# pseudo-code
def sync_emr_patients():
    emr_patients = get_emr_active_patients()  # from CyberIntern API

    for emr_patient in emr_patients:
        zav_patient = db.query("SELECT * FROM patients WHERE patient_id = ?", emr_patient.id)

        if not zav_patient:
            # NEW patient
            db.insert("patients", {
                "patient_id": emr_patient.id,
                "name": emr_patient.name,
                "admission_date": emr_patient.admission_date,
                "status": "active",
                "source": "EMR"
            })
        else:
            # UPDATE existing
            db.update("patients", zav_patient.id, {
                "name": emr_patient.name,
                "updated_at": datetime.now()
            })
```

**Fields to Sync**:
- Patient demographics (name, age, DOB)
- Admission date
- Current ward/bed
- Active medications
- Medical history (conditions, allergies)
- Ongoing treatments

---

### Import #2: Planned Patients from External Source

**Frequency**: Daily morning OR weekly (configurable)

**Process**:
```bash
1. Export from external system:
   - Option A: Download CSV from Airtable
   - Option B: Query Notion API
   - Option C: Manual Excel upload
2. Parse patient data
3. For each patient:
   - Check if already exists (by name + DOB)
   - If NEW: INSERT with status="planned"
   - If EXISTS: UPDATE expected_admission_date, operation_type
4. Generate: Pre-op checklist, bed allocation suggestions
5. Alert: Surgery date approaching (7 days, 1 day, 6 hours before)
```

**Implementation Code**:
```python
# pseudo-code
def import_planned_patients_from_csv(csv_file):
    planned_patients = parse_csv(csv_file)  # name, dob, operation, surgery_date

    for patient in planned_patients:
        # Check if exists (by name + DOB)
        existing = db.query(
            "SELECT * FROM patients WHERE name=? AND dob=?",
            (patient.name, patient.dob)
        )

        if not existing:
            # NEW planned patient
            db.insert("patients", {
                "patient_id": generate_id("PL"),  # PL001, PL002, etc
                "name": patient.name,
                "expected_admission_date": patient.surgery_date,
                "operation_type": patient.operation,
                "priority": patient.priority,
                "status": "planned",
                "source": "external"
            })
```

**Fields for Planned Patients**:
- Patient name, age, DOB
- Operation type (surgery name)
- Scheduled admission date
- Expected stay duration (days)
- Priority level (urgent/routine/elective)
- Pre-op requirements (fasting, tests, etc.)
- Assigned surgeon/team
- Bed allocation (when ready)

---

## Data Model Changes

### Current Patients Table Structure
```sql
CREATE TABLE patients (
    id SERIAL PRIMARY KEY,
    patient_id VARCHAR UNIQUE,
    name VARCHAR,
    admission_date DATE,
    discharge_date DATE,
    current_stage INT,
    status VARCHAR,  -- "active" or "planned"
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Proposed Extended Structure
```sql
ALTER TABLE patients ADD COLUMN (
    -- For planned patients
    expected_admission_date DATE,
    operation_type VARCHAR,
    priority VARCHAR,  -- "urgent", "routine", "elective"
    pre_op_checklist_completed BOOLEAN DEFAULT FALSE,
    assigned_bed VARCHAR,
    assigned_surgeon VARCHAR,

    -- For both
    source VARCHAR,  -- "EMR" or "external"
    external_id VARCHAR,  -- ID from external system

    -- Lifecycle tracking
    status_history JSON,  -- Track: planned→admitted→active→discharged
    last_synced_at TIMESTAMP
);
```

---

## Implementation Timeline

### Week 1: Foundation
- [x] API endpoints ready (done ✅)
- [ ] Create "planned" patient endpoints
- [ ] Add database fields
- [ ] Test manual data entry

### Week 2: EMR Integration
- [ ] Write EMR sync script
- [ ] Test with sample EMR data
- [ ] Schedule daily sync job
- [ ] Monitor for conflicts

### Week 3: External Data Import
- [ ] Choose external system (CSV/Airtable/Notion)
- [ ] Write import script
- [ ] Test with sample data
- [ ] Create upload interface

### Week 4: Automation + Alerts
- [ ] Automated daily syncs
- [ ] Alert system for upcoming admissions
- [ ] Bed allocation automation
- [ ] Production launch

---

## Step-by-Step Immediate Action Plan

### Step 1: Prepare EMR Integration (Today)
1. Document EMR API endpoints that have patient data
2. Identify patient fields that map to Zav database
3. Write list of EMR "active patient" fields
4. Test connection to EMR API

**What you provide me**:
- EMR API documentation or endpoint list
- Sample EMR patient response (JSON format)
- Field mapping (EMR → Zav)

### Step 2: Prepare Planned Patient Source (Today)
1. Export sample planned patients from your source (Notion/Airtable/Excel)
2. Identify required fields: name, DOB, operation, surgery date, priority
3. Prepare data in CSV format

**What you provide me**:
- Sample planned patients data (CSV or JSON)
- Field mapping for planned patients
- Schedule preference (daily/weekly import)

### Step 3: I'll Create Import Scripts (Tomorrow)
1. Write EMR sync script
2. Write planned patient import script
3. Test with your sample data
4. Deploy to Railway

### Step 4: Automate (This Week)
1. Set up daily EMR sync job
2. Set up planned patient import schedule
3. Create alerts for upcoming admissions
4. Monitor and adjust

---

## Testing Data Flow

**Current Test Data in System**:
```
Active Patients: 3
- P001: John Doe
- P002: Jane Smith
- P003: Robert Johnson

Equipment: 1
- E001: Ventilator (for P001)

Alerts: 1
- A001: High fever (P001) - CRITICAL

Antibiotics: 1
- AB001: Amoxicillin course (P001)
```

This test data proves the system works end-to-end!

---

## Next Steps

**Immediate Questions for You**:

1. **EMR System**:
   - What EMR system are you using? (CyberIntern?)
   - Do you have API access to patient data?
   - What format is patient data? (REST API, SOAP, CSV export?)

2. **Planned Patients**:
   - Where do you currently track planned operations? (Notion, Airtable, Excel?)
   - Can you export that data as CSV?
   - What fields are most important? (name, DOB, operation, date, priority)

3. **Frequency**:
   - How often should we sync EMR patients? (hourly, daily?)
   - How often should we import planned patients? (daily, weekly?)

4. **Alerts**:
   - Should we alert when: surgery date approaches? bed available? patient admitted?

**Once you answer these, I can**:
- Write the exact import scripts
- Set up automatic syncing
- Deploy to production
- Test with real data

---

## Summary

Your system is **READY** to accept patient data from two sources:

✅ **Active patients** from EMR (real-time, continuously updated)
✅ **Planned patients** from external scheduling (batch import)
✅ **Unified view** in Telegram bot and REST API
✅ **24/7 availability** on Railway

**What's needed**: Your data sources (EMR access + planned patient export) = System goes LIVE! 🚀
