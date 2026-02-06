---
name: sync-check
description: Check all service connections - CyberIntern, Boss API, n8n, Airtable, Slack, ngrok. Diagnose connectivity issues.
user-invocable: true
---

# System Connection Check

Check all service connections and report status.

## Service Checks

Run all checks in parallel:

### 1. CyberIntern API (Port 8082)
```bash
curl -s --max-time 5 "http://localhost:8082/mcp/health"
```

### 2. Boss API (Port 8083/8084)
```bash
curl -s --max-time 5 "http://localhost:8083/health" 2>/dev/null || curl -s --max-time 5 "http://localhost:8084/health"
```

### 3. n8n (Port 5678)
```bash
curl -s --max-time 5 "http://localhost:5678/healthz"
```

### 4. ngrok Tunnel
```bash
curl -s --max-time 10 "https://kristeen-rootlike-unflirtatiously.ngrok-free.dev/healthz"
```

### 5. Airtable
Test via MCP - list records from Patients table (tblcMn6CHbW10pQfq), limit 1.

### 6. Slack
Test via MCP - post a test message or check auth.

## Output Format

```
╔══════════════════════════════════════════════════════╗
║  🔧 SYSTEM STATUS │ [date] [time]                     ║
╚══════════════════════════════════════════════════════╝

| Service | Status | URL | Details |
|---------|--------|-----|---------|
| CyberIntern | ✅/❌ | localhost:8082 | v4.2 |
| Boss API | ✅/❌ | localhost:8083 | [version] |
| n8n | ✅/❌ | localhost:5678 | [workflows] |
| ngrok | ✅/❌ | [domain] | Tunnel [up/down] |
| Airtable | ✅/❌ | API | [record count] |
| Slack | ✅/❌ | API | [workspace] |

### Issues Found

[List any services that are down with troubleshooting steps]

### Quick Fixes

- CyberIntern down: `cd cyberintern && python -m uvicorn src.api.main:app --port 8082`
- Boss API down: `boss` (starts TUI which auto-starts API)
- n8n down: Check if Boss TUI started it, or `n8n start`
- ngrok down: `ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev`
```
