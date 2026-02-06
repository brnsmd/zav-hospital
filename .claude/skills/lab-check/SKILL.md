---
name: lab-check
description: Check for outdated lab results across all patients. Shows who needs fresh bloodwork, biochemistry, or coagulation tests.
user-invocable: true
---

# Lab Freshness Check

Check all patients for outdated laboratory results.

## Data Collection

```bash
curl -s "http://localhost:8082/mcp/alerts?severity=all" | jq '[.data[] | select(.alert_type | contains("lab"))]'
```

Also fetch patient list for context:
```bash
curl -s "http://localhost:8082/mcp/workflow/patient-list"
```

## Lab Freshness Rules

| Test Type | Max Age | Priority When Overdue |
|-----------|---------|----------------------|
| CBC (ЗАК) | 7 days | High |
| Biochemistry | 7 days | High |
| Coagulation | 7 days | High (critical if pre-op) |
| Urinalysis | 14 days | Medium |
| Blood type | Once | Low (only if missing) |

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🔬 LAB FRESHNESS │ [date]                             ║
╚══════════════════════════════════════════════════════╝

### 🔴 Critical (Pre-op patients with outdated labs)

| Patient | Test | Last Done | Days Old | Surgery Date |
|---------|------|-----------|----------|--------------|
| [name]  | CBC  | [date]    | [X]      | [date]       |

### 🟠 Overdue

| Patient | Test | Last Done | Days Overdue |
|---------|------|-----------|-------------|
| [name]  | [test] | [date] | [X]         |

### 🟢 Fresh (all patients with up-to-date labs)

[X] patients have current lab results

---
► Order labs through EMR or contact laboratory
```
