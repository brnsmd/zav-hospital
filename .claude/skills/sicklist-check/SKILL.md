---
name: sicklist-check
description: Check sick leave certificates (лікарняні) for all patients. Shows expired, expiring, and missing sicklists.
user-invocable: true
---

# Sicklist Status Check

Check sick leave certificate status for all active patients.

## Data Collection

```bash
curl -s "http://localhost:8082/mcp/alerts?severity=all" | jq '[.data[] | select(.alert_type | contains("sicklist"))]'
```

```bash
curl -s "http://localhost:8082/mcp/workflow/patient-list"
```

## Sicklist Rules

| Status | Condition | Action |
|--------|-----------|--------|
| 🔴 Expired | End date passed, patient still hospitalized | Extend or renew immediately |
| 🟠 Expiring | Expires within 3 days | Schedule renewal |
| 🔴 Missing | No sicklist on record | Create one |
| 🟢 Active | Valid and current | No action |

**Important:** Backdating is only possible within 3 days. After that, a new sicklist must be issued from the current date.

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  📋 SICKLIST STATUS │ [date]                           ║
╚══════════════════════════════════════════════════════╝

### 🔴 EXPIRED

| Patient | Expired | Days Ago | Can Backdate? |
|---------|---------|----------|---------------|
| [name]  | [date]  | [X]      | Yes/No        |

### 🟠 EXPIRING SOON

| Patient | Expires | Days Left |
|---------|---------|-----------|
| [name]  | [date]  | [X]       |

### 🔴 MISSING SICKLIST

| Patient | Admitted | Days Without |
|---------|----------|-------------|
| [name]  | [date]   | [X]         |

### 🟢 Active ([X] patients)

All other patients have valid sick leaves.

---
► Renew sicklist through EMR or use CyberIntern web UI
```
