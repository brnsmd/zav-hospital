# Zav Hospital Management System - Menu

Display the Zav CLI menu using the A+B hybrid format (Unicode box headers + Markdown tables).

## Your Response Format

Show this menu:

```
╔══════════════════════════════════════════════════════╗
║  🏥 ZAV HOSPITAL MANAGEMENT SYSTEM                   ║
║  v3.0-doctor-is-in                                   ║
╚══════════════════════════════════════════════════════╝
```

### Available Commands

| Command | Description |
|---------|-------------|
| `/zav` | Show this menu |
| `/daily` | Full daily briefing report |
| `/alerts` | Everything needing attention (prioritized) |
| `/patient <name>` | Quick patient lookup by name or ID |
| `/ops` | Today's operations and OR status |
| `/beds` | Current bed occupancy |

### Quick Actions

| Action | How |
|--------|-----|
| Find patient | `/patient Іванов` or `/patient EX123` |
| Today's surgeries | `/ops` |
| Bed availability | `/beds` |
| Pending approvals | Ask: "pending requests" |

### Data Sources

- **CyberIntern MCP**: Patient records, diaries, prescriptions, labs, alerts
- **Zav Cloud (Railway)**: Consultations, external requests, doctor availability

---

**Tip**: Use `/alerts` for a quick overview of what needs attention, or `/daily` for the full morning briefing.
