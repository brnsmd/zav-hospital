# Browser Automation Setup - Zav Project

**Last Updated**: January 20, 2026
**Status**: ✅ WORKING

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Claude Code CLI                          │
│                         │                                   │
│           ┌─────────────┴─────────────┐                     │
│           ▼                           ▼                     │
│  ┌─────────────────┐        ┌──────────────────┐           │
│  │ claude-in-chrome│        │ chrome-devtools  │           │
│  │      MCP        │        │      MCP         │           │
│  │  (Extension)    │        │ (Remote Debug)   │           │
│  └────────┬────────┘        └────────┬─────────┘           │
│           │                          │                      │
│           ▼                          ▼                      │
│  ┌─────────────────┐        ┌──────────────────┐           │
│  │ Chrome Browser  │        │ Chromium         │           │
│  │ (with extension)│        │ (in toolbox)     │           │
│  └─────────────────┘        └──────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Method 1: Chrome DevTools MCP (RECOMMENDED for Fedora Atomic)

### Why This Method?
- Works on Fedora Atomic/Silverblue/Kinoite
- No Chrome extension installation required
- Connects via Chrome DevTools Protocol (CDP)
- Full browser automation capabilities

### Setup Steps

#### 1. Create Toolbox Container with Chromium
```bash
# Create toolbox container
toolbox create chrome-dev

# Install Chromium inside container
toolbox run -c chrome-dev bash -c "sudo dnf install -y chromium"
```

#### 2. Create Chrome Wrapper Script
Create file at `/opt/google/chrome/chrome`:
```bash
#!/bin/bash
# Wrapper script to launch Chromium from toolbox with remote debugging
toolbox run -c chrome-dev chromium-browser --remote-debugging-port=9222 "$@"
```

Make executable:
```bash
chmod +x /opt/google/chrome/chrome
```

#### 3. Configure MCP in Claude Code
```bash
claude mcp add --transport stdio chrome-devtools -- npx -y chrome-devtools-mcp@latest --browser-url=http://127.0.0.1:9222
```

#### 4. Launch Chromium with Remote Debugging
```bash
toolbox run -c chrome-dev chromium-browser \
  --remote-debugging-port=9222 \
  --no-sandbox \
  --disable-dev-shm-usage \
  http://localhost:8082 &
```

#### 5. Verify Connection
```bash
# Check if debugging endpoint is available
curl http://127.0.0.1:9222/json/version
```

### Available Tools

| Tool | Purpose |
|------|---------|
| `mcp__chrome-devtools__list_pages` | List open browser tabs |
| `mcp__chrome-devtools__select_page` | Switch to specific tab |
| `mcp__chrome-devtools__take_snapshot` | Get accessibility tree (DOM) |
| `mcp__chrome-devtools__take_screenshot` | Visual screenshot |
| `mcp__chrome-devtools__click` | Click on element by uid |
| `mcp__chrome-devtools__fill` | Fill form input |
| `mcp__chrome-devtools__fill_form` | Fill multiple form fields |
| `mcp__chrome-devtools__navigate_page` | Navigate/reload page |
| `mcp__chrome-devtools__press_key` | Press keyboard key |
| `mcp__chrome-devtools__hover` | Hover over element |
| `mcp__chrome-devtools__evaluate_script` | Run JavaScript |
| `mcp__chrome-devtools__wait_for` | Wait for text to appear |

### Troubleshooting

**Problem**: Connection refused
```bash
# Check if Chromium is running with remote debugging
ps aux | grep chromium
# Should see --remote-debugging-port=9222

# Check if port is listening
netstat -tlnp | grep 9222
```

**Problem**: MCP not connecting
```bash
# Reconnect MCP
/mcp
```

**Problem**: Toolbox not found
```bash
# List available toolboxes
toolbox list

# Enter toolbox manually
toolbox enter chrome-dev
```

---

## Method 2: Claude-in-Chrome (Alternative)

### Requirements
- Chrome browser with Claude extension installed
- Extension must be running
- Works on standard Linux distributions

### Setup
1. Install Chrome browser
2. Install Claude browser extension from https://claude.ai/chrome
3. Restart Chrome
4. MCP automatically connects

### Available Tools
Similar to chrome-devtools but with additional features:
- `mcp__claude-in-chrome__computer` - Full computer control
- `mcp__claude-in-chrome__gif_creator` - Record GIFs
- `mcp__claude-in-chrome__upload_image` - Upload images

### Note
This method requires the Chrome extension which may not work on all systems (especially Fedora Atomic with Flatpak/toolbox setup).

---

## Current Configuration

### Active Method: Chrome DevTools MCP
- **Browser**: Chromium in toolbox container `chrome-dev`
- **Debug Port**: 9222
- **Connection**: `http://127.0.0.1:9222`
- **Status**: ✅ Connected

### Verified Working
```
# MCP Tools Available:
✅ mcp__chrome-devtools__list_pages
✅ mcp__chrome-devtools__take_snapshot
✅ mcp__chrome-devtools__click
✅ mcp__chrome-devtools__fill
✅ mcp__chrome-devtools__navigate_page
✅ mcp__chrome-devtools__press_key
✅ mcp__chrome-devtools__hover
✅ mcp__chrome-devtools__evaluate_script
```

---

## Usage Examples

### Navigate to URL
```
mcp__chrome-devtools__navigate_page
  url: "https://app.clickup.com"
```

### Click Element
```
# First, take snapshot to get element uid
mcp__chrome-devtools__take_snapshot

# Then click using uid from snapshot
mcp__chrome-devtools__click
  uid: "39_97"
```

### Fill Form
```
mcp__chrome-devtools__fill
  uid: "input_uid"
  value: "text to enter"
```

### Wait for Element
```
mcp__chrome-devtools__wait_for
  text: "Success"
  timeout: 5000
```

---

## Integration with Zav Project

### Use Cases
1. **ClickUp Automation** - Tasks that can't be done via API (status changes, dashboards)
2. **Testing** - Visual verification of UI changes
3. **Screenshots** - Documentation and reporting
4. **Form Filling** - Bulk data entry

### Best Practices
1. Always take snapshot before clicking to get current UIDs
2. Use `wait_for` after navigation to ensure page loaded
3. Prefer API calls when available (faster, more reliable)
4. Use browser automation only when API doesn't support the operation

---

**Document Version**: 1.0
**Tested On**: Fedora Atomic 42, Sway WM
