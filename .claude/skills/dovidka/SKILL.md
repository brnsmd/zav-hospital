---
name: dovidka
description: Generate a hospital stay certificate (Довідка) for a patient. Used for military patients to confirm treatment period.
argument-hint: "[patient_name_or_id]"
user-invocable: true
---

# Hospital Stay Certificate (Довідка)

Generate a medical certificate confirming a patient's hospital stay.

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

### Step 2: Generate Dovidka (1 API call)

**Standard dovidka (without diagnosis):**
```bash
curl -s -X POST "http://localhost:8082/mcp/generate/document" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "{patient_id}", "document_type": "dovidka"}'
```

**Dovidka with diagnosis (for VLK/commission):**
```bash
curl -s -X POST "http://localhost:8082/mcp/generate/document" \
  -H "Content-Type: application/json" \
  -d '{"patient_id": "{patient_id}", "document_type": "dovidka", "with_diagnosis": true}'
```

## Document Placeholders

| Field | Source |
|-------|--------|
| {{ДАТА}} | Today's date |
| {{ПІБ}} | Patient full name |
| {{Дата_народження}} | Date of birth |
| {{Діагноз}} | Diagnosis (if with_diagnosis) |
| {{Дата_госпіталізації}} | Admission date |
| {{№_історії}} | Case number |
| {{Хірург}} | Attending surgeon |
| {{ЗВАННЯ}} | Military rank |
| {{ПІДРОЗДІЛ}} | Military unit |
| {{ПОСАДА}} | Position |
| {{ПЕРІОД_ПЕРЕБУВАННЯ}} | Stay period |
| {{СТАН_ХВОРОГО}} | Current condition |

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  📋 DOVIDKA │ Patient: [Name]                         ║
╚══════════════════════════════════════════════════════╝

✓ Patient: [name] ([rank], [unit])
✓ Stay: [admission] - [today/discharge]
✓ Diagnosis: [diagnosis] (if included)

📋 Certificate generated: output/dovidka_[name]_[date].docx

Next steps:
- Print certificate
- Get signatures (Панфьоров С.В., Кондратов Д.С., [surgeon])
- Give to patient/military representative
```

## API Call Limit: Maximum 2 calls
