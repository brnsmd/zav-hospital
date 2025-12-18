# Zav Daily Report - Full Morning Briefing

Generate a comprehensive daily briefing for the department head (Завідувач).

## Data Collection Steps

### 1. CyberIntern MCP Tools
Use these tools to gather patient data:

- **search_cyberintern** type="patients": Get all current patients
- **get_alerts**: Get all clinical alerts
- **get_doctor_diaries** for each doctor: Documentation status
- **get_lab_results** with abnormal_only=true: Critical lab findings
- **analyze_patient_data** for risk patients: AI analysis

### 2. Zav Cloud (Railway) API
```bash
# Today's consultations
curl -s https://zav-production.up.railway.app/api/consultations?date=today

# All doctors
curl -s https://zav-production.up.railway.app/api/doctors

# Pending external requests
curl -s https://zav-production.up.railway.app/api/patients/pending

# System stats
curl -s https://zav-production.up.railway.app/stats
```

### 3. Compliance Checks
- Discharge queue: Patients discharged but history not signed off
- Documentation: Doctors with missing diary entries
- Prescriptions: Long-running antibiotic courses
- Sicklists: Expiring soon

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  📋 ZAV HOSPITAL │ Daily Report                      ║
║  [Day of week], [Date]                               ║
║  Prepared for: Др. Цапенко Георгій                   ║
╚══════════════════════════════════════════════════════╝
```

### 📊 Department Overview

| Metric | Today | Yesterday | Trend |
|--------|-------|-----------|-------|
| Beds Occupied | X/Y | A/Y | 📈/📉 |
| Consultations Scheduled | X | A | 📈/📉 |
| Pending Approvals | X | A | ⚠️ if new |
| Active Sicklists | X | A | 📈/📉 |

---

### 🗓️ Today's Schedule

**Consultations:**

| Time | Doctor | Patient | Type |
|------|--------|---------|------|
| HH:MM | [name] | [name] | [type] |

**Procedures/Operations:**
- [time] - [procedure] ([patient]) - [doctor]

---

### 🏥 Inpatient Status

**Current Patients ([count]):**

| Ward | Patient | Days | Status | Notes |
|------|---------|------|--------|-------|
| [#] | [name] | [X] | 🟢/🟠/🔴 | [notes] |

**Status Legend:**
- 🟢 Normal (< 14 days)
- 🟠 Extended (14-30 days)
- 🔴 Overstay (> 30 days)

**Expected Today:**
- 🔵 Admissions: [count] ([names])
- 🔴 Discharges: [count] ([names])

---

### 📝 Discharge Queue (Unsigned Histories)

| Patient | Discharged | Days Waiting | Action |
|---------|------------|--------------|--------|
| [name] | [date] | [X] | Sign off required |

---

### 👨‍⚕️ Doctor Documentation Status

| Doctor | Patients | Last Diary | Status |
|--------|----------|------------|--------|
| [name] | [X] | [date] | 🟢/🟠/🔴 |

**Status:**
- 🟢 Up to date (diary within 2 days)
- 🟠 Needs attention (3-5 days)
- 🔴 Slacking (> 5 days)

---

### 🚨 Alerts Summary

| Priority | Count | Top Issue |
|----------|-------|-----------|
| 🔴 Critical | X | [issue] |
| 🟠 Warning | X | [issue] |
| 🟢 Info | X | [issue] |

**→ Run `/alerts` for full details**

---

### ✅ Action Items for Today

1. **[Priority]** [Action] for [patient/issue]
2. **[Priority]** [Action] for [patient/issue]
3. ...

---

```
► Report generated: [timestamp]
► Next briefing: Tomorrow 08:00
► Run `/alerts` for detailed alerts
```
