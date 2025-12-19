# Zav Operations - Today's Procedures

Quick view of today's scheduled operations and procedures.

## Data Collection

### 1. Zav Cloud (Railway)
```bash
# Today's operation slots
curl -s https://web-production-d80eb.up.railway.app/api/operation-slots

# Today's consultations (some may be procedures)
curl -s https://web-production-d80eb.up.railway.app/api/consultations
```

### 2. CyberIntern MCP (if available)
- **search_cyberintern** type="operations": Find scheduled operations
- **get_patient_record** for each patient: Get procedure details

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🔪 ZAV HOSPITAL │ Operations Today                  ║
║  [Date]                                              ║
╚══════════════════════════════════════════════════════╝
```

### Scheduled Operations

| Time | OR | Patient | Procedure | Doctor | Status |
|------|-----|---------|-----------|--------|--------|
| 08:00 | 1 | [name] | [procedure] | [doctor] | 🟢 Ready |
| 10:30 | 2 | [name] | [procedure] | [doctor] | 🟠 Prep |
| 14:00 | 1 | [name] | [procedure] | [doctor] | ⏳ Waiting |

**Status Legend:**
- 🟢 Ready - Patient prepped, OR available
- 🟠 Prep - Patient being prepared
- ⏳ Waiting - Scheduled, not yet started
- ✅ Complete - Finished
- ❌ Cancelled

---

### OR Room Status

| Room | Status | Current/Next |
|------|--------|--------------|
| OR 1 | 🟢 Available | Next: 14:00 |
| OR 2 | 🔴 In Use | [Patient] - Est. 11:30 |
| OR 3 | 🟢 Available | No procedures |

---

### Summary

```
► Total: X operations scheduled
► Completed: Y | Remaining: Z
► Next: [Patient] at [Time] in OR [#]
```

## If No Operations Today

```
╔══════════════════════════════════════════════════════╗
║  🔪 ZAV HOSPITAL │ Operations Today                  ║
╚══════════════════════════════════════════════════════╝

No operations scheduled for today.

► Use /daily for full department overview
```
