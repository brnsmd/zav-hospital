# Zav Patient Lookup

Quick lookup for a specific patient by name or ID.

**Argument**: $ARGUMENTS (patient name or ID)

## Data Collection

### 1. CyberIntern MCP
Use these tools to find the patient:

- **search_cyberintern** with query="$ARGUMENTS" type="patients": Find patient by name
- **get_patient_record** with patient_id: Get full patient details (if ID provided)

### 2. Zav Cloud (Railway)
```bash
# Get all patients and filter
curl -s https://web-production-d80eb.up.railway.app/api/patients
```

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🔍 ZAV HOSPITAL │ Patient: [Name]                   ║
╚══════════════════════════════════════════════════════╝
```

### Patient Info

| Field | Value |
|-------|-------|
| ID | [patient_id] |
| Name | [name] |
| Age | [age] |
| Status | [hospitalized/discharged/pending] |
| Admission Date | [date] |
| Days in Hospital | [X] |
| Assigned Doctor | [doctor_name] |

### Current Treatment

| Item | Details |
|------|---------|
| Diagnosis | [from diary] |
| Antibiotics | [active courses] |
| Equipment | [VAC, fixators, etc.] |

### Recent Notes
- [Latest diary entry summary]

### Alerts
- [Any active alerts for this patient]

---

```
► Use /alerts for all alerts
► Use /daily for full briefing
```

## If No Patient Found

```
╔══════════════════════════════════════════════════════╗
║  ❌ ZAV HOSPITAL │ Patient Not Found                 ║
╚══════════════════════════════════════════════════════╝

No patient matching "$ARGUMENTS" found.

Try:
- Check spelling
- Use patient ID instead of name
- Run /daily to see all current patients
```
