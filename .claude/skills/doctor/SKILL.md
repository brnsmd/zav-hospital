---
name: doctor
description: Doctor mode - medical assistant menu with all available clinical actions. Shows patient management, document generation, and monitoring commands.
user-invocable: true
---

# Doctor Mode - Medical Assistant

Quick access to all medical actions available through Claude Code.

## Display Menu

```
╔══════════════════════════════════════════════════════╗
║  🩺 DOCTOR MODE │ CyberIntern Medical Assistant       ║
║  v4.2 │ http://localhost:8082                         ║
╚══════════════════════════════════════════════════════╝
```

### 📋 Patient Management

| Command | Description |
|---------|-------------|
| `/patient <name>` | Quick patient lookup |
| `/morning-rounds` | Full morning briefing with all alerts |
| `/triage-alerts` | Prioritized alert triage |
| `/complete-diaries` | Check/create missing diaries |

### 📄 Document Generation

| Command | Description |
|---------|-------------|
| `/discharge <name/id>` | Generate 027 discharge papers (Виписка) |
| `/dovidka <name/id>` | Hospital stay certificate (Довідка) |
| `/batch-diaries` | Batch diary generation for all patients |

### 🔬 Monitoring

| Command | Description |
|---------|-------------|
| `/vlk-check` | VLK status for all military patients |
| `/lab-check` | Outdated lab results |
| `/sicklist-check` | Expiring/expired sick leaves |

### 🏥 Hospital Operations

| Command | Description |
|---------|-------------|
| `/ops` | Today's operations schedule |
| `/beds` | Bed occupancy status |
| `/daily` | Morning briefing (Slack format) |
| `/alerts` | Aggregated system alerts |

### 🔧 System

| Command | Description |
|---------|-------------|
| `/zav` | Main system menu |
| `/sync-check` | Check all service connections |

---

**Tip:** Start with `/morning-rounds` for a complete overview, then use specific commands for actions.

**CyberIntern API:** http://localhost:8082
**Boss API:** http://localhost:8083
**n8n:** http://localhost:5678
