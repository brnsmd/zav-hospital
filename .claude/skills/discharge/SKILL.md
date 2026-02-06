---
name: discharge
description: Generate 027 discharge papers for a patient. Fetches EMR data, fills template, generates DOCX.
argument-hint: "[patient_name_or_id]"
user-invocable: true
---

# Patient Discharge - Generate 027 Vypyska

Generate a full discharge summary (Form 027/o - Виписка) for a patient.

**Argument:** $ARGUMENTS (patient name or ID)

## Workflow

### Step 1: Find Patient

If $ARGUMENTS looks like a number/ID:
```bash
curl -s "http://localhost:8082/mcp/patient/$ARGUMENTS/full"
```

If $ARGUMENTS is a name:
```bash
curl -s "http://localhost:8082/mcp/search?q=$ARGUMENTS&type=patients"
```
Then use the patient_id from the search result.

### Step 2: Get Full Patient Record (1 API call)

```bash
curl -s "http://localhost:8082/mcp/patient/{patient_id}/full"
```

This returns EVERYTHING: demographics, diaries, alerts, prescriptions, lab results, procedures, consultations.

### Step 3: Fetch EMR Data (optional, 1 API call)

```bash
curl -s -X POST "http://localhost:8082/api/documents/fetch-emr" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "{patient_id}"}'
```

If EMR credentials not available or fetch fails, continue with local data only.

### Step 4: Generate Vypyska (1 API call)

```bash
curl -s -X POST "http://localhost:8082/mcp/generate/document" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "{patient_id}", "document_type": "vypyska"}'
```

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  📄 DISCHARGE │ Patient: [Name]                       ║
╚══════════════════════════════════════════════════════╝

Step 1: Patient data ✓
  Name: [name]
  Admitted: [date] ([X] days)
  Diagnosis: [diagnosis]

Step 2: EMR data ✓ (or ⊘ skipped)

Step 3: Document generated ✓
  File: output/vypyska_[name]_[date].docx

✅ Discharge document ready for review

Next steps:
- Review and print document
- Have department chief sign
- Upload signed PDF to Airtable
```

## Error Handling

- Patient not found → suggest search
- EMR unavailable → proceed with local data
- Missing fields → list what's missing, suggest fixes

## API Call Limit: Maximum 3 calls
