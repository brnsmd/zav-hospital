# Zav Alerts - Everything Needing Attention

Gather alerts from all sources and present them in prioritized format.

## Data Collection Steps

### 1. CyberIntern MCP (if available)
Use these MCP tools to gather clinical alerts:

- **get_alerts**: Get all clinical alerts (overdue labs, sicklists, etc.)
- **search_cyberintern** with query "fever" or "temperature": Find feverish patients
- **get_doctor_diaries** for each doctor: Check documentation compliance

### 2. Zav Cloud (Railway)
Make these API calls:

```bash
# Pending external patient requests
curl -s https://zav-production.up.railway.app/api/patients/pending

# Today's consultations (check for gaps)
curl -s https://zav-production.up.railway.app/api/consultations?date=today

# System health
curl -s https://zav-production.up.railway.app/health
```

### 3. Documentation Compliance Check
For each doctor, check if they have diary entries in the last 3 days for their patients.
Flag doctors with patients who have no recent diary entries.

## Output Format

Present results using A+B hybrid format:

```
╔══════════════════════════════════════════════════════╗
║  🚨 ZAV HOSPITAL │ Alerts                            ║
║  Generated: [current date/time]                      ║
╚══════════════════════════════════════════════════════╝
```

### 🔴 CRITICAL (Action Required Today)

| Issue | Details | Action |
|-------|---------|--------|
| [type] | [description] | [what to do] |

### 🟠 WARNING (Review This Week)

| Issue | Details | Action |
|-------|---------|--------|
| [type] | [description] | [what to do] |

### 🟢 INFO (Awareness)

| Issue | Details | Action |
|-------|---------|--------|
| [type] | [description] | [what to do] |

## Alert Categories

**CRITICAL (🔴)**:
- Patient with fever > 38°C
- Pending external requests > 24h old
- Discharge queue > 5 unsigned histories
- Critical lab results

**WARNING (🟠)**:
- Patient overstay (> 30 days)
- Doctor missing diary entries > 3 days
- Sicklist expiring in < 3 days
- Antibiotic course > 14 days

**INFO (🟢)**:
- Equipment ready for removal
- Low consultation bookings
- Upcoming planned procedures

## Summary Footer

```
► Total: X alerts (Y critical, Z warnings)
► Run `/daily` for full briefing
```
