---
name: vlk-check
description: Check VLK (military medical commission) status for all patients. Shows who needs scheduling, who is overdue.
user-invocable: true
---

# VLK Status Check

Check military medical commission (ВЛК) status for all active patients.

## Data Collection

### From Airtable (via MCP)
Query the Patients table (tblcMn6CHbW10pQfq) for VLK-relevant fields:
- ПІБ (name)
- Дата госпіталізації (admission date)
- Дата ВЛК (fldCt5NDGU8vKotHl) - VLK date
- Рішення ВЛК (fldrC2XBPNOcm3Lhl) - VLK decision
- Дні продовження (fld9mAFPVh25ueDVm) - Extension days
- ВЛК статус (fldcfU96tCM4hWoX4) - Calculated status

### From CyberIntern
```bash
curl -s "http://localhost:8082/mcp/alerts?severity=all" | jq '.data[] | select(.alert_type | contains("vlk"))'
```

## VLK Thresholds

| Days Since Admission | Status | Action |
|---------------------|--------|--------|
| <100 | 🟢 OK | No action |
| 100-114 | 🟠 Warning | Schedule soon |
| 115-119 | 🟠 Critical Warning | Schedule urgently |
| ≥120 | 🔴 OVERDUE | VLK required NOW |
| VLK completed | ✅ Done | Check next cycle |

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🔬 VLK STATUS │ [date]                               ║
╚══════════════════════════════════════════════════════╝

### 🔴 OVERDUE - VLK Required

| Patient | Days | Admission | Action |
|---------|------|-----------|--------|
| [name]  | [X]  | [date]    | Schedule immediately |

### 🟠 WARNING - Schedule Soon

| Patient | Days | Admission | Deadline |
|---------|------|-----------|----------|
| [name]  | [X]  | [date]    | [date]   |

### 🟢 OK

| Patient | Days | Next Check |
|---------|------|------------|
| [name]  | [X]  | [date]     |

### ✅ VLK Completed

| Patient | VLK Date | Decision | Extension |
|---------|----------|----------|-----------|
| [name]  | [date]   | [decision] | [days] |

---
VLK Schedule: Tuesday / Friday
► To schedule: Use Slack /vlk command or MEGALITH 6 buttons
```
