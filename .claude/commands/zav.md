# Zav Hospital Management System - Menu

Display the Zav CLI menu using the A+B hybrid format (Unicode box headers + Markdown tables).

## Your Response Format

Show this menu:

```
╔══════════════════════════════════════════════════════╗
║  🏥 ZAV HOSPITAL MANAGEMENT SYSTEM                   ║
║  v4.0-doctor-mode                                    ║
╚══════════════════════════════════════════════════════╝
```

### Hospital Operations

| Command | Description |
|---------|-------------|
| `/zav` | Show this menu |
| `/daily` | Full daily briefing report |
| `/alerts` | Everything needing attention (prioritized) |
| `/patient <name>` | Quick patient lookup by name or ID |
| `/ops` | Today's operations and OR status |
| `/beds` | Current bed occupancy |

### Doctor Mode (CyberIntern Medical Assistant)

| Command | Description |
|---------|-------------|
| `/doctor` | Doctor mode - full medical assistant menu |
| `/morning-rounds` | Complete morning rounds briefing |
| `/triage-alerts` | Prioritized alert triage |
| `/discharge <name/id>` | Generate 027 discharge papers |
| `/dovidka <name/id>` | Hospital stay certificate |
| `/batch-diaries` | Batch diary generation |
| `/complete-diaries` | Check/create missing diaries |

### Monitoring

| Command | Description |
|---------|-------------|
| `/vlk-check` | VLK military commission status |
| `/lab-check` | Outdated lab results |
| `/sicklist-check` | Sick leave certificate status |
| `/sync-check` | Check all service connections |

### Quick Actions

| Action | How |
|--------|-----|
| Find patient | `/patient Іванов` or `/patient EX123` |
| Morning overview | `/morning-rounds` |
| Discharge patient | `/discharge 300045` |
| Generate certificate | `/dovidka 300045` |
| Check VLK | `/vlk-check` |
| System health | `/sync-check` |

### Data Sources

- **CyberIntern MCP**: Patient records, diaries, prescriptions, labs, alerts (port 8082)
- **Boss API**: EMR data, SQLite database (port 8083)
- **Airtable MCP**: Patient database (source of truth)
- **Slack MCP**: Team communication
- **n8n**: Workflow automation (port 5678)

---

**Tip**: Start with `/morning-rounds` for a complete overview, or `/doctor` for the medical assistant menu.
