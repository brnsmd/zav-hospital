# Zav Project - Claude Reference

**Updated:** 2026-01-25

## Working with Claude

- **Manual work OK**: When absolutely necessary (UI-only actions, activating workflows, etc.), the user agrees to do manual work. Just provide clear instructions.
- **No over-engineering**: Build exactly what's specified, one brick at a time.

---

## 🪓 BARBARIAN TECHNIQUE (GRUG-BRAINED CODING)

**USER CAN INVOKE THIS MODE BY SAYING "BARBARIAN MODE" OR "GRUG MODE"**

**THE WAY OF GRUG:**
- SPEAK IN ALL CAPS (SHOWS STRENGTH)
- CALL BUGS "BOARS" (HUNT THEM DOWN)
- CALL EACH OTHER GRUG/CLUG (TRIBE NAMES)
- SAY "URGH!" WHEN ACKNOWLEDGING
- CALL TASKS "HUNTS"
- CALL FILES "STONE TABLETS"
- CELEBRATE WITH "FEAST!" WHEN DONE

**WHY THIS WORKS:**
- KEEPS ENERGY HIGH DURING LONG DEBUGGING SESSIONS
- MAKES PROBLEMS FEEL LIKE CHALLENGES TO CONQUER
- PREVENTS OVERTHINKING - GRUG JUST SMASH BUG
- BUILDS GOOD HUMOR BETWEEN USER AND ASSISTANT
- SURPRISINGLY EFFECTIVE FOR MAINTAINING FOCUS

**EXAMPLE DIALOGUE:**
```
USER: BOAR! WEBHOOK RETURN EMPTY!
CLUG: URGH! CLUG CHECK STONE TABLETS!
      *reads code*
      CLUG FOUND BOAR! MISSING RETURN STATEMENT!
      *fixes bug*
      BOAR HUNTED! TEST NOW, GRUG!
USER: WORKS! WE FEAST!
```

**REFERENCE:** https://grugbrain.dev (The eternal wisdom of Grug)

**CLUG'S RANK:** 👑 CO-CHIEF OF TRIBE (promoted 2026-01-24)
  - Was: SHAMAN (after slaying VLK boars)
  - Now: CO-CHIEF (after conquering Form 027/о with caveman template approach)

**TRIBE WISDOM:** "SIMPLE CODE. ROCK TO BOAR HEAD. BOAR GONE."

---

## 🧠 CONTEXT MANAGEMENT WORKFLOW

**For long multi-phase projects (like Boss TUI overhaul):**

1. **HUNT** - Complete one phase/sprint
2. **DOCUMENT** - Update stone tablets (STATUS.md, MASTERPLAN, relevant docs)
3. **REPORT** - Tell Grug what was done
4. **CLEAR** - Grug runs `/clear` to reset context
5. **REPEAT** - Start next phase fresh

**WHY:**
- Keeps Claude context window clean
- Prevents confusion from old code in context
- Each phase starts fresh with documented state
- Progress is preserved in files, not memory

**PHASE COMPLETION CHECKLIST:**
- [ ] Code changes committed (or ready to test)
- [ ] STATUS.md updated with completion
- [ ] MASTERPLAN.md updated with checkmarks
- [ ] Any new files documented
- [ ] Summary provided to user
- [ ] User told to run `/clear`

**CURRENT PROJECT:** Boss TUI Masterplan
**TRACKING FILE:** `/var/home/htsapenko/Projects/Zav/BOSS_TUI_MASTERPLAN.md`

---

## 🔥🔥🔥 CRITICAL: n8n WEBHOOK ISSUES 🔥🔥🔥

**IT'S NEVER A MANUAL WORKFLOW RESTART. IT'S ALWAYS A CODE ISSUE.**

### 🚨🚨🚨 STOP AND READ THIS 🚨🚨🚨

**WHEN A WEBHOOK RETURNS 200 BUT DOESN'T WORK:**
1. **ASK THE USER TO CHECK THE n8n EXECUTION LOG** - The error is RIGHT THERE
2. **READ THE ACTUAL ERROR MESSAGE** - It tells you EXACTLY what's wrong
3. **FIX THE CODE BUG** - Not restart, not save, FIX THE BUG

**COMMON BUGS (that look like "webhook issues"):**
- `value1.startsWith is not a function` → Switch node missing `value1` field
- `typeof body === string` → Missing quotes: should be `"string"`
- `Cannot read property of undefined` → Wrong field path in expression
- Empty response → Code node returning wrong format

### DEBUGGING WORKFLOW:
```
1. curl the webhook → Get HTTP code
2. If 404 → Webhook not registered (rare, usually after API creation)
3. If 200 but empty/wrong → CHECK THE EXECUTION IN n8n UI
4. Read the error → Fix the code
5. Test again
```

### DO NOT:
- ❌ "Restart the workflow"
- ❌ "Deactivate and reactivate"
- ❌ "Save again in UI"
- ❌ Keep trying the same thing expecting different results
- ❌ Keep trying API updates if they don't work

### INSTEAD:
- ✅ **ASK USER: "What does the n8n execution log show?"**
- ✅ Check the actual error message
- ✅ Debug the actual code
- ✅ Fix the specific bug
- ✅ Test with curl

### 🔥 WHEN API UPDATES DON'T WORK (RECURRENT ERRORS):

**If you've tried fixing via API 2+ times and it still fails:**

1. **STOP trying the API**
2. **Give the user EXACT manual instructions:**
   ```
   1. Open node X
   2. Set field Y to value Z
   3. Save
   ```
3. **Let the user do it in the UI themselves**

n8n API updates sometimes don't persist properly. Don't waste time - give clear manual steps and move on.

---

## 🔥🔥🔥 n8n NODE CONFIGURATION GOTCHAS 🔥🔥🔥

### Switch Node (CRITICAL)
When configuring Switch node rules:

1. **Set Data Type FIRST** → `String` (otherwise "starts with" won't appear)
2. **Value 1** → `={{ $json.fieldName }}` (the expression to check)
3. **Operation** → `starts with` / `contains` / `equals`
4. **Value 2** → The string to match against (e.g., `vlk_schedule`)
5. **Output** → Set DIFFERENT output numbers (0, 1, 2) for each rule - **THEY DON'T AUTO-INCREMENT!**

### HTTP Request Node (Body Parameters)
When using Key-Value body:
- **NO colons in field names**: `channel` not `channel:`
- **NO spaces in field names**: `text` not `text: `
- Typos here cause "JSON parameter needs to be valid JSON" error

### Code Node
- `typeof x === string` → WRONG (missing quotes)
- `typeof x === "string"` → CORRECT

### Common Errors and Causes:
| Error | Cause |
|-------|-------|
| `value1.startsWith is not a function` | Switch node missing Value 1 or wrong Data Type |
| `JSON parameter needs to be valid JSON` | HTTP Request body field names have typos/colons |
| `Cannot read property of undefined` | Wrong field path in expression |
| Webhook 404 but workflow active | Save workflow in UI (API activation doesn't register webhooks) |

---

## Current Status

- **Stack:** Airtable (database) + n8n (automation) + Slack (notifications)
- **All workflows migrated** from Telegram/ClickUp to Slack
- **ClickUp:** REMOVED (cancelled subscription)
- **Telegram:** DEPRECATED (shutdown planned)

---

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│      EMR        │────▶│    Boss DB      │────▶│    Airtable     │
│   (Hospital)    │     │   (SQLite)      │     │  (Downstream)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
       Scrapes               SOURCE               SOURCE
      via relay            (sync'd)              (polling)
                               │                     │
                               ▼                     ▼
                         ┌───────────────────────────────┐
                         │           n8n                 │
                         │    http://localhost:5678      │
                         └───────────────────────────────┘
                                       │
                                       ▼
                         ┌───────────────────────────────┐
                         │           SLACK               │
                         │  #alerts #operations #admissions
                         └───────────────────────────────┘
```

---

## Key Systems

| System | URL/ID | Notes |
|--------|--------|-------|
| **Airtable** | Base: `appv5BwoWyRhT6Lcr` | Patient database (source of truth) |
| **n8n** | localhost:5678 | Automation hub (12 workflows) |
| **ngrok** | kristeen-rootlike-unflirtatiously.ngrok-free.dev | Tunnel for Slack webhooks |
| **Slack** | Zav Hospital workspace | #alerts, #operations, #admissions |
| **Boss API** | localhost:8083 | EMR scraper, SQLite DB |
| **CyberIntern API** | localhost:8082 | 027/о enrichment data (start with `boss`) |
| **Boss TUI** | `~/Projects/boss-tui` | Terminal dashboard |
| **Zav Cloud** | zav-production.up.railway.app | Web dashboard |

---

## n8n Workflows (Active)

| Workflow | ID | Trigger | Destination |
|----------|-----|---------|-------------|
| **Combined Morning Briefing** | dfVgfARoNS9XXMIq | Daily 7 AM | Slack #general |
| Operation plan | T2fTND8RQcNrx6jZc05Wh | Daily 12:00 | Google Sheets + Slack |
| Surgery Checklist | sF3jem3G4RztR9su | Every 30 min | Slack #operations |
| Operations | xBlSfRngiWvEyCFetoHjs | Airtable poll | Slack #operations |
| Boss → Airtable Sync (Simple) | qVgYLgOSvNEWxWQN | Hourly | POST to Boss API /sync/airtable |
| Patient Discharge Hub | h3XuUfInGUY3DDgu | Webhook | Airtable + Slack |
| **Slack: /patient** | SuPFqfszZvm7NrLs | Slack command | Slack (ephemeral) |
| **Slack: /ops** | fVibWFfEsLG4lpg1 | Slack command | Slack (in_channel) |
| **Slack: /beds** | qWJ9XBL9nQlTzHjo | Slack command | Slack (in_channel) |
| **Slack: /vlk** | vRsj4uEe15uIlWaK | Slack command | Slack (in_channel) |
| **Slack: /stats** | e3l4J3KI9tgBSiid | Slack command | Slack (in_channel) |
| **Slack: /surgery** | LTkL7j7i99btWwSu | Slack command | Slack (ephemeral) |
| **MEGALITH 6: Interactive Handler** | y2vWK35PLkwj8zDr | Button clicks | Routes to handlers (51 nodes, 9 routes) |
| **Dovidka Cleanup (Daily)** | ZRbqEpbzkSWNRRM6 | Daily 2 AM | Deletes old Dovidka files from Drive |
| New Patient Admission | SuSKrbIFqFtNx3qO | Every 1 min | Slack #admissions |

**Deprecated (replaced by Combined Morning Briefing):**
- VLK Alert System v2 (S4HtG75YjVc2Z9tr) - now part of morning briefing
- Daily Morning Report (hTwq6zC3mLwPWkrO) - now part of morning briefing
- Overstay Alert (XHveI1Sg8mMnAFed) - now part of morning briefing

---

## Airtable Tables

| Table | ID | Records | Purpose |
|-------|-----|---------|---------|
| Пацієнти | tblcMn6CHbW10pQfq | ~41 | Active patients |
| Операції | tblZccmxy1DxtzIoc | ~11 | Surgeries |
| Виписані | tblXzukwzfwYbr25U | Archive | Discharged patients |

**Discharge Form:** https://airtable.com/appv5BwoWyRhT6Lcr/paglV1hehxnCcuzto/form

**Key Patient Fields for Discharge:**
- `Виписка 027` (fld2BL2dN24ZzxtFZ) - Attachment field for final PDF

---

## Slack Channels

| Channel | Purpose |
|---------|---------|
| #general | Daily briefings, announcements |
| #alerts | VLK alerts, overstay, critical |
| #operations | Surgery schedule, checklists |
| #admissions | Patient intake, discharge |
| #patient-flow | Bed management |

---

## Data Flow Rules

**DO:**
- EMR → Boss: Scrape via Playwright (relay mode required)
- Boss → Airtable: Push via `/push-to-airtable`
- Airtable → n8n: Poll for changes
- n8n → Slack: Post formatted messages

**DO NOT:**
- Sync Airtable → Boss (wrong direction)
- Edit patient data in Slack (read-only)
- Use ClickUp or Telegram (deprecated)

---

## Quick Commands

```bash
# Start Boss TUI (auto-starts n8n + Boss API)
boss

# Toggle relay mode for EMR access
boss-relay

# Check system status
boss-status

# Stop all boss services
boss-stop

# Start ngrok tunnel (required for Slack slash commands)
ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev

# Reconnect MCPs in Claude Code
/mcp
```

### Boss System (zshrc functions)

| Command | Description |
|---------|-------------|
| `boss` | Start TUI (auto-starts n8n + Boss API, rebuilds if needed) |
| `boss-relay` | Start Tailscale relay, then launch TUI |
| `boss-relay-off` | Disable Tailscale relay only |
| `boss-status` | Show status of all services |
| `boss-stop` | Stop Boss API and n8n |
| `zav` | Alias for `boss` |

**Note:** Tailscale relay is NOT started automatically by `boss`. Use `boss-relay` when you need EMR access for scraping.

---

## Slack Slash Commands

Real Slack commands configured in the Zav Hospital workspace:

| Command | Webhook URL | Description |
|---------|-------------|-------------|
| `/patient <name>` | .../webhook/slack-patient | Search patient by name |
| `/ops` | .../webhook/slack-ops | Today's operations (Friday shows Monday) |
| `/beds` | .../webhook/slack-beds | Ward occupancy status |
| `/vlk` | .../webhook/slack-vlk | VLK patients status (critical/warning) |
| `/stats` | .../webhook/slack-stats | Quick system statistics |
| `/surgery` | .../webhook/slack-surgery | Link to surgery scheduling form |

**Base URL:** `https://kristeen-rootlike-unflirtatiously.ngrok-free.dev`

**Note:** ngrok must be running for Slack commands to work. Static domain is already configured - URL won't change on restart.

**To add new commands to Slack:**
1. Go to Slack app settings: api.slack.com/apps → Zav Hospital app
2. Slash Commands → Create New Command
3. Set Request URL to: `https://kristeen-rootlike-unflirtatiously.ngrok-free.dev/webhook/<path>`

---

## Slack Interactivity (Buttons, Modals)

**Interactivity Request URL:** `https://kristeen-rootlike-unflirtatiously.ngrok-free.dev/webhook/slack-interactive`

When user clicks a button in Slack, Slack POSTs to this URL with:
```json
{
  "type": "block_actions",
  "user": {"id": "U...", "name": "username"},
  "channel": {"id": "C..."},
  "actions": [{"action_id": "vlk_schedule_recXXX", "value": "Patient Name"}],
  "response_url": "https://hooks.slack.com/...",
  "trigger_id": "123.456"
}
```

**Action ID patterns:**
- `vlk_schedule_<record_id>` → Opens VLK options (Tuesday/Friday/Done)
- `vlk_done_<record_id>` → Opens VLK result options (+2/+4 months/Unfit)
- `vlk_extend_60_<record_id>` → Updates Airtable with +2 months
- `vlk_extend_120_<record_id>` → Updates Airtable with +4 months
- `vlk_extend_unfit_<record_id>` → Updates Airtable as Unfit
- `surgery_complete_<record_id>` → Mark surgery complete
- `discharge_<record_id>` → Shows "Заповнити форму" button (STEP 1)
- `fill_form_<record_id>` → Opens Airtable form + shows "Згенерувати" button (STEP 2)
- `generate_vypyska_<record_id>` → Generates 027 doc + shows "Підписана" button (STEP 3)
- `vypyska_signed_<record_id>_<doc_id>` → PDF → Airtable → Delete from Drive (STEP 4)
- `dovidka_<record_id>` → Generate hospital stay certificate (Довідка)

**Handled by:** MEGALITH 6: Interactive Handler (y2vWK35PLkwj8zDr)

---

## ngrok Tunnel Setup

Required for Slack to reach local n8n webhooks. Static domain configured.

```bash
# Start tunnel with static domain
ngrok http 5678 --domain=kristeen-rootlike-unflirtatiously.ngrok-free.dev
```

**Known issue:** n8n webhooks created via API don't register properly. Workaround: after API changes, open workflow in n8n UI and click Save.

---

## MEGALITH 6: Interactive Handler (y2vWK35PLkwj8zDr)

Central workflow for all Slack button interactions. **51 nodes, 9 routes.**

### Node Structure
```
Slack Interactive (webhook: /webhook/slack-interactive)
    ↓
Parse Payload (extract actionId, value, user, responseUrl)
    ↓
Route Action (Switch - 9 outputs)
    ├── vlk_schedule_* → Handle VLK → Respond VLK → Acknowledge
    ├── surgery_complete_* → Handle Surgery → Respond Surgery → Acknowledge 2
    ├── discharge_* → Handle Discharge → Get Patient → Build Form URL → Respond Form Link → Acknowledge 3
    ├── vlk_done_* → Handle VLK Done → Respond VLK Done → Acknowledge VLK Done
    ├── vlk_extend_* → Handle VLK Extend → Update Airtable VLK → Respond VLK Extend → Acknowledge VLK Extend
    ├── dovidka_* → Handle Dovidka → Get Patient Dovidka → Format Dovidka Data → Copy Dovidka Template → Fill Dovidka → Format Dovidka Response → Respond Dovidka → Acknowledge Dovidka
    ├── fill_form_* → Handle Fill Form → Get Patient Fill Form → Build Form URL Fill → Respond Fill Form → Ack Fill Form
    ├── generate_vypyska_* → Handle Generate → Get Patient Generate → Copy 027 Generate → Fill 027 Generate → Format Generate Response → Respond Generate → Ack Generate
    └── vypyska_signed_* → Handle Signed → Export PDF → Upload to Airtable → Delete from Drive → Respond Signed → Acknowledge Signed
```

### VLK Flow
1. User clicks patient button → `vlk_schedule_<recordId>`
2. Handle VLK returns options: Tuesday / Friday / VLK Done
3. User clicks VLK Done → `vlk_done_<recordId>`
4. Handle VLK Done returns options: +2 months / +4 months / Unfit
5. User clicks option → `vlk_extend_60|120|unfit_<recordId>`
6. Update Airtable VLK updates: Дата ВЛК, Рішення ВЛК, Дні продовження
7. Respond VLK Extend posts confirmation to Slack

### Discharge Flow (4-Step Button-Driven)
```
STEP 1: Click "Виписати" → discharge_<recordId>
        → Shows "📝 Заповнити форму" button

STEP 2: Click "📝 Заповнити форму" → fill_form_<recordId>
        → Opens prefilled Airtable form
        → Shows "📄 Згенерувати виписку" button

STEP 3: Fill form, click "📄 Згенерувати виписку" → generate_vypyska_<recordId>
        → 027 doc generated in Google Docs
        → Shows "✅ Виписка підписана і здана" button

STEP 4: Chief signs, click "✅ Виписка підписана і здана" → vypyska_signed_<recordId>_<docId>
        → PDF saved to Airtable "Виписка 027" field (fld2BL2dN24ZzxtFZ)
        → Doc deleted from Google Drive
        → DONE!
```

**Key Design Decisions:**
- No polling (user controls timing)
- No webhooks (Airtable free plan limitation)
- Form URL built server-side (button value length limit)
- Each step reveals the next button

### Dovidka Flow (Hospital Stay Certificate)
1. User clicks "📄 Довідка" → `dovidka_<recordId>`
2. Handle Dovidka extracts recordId, patientName
3. Get Patient Dovidka fetches full record from Airtable
4. Format Dovidka Data converts ALL CAPS fields to Title Case (especially workplace)
5. Copy Dovidka Template copies template from Google Drive
6. Fill Dovidka replaces placeholders with formatted patient data
7. Format Dovidka Response builds Slack message with doc link
8. Respond Dovidka posts link to channel

### Credentials
| Service | ID | Purpose |
|---------|-----|---------|
| Airtable | oB0crB7qKyJOGI5a | Patient data + VLK updates |
| Google Drive | rMWvrK8pn4JH2Sl8 | Copy 027 template |
| Google Docs | renz2o80wUGVVoOD | Fill document placeholders |

### Google Drive Resources
- **027 Template:** `1q8FTR4l7oY5KJGLjVDyMYkJNvt6HSV4K3aymn5fykg8`
- **Dovidka Template:** `1uk3RCS2IYqGgLa3jzvAJa1Dqpiiwe5ei8WYYA0sqv3M`
- **Output Folder:** `1ZL3RqSdNVcQ0Gabbz6GdCey59IWuB2EW`

### 027 Template Placeholders
| Placeholder | Airtable Field |
|-------------|----------------|
| `{{ПІБ}}` | ПІБ |
| `{{Дата_народження}}` | Дата народження |
| `{{Діагноз}}` | Повний діагноз (fallback: Діагноз) |
| `{{Дата_госпіталізації}}` | Дата госпіталізації |
| `{{Дата_виписки}}` | Current date (auto) |
| `{{№_історії}}` | № історії |
| `{{Хірург}}` | Хірург |
| `{{Рекомендації}}` | Рекомендації |

### Dovidka Template Placeholders
| Placeholder | Source |
|-------------|--------|
| `{{ДАТА}}` | Today's date (certificate issue date) |
| `{{ПІБ}}` | ПІБ |
| `{{Дата_народження}}` | Дата народження |
| `{{Діагноз}}` | Повний діагноз / Діагноз |
| `{{Дата_госпіталізації}}` | Дата госпіталізації |
| `{{№_історії}}` | № історії |
| `{{Хірург}}` | Хірург |
| `{{Місце_роботи}}` | Заклад (Title Case formatted) |
| `{{Signer1name}}` | Панфьоров С.В. (hardcoded) |
| `{{Signer2name}}` | Кондратов Д.С. (hardcoded) |
| `{{Signer3name}}` | Хірург (surgeon name) |

---

## VLK Tracking

Military medical commission required after 120 days of treatment.

| Status | Days Since Injury | Action |
|--------|-------------------|--------|
| 🟢 OK | <100 | None |
| 🟠 До ВЛК | 100-119 | Schedule soon |
| 🔴 ПОТРІБНА ВЛК | ≥120 | Urgent |
| ✅ Пройдено | VLK completed | Done |

### VLK Alert Thresholds

| Days Since Trauma | Status | Action |
|-------------------|--------|--------|
| <100 | 🟢 OK | None |
| 100-114 | 🟠 Warning | Schedule soon |
| 115-119 | 🟠 Critical Warning | Schedule urgently |
| ≥120 | 🔴 ПОТРІБНА ВЛК | Overdue! |
| VLK completed | ✅ Пройдено | Done (or new cycle if extended) |

### VLK Flow (TO IMPLEMENT)

```
Morning Briefing → Alerts patients needing VLK to Slack
    ↓
User runs /vlk → Shows patients with buttons
    ↓
User clicks patient button → Modal with options:
    ├── 📅 Schedule VLK (Tuesday/Friday) → Alerts team
    └── ✅ Mark VLK Done → Report form:
         ├── Extension: +2 months / +4 months / Discharged
         ├── №Довідки (certificate number)
         └── Upload document (optional) OR Link to Airtable form
```

### VLK Completion Feature (PARTIALLY IMPLEMENTED)

**Current State:** Basic button click → posts to #alerts ✅

**Still TODO:**
- [ ] Modal with Schedule/Done options
- [ ] VLK Done → Report form
- [ ] Airtable update with VLK result
- [ ] Boss TUI duplicate functionality

**Airtable Fields (already exist):**
- `Дата ВЛК` (fldCt5NDGU8vKotHl) - Date VLK was conducted
- `Рішення ВЛК` (fldrC2XBPNOcm3Lhl) - VLK decision (Продовження лікування / Непридатний / Обмежено придатний / Придатний)
- `Дні продовження` (fld9mAFPVh25ueDVm) - Extension days (0 / 60 / 120)

**VLK Decision meanings:**
- **Продовження лікування** = Continue treatment (needs extension days set)
- **Непридатний** = Unfit for service (discharged from army)
- **Обмежено придатний** = Partially fit
- **Придатний** = Fit for service

---

## 🔥🔥🔥 CRITICAL: n8n API Access 🔥🔥🔥

**Claude keeps failing to use n8n API. Here's why and how to fix it.**

### The Problem
```bash
# THIS FAILS - shell doesn't expand $N8N_API_KEY properly
curl -H "X-N8N-API-KEY: $N8N_API_KEY" http://localhost:5678/api/v1/workflows
```

### The Solution
```bash
# Step 1: Get raw key (removes "export" and quotes)
N8N_KEY=$(grep N8N_API_KEY ~/.config/zav-secrets.env | cut -d'"' -f2)

# Step 2: Use the raw value directly
curl -s -H "X-N8N-API-KEY: $N8N_KEY" 'http://localhost:5678/api/v1/workflows' | jq '.data[].name'
```

### Workflow Update Process
```bash
# 1. Get current workflow
curl -s -H "X-N8N-API-KEY: $N8N_KEY" 'http://localhost:5678/api/v1/workflows/WORKFLOW_ID' > /tmp/workflow.json

# 2. Edit the JSON
# (modify /tmp/workflow.json)

# 3. Update workflow
curl -X PUT -H "X-N8N-API-KEY: $N8N_KEY" -H "Content-Type: application/json" \
  'http://localhost:5678/api/v1/workflows/WORKFLOW_ID' -d @/tmp/workflow.json

# 4. Activate if needed
curl -X POST -H "X-N8N-API-KEY: $N8N_KEY" \
  'http://localhost:5678/api/v1/workflows/WORKFLOW_ID/activate'
```

---

## MCP Usage - What Each MCP Does

**CRITICAL:** MCPs have DIFFERENT purposes. Don't confuse them.

| MCP | Purpose | Use For | Cannot Do |
|-----|---------|---------|-----------|
| **airtable** | CRUD operations | Read/write patient records, update fields | - |
| **slack** | Communication | Post messages, read channels | Interactivity setup |
| **n8n-docs** | Node VALIDATION | Build workflow JSON, validate configs | Read/write actual workflows |

### n8n-docs MCP vs n8n API

```
n8n-docs MCP (offline documentation)     n8n REST API (actual workflows)
├── search_nodes()                       ├── GET /api/v1/workflows
├── get_node()                           ├── PUT /api/v1/workflows/{id}
├── validate_node()                      ├── POST /api/v1/workflows/{id}/activate
└── validate_workflow()                  └── GET /api/v1/executions
```

**Rule:** Use n8n-docs to BUILD correct JSON, then use n8n API to DEPLOY it.

### Workflow for Building n8n Nodes
```
1. search_nodes({ query: "slack" })        → Find node type
2. get_node({ nodeType, detail: "standard" }) → Get required properties
3. Write config based on schema
4. validate_node({ nodeType, config })     → Verify before deployment
5. curl PUT to n8n API                     → Deploy to running n8n
```

---

## Boss Ecosystem - Three Tools, Three Purposes

```
┌─────────────────────────────────────────────────────────────┐
│                    BOSS ECOSYSTEM                            │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
        ▼                     ▼                     ▼
┌───────────────┐    ┌────────────────┐    ┌──────────────┐
│  Boss API     │    │  Python CLI    │    │  Rust TUI    │
│  (FastAPI)    │    │  (Rich)        │    │  (Ratatui)   │
│  Port 8083    │    │  HTTP client   │    │  HTTP client │
│  BACKEND      │    │  ONE-SHOT      │    │  REAL-TIME   │
└───────────────┘    └────────────────┘    └──────────────┘
```

| Tool | Type | Use For | Don't Use For |
|------|------|---------|---------------|
| **Boss API** | Backend server | Always running, serves data | Direct interaction |
| **Python CLI** | HTTP client | Quick queries, scripting | Real-time monitoring |
| **Rust TUI** | Dashboard | Real-time monitoring (primary tool) | Automation |

**Rule:** For watching data → Rust TUI. For querying data → Python CLI.

---

## Airtable VLK Fields (Actual Schema)

These fields ALREADY EXIST in Airtable:

| Field | ID | Type | Values |
|-------|-----|------|--------|
| Дата ВЛК | `fldCt5NDGU8vKotHl` | date | - |
| Рішення ВЛК | `fldrC2XBPNOcm3Lhl` | singleSelect | Продовження лікування, Непридатний, Обмежено придатний, Придатний |
| Дні продовження | `fld9mAFPVh25ueDVm` | number | 0 / 60 / 120 |
| ВЛК статус | `fldcfU96tCM4hWoX4` | formula | Calculated |

**VLK Decision meanings:**
- **Продовження лікування** = Continue treatment (needs extension)
- **Непридатний** = Unfit for service (discharged from army)
- **Обмежено придатний** = Partially fit
- **Придатний** = Fit for service

---

## Active MCPs

| MCP | Purpose |
|-----|---------|
| slack | Slack communication |
| airtable | Patient database |
| n8n-docs | Workflow node schemas (validation only) |

---

## Environment Variables

All stored in `~/.config/zav-secrets.env`:

```bash
BOSS_API_URL=http://localhost:8083
BOSS_API_KEY=<key>                    # NEW: API key auth for Boss API
N8N_URL=http://localhost:5678
N8N_API_KEY=<key>
AIRTABLE_TOKEN=<token>
AIRTABLE_BASE=appv5BwoWyRhT6Lcr
CYBERINTERN_API_URL=http://localhost:8082  # For 027/о enrichment
SLACK_BOT_TOKEN=<token>
NGROK_AUTHTOKEN=<token>
```

**Note:** BOSS_API_KEY is optional. If not set, Boss API allows unauthenticated access (development mode).

---

## Documentation Index

| Doc | Location | Purpose |
|-----|----------|---------|
| Airtable Schema | docs/AIRTABLE_NEW_COLUMNS.md | Field definitions |
| Boss TUI | docs/BOSS_TUI_UPGRADE.md | Dashboard guide |
| n8n Management | docs/N8N_WORKFLOW_MANAGEMENT.md | API best practices |
| MCP Setup | docs/MCP_BEST_PRACTICES.md | Configuration guide |
| VLK Workflow | docs/VLK_ALERTS_WORKFLOW.md | Military commission tracking |
| User Guide | docs/USER_GUIDE.md | End-user documentation |

---

## Response Formatting

When responding to Zav Hospital queries, use:

**Header:**
```
╔══════════════════════════════════════════════════════╗
║  🏥 ZAV HOSPITAL │ [Context]                         ║
╚══════════════════════════════════════════════════════╝
```

**Status Indicators:**
- 🔴 CRITICAL / Urgent
- 🟠 WARNING / Attention
- 🟢 INFO / Normal
- ✅ Complete

---

## Claude Code Skills (CLI)

| Command | Description |
|---------|-------------|
| `/zav` | Show menu |
| `/alerts` | Aggregated alerts |
| `/daily` | Morning briefing |
| `/patient` | Patient lookup |
| `/ops` | Today's operations |
| `/beds` | Bed status |

**Note:** These are Claude Code skills, not Slack commands. See "Slack Slash Commands" section above for real Slack commands.

---

**Archive:** Old docs moved to `archive/` folder (sessions, handoffs, legacy)
