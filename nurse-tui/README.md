# Nurse TUI 🩺

Terminal-based temperature sheet automation for hospital EMR.

## Features

- **One-click login** - Save multiple nurse credentials, quick switch
- **Auto-fill vitals** - Generate realistic BP/pulse/temp values
- **Batch submit** - BRRRRRT through all patients
- **Weird patient detection** - Flags abnormal values for manual review

## Workflow

```
L → Login (select nurse)
R → Refresh (load patients)
A → Select All (normal patients only)
Enter → Confirm
Y → Submit (BRRRRRT!)
```

## Keybindings

| Key | Action |
|-----|--------|
| `L` | Open nurse login |
| `R` | Load/refresh patients |
| `A` | Select all normal patients |
| `Space` | Toggle selection |
| `j/k` | Navigate up/down |
| `Enter` | Confirm submit |
| `Y/N` | Yes/No in dialogs |
| `Q` | Quit |
| `Esc` | Back/Cancel |

## Nurse Management

In nurse select dialog:
- `1-9, 0` - Quick login by number
- `+` - Add new nurse
- `-` - Remove nurse
- `Enter` - Login selected

## Build

```bash
cargo build --release
```

Binary: `target/release/nurse-tui`

## Requirements

- Chrome/Chromium browser (for automation)
- EMR credentials

## Environment

Create `.env` or set:
```
NURSE_EMR_EMAIL=nurse@hospital.com
NURSE_EMR_PASSWORD=secret
```

Or add nurses via TUI (saved to `~/.config/nurse-tui/nurse-tui.json`).

## Project Structure

```
src/
├── main.rs          # Entry point, event loop
├── app.rs           # App state, nurse profiles
├── emr/
│   ├── mod.rs       # Module exports
│   ├── client.rs    # Browser automation
│   └── temperature.rs # Vitals generation, EMR submit
└── ui/
    ├── mod.rs       # UI router, dialogs
    └── temperature.rs # Patient list view
```

---
Built with 🦀 Rust + Ratatui + Chromiumoxide
