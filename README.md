# TimerKiller — Windows MVP

A Windows-only desktop productivity enforcement tool combining a Pomodoro timer with hard application blocking.

**Core Promise:** Applications (e.g., games) remain blocked until you complete your daily focus goal.

---

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Run the Application

```bash
python run.py
```

The app will:
- Create `app/state.json` with default settings (180-minute daily goal)
- Start the background enforcer thread immediately
- Launch the UI window

---

## Usage

### Timer
1. Click **Start Focus** to begin a Pomodoro session (25 minutes)
2. Click **Pause** to end the session and add time to today's total
3. Repeat until daily goal is met

### Blocked Apps
1. Click **+ Add App** and enter a process name (e.g., `steam.exe`, `overwatch.exe`)
2. The app will be blocked until your daily goal is met
3. Click **- Remove App** to stop blocking an application

### Status
- **Goal: X / Y minutes** — Shows progress toward daily goal
- **Status: Goal Met!** — All apps unblocked (green highlight)

---

## How It Works

**State File:** `app/state.json` — Single source of truth for all application state
```json
{
  "daily_goal_minutes": 180,
  "focused_minutes_today": 0,
  "pomodoro_active": false,
  "pomodoro_start_ts": null,
  "blocked_apps": ["steam.exe", "overwatch.exe"],
  "last_reset_date": "2024-01-23"
}
```

**Enforcement:**
- Background thread continuously monitors processes
- When a blocked app starts AND daily goal is NOT met → Process killed immediately
- No warning. No confirmation. No delay.
- Once daily goal is met → All blocking stops

**Daily Reset:**
- Automatically resets `focused_minutes_today` when calendar day changes
- Blocking resumes at 00:00 unless goal was met

---

## Architecture

```
app/
├── main.py              # Entry point (starts enforcer + UI)
├── state_manager.py     # State persistence & access
├── pomodoro.py          # Timer logic
├── blocker.py           # Process enforcement (background thread)
├── ui.py                # PySide6 UI
├── state.json           # Application state
└── __init__.py          # Package initialization
```

### Module Responsibilities

| Module | Purpose |
|--------|---------|
| **state_manager** | Load/save state, thread-safe access, daily reset |
| **pomodoro** | Timer tracking, elapsed time calculation |
| **blocker** | Process monitoring & killing (independent thread) |
| **ui** | PySide6 window, user interactions |
| **main** | Bootstrap, start enforcer thread, launch UI |

---

## Testing Scenarios

1. **Start app → Try to open Steam → Steam closes immediately** ✓
2. **Start Pomodoro → Time increments correctly** ✓
3. **Pause Pomodoro → Time stops incrementing** ✓
4. **Reach daily goal → Steam launches normally** ✓
5. **Close UI → Blocking still active** ✓
6. **Reboot Windows → App auto-starts → Blocking resumes** (Optional setup)

---

## Configuration

### Daily Goal
Edit `app/state.json` and change `daily_goal_minutes`:
```json
"daily_goal_minutes": 120
```

### Blocked Apps
Edit `app/state.json` and add/remove from `blocked_apps`:
```json
"blocked_apps": ["steam.exe", "discord.exe", "bluestacks.exe"]
```

Or use the UI to add/remove apps dynamically.

---

## Logging

Application logs are saved to `app/timerkiller.log` and also printed to console.

Check logs for:
- Process kills (enforcement events)
- State changes
- Errors or warnings

---

## Windows Startup (Optional)

To auto-start TimerKiller on Windows boot:
1. Run the app once
2. It will add itself to Windows startup registry

Or manually add to `HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`:
```
Key: "TimerKiller"
Value: "python -m timerkiller"
```

---

## Non-Goals (MVP)

The following are **not** included in this MVP:
- Website blocking
- Network filtering
- Scheduling (day-specific rules)
- Analytics dashboards
- Anti-tamper protection
- Kernel drivers

These are planned for future versions.

---

## Troubleshooting

### App won't launch
- Check that Python 3.11+ is installed
- Verify `PySide6` and `psutil` are installed: `pip install -r requirements.txt`
- Check `app/timerkiller.log` for errors

### Blocked apps aren't being killed
- Verify app name is correct (use Task Manager to check exact process name)
- Check that goal is NOT met: Refresh UI to see current progress
- Ensure enforcer thread is running (check `timerkiller.log`)

### Daily goal doesn't reset
- Check `state.json` — `last_reset_date` should be today's date
- Relaunch the app to trigger daily reset logic

---

## Support

For bugs, feature requests, or questions, refer to the project specification in `.github/instructions/`.

---
