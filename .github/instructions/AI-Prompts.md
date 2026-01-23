# TimerKiller AI Prompt Chunks

Use these focused prompts when implementing or reviewing each module. Each prompt includes context, requirements, and testing criteria.

---

## 1. state_manager.py

**Purpose:** Load, save, and manage application state with daily reset logic.

**Prompt:**

```
Create a state_manager.py module for TimerKiller that handles persistent JSON state.

REQUIREMENTS:
1. Load state from app/state.json (or create with defaults if missing)
2. Save state atomically to prevent corruption
3. Auto-reset focused_minutes_today when calendar day changes
4. Provide thread-safe getter/setter methods
5. Initialize missing keys gracefully

STATE STRUCTURE:
{
  "daily_goal_minutes": 180,
  "focused_minutes_today": 0,
  "pomodoro_active": false,
  "pomodoro_start_ts": null,
  "blocked_apps": ["steam.exe", "overwatch.exe"],
  "last_reset_date": "YYYY-MM-DD"
}

KEY FUNCTIONS:
- load_state() → dict (load from disk, create if missing)
- save_state(state: dict) → None (atomic write)
- get_focused_minutes() → int
- set_focused_minutes(minutes: int) → None
- add_blocked_app(app_name: str) → None
- remove_blocked_app(app_name: str) → None
- get_blocked_apps() → list
- get_daily_goal() → int
- set_daily_goal(minutes: int) → None
- is_goal_met() → bool (focused_minutes_today >= daily_goal_minutes)
- reset_if_day_changed() → None (check last_reset_date, reset if new day)

CONSTRAINTS:
- Use locks for thread safety (threading.Lock)
- Handle missing state.json gracefully
- Don't crash if JSON is malformed (log error, create default)
- All mutations must call save_state() immediately

TESTING:
- Create state.json if missing
- Load existing state correctly
- Daily reset triggers on new calendar day
- Concurrent reads don't block
- State persists across application restarts
```

---

## 2. pomodoro.py

**Purpose:** Manage Pomodoro timer, state tracking, and focus time accumulation.

**Prompt:**

```
Create a pomodoro.py module for TimerKiller that tracks focus sessions.

REQUIREMENTS:
1. 25-minute focus sessions (FOCUS_DURATION = 1500 seconds)
2. 5-minute breaks (BREAK_DURATION = 300 seconds)
3. Only focus time counts toward daily goal
4. Timer resilient to UI refresh (use timestamps, not counters)
5. Pause/resume capability

CORE FUNCTIONS:
- start_focus_session() → None (set pomodoro_active=true, record start_ts)
- pause_session() → None (accumulate focused_minutes_today, set active=false)
- get_elapsed_seconds() → int (calculate from start_ts, handle pause state)
- is_session_active() → bool
- get_remaining_seconds() → int (for display in UI)
- update_focus_minutes() → None (called by background thread, accumulates time)
- reset_for_new_session() → None (prep for next Pomodoro)

BEHAVIOR:
- Timer uses time.time() for resilience to pauses
- Elapsed time = current_time - pomodoro_start_ts
- When pause_session(): focused_minutes_today += elapsed_seconds / 60
- Set pomodoro_active=False, pomodoro_start_ts=None
- Check if daily goal is met after each pause

CONSTRAINTS:
- No actual Sleep timers (use background thread polling)
- State always written via state_manager
- Thread-safe updates
- Handle edge cases: pause without start, double pause, etc.

TESTING:
- Start session → elapsed time increments
- Pause session → focused_minutes_today increases
- Multiple sessions accumulate correctly
- Pause prevents time from counting
- Goal met triggers immediately after pause
```

---

## 3. blocker.py

**Purpose:** Background process monitor that kills blocked apps when goal is NOT met.

**Prompt:**

```
Create a blocker.py module for TimerKiller that enforces app blocking.

REQUIREMENTS:
1. Continuous process monitoring (poll every 1-2 seconds)
2. Kill blocked processes if goal is NOT met
3. Never crash; handle missing processes gracefully
4. Run in background thread (started by main.py)
5. Check state_manager for current goal/progress
6. Independent of UI (must run even if UI closes)

CORE FUNCTION:
- start_enforcer() → None (infinite loop in background thread)

ENFORCER LOOP LOGIC:
```
while True:
    state = state_manager.load_state()
    
    if state['focused_minutes_today'] >= state['daily_goal_minutes']:
        # Goal met, all apps allowed
        time.sleep(2)
        continue
    
    # Goal NOT met, enforce blocking
    blocked_apps = state['blocked_apps']
    running_processes = psutil.process_iter(['name'])
    
    for proc in running_processes:
        try:
            if proc.name().lower() in [app.lower() for app in blocked_apps]:
                proc.kill()  # Immediate termination, no warning
                logging.info(f"Killed blocked process: {proc.name()}")
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass  # Process disappeared or permission denied
    
    time.sleep(1.5)  # Poll interval
```

CONSTRAINTS:
- Handle psutil.NoSuchProcess gracefully
- Handle psutil.AccessDenied (may not have permission to kill some procs)
- Case-insensitive process matching
- Log all blocks for debugging
- Never crash on process scan errors

TESTING:
- Goal NOT met → launch Steam → killed immediately
- Goal met → launch Steam → runs normally
- UI closed → blocking still active
- Process list changes → handles gracefully
- Repeated app launches → consistently killed
```

---

## 4. ui.py

**Purpose:** PySide6 UI displaying timer, goal progress, and app management.

**Prompt:**

```
Create a ui.py module for TimerKiller using PySide6 with minimal design.

REQUIREMENTS:
1. Display focused minutes today
2. Display daily goal
3. Display timer (HH:MM:SS format)
4. Show session status (running/paused/none)
5. Start/pause Pomodoro buttons
6. Add/remove blocked apps (simple list view)
7. Tray icon or minimal window (can be simple)
8. Refresh timer display every 1 second
9. No fancy animations or themes

MAIN WINDOW LAYOUT:
┌─────────────────────────────┐
│ TimerKiller                 │
├─────────────────────────────┤
│ Focus Goal: 180 min         │
│ Focused Today: 45 min       │
├─────────────────────────────┤
│ [Timer Display: 15:32]      │
│ [Start] [Pause]             │
├─────────────────────────────┤
│ Blocked Apps:               │
│ ☐ steam.exe                 │
│ ☐ overwatch.exe             │
│ [+ Add] [- Remove]          │
├─────────────────────────────┤
│ Status: Running / Paused    │
└─────────────────────────────┘

CORE COMPONENTS:
- QMainWindow or QWidget (simple)
- QLabel for timer display (update every 1 sec)
- QLabel for progress (X min / Y min goal)
- QPushButton for Start/Pause
- QListWidget for blocked apps
- QPushButton for Add/Remove apps
- QTimer connected to refresh_display()

FUNCTIONS:
- __init__() - Setup UI, connect signals
- refresh_display() - Update labels from state_manager & pomodoro
- on_start_clicked() - Call pomodoro.start_focus_session()
- on_pause_clicked() - Call pomodoro.pause_session()
- on_add_app_clicked() - Prompt for app name, call state_manager.add_blocked_app()
- on_remove_app_clicked() - Remove selected app from list
- update_blocked_apps_list() - Sync UI list with state_manager
- closeEvent() - Allow UI to close (enforcer continues running)

CONSTRAINTS:
- Minimal, functional UI (no animations)
- Timer updates every 1 second
- Closing UI does NOT stop enforcer
- Display is read-only from state (no stale data)
- App list editable (write to state_manager)

TESTING:
- Timer display increments while running
- Pause button works
- Add app to list, verify in state.json
- Remove app from list, verify in state.json
- Close UI, verify enforcer still runs
- Reopen UI, state reflects correct values
```

---

## 5. main.py

**Purpose:** Application entry point that starts UI and enforcer thread.

**Prompt:**

```
Create a main.py module for TimerKiller that bootstraps the application.

REQUIREMENTS:
1. Initialize state_manager (load state from disk)
2. Start blocker enforcer in background thread (daemon=True)
3. Launch PySide6 UI in main thread
4. Handle graceful shutdown
5. Optional: Add Windows startup registry entry for auto-launch

MAIN FUNCTION FLOW:
```
def main():
    # 1. Initialize state (create if missing)
    state_manager.load_state()
    
    # 2. Start background enforcer thread
    enforcer_thread = threading.Thread(target=blocker.start_enforcer, daemon=True)
    enforcer_thread.start()
    logging.info("Enforcer thread started")
    
    # 3. Launch Qt UI
    app = QApplication(sys.argv)
    window = TimerKillerUI()
    window.show()
    
    # 4. Run event loop
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
```

STARTUP CHECKLIST:
- Verify state.json exists (create if missing)
- Verify app/ folder structure exists
- Load default values if needed
- Start enforcer thread BEFORE UI
- Log startup info
- Handle Ctrl+C gracefully (allows cleanup)

OPTIONAL: AUTO-START WITH WINDOWS
- Add registry entry: HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
- Entry: "TimerKiller" → full path to main.py or executable
- Can be triggered on first run with user prompt

CONSTRAINTS:
- Enforcer must start before UI (critical for coverage)
- UI closing must NOT stop enforcer
- Daemon thread OK (will terminate with app)
- Logging to console or file
- No user confirmation for startup

TESTING:
- App launches without errors
- Enforcer thread visible in task manager
- UI displays correctly
- Closing UI keeps enforcer running
- Relaunch app, state persists
- Process monitor shows enforcer active
```

---

## Usage Instructions

1. **Review each prompt before AI implementation**
2. **Copy the relevant section** when asking Cursor/Copilot to generate code
3. **Verify the generated code** against the "TESTING" section
4. **Check for thread safety**, state consistency, and error handling
5. **Run all test scenarios** before marking complete

---

## Integration Notes

- **state_manager** is imported by all other modules
- **blocker** is started by **main** in a background thread
- **pomodoro** is called by **ui** for user actions
- **ui** is the only module with PySide6 imports
- All file I/O goes through **state_manager**

---
