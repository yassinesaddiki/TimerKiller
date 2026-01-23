# TimerKiller Quick Reference

Fast lookup for common tasks and troubleshooting.

---

## 🚀 Launch the App

```bash
cd c:\Users\Yassine Saddiki\Desktop\SaaS\TimerKiller
pip install -r requirements.txt
python run.py
```

The app will:
1. Initialize `app/state.json` (if missing)
2. Start the background enforcer thread
3. Launch the UI window

---

## 📖 How Enforcement Works

**Goal NOT Met (e.g., 45 / 180 minutes):**
```
Every 1.5 seconds:
  - Load blocked apps list
  - Scan all running processes
  - Find "steam.exe" → KILL IT
  - Find "discord.exe" → KILL IT
  - ...repeat
```

**Goal IS Met (e.g., 180 / 180 minutes):**
```
Every 1.5 seconds:
  - Check goal
  - All apps are FREE
  - Sleep 2 seconds
  - ...repeat
```

---

## 🛠️ Configuration

### Change Daily Goal
Edit `app/state.json`:
```json
"daily_goal_minutes": 120  // Change from 180 to 120
```
Restart app to reload.

### Add Blocked App Manually
Edit `app/state.json`:
```json
"blocked_apps": [
  "steam.exe",
  "discord.exe",
  "bluestacks.exe"  // Add new app
]
```
Restart app to reload.

---

## 🔍 Verify It's Working

### Check if Enforcer is Running
1. Open Task Manager
2. Look for Python process
3. Should see enforcer thread active

### Check Logs
Open `app/timerkiller.log`:
```
[Time] - TimerKiller - INFO - Blocker enforcer started
[Time] - TimerKiller - WARNING - Killed blocked process: steam.exe (PID: 1234)
```

### Manually Test Blocking
1. Start app with 0 focused minutes, goal = 10 min
2. Add "notepad.exe" to blocked apps
3. Launch Notepad
4. **Expected:** Notepad closes immediately
5. Check logs for "Killed blocked process"

---

## 📊 State File Reference

**Location:** `app/state.json`

```json
{
  "daily_goal_minutes": 180,          // How many minutes to focus
  "focused_minutes_today": 45,        // Minutes accumulated today
  "pomodoro_active": true,            // Is timer running now?
  "pomodoro_start_ts": 1705123456.78, // When did session start? (Unix timestamp)
  "blocked_apps": [                   // List of blocked process names
    "steam.exe",
    "discord.exe"
  ],
  "last_reset_date": "2024-01-23"     // When was daily reset last done?
}
```

**Rules:**
- Edit manually only if necessary
- Always use UI to add/remove apps when possible
- `pomodoro_start_ts` is only set when `pomodoro_active` is true
- `last_reset_date` is checked and updated daily

---

## 🧵 Module Dependencies

```
state_manager
    ↑
    ├─ pomodoro    (calls to read/write state)
    ├─ blocker     (calls to check goal & blocked apps)
    └─ ui          (calls to read/write state)

blocker
    ↑
    └─ Runs in background thread started by main.py

ui
    ↑
    └─ Runs in main thread (Qt event loop)
```

---

## 📋 Common Issues

### Issue: "Module not found: PySide6"
**Fix:**
```bash
pip install PySide6
```

### Issue: "Module not found: psutil"
**Fix:**
```bash
pip install psutil
```

### Issue: App won't launch
**Debug:**
1. Check `app/timerkiller.log` for errors
2. Verify Python 3.11+: `python --version`
3. Verify dependencies: `pip list | findstr "PySide6\|psutil"`

### Issue: Blocked apps not being killed
**Debug Checklist:**
1. Check goal is NOT met (UI shows progress)
2. Verify process name: Open Task Manager, check exact .exe name
3. Check logs for "Killed blocked process"
4. Verify enforcer thread is running (Task Manager)

### Issue: Daily goal doesn't reset
**Fix:**
```json
"last_reset_date": "2024-01-23"  // Change to yesterday's date
```
Restart app to trigger reset.

---

## 🎯 Success Criteria

MVP is successful when:

✅ Launch app → enforcer starts before UI  
✅ Set blocked app → app killed immediately when launched  
✅ Reach goal → app runs freely  
✅ Close UI → enforcer still running  
✅ Restart app → state persists, enforcement resumes  

---

## 📞 Reference Documentation

| Document | Use When |
|----------|----------|
| `README.md` | Understanding how to use the app |
| `Project Resume.instructions.md` | Understanding project requirements |
| `AI-Prompts.md` | Implementing new features |
| `Code-Review-Checklist.md` | Verifying code correctness |
| `IMPLEMENTATION-COMPLETE.md` | Checking what's implemented |
| `Quick-Reference.md` | This document — quick lookup |

---

## 🔧 Key Files

| Path | Purpose | Editable? |
|------|---------|-----------|
| `app/state.json` | Application state | Yes (carefully) |
| `app/timerkiller.log` | Debug logs | View only |
| `app/main.py` | Entry point | No (unless extending) |
| `README.md` | User guide | Yes |

---

## 🚀 Next: Test the Implementation

Run against `Code-Review-Checklist.md`:

1. Start app
2. Try to open blocked app → **Should close**
3. Start Pomodoro → **Time should increment**
4. Pause → **Time should be saved**
5. Reach goal → **All apps allowed**
6. Close UI → **Enforcer keeps running**

All tests pass = MVP success! ✓

---
