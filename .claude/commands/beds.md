# Zav Beds - Current Bed Status

Quick view of bed occupancy and availability.

## Data Collection

### 1. Zav Cloud (Railway)
```bash
# System stats (includes bed count)
curl -s https://web-production-d80eb.up.railway.app/stats

# All patients (filter hospitalized)
curl -s https://web-production-d80eb.up.railway.app/api/patients
```

### 2. CyberIntern MCP (if available)
- **search_cyberintern** type="patients" status="hospitalized": Get inpatients

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🛏️  ZAV HOSPITAL │ Bed Status                       ║
║  [Date] [Time]                                       ║
╚══════════════════════════════════════════════════════╝
```

### Occupancy Overview

```
Occupied: [X] / [Total] beds  ([Y]%)

[██████████░░░░░░░░░░] 50%
```

### Current Inpatients

| Bed | Patient | Days | Status | Expected Discharge |
|-----|---------|------|--------|-------------------|
| 1 | [name] | 5 | 🟢 | Dec 20 |
| 2 | [name] | 14 | 🟠 | Dec 22 |
| 3 | [name] | 35 | 🔴 | TBD |
| 4 | - | - | ⬜ Available | - |

**Status Legend:**
- 🟢 Normal stay (< 14 days)
- 🟠 Extended stay (14-30 days)
- 🔴 Overstay (> 30 days)
- ⬜ Available

---

### Today's Movement

| Type | Count | Patients |
|------|-------|----------|
| 🔵 Admissions | X | [names] |
| 🔴 Discharges | Y | [names] |
| 📊 Net Change | +/- Z | |

---

### Alerts

- 🔴 [X] patients overstaying (> 30 days)
- 🟠 [Y] patients approaching 30-day mark

---

```
► Capacity: [X]/[Total] ([Y]% full)
► Run /patient <name> for patient details
► Run /daily for full briefing
```
