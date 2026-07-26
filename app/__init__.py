"""
TimerKiller Package — app/__init__.py

CONTEXT:
- Windows desktop productivity tool: Pomodoro focus timer + hard app blocking.
- Blocked apps stay killed until the daily focus goal (state.json) is met.
- Package layout:
  - app.core        -> state_manager, pomodoro (domain logic, no UI/OS deps)
  - app.enforcement -> blocker, game_detection (kills processes, runs in a thread)
  - app.system      -> startup (Windows registry "run on boot")
  - app.ui          -> main_window, notifications (PySide6 presentation)
  - app.main        -> wires everything together and is the process entry point
- See /CONTEXT.md at the repo root for the full architecture overview.
"""

__version__ = "0.1.0"
__author__ = "TimerKiller Team"

from .core import state_manager, pomodoro
from .enforcement import blocker
from .ui import TimerKillerUI
from .main import main

__all__ = [
    "state_manager",
    "pomodoro",
    "blocker",
    "TimerKillerUI",
    "main"
]
