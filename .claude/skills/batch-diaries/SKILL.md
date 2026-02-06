---
name: batch-diaries
description: Batch generate missing diary entries for all active patients. Checks who needs diaries and creates them.
argument-hint: "[date or 'all']"
user-invocable: true
---

# Batch Diary Generation

Generate missing diary entries for patients.

**Argument:** $ARGUMENTS (optional date YYYY-MM-DD, or "all" for all missing, defaults to today)

## Workflow

### Step 1: Get Diary Queue

```bash
curl -s "http://localhost:8082/api/diaries/queue"
```

Or with specific date:
```bash
curl -s "http://localhost:8082/mcp/workflow/patient-list?date=$ARGUMENTS"
```

### Step 2: Show Status

Present the queue to the user:

```
╔══════════════════════════════════════════════════════╗
║  📋 DIARY BATCH │ [date]                               ║
╚══════════════════════════════════════════════════════╝

Patients needing diaries:

| # | Patient | Days Since | Alerts | Priority |
|---|---------|-----------|--------|----------|
| 1 | [name]  | [days]    | [count] | 🔴/🟠/🟢 |

Generate diaries for [X] patients? [Yes/No/Select]
```

### Step 3: Generate (after confirmation)

For each patient:
```bash
curl -s -X POST "http://localhost:8082/api/diaries/batch-generate" \
  -H "Content-Type: application/json" \
  -d '{
    "patient_ids": ["id1", "id2"],
    "diary_date": "YYYY-MM-DD",
    "diary_type": "daily",
    "use_ai": true
  }'
```

### Step 4: Report Results

```
Batch Diary Results:

✅ [name] - Generated (daily, 150 words)
✅ [name] - Generated (daily, 130 words)
❌ [name] - Failed: [reason]

Summary: [X] generated, [Y] failed
```

## API Call Limit: Maximum 2 + 1 per patient batch
