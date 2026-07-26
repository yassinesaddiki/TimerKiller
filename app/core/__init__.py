"""
Core Package
------------
- Owns application domain logic: persistent state and the Pomodoro timer.
- No UI or OS-specific dependencies live here (keeps this package testable/portable).
- Modules: state_manager (single source of truth for state.json), pomodoro (focus session logic).
"""
