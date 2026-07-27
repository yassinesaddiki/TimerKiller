# TimerKiller — Project Context

## What this is
- A Windows desktop productivity tool: a Pomodoro-based focus timer that
  **hard-blocks** (kills) chosen applications until the user's daily focus
  goal is met.
- Built with Python + PySide6 (Qt) for the UI, `psutil` for process control,
  packaged to a Windows `.exe` via PyInstaller.

## Architecture (SOLID-oriented layering)
Each package has one responsibility and only depends "downward" — nothing in
`core` depends on `ui`, nothing in `enforcement` depends on `ui`, etc.

```
run.py                  # thin launcher, calls app.main.main()
app/
  __init__.py           # package facade, re-exports the public API
  main.py               # composition root: wires core+enforcement+ui together
  core/                 # domain logic — no UI, no OS-specific deps
    state_manager.py    # single source of truth: app/data/state.json (thread-safe, atomic writes)
                         # also owns is_unblocked() = goal met OR all tasks done
    pomodoro.py          # focus-session timing logic (timestamp-based, crash-resilient)
    task_manager.py      # task CRUD + per-task timer (timestamp-based, mirrors pomodoro.py)
  enforcement/          # process killing — runs independently of the UI
    blocker.py           # background poll loop (daemon thread), kills blocked processes
                          # while state_manager.is_unblocked() is False
    game_detection.py    # heuristics to categorize processes (games/chat/other)
  system/                # OS integration, isolated from domain logic
    startup.py            # Windows registry "run on login" toggle
  ui/                    # PySide6 presentation layer only
    main_window.py        # TimerKillerUI, ProcessSelectorDialog, TimerCircle, tray icon
    notifications.py      # BlockingNotificationDialog (randomized motivational pop-up)
    close_dialog.py       # CloseConfirmDialog — 5s forced wait before hiding to tray
    task_widget.py        # TaskListWidget — add/check-off/timer/delete tasks
  data/                  # runtime state (state.json) — gitignored, regenerated on first run
  logs/                  # runtime logs — gitignored
  Media/                 # bundled GIF assets for notifications
```

## Key invariants / behavior to preserve
- **The X button never quits the app.** `TimerKillerUI.closeEvent` shows
  `CloseConfirmDialog` (confirm button locked for 5s) and, if confirmed, hides
  the window to a `QSystemTrayIcon` instead of closing. The only real exit is
  the tray menu's "Quit", which sets a `_force_quit` flag before calling
  `QApplication.quit()`. `app.main` sets `setQuitOnLastWindowClosed(False)` so
  hiding never accidentally exits the process.
- **The enforcer thread must never stop when the UI window closes/hides** — it's a
  daemon thread started once in `app.main.main()`, independent of the Qt event loop.
- **Unblocking is `state_manager.is_unblocked()`**: daily goal met OR all tasks
  done (only counts if at least one task exists). `blocker.py` and
  `TimerKillerUI` must go through this function, never re-derive the condition.
- `blocker.py`'s poll loop must never raise out of its `while True` — all
  `psutil` errors are caught; a critical exception backs off 5s and continues.
- `state_manager.py` is the **only** module that touches `app/data/state.json`.
  Every other module reads/writes state through its functions, never the file directly.
- State writes are atomic (write to `.tmp`, then `Path.replace`) to avoid
  corrupting `state.json` if the process is killed mid-write.
- Daily reset (`reset_if_day_changed`) is checked by the enforcer loop, not by a timer —
  don't assume it fires on a schedule; it fires on next state read after midnight.

## Data flow (happy path)
1. `app.main.main()` loads state, starts `blocker.start_enforcer()` in a thread, shows `TimerKillerUI`.
2. User clicks "Start Focus" → `pomodoro.start_focus_session()` records a start timestamp in state.
3. `blocker`'s loop reads state every ~1.5s; if `focused_minutes_today < daily_goal_minutes`,
   it kills any running process matching `blocked_apps` and queues a notification.
4. `TimerKillerUI` polls every 1s, drains `blocker.get_pending_notifications()`, and pops
   `BlockingNotificationDialog` for each kill event.
5. User clicks "Pause" → `pomodoro.pause_session()` accumulates elapsed minutes into
   `focused_minutes_today` via `state_manager`.

## Conventions going forward
- **File header comments**: every module/class starts with a `CONTEXT:` bullet-point
  docstring summarizing purpose, what it depends on, and what depends on it — so future
  changes only require reading the header, not the whole file. Keep these updated when
  responsibilities change.
- **New features get a new module in the matching package**, not appended to an
  existing file where the responsibility doesn't already fit (SRP).
- **Packages only import "downward"**: `ui` → `core`/`enforcement`/`system`; `enforcement` → `core`;
  `core` → nothing internal. `app.main` is the only place allowed to wire all of them together.
- Runtime-generated files (`app/data/*.json`, `app/logs/*.log`, `build/`, `dist/`, `venv/`,
  `__pycache__/`) are gitignored — never commit them.

## Build / run
- Dev run: `python run.py` (from repo root, with `venv` activated, deps from `requirements.txt`).
- Package to `.exe`: `pyinstaller TimerKiller.spec` (datas paths already point at `app/data/state.json`
  and `app/Media/`).
