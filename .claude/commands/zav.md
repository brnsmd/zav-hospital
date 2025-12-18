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
| `/alerts` | Everything needing attention (prioritized) |
| `/daily` | Full daily briefing report |

### Quick Actions

| Action | How |
|--------|-----|
| Show doctors | Ask: "show me the doctors" |
| Show patients | Ask: "list patients" or use CyberIntern MCP |
| Check consultations | Ask: "today's consultations" |
| Pending approvals | Ask: "pending requests" |

### Data Sources

- **CyberIntern MCP**: Patient records, diaries, prescriptions, labs, alerts
- **Zav Cloud (Railway)**: Consultations, external requests, doctor availability

---

**Tip**: Use `/alerts` for a quick overview of what needs attention, or `/daily` for the full morning briefing.
