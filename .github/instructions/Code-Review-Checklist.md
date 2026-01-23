# TimerKiller Code Review Checklist

Use this checklist to verify all implementations pass MVP requirements.

---

## State Manager (`state_manager.py`)

- [ ] **Initialization**
  - [ ] Loads `state.json` if exists, creates with defaults if missing
  - [ ] No crash on malformed JSON (logs error, creates default)
  - [ ] `DEFAULT_STATE` contains all required keys

- [ ] **Thread Safety**
  - [ ] Uses `threading.Lock` for all state access
  - [ ] `load_state()` acquires lock before reading/writing
  - [ ] `save_state()` acquires lock before writing

- [ ] **Persistence**
  - [ ] `save_state()` writes atomically (uses temp file + rename)
  - [ ] All mutations immediately call `save_state()`
  - [ ] State persists across restarts

- [ ] **Daily Reset**
  - [ ] `reset_if_day_changed()` checks `last_reset_date`
  - [ ] Resets `focused_minutes_today` to 0 on new day
  - [ ] Updates `last_reset_date` to today
  - [ ] Called periodically or on enforcer start

- [ ] **API Completeness**
  - [ ] `get_focused_minutes()` returns int
  - [ ] `set_focused_minutes(minutes)` accepts int
  - [ ] `add_focused_minutes(minutes)` accumulates time
  - [ ] `add_blocked_app(name)` prevents duplicates
  - [ ] `remove_blocked_app(name)` case-insensitive match
  - [ ] `get_blocked_apps()` returns list copy
  - [ ] `get_daily_goal()` returns int
  - [ ] `set_daily_goal(minutes)` validates > 0
  - [ ] `is_goal_met()` returns bool
  - [ ] `get_pomodoro_state()` returns (is_active, start_ts)
  - [ ] `set_pomodoro_state(is_active, start_ts)` saves state

---

## Pomodoro Timer (`pomodoro.py`)

- [ ] **Timer Constants**
  - [ ] `FOCUS_DURATION = 1500` (25 minutes)
  - [ ] `BREAK_DURATION = 300` (5 minutes)

- [ ] **Start/Pause Logic**
  - [ ] `start_focus_session()` records `time.time()` as start
  - [ ] `pause_session()` calculates elapsed seconds
  - [ ] `pause_session()` converts to minutes and adds to daily total
  - [ ] `pause_session()` deactivates session (sets `pomodoro_active=False`)
  - [ ] `pause_session()` logs completion

- [ ] **Elapsed Time Calculation**
  - [ ] Uses `time.time()` for resilience (not counters)
  - [ ] `get_elapsed_seconds()` returns 0 if not active
  - [ ] `get_remaining_seconds()` returns `max(0, FOCUS_DURATION - elapsed)`
  - [ ] Handles pause state gracefully

- [ ] **Display Formatting**
  - [ ] `format_time(seconds)` returns "HH:MM:SS" format
  - [ ] `get_formatted_elapsed()` returns formatted elapsed time
  - [ ] `get_formatted_remaining()` returns formatted remaining time

- [ ] **State Consistency**
  - [ ] All operations go through `state_manager`
  - [ ] Session state is thread-safe
  - [ ] No hardcoded timers or sleep() in production paths

---

## Application Blocker (`blocker.py`)

- [ ] **Enforcer Loop**
  - [ ] `start_enforcer()` runs infinite loop in background thread
  - [ ] Polls processes every 1-2 seconds (`POLL_INTERVAL = 1.5`)
  - [ ] Calls `state_manager.reset_if_day_changed()` regularly

- [ ] **Blocking Logic**
  - [ ] Loads current state (goal, blocked_apps, focused_minutes)
  - [ ] **IF** goal is met → sleeps 2 seconds and continues (no blocking)
  - [ ] **IF** goal is NOT met → scans all processes
  - [ ] Matches blocked process names case-insensitive
  - [ ] Calls `proc.kill()` immediately on match (no warnings)

- [ ] **Error Handling**
  - [ ] Catches `psutil.NoSuchProcess` gracefully (process disappeared)
  - [ ] Catches `psutil.AccessDenied` gracefully (permission denied)
  - [ ] Never crashes on process scan errors
  - [ ] Logs all kills and errors

- [ ] **Independence from UI**
  - [ ] Runs in separate background thread
  - [ ] Continues running even if UI is closed
  - [ ] No dependency on UI state or signals

---

## User Interface (`ui.py`)

- [ ] **Initialization**
  - [ ] Creates `QMainWindow` with title "TimerKiller"
  - [ ] Sets reasonable window size (e.g., 400x500)
  - [ ] Calls `refresh_display()` on init

- [ ] **Display Elements**
  - [ ] Shows focused minutes and daily goal: "Goal: X / Y minutes"
  - [ ] Shows timer in HH:MM:SS format (e.g., "15:32:45")
  - [ ] Shows session status: "Running", "Paused", or "Idle"
  - [ ] Shows blocked apps list (QListWidget)
  - [ ] Updates every 1 second (QTimer at 1000ms)

- [ ] **User Controls**
  - [ ] "Start Focus" button calls `pomodoro.start_focus_session()`
  - [ ] "Pause" button calls `pomodoro.pause_session()`
  - [ ] "Start Focus" enabled only when not active
  - [ ] "Pause" enabled only when active
  - [ ] "+ Add App" prompts for process name, calls `state_manager.add_blocked_app()`
  - [ ] "- Remove App" removes selected app, calls `state_manager.remove_blocked_app()`

- [ ] **Refresh Display**
  - [ ] Updates goal label from state_manager
  - [ ] Updates timer display from pomodoro.get_formatted_elapsed()
  - [ ] Updates status label based on session state
  - [ ] Highlights goal in green when met
  - [ ] Handles errors gracefully (logs, doesn't crash)

- [ ] **Blocked Apps List**
  - [ ] Syncs with state_manager on init and after add/remove
  - [ ] Shows all currently blocked apps
  - [ ] Selectable for removal

- [ ] **Minimal Design**
  - [ ] No fancy animations or themes
  - [ ] Functional, clean layout
  - [ ] No animations or transitions

- [ ] **Close Event**
  - [ ] `closeEvent()` allows UI to close without confirmation
  - [ ] Logs that UI is closing
  - [ ] Enforcer thread continues running

---

## Main Entry Point (`main.py`)

- [ ] **Initialization Sequence**
  1. [ ] Loads logging configuration (console + file)
  2. [ ] Calls `state_manager.load_state()` (initializes state)
  3. [ ] Creates enforcer thread with `blocker.start_enforcer()`
  4. [ ] Sets daemon=True for enforcer thread
  5. [ ] Starts enforcer thread **before** launching UI
  6. [ ] Creates `QApplication`
  7. [ ] Creates `TimerKillerUI` window
  8. [ ] Shows window
  9. [ ] Runs `app.exec()` (blocks until UI closed)

- [ ] **Error Handling**
  - [ ] Catches initialization errors and logs them
  - [ ] Exits with error code on failure
  - [ ] Handles Ctrl+C gracefully

- [ ] **Logging**
  - [ ] Logs startup with separator
  - [ ] Logs state initialization
  - [ ] Logs enforcer thread start
  - [ ] Logs UI show
  - [ ] Logs application exit
  - [ ] File log at `app/timerkiller.log`

- [ ] **Optional: Windows Startup** (nice-to-have)
  - [ ] `add_to_windows_startup()` function exists
  - [ ] Adds registry entry to `HKEY_CURRENT_USER\...\Run`
  - [ ] Can be called on first launch
  - [ ] Handles errors gracefully

---

## Integration Tests

Run all scenarios to verify enforcement correctness:

1. **Test: Blocking Active (Goal NOT Met)**
   - [ ] Start app with 0 focused minutes, goal = 10
   - [ ] Launch blocked app (Steam)
   - [ ] **Expected:** Process killed within 2 seconds
   - [ ] Check logs for "Killed blocked process"

2. **Test: Timer Accumulation**
   - [ ] Click "Start Focus"
   - [ ] Wait 5 seconds
   - [ ] Click "Pause"
   - [ ] **Expected:** `focused_minutes_today` increases by at least 1 (5 seconds = 0.08 min, should round up)
   - [ ] Check `state.json` for updated value

3. **Test: Goal Met → No Blocking**
   - [ ] Set daily goal to 1 minute
   - [ ] Start and pause Pomodoro twice (or manually set focused_minutes = goal)
   - [ ] Launch blocked app
   - [ ] **Expected:** App runs normally (not killed)
   - [ ] UI shows "Goal Met! ✓"

4. **Test: UI Close → Enforcer Running**
   - [ ] Start app
   - [ ] Close UI window (X button)
   - [ ] Check Task Manager: Python process still running
   - [ ] Launch blocked app
   - [ ] **Expected:** App still blocked (enforcer active)

5. **Test: Daily Reset**
   - [ ] Set goal to 60 minutes
   - [ ] Manually accumulate 30 minutes
   - [ ] Set `last_reset_date` in `state.json` to yesterday
   - [ ] Restart app
   - [ ] **Expected:** `focused_minutes_today` resets to 0
   - [ ] Blocking resumes

6. **Test: Add/Remove Apps**
   - [ ] Click "+ Add App", enter "notepad.exe"
   - [ ] **Expected:** App appears in list, saved in `state.json`
   - [ ] Select "notepad.exe" and click "- Remove App"
   - [ ] **Expected:** App removed from list and `state.json`

---

## Code Quality Checklist

- [ ] All imports are present and correct
- [ ] No hardcoded paths (use `Path` objects)
- [ ] No bare `except:` clauses (all exceptions specific)
- [ ] Logging used instead of print() for debug messages
- [ ] Docstrings present for all functions
- [ ] Thread-safe operations (no race conditions)
- [ ] No blocking operations in UI thread
- [ ] Graceful error handling (never crashes silently)
- [ ] State consistency maintained across operations
- [ ] Performance acceptable (low CPU usage when idle)

---

## Final Approval Criteria

✅ **MVP is production-ready when:**

1. All code quality items checked
2. All integration tests pass
3. No syntax errors
4. Blocker works without UI
5. State persists across restarts
6. Daily reset works correctly
7. All blocked apps killed immediately (no delay)
8. UI updates smoothly (1-second refresh rate)

---
