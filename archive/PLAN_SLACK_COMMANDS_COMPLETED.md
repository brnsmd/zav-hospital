# Plan: Slack Slash Commands & New Workflows

**Date:** 2026-01-24
**Status:** Ready for implementation

## Scope

### 1. Slack Slash Commands (3 commands)
- `/patient <name>` - Search patient by name, return patient card
- `/ops` - Today's operations list
- `/beds` - Current bed/ward occupancy

### 2. New n8n Workflows (2 workflows)
- **Overstay Alert** - Daily 9 AM, patients >30d (warning) or >60d (critical) → #alerts
- **New Patient Admission** - When patient created in Airtable → #admissions

---

## Architecture

```
User types /patient Іванов in Slack
    ↓
Slack sends POST to n8n webhook
    ↓
n8n workflow: Query Airtable → Format Block Kit → Respond
    ↓
Slack displays formatted patient card
```

---

## Implementation Steps

### Step 1: Get Slack Channel IDs (5 min)

Query Slack MCP for exact channel IDs needed:
- #alerts (for overstay alerts)
- #admissions (for new patient notifications)

### Step 2: Configure Slack App Slash Commands (15 min)

1. Open https://api.slack.com/apps → Select Zav Hospital app
2. Go to **Features > Slash Commands**
3. Add three commands:

| Command | Request URL | Description |
|---------|-------------|-------------|
| `/patient` | `http://localhost:5678/webhook/slack-patient` | Search patient |
| `/ops` | `http://localhost:5678/webhook/slack-ops` | Today's operations |
| `/beds` | `http://localhost:5678/webhook/slack-beds` | Bed status |

4. Reinstall app to workspace

### Step 3: Create n8n Workflows (60 min)

Create 5 workflows via n8n UI or REST API:

#### Workflow 1: `/patient` Command
- **Trigger:** Webhook POST `/webhook/slack-patient`
- **Nodes:** Extract search term → Search Airtable (FIND in ПІБ) → Format patient card → Respond
- **Response:** Ephemeral (private to user)

#### Workflow 2: `/ops` Command
- **Trigger:** Webhook POST `/webhook/slack-ops`
- **Nodes:** Get today's date → Query Операції (Дата операції = TODAY()) → Format list → Respond
- **Response:** In-channel (visible to all)

#### Workflow 3: `/beds` Command
- **Trigger:** Webhook POST `/webhook/slack-beds`
- **Nodes:** HTTP GET Boss API /patients → Aggregate by ward → Format occupancy → Respond
- **Response:** In-channel (visible to all)

#### Workflow 4: Overstay Alert
- **Trigger:** Schedule daily 9:00 AM (Europe/Kyiv)
- **Nodes:** Get hospitalized patients → Calculate days → Filter >30d / >60d → Format alert → Post to #alerts
- **Surgeon mentions:** Tag @U0AABU2LRS7 (Цапенко) for critical patients

#### Workflow 5: New Patient Admission
- **Trigger:** Schedule every 1 minute (polling)
- **Nodes:** Query Airtable (Created in last 2 min, Статус = Госпіталізований) → Format card → Post to #admissions

### Step 4: Test Commands (20 min)

```bash
# Test /patient
curl -X POST http://localhost:5678/webhook/slack-patient \
  -d "command=/patient&text=Іванов&user_id=U0AABU2LRS7"

# Test /ops
curl -X POST http://localhost:5678/webhook/slack-ops \
  -d "command=/ops&user_id=U0AABU2LRS7"

# Test /beds
curl -X POST http://localhost:5678/webhook/slack-beds \
  -d "command=/beds&user_id=U0AABU2LRS7"
```

Then test from Slack directly.

### Step 5: Update Documentation (10 min)

Update CLAUDE.md with:
- New workflow IDs
- Webhook paths
- Slack channel IDs

---

## Key References

### Credentials (Already Configured)
- **Airtable:** q1hgA8Zwq8FjYUGr
- **Slack:** iV5Vlwovbmg7gNJP
- **n8n URL:** localhost:5678

### Airtable IDs
- **Base:** appv5BwoWyRhT6Lcr
- **Пацієнти:** tblcMn6CHbW10pQfq
- **Операції:** tblZccmxy1DxtzIoc

### Slack Channel IDs (Verified)
| Channel | ID | Purpose |
|---------|-----|---------|
| #alerts | C0AAXQESL4R | Overstay alerts, VLK alerts |
| #admissions | C0AAJSGLCPL | New patient notifications |
| #operations | C0AACFEURNX | Surgery updates |

### Surgeon → Slack Mapping
| Surgeon | Slack ID |
|---------|----------|
| Цапенко Г. | U0AABU2LRS7 |
| Бабаев Т.А. | U0AB12A9EAD |

---

## Output Formats

### /patient Response (Block Kit)
```
🏥 Знайдено пацієнтів: 2
────────────────────────
*Іванов Іван Іванович*
🟢 Госпіталізований | Палата: 801
👨‍⚕️ Цапенко Г.
📋 Вивих правого колінного суглоба...
```

### /ops Response (Block Kit)
```
🏥 Операції на 24 січня 2026
────────────────────────────
1. ⏳ *ПХО рани*
   👤 Петров П.П. | 👨‍⚕️ Цапенко Г.

2. ✅ *Остеосинтез*
   👤 Сидоров С.С. | 👨‍⚕️ Бабаев Т.А.
────────────────────────────
📊 Всього: 2 | ✅ Завершено: 1
```

### /beds Response (Block Kit)
```
🛏️ Статус палат
────────────────
🟢 *Палата 801*: 2/4
   _Іванов І.І., Петров П.П._

🟠 *Палата 802*: 3/4
   _Сидоров С.С., Козлов К.К., Бондар Б.Б._

🔴 *Палата ПІТ*: 6/6
   _Мельник М.М., Шевченко Ш.Ш. (+4)_
────────────────
📊 Всього: 32 | 🟢 <50% | 🟠 75%+ | 🔴 100%
```

### Overstay Alert (Scheduled)
```
📋 Звіт про тривалу госпіталізацію
24 січня 2026

🔴 КРИТИЧНО (>60 днів): 2
• *Мельник М.М.* - 75 дн.
  Палата ПІТ | Цапенко Г.
• *Шевченко Ш.Ш.* - 65 дн.
  Палата 805 | Бабаев Т.А.

🟠 УВАГА (30-60 днів): 3
• *Козлов К.К.* - 45 дн.
  Палата 802 | Цапенко Г.

👨‍⚕️ <@U0AABU2LRS7> <@U0AB12A9EAD> - зверніть увагу
```

---

## Verification

After implementation, verify:

1. **Slash commands work from Slack:**
   - Type `/patient Іванов` in any channel
   - Type `/ops` in #operations
   - Type `/beds` in #general

2. **Scheduled workflows run:**
   - Check n8n executions at 9:00 AM for Overstay Alert
   - Create test patient, verify #admissions notification

3. **Formatting is correct:**
   - Block Kit renders properly
   - Emojis display correctly
   - Surgeon @mentions work

---

## Files to Modify

1. **Slack App** (https://api.slack.com/apps) - Add slash commands
2. **n8n** (localhost:5678) - Create 5 workflows
3. **CLAUDE.md** - Update with new workflow IDs

---

## Estimated Time: 1.5-2 hours
