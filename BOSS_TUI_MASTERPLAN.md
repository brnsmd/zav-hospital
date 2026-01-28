# BOSS-TUI MASTERPLAN - THE GREAT UI HUNT

**Created:** 2026-01-25
**Status:** PLANNING
**Tribe:** Grug (User) + Clug (Claude) - Co-Chiefs

---

## OVERVIEW

Transform Boss-TUI from a functional dashboard into a POLISHED, PROFESSIONAL hospital management interface using the full power of the Ratatui ecosystem.

---

## PHASE 0: CRITICAL FIXES (Hunt the Obvious Boars) ✅ COMPLETE

### 0.1 Fix Button 8 Not Working ✅
**Priority:** CRITICAL
**Time:** 5 minutes
**Location:** `main.rs:148`
**Status:** DONE (2026-01-25)

```rust
// BEFORE (broken):
KeyCode::Char(c @ '1'..='7') => {

// AFTER (fixed):
KeyCode::Char(c @ '1'..='8') => {
```

### 0.2 Add Operations Tab Navigation
**Priority:** LOW (deferred to Phase 4)
**Note:** Operations and Sync tabs display data but don't have row selection.
         This is a visual-only enhancement, not a blocker.

---

## PHASE 1: POWER-ON SEQUENCE (The Grand Entrance)

### 1.1 Add Dependencies
```toml
# Cargo.toml additions
tui-big-text = "0.7"           # Large ASCII logo
throbber-widgets-tui = "0.7"   # Animated spinners
tachyonfx = "0.11"             # Shader effects (optional, heavier)
```

### 1.2 Create Splash Screen Module
**New file:** `src/ui/splash.rs`

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│        ███████╗ █████╗ ██╗   ██╗                           │
│        ╚══███╔╝██╔══██╗██║   ██║                           │
│          ███╔╝ ███████║██║   ██║                           │
│         ███╔╝  ██╔══██║╚██╗ ██╔╝                           │
│        ███████╗██║  ██║ ╚████╔╝                            │
│        ╚══════╝╚═╝  ╚═╝  ╚═══╝                             │
│                                                             │
│              HOSPITAL MANAGEMENT SYSTEM                     │
│                                                             │
│                   [████████░░] 80%                          │
│                                                             │
│        ⣾ Connecting to Boss API...                          │
│        ✓ n8n connected                                      │
│        ✓ Airtable connected                                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 1.3 Splash State Machine
```rust
pub enum StartupPhase {
    Logo,           // Show logo (0.5s)
    Connecting,     // Check services (animated)
    Loading,        // Fetch data (progress bar)
    Ready,          // Fade to main UI
}
```

### 1.4 Service Check Animation
- Spinner next to each service while checking
- ✓ Green when connected
- ✗ Red if failed (with retry option)

### 1.5 Transition Effect (Optional with tachyonfx)
- Fade out splash
- Sweep in main UI

---

## PHASE 2: WARDS TAB (The Visual Hunt)

### 2.1 New Tab: Wards [9]
**From STATUS.md requirements:**
- [ ] Wards tab with visual layout
- [ ] Ward cleanliness colors (Green/Yellow/Red)
- [ ] Allow changing ward cleanliness via keyboard

### 2.2 Ward Canvas Layout
Using ratatui Canvas widget with HalfBlock markers:

```
┌─────────────────────────────────────────────────────────────┐
│  WARD 1                    │  WARD 2                        │
│  ┌────┬────┬────┬────┐     │  ┌────┬────┬────┬────┐         │
│  │ 1A │ 1B │ 1C │ 1D │     │  │ 2A │ 2B │ 2C │ 2D │         │
│  │ 🟢 │ 🔴 │ 🟢 │ 🟡 │     │  │ 🔴 │ 🟢 │ 🟢 │ 🟢 │         │
│  ├────┼────┼────┼────┤     │  ├────┼────┼────┼────┤         │
│  │ 1E │ 1F │ 1G │ 1H │     │  │ 2E │ 2F │ 2G │ 2H │         │
│  │ 🟢 │ 🟢 │    │ 🔴 │     │  │ 🟡 │ 🟢 │    │    │         │
│  └────┴────┴────┴────┘     │  └────┴────┴────┴────┘         │
│  Occupied: 6/8  Clean: 5   │  Occupied: 5/8  Clean: 4       │
├─────────────────────────────────────────────────────────────┤
│  LEGEND: 🟢 Clean  🟡 Needs cleaning  🔴 Critical/ICU       │
│  KEYS: [←→] Select bed  [c] Toggle cleanliness  [Enter] Details
└─────────────────────────────────────────────────────────────┘
```

### 2.3 Ward Data Model
```rust
pub struct WardBed {
    pub ward: String,
    pub bed: String,
    pub patient: Option<String>,
    pub cleanliness: Cleanliness,
    pub is_icu: bool,
}

pub enum Cleanliness {
    Clean,      // Green
    NeedsCleaning, // Yellow
    Critical,   // Red (ICU or urgent)
}
```

### 2.4 Ward Interactions
| Key | Action |
|-----|--------|
| ←/→ | Select bed |
| ↑/↓ | Select ward |
| c | Cycle cleanliness |
| Enter | Open patient detail |
| r | Refresh ward data |

---

## PHASE 3: HEADER ENHANCEMENT

### 3.1 Add Sparklines to Header
Mini patient trend visualization:
```
┌─ ZAV ─ LAN ── BOSS ── N8N ── AIR ─│ ВЛК:5 │ 🔴 3 │ ▁▂▄▅▇ │ ⟳ 5m ago ─┐
```

Using ratatui's Sparkline widget for patient count trend.

### 3.2 Better VLK Badge
Current: `ВЛК:5`
Enhanced: `🔴 ВЛК 5 critical │ 🟠 3 warning`

### 3.3 Animated Sync Indicator
Current: `[|] SYNC 5s`
Enhanced: Better spinner from throbber-widgets-tui

---

## PHASE 4: TABLE IMPROVEMENTS

### 4.1 Sortable Column Headers
Click or key to sort by column:
```
│ # │ Case ▼ │ Name │ Ward │ Bed │ Doctor │ Days ▲ │ Status │
```

### 4.2 Column Width Auto-Adjust
Calculate optimal widths based on content.

### 4.3 Row Highlighting Improvements
- Alternating row backgrounds
- ICU rows with red left border
- VLK critical rows with yellow highlight

---

## PHASE 5: IMPROVED POPUPS

### 5.1 Confirmation Dialogs
For destructive actions (discharge, VLK extend):
```
┌────────────────────────────────────────┐
│  Confirm Discharge                      │
│                                         │
│  Patient: Петренко І.В.                 │
│  Ward 3, Bed 3A                         │
│  Days in hospital: 45                   │
│                                         │
│  [Enter] Confirm    [Esc] Cancel        │
└────────────────────────────────────────┘
```

### 5.2 Toast Queue
Multiple toasts stack, auto-dismiss after 3s:
```
┌────────────────────────────┐
│ ✓ Sync completed           │
│ ✓ VLK updated: +60 days    │
└────────────────────────────┘
```

### 5.3 Error Details Modal
When error occurs, show full details on Enter:
```
┌─ Error Details ──────────────────────────┐
│ Boss API: Connection refused             │
│ URL: http://localhost:8083/patients      │
│ Time: 14:32:15                           │
│                                          │
│ [r] Retry    [Esc] Dismiss               │
└──────────────────────────────────────────┘
```

---

## PHASE 6: STATS VISUALIZATION

### 6.1 Bar Charts for Ward Distribution
Using ratatui BarChart:
```
Ward Distribution
█████████ 9  Ward 1
██████    6  Ward 2
████      4  Ward 3
███       3  ICU
```

### 6.2 Pie Chart for VLK Status
Using tui-piechart (optional):
```
    ╭──────╮
   ╱ 🟢 OK  ╲
  │ 🟠 Warn  │
   ╲ 🔴 Crit╱
    ╰──────╯
```

### 6.3 Timeline Sparkline
Hospital census over last 7 days.

---

## PHASE 7: KEYBOARD NAVIGATION IMPROVEMENTS

### 7.1 Vim-Style Number Prefix
`5j` = move down 5 items

### 7.2 Quick Jump
`/name<Enter>` = jump to first match

### 7.3 Tab History
`<Backspace>` = return to previous tab

### 7.4 Global Search
`Ctrl+/` = search across all tabs

---

## PHASE 8: FOOTER ENHANCEMENT

### 8.1 Context-Sensitive Shortcuts
Show only relevant shortcuts for current state.

### 8.2 Status Line Sections
```
│ Patients: 42 │ VLK: 5 │ Ops: 3 │ Sync: 15m │ v0.2.0 │
```

### 8.3 Progress Indicator for Long Operations
```
│ Syncing... [████████░░] 80% │
```

---

## IMPLEMENTATION ORDER

### Sprint 1: Foundation (Critical) ✅ COMPLETE 2026-01-25
1. [x] Fix button 8 (5 min) ✅ DONE 2026-01-25
2. [x] Add tui-big-text, throbber-widgets-tui to Cargo.toml ✅
3. [x] Create splash.rs module ✅
4. [x] Implement basic splash screen (logo + progress) ✅
5. [x] Wire up splash to main.rs ✅

**Sprint 1 Details:**
- Updated ratatui from 0.29 → 0.30 (required for compatible deps)
- Added tui-big-text 0.8, throbber-widgets-tui 0.10
- Created `src/ui/splash.rs` with:
  - BigText "ZAV" logo
  - Progress bar with phase text
  - Service status list (Boss API, n8n, Airtable)
  - Animated throbber for checking state
- Added StartupPhase enum to app.rs
- Modified main.rs with run_startup_sequence() function
- Service checks run in sequence with visual feedback
- User can press 'q' to quit during startup

### Sprint 2: Power-On Polish ✅ COMPLETE 2026-01-25
1. [x] Add service check animation ✅ (ServiceCheckState enum in splash.rs)
2. [x] Add spinner for each service ✅ (Throbber widget for Checking state)
3. [x] Implement progress bar during data fetch ✅ (Gauge widget in splash.rs)
4. [x] Add fade transition (tachyonfx) ✅ (fade_to black, 500ms QuadOut easing)

**Sprint 2 Details:**
- Added tachyonfx 0.22 for ratatui 0.30 compatibility
- Created `StartupPhase::Transitioning` phase
- Fade-to-black effect (500ms) runs after "Ready!" message
- User can still press 'q' to quit during transition

### Sprint 3: Wards Tab ✅ COMPLETE 2026-01-25
1. [x] Create wards.rs module ✅
2. [x] Add Tab::Wards to enum ✅
3. [x] Implement ward grid layout ✅
4. [x] Add bed selection navigation ✅
5. [x] Implement cleanliness toggle ✅
6. [x] Cleanliness persists to ~/.config/boss-tui/wards.json ✅

**Sprint 3 Details:**
- Created `src/models/ward.rs` with Cleanliness enum and WardCleanlinessData
- Added Tab::Wards (key '9', index 8)
- Created `src/ui/wards.rs` with visual grid layout
- Ward data derived from existing patient data (ward + bed fields)
- Navigation: Tab/Shift-Tab or h/l for wards, j/k for beds
- 'c' key cycles cleanliness (Clean → NeedsCleaning → Critical)
- Added `dirs` crate for config path
- Cleanliness state saves to JSON and persists across restarts

### Sprint 4: Visual Polish ✅ COMPLETE 2026-01-25
1. [x] Add sparkline to header ✅ 2026-01-25
2. [x] Improve table row highlighting ✅ 2026-01-25
3. [x] Add confirmation dialogs ✅ 2026-01-25
4. [x] Implement toast queue ✅ 2026-01-25
5. [x] Better error display ✅ 2026-01-25

### Sprint 5: Advanced Features ✅ COMPLETE 2026-01-25
1. [x] Sortable columns ✅ - Visual indicators (▲/▼) on sorted column headers
2. [x] Bar charts in stats ✅ - Ward distribution BarChart widget
3. [x] Keyboard navigation improvements ✅ - Backspace returns to previous tab
4. [x] Footer status line ✅ - Patients/VLK/Ops counts + sync time + version

---

## NEW FILES TO CREATE

| File | Purpose |
|------|---------|
| `src/ui/splash.rs` | Power-on splash screen |
| `src/ui/wards.rs` | Ward visual layout tab |
| `src/models/ward.rs` | Ward/bed data models |
| `src/ui/confirm.rs` | Confirmation dialog |

---

## CARGO.TOML CHANGES

```toml
[dependencies]
# Existing...

# NEW: Visual enhancements
tui-big-text = "0.7"
throbber-widgets-tui = "0.7"

# OPTIONAL: Advanced effects
# tachyonfx = "0.11"
# tui-piechart = "0.2"
```

---

## TESTING CHECKLIST

### Manual Tests
- [x] Button 8 switches to Operations tab ✅
- [x] Splash screen displays on startup ✅
- [x] Progress bar updates during loading ✅
- [x] Services show correct status ✅
- [ ] Wards tab renders correctly (READY FOR TESTING)
- [ ] Cleanliness toggle works (READY FOR TESTING)
- [ ] Cleanliness persists after restart (READY FOR TESTING)
- [x] All existing features still work ✅

### Edge Cases
- [ ] Startup with Boss API offline
- [ ] Startup with n8n offline
- [ ] Startup with Airtable offline
- [ ] Small terminal (< 80 columns)
- [ ] Very large patient list (100+)

---

## SUCCESS CRITERIA

1. **Power-on feels professional** - Logo, progress, smooth transition
2. **Wards tab is useful** - Visual bed layout, cleanliness tracking
3. **Interface is polished** - Consistent colors, good spacing, no jank
4. **All 9 tabs work** - 1-9 keyboard shortcuts functional
5. **Error handling is graceful** - Clear messages, retry options
6. **Performance is maintained** - 60+ FPS, responsive input

---

## NOTES

- Keep it simple - don't over-engineer
- Test on small terminals (80x24)
- Ukrainian text must display correctly
- All changes backward compatible
- Document new keyboard shortcuts in help

---

## PHASE 9: RUST ALL-IN-ONE (Embedded Server) ✅ COMPLETE 2026-01-27

### 9.1 Embedded API Server
- [x] **src/server/mod.rs** - Server orchestration
- [x] **src/server/db.rs** - SQLite database (50+ fields)
- [x] **src/server/routes.rs** - 15 API endpoints

### 9.2 Run Modes
```bash
./boss-tui              # TUI + Server (default)
./boss-tui --server     # Server only
./boss-tui --tui        # TUI only
```

### 9.3 Binary Stats
- **Size:** 7.0MB
- **Contains:** TUI + API Server + SQLite + HTTP Client
- **Port:** 8083

---

## PHASE 10: RUST SCRAPER (The Final Hunt) ✅ COMPLETE 2026-01-28

### Goal
Replace Python Playwright scraper with `chromiumoxide` (Rust CDP client).

### Why
- True single binary (no Python dependency)
- Smaller footprint (~8MB vs ~50MB)
- Direct function calls instead of subprocess

### Implementation
See: `/var/home/htsapenko/Projects/Zav/RUST_SCRAPER_MASTERPLAN.md`

### Completed Steps
1. [x] Add `chromiumoxide = "0.7"` to Cargo.toml ✅
2. [x] Create `src/scraper/` module structure ✅
3. [x] Implement browser launch ✅
4. [x] Implement login flow ✅
5. [x] Implement patient list extraction ✅
6. [x] Implement detail page extraction ✅
7. [x] Update routes.rs to use Rust scraper ✅
8. [x] Remove Python subprocess calls ✅
9. [ ] Test with real EMR (requires relay mode)

### Files Created
- `src/scraper/mod.rs` - EMRScraper, login, API (230 lines)
- `src/scraper/browser.rs` - Browser lifecycle, JS eval (230 lines)
- `src/scraper/types.rs` - Data types (100 lines)
- `src/scraper/patients.rs` - Table extraction (250 lines)
- `src/scraper/enrichment.rs` - Detail + diagnosis (300 lines)

**Total: ~1100 lines of Rust replacing 845 lines of Python**

---

**GRUG READY? LET'S HUNT!** 🪓
