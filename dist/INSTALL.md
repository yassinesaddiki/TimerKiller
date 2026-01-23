# TimerKiller v1.0 - Installation Guide

## What is TimerKiller?

TimerKiller is a **Windows productivity enforcement tool** that blocks distracting games and apps until you complete your daily focus goal.

**Core Features:**
- 🍅 Pomodoro timer (25 min focus + 5 min break)
- 📊 Daily focus goal tracking
- 🚫 Hard app blocking (enforced even if you close the app)
- 🎮 Smart game detection
- 💪 Motivational notifications
- 📱 Non-resizable window for distraction-free UI

## Installation

### Option 1: Direct Executable
1. Download and extract `TimerKiller-v1.0.zip`
2. Navigate to `TimerKiller/` folder
3. Double-click `TimerKiller.exe` to launch
4. App will start the background enforcer automatically

### Option 2: From Repository
1. Clone the repository
2. Install Python 3.11+
3. Run: `pip install -r requirements.txt`
4. Run: `python run.py`

## Quick Start

1. **Set Your Daily Goal:** Click "✏️ Edit Goal" (default: 180 minutes)
2. **Add Apps to Block:** Use "🎮 Select Games" to pick games or "+Add App" to add by name
3. **Start Working:** Click "Start Focus" to begin a 25-minute Pomodoro session
4. **Earn Access:** Once your daily focus goal is met, all blocked apps unlock
5. **Reset:** Goal resets daily at midnight

## How It Works

- **Background Enforcer:** Runs continuously in the background, even if you close the window
- **Hard Blocking:** Automatically terminates blocked apps (no warnings, no delays)
- **Goal-Based:** Blocking stops as soon as daily goal is achieved
- **Windows Auto-Start:** (Optional) Configure for auto-launch at login

## Blocked Applications

Add games/apps by process name:
- Examples: `steam.exe`, `valorant.exe`, `discord.exe`, `overwatch.exe`
- Use "🎮 Select Games" for a pre-populated list
- Or manually add executables via "+ Add App"

## Notifications

When a blocked app is detected while goal incomplete:
- 🎮 **Modal Dialog** pops up with motivational message
- Shows app name and progress toward daily goal
- User must click "Back to Work! 💻" to close (no auto-timeout)
- Includes animated emoji/GIF (if available)

## Troubleshooting

**App not blocking?**
- Ensure daily goal is set and not already met
- Verify app name is exactly correct (e.g., `steam.exe` not `Steam.exe`)
- Check that enforcer is running (it runs in background)

**Performance issues?**
- App polls processes every 1.5 seconds (low CPU)
- If slow, reduce number of blocked apps

**Want to stop enforcement?**
- Either complete your daily goal or remove apps from blocked list
- Closing UI doesn't stop enforcer (it runs in background)

## File Locations

- **State File:** Created in app directory as `app/state.json`
- **Settings:** Stored in JSON (manually editable)
- **Logs:** Printed to console when running in development mode

## System Requirements

- **OS:** Windows 10 / Windows 11 (64-bit)
- **RAM:** 100+ MB
- **Disk:** 50 MB
- **Python:** 3.11+ (if running from source)

## License

Built for personal productivity. Use at your own discretion.

---

**Questions?** Review the code or check the project README.md in the source repository.
