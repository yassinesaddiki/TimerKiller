---
applyTo: "*"
description: "TimerKiller MVP project specification and AI guidelines for all code generation, reviews, and feature implementation"
---

# TimerKiller (Windows MVP) — Complete Project Reference

## 1. Project Overview

TimerKiller is a Windows-only desktop productivity enforcement tool.

The application combines:
- A Pomodoro-based focus timer
- A daily focus goal
- A hard application/game blocker

**Core Idea — Earned Access:**
- Applications (e.g., games) remain blocked until the user completes their daily focus goal.
- This is a commitment device, not a reminder tool.
- **Enforcement reliability is more important than UI polish.**

## 2. Target Platform

- **Operating System:** Windows 10 / 11
- **Architecture:** User-space (no kernel drivers for MVP)
- **Language:** Python 3.11+
- **UI Framework:** PySide6 (Qt for Python)
- **Process Control:** psutil
- **Persistence:** Local JSON file
- **Execution Model:** Background process + UI

## 3. Core Functional Requirements

### 3.1 Pomodoro System

**Default Pomodoro:**
- 25 minutes focus
- 5 minutes break
- Focus time counts toward daily goal
- Break time does NOT count

**User Actions:**
- Start focus session
- Pause focus session
- Timer must be resilient to UI refreshes

### 3.2 Daily Goal System

- User sets a daily focus goal in minutes (e.g., 180 minutes)
- System tracks `focused_minutes_today`
- Goal resets automatically when calendar day changes
- When goal is met: All blocked apps are immediately unblocked

### 3.3 Application Blocking (Critical Feature)

User defines a list of blocked applications by process name:
- Example: `steam.exe`, `overwatch.exe`

**Background Enforcer Behavior:**
- Continuously monitors running processes (every 1–2 seconds)
- **IF:** A blocked app is detected **AND** daily goal is NOT completed
- **THEN:** The process is terminated immediately
  - No warning
  - No confirmation
  - No delay
- Blocking stops automatically once goal is met
- This enforcement logic must run independently of the UI

### 3.4 Background Enforcement

Blocking logic must:
- Run continuously
- Be started when the app launches
- UI closure must NOT stop enforcement
- Auto-start with Windows login (startup persistence)

## 4. Non-Goals (Explicitly Excluded)

The MVP does NOT include:
- Website blocking
- Network filtering
- Scheduling by day/week
- Usage analytics dashboards
- Anti-uninstall protection
- Kernel drivers
- AI coaching

These are future iterations.

## 5. System Architecture

### 5.1 High-Level Design

```
UI (PySide6)
│
├── Displays timer & progress
├── Allows editing blocked apps
└── Controls Pomodoro start/pause

Shared State (JSON)
│
├── Daily goal
├── Focused minutes
├── Block list
└── Pomodoro state

Background Enforcer (Python Thread / Process)
│
├── Reads shared state
├── Scans OS processes
└── Kills blocked apps when required
```

## 6. File Structure (Fixed Contract)

```
TimerKiller/
│
├── venv/
│
├── app/
│   ├── main.py              # App entry point
│   ├── state_manager.py     # State load/save & daily reset
│   ├── pomodoro.py          # Timer & focus logic
│   ├── blocker.py           # Process enforcement loop
│   ├── ui.py                # PySide6 UI
│   └── state.json           # Persistent state
│
├── .github/
│   └── instructions/
│       └── Project Resume.instructions.md  # This file
│
└── venv/
```

**AI tools must follow this structure exactly.**

## 7. Shared State Specification (state.json)

```json
{
  "daily_goal_minutes": 180,
  "focused_minutes_today": 0,
  "pomodoro_active": false,
  "pomodoro_start_ts": null,
  "blocked_apps": [
    "steam.exe",
    "overwatch.exe"
  ],
  "last_reset_date": "YYYY-MM-DD"
}
```

**Rules:**
- This file is the single source of truth
- All modules must read/write via `state_manager`
- Daily reset happens automatically when date changes

## 8. Blocking Rules (Strict)

- **IF** `focused_minutes_today < daily_goal_minutes`
  - Blocked apps must not run

- **IF** `focused_minutes_today >= daily_goal_minutes`
  - All apps are allowed

**Blocking must be enforced even if:**
- UI is closed
- User restarts a blocked app repeatedly

## 9. UX Expectations (Minimal)

**Display:**
- Focused minutes today
- Daily goal
- Timer status

**Controls:**
- Start / pause Pomodoro
- Add/remove blocked apps
- No fancy animations or themes

**Form Factor:** Tray or simple window UI

## 10. Quality & Behavior Constraints

- Low CPU usage (poll every ~1–2 seconds)
- No crashes if a process disappears mid-scan
- Graceful handling of missing `state.json`
- Thread-safe state access

## 11. Testing Scenarios (Required)

AI-generated code must pass these scenarios:

1. Start app → try to open Steam → Steam closes immediately
2. Start Pomodoro → time increments correctly
3. Pause Pomodoro → time stops incrementing
4. Reach daily goal → Steam launches normally
5. Close UI → blocking still active
6. Reboot Windows → app auto-starts → blocking resumes

## 12. Success Definition

The MVP is considered successful if:

> **A user cannot access blocked games until they complete their daily focus goal, regardless of intent.**

## 13. Future Upgrade Path (Context Only)

This architecture must later support:
- Native Windows service
- C++ enforcement core
- macOS / Linux ports
- Kernel-level blocking
- AI-based coaching

**UI and logic separation is mandatory.**

## 14. Instructions to AI Tools

- Generate clean, modular, readable Python code following this specification exactly
- Do not add features not listed
- Prioritize enforcement correctness over UI aesthetics
- Follow the file structure contract
- Ensure thread safety and state consistency
- Test against all required scenarios before marking as complete