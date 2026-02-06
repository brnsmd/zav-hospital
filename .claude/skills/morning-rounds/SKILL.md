---
name: morning-rounds
description: Complete morning rounds report - all alerts, diary status, VLK warnings, operations schedule. Run this first thing in the morning.
user-invocable: true
---

# Morning Rounds Report

Complete morning rounds briefing for the department.

## Data Collection (Parallel)

### 1. CyberIntern Alerts
```bash
curl -s "http://localhost:8082/mcp/alerts?severity=all&limit=100"
```

### 2. Diary Queue
```bash
curl -s "http://localhost:8082/api/diaries/queue"
```

### 3. Patient List
```bash
curl -s "http://localhost:8082/mcp/workflow/patient-list"
```

### 4. Boss API - Operations
```bash
curl -s "http://localhost:8083/api/operations/today" 2>/dev/null || echo "Boss API unavailable"
```

### 5. Airtable VLK Status
Use the Airtable MCP to query patients table for VLK fields:
- Filter patients where VLK status is "До ВЛК" or "ПОТРІБНА ВЛК"

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🌅 MORNING ROUNDS │ [date] [time]                    ║
╚══════════════════════════════════════════════════════╝

### 🚨 CRITICAL ALERTS ([count])

| Patient | Alert | Action Required |
|---------|-------|-----------------|
| [name]  | [type] | [action]       |

### 📋 DIARY STATUS

✅ Complete: [X] patients
⚠️ Missing: [Y] patients need today's diary

| Patient | Days Since Diary | Priority |
|---------|-----------------|----------|
| [name]  | [days]          | [🔴/🟠/🟢] |

### 🔬 VLK TRACKING

| Patient | Days Since Trauma | Status | Action |
|---------|-------------------|--------|--------|
| [name]  | [days]            | [status] | [action] |

### 🔪 TODAY'S OPERATIONS

| Time | Patient | Operation | Surgeon |
|------|---------|-----------|---------|
| [time] | [name] | [procedure] | [surgeon] |

### 💊 EXPIRING PRESCRIPTIONS

[List any prescriptions expiring today or already expired]

### 📊 DEPARTMENT SUMMARY

- Total patients: [X]
- Beds occupied: [X]/[total]
- Operations today: [X]
- Discharges pending: [X]

---
► /discharge [name] - Generate discharge papers
► /dovidka [name] - Generate certificate
► /triage-alerts - Detailed alert triage
► /complete-diaries - Fix missing diaries
```

## API Call Limit: Maximum 5 calls
