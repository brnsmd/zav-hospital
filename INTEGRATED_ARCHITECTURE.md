# 🏥 Zav Integrated Architecture - Two-Source Real-Time System

**Status**: READY TO BUILD
**Architecture**: Cyberintern MCP + Google Sheets MCP + Zav DB + Claude
**Approach**: Free, automated, collaborative

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                     CLAUDE INTERFACE                             │
│              (Daily decision-making & analysis)                  │
└─────────────┬──────────────────────────────────────┬─────────────┘
              │                                      │
         ┌────▼─────────┐                  ┌────────▼────────┐
         │ Cyberintern  │                  │ Google Sheets   │
         │ MCP          │                  │ MCP             │
         │ (Active)     │                  │ (Planned)       │
         └────┬─────────┘                  └────────┬────────┘
              │                                     │
              └─────────────────┬───────────────────┘
                                │
                        ┌───────▼───────┐
                        │  Zav Database │
                        │ (Interventions│
                        │  & Alerts)    │
                        └───────┬───────┘
                                │
            ┌───────────────────┼───────────────────┐
            │                   │                   │
       ┌────▼─────┐    ┌────────▼────────┐   ┌─────▼────────┐
       │ Telegram │    │   REST API      │   │  Daily Sync  │
       │  Bot     │    │   Endpoints     │   │   Job (5 AM) │
       └──────────┘    └─────────────────┘   └──────────────┘
```

---

## Data Flow - Daily Cycle

### **5:00 AM - Automated Sync Job**
```
1. Fetch from Cyberintern MCP:
   - All active patients
   - Admission dates
   - Current status
   - Medical history

2. Fetch from Google Sheets:
   - Planned patients (new requests)
   - Proposed allocations
   - Operation dates
   - Pre-op status

3. Update Zav Database:
   - Patient master data
   - Status: active/planned/discharged
   - Equipment assignments
   - Alert updates

4. Generate Summary:
   - X active patients
   - Y planned patients
   - Z pending requests
   - Alerts: critical, urgent
```

### **9:00 AM - User Opens Claude**
```
Claude automatically:

1. Fetches fresh data:
   - Query Cyberintern MCP → active patients
   - Read Google Sheets → planned patients
   - Query Zav DB → equipment/alerts/meds

2. Analyzes & Proposes:
   ✓ Discharge recommendations
   ✓ Admission recommendations
   ✓ Bed allocation
   ✓ Operation scheduling
   ✓ Equipment needs
   ✓ Pre-op checklist items

3. Presents to User:
   "Active: 12 patients | Planned: 5 patients | Pending: 2 requests"
   [Detailed proposals for each]

4. Waits for User Decision:
   - User reviews proposals
   - User modifies/confirms
   - User comments/notes
```

### **Throughout Day - Telegram Bot**
```
Doctor encounters external patient:

1. Doctor: /external-patient Ahmed Ali, 45, appendectomy
2. Bot stores in Google Sheets: "New Requests" tab
3. Bot acknowledges: "Patient request recorded. Review in Claude."
4. Entry waits for next Claude review (5 AM sync or manual check)
```

### **Evening - Final Updates**
```
User confirms proposals in Claude:

1. Claude updates Google Sheets:
   - Mark planned patients: admitted/scheduled
   - Update allocation decisions

2. Claude updates Zav DB:
   - Create patient records
   - Assign beds
   - Schedule operations
   - Flag needed equipment

3. Claude sends Telegram alerts:
   - Staff: "Prepare bay 3 for operation tomorrow"
   - Equipment team: "Get ventilator for bed 2"
   - Pre-op: "Ahmed Ali fasting from midnight"
```

---

## Google Sheets Structure

### **Workbook: "Zav Hospital - Patient Management"**

#### **Sheet 1: Active Patients (Auto-synced from Cyberintern)**
```
| Patient ID | Name | Age | Admission Date | Ward | Bed | Status | Discharge Date | Notes |
|------------|------|-----|----------------|------|-----|--------|----------------|-------|
| P001       | John Doe | 65 | 2025-12-18 | ICU | 3 | critical | | Post-op day 2 |
| P002       | Jane Smith | 42 | 2025-12-17 | Ward A | 5 | stable | 2025-12-22 | Ready for discharge |
```

#### **Sheet 2: Planned Patients (Manual + Telegram)**
```
| Patient ID | Name | Age | DOB | Operation | Planned Date | Priority | Status | Pre-op Done? | Comments |
|------------|------|-----|-----|-----------|--------------|----------|--------|--------------|----------|
| PL001      | Ahmed Ali | 45 | 1980-03-15 | Appendectomy | 2025-12-25 | Urgent | approved | NO | Requested today |
| PL002      | Maria Garcia | 58 | 1967-02-20 | Gallbladder | 2025-12-26 | Routine | pending | NO | Waiting bed |
```

#### **Sheet 3: New Requests (from Telegram Bot)**
```
| Timestamp | Doctor | Patient Name | Age | Operation | Notes | Status |
|-----------|--------|--------------|-----|-----------|-------|--------|
| 09:15 | Dr. Ahmed | Ahmed Ali | 45 | Appendectomy | Acute appendicitis | pending_review |
| 10:30 | Dr. Sara | Maria Garcia | 58 | Gallbladder | Chronic cholecystitis | pending_review |
```

#### **Sheet 4: Allocations (Proposed by Claude)**
```
| Patient ID | Name | Operation | Proposed Date | Proposed Time | Bay | Surgeon | Anesthetist | Equipment Needed | Status |
|------------|------|-----------|----------------|---------------|-----|---------|-------------|-----------------|--------|
| PL001      | Ahmed Ali | Appendectomy | 2025-12-25 | 09:00 | 2 | Dr. Hassan | Dr. Layla | Ventilator, Monitor | proposed |
| PL002      | Maria Garcia | Gallbladder | 2025-12-26 | 14:00 | 3 | Dr. Noor | Dr. Ahmed | Endoscope, Monitor | proposed |
```

#### **Sheet 5: Discharge Planning**
```
| Patient ID | Name | Current Status | Recommended Discharge | Reason | Follow-up | Notes |
|------------|------|----------------|----------------------|--------|-----------|-------|
| P002       | Jane Smith | stable | 2025-12-22 | Post-op day 5, recovering well | Clinic day 10 | |
```

---

## Telegram Bot Integration

### **New Command: /external-patient**

**Syntax**:
```
/external-patient [name], [age], [operation], [details]
```

**Examples**:
```
/external-patient Ahmed Ali, 45, Appendectomy, acute appendicitis, needs urgent surgery
/external-patient Maria Garcia, 58, Gallbladder removal, chronic pain, scheduled for next week
```

**Bot Response**:
```
✅ Patient request recorded!

Patient: Ahmed Ali, 45
Operation: Appendectomy
Request Time: 2025-12-18 09:15

📋 Status: Awaiting review
⏰ Next Claude review: Today at 5 AM or when user opens Claude
💬 Message will appear in "New Requests" tab in Google Sheets
```

### **Existing Commands Enhanced**:
```
/patients → Show all active patients (from Cyberintern)
/planned  → Show all planned patients (from Sheets)
/pending  → Show pending external requests (from Sheets)
/alerts   → Show critical alerts
/beds     → Show bed occupancy (calculated from Cyberintern + Zav)
/discharge → Show discharge recommendations
```

---

## Claude's Daily Analysis

### **What Claude Does When User Opens It**

```python
# Pseudo-code for Claude's analysis

def analyze_hospital_state():
    # 1. Fetch active patients from Cyberintern MCP
    active_patients = cyberintern_mcp.get_active_patients()
    # Result: [P001: John Doe (ICU, day 2 post-op), P002: Jane Smith (Ward, ready)]

    # 2. Fetch planned patients from Google Sheets
    planned_patients = sheets_mcp.read_sheet("Planned Patients")
    # Result: [PL001: Ahmed Ali (appendectomy, 2025-12-25), ...]

    # 3. Fetch new requests from Sheets
    new_requests = sheets_mcp.read_sheet("New Requests")
    # Result: [Ahmed Ali (9:15), Maria Garcia (10:30)]

    # 4. Query Zav DB for equipment status
    equipment = zav_db.get_equipment_available()
    # Result: [Ventilator x2, Monitor x5, Endoscope x1]

    # 5. Analyze & Propose
    analysis = {
        "discharge_ready": [P002],  # Jane can go home
        "admit_urgent": [PL001],    # Ahmed needs surgery ASAP
        "admit_planned": [PL002],   # Maria next week
        "equipment_gaps": [],        # All needed equipment available
        "critical_alerts": [],       # None
    }

    # 6. Present to user with specific proposals
    return analysis
```

### **Example Output Format**

```
🏥 HOSPITAL STATE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 CURRENT STATUS
• Active Patients: 12 (ICU:3, Ward:9)
• Planned Patients: 5
• Pending Requests: 2 (NEW)
• Available Beds: 3
• Discharge Ready: 1

━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ RECOMMENDATIONS

1. DISCHARGE TODAY
   • Jane Smith (P002)
   • Ward A, Bed 5
   • Post-op day 5, fully recovered
   • Action: Discharge paperwork + follow-up clinic

2. ADMIT URGENT (This Week)
   • Ahmed Ali (NEW REQUEST)
   • Acute appendicitis
   • Recommend: Admission 2025-12-25, Operation 2025-12-25 09:00
   • Bay: 2 (has ventilator)
   • Surgeon: Dr. Hassan

3. ADMIT PLANNED (Next Week)
   • Maria Garcia (NEW REQUEST)
   • Chronic gallbladder issue
   • Recommend: Admission 2025-12-26, Operation 2025-12-26 14:00
   • Bay: 3 (has endoscope)

━━━━━━━━━━━━━━━━━━━━━━━━━━

⚠️ ALERTS
• None critical
• Equipment ready for all planned operations

━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 NEXT STEPS
1. Confirm discharge: Jane Smith
2. Approve admission: Ahmed Ali (urgent)
3. Approve admission: Maria Garcia (planned)
4. Update: Yes/No/Modify?
```

---

## Implementation Steps

### **Phase 1: Setup (Today)**

- [x] ✅ Google Sheets MCP installed
- [ ] Create Google Sheet "Zav Hospital - Patient Management" with 5 sheets
- [ ] Create Telegram bot `/external-patient` command
- [ ] Verify Cyberintern MCP access
- [ ] Test MCP connections

### **Phase 2: Integration (Tomorrow)**

- [ ] Write daily sync script (5 AM job)
- [ ] Create Claude analysis prompt
- [ ] Test data flow: Cyberintern → Zav DB
- [ ] Test data flow: Sheets → Zav DB
- [ ] Test Telegram bot integration

### **Phase 3: Production (This Week)**

- [ ] Schedule daily sync job on Railway
- [ ] Deploy to production
- [ ] Train hospital staff on Telegram bot commands
- [ ] Go live with real data

---

## API Endpoints Needed

### **For Daily Sync Job**

```
GET /api/patients/sync-cyberintern
  - Pull from Cyberintern MCP
  - Update Zav DB with active patients
  - Return: {synced: X, errors: Y}

GET /api/patients/sync-sheets
  - Pull from Google Sheets
  - Update Zav DB with planned patients
  - Return: {synced: X, errors: Y}

POST /api/telegram/external-request
  - Receives external patient request from Telegram
  - Stores in Google Sheets + Zav DB
  - Return: {status: "recorded", request_id: "R123"}
```

---

## Database Schema Updates

### **Add Columns to Patients Table**

```sql
ALTER TABLE patients ADD (
    source VARCHAR,                    -- "cyberintern" or "external"
    external_id VARCHAR,               -- ID from source system
    operation_type VARCHAR,            -- For planned patients
    planned_admission_date DATE,       -- When they should come
    planned_operation_date DATE,       -- When surgery scheduled
    priority VARCHAR,                  -- "urgent", "routine", "elective"
    pre_op_checklist_completed BOOLEAN,
    assigned_surgeon VARCHAR,
    assigned_bay INT,
    last_synced_at TIMESTAMP
);
```

---

## Cost Analysis

- **Google Sheets**: ✅ FREE (1 sheet, unlimited rows)
- **Cyberintern MCP**: ✅ FREE (read-only access)
- **Railway**: ✅ $5/month (already included)
- **Telegram Bot**: ✅ FREE
- **Claude**: ✅ Depends on API usage (minimal for daily analysis)

**Total Additional Cost**: $0 🎉

---

## Success Criteria

✅ System is live when:
1. Daily sync runs automatically at 5 AM
2. User opens Claude and sees analysis
3. User confirms proposals
4. Data syncs back to sheets + database
5. Telegram bot receives `/external-patient` requests
6. Doctor sees alerts about bed assignments

---

## Next Question for You

**Do you have a Google Account with access to create a shared sheet?**

Once you provide:
1. Google Sheet URL (we'll create it)
2. Confirmation that Cyberintern MCP is accessible
3. List of Cyberintern patient fields we should pull

I can:
- Set up the sheets structure
- Write the sync scripts
- Deploy everything today
- System goes LIVE today! 🚀

---

**Status**: Architecture designed, ready to build
