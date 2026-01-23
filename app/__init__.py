"""
TimerKiller - Windows Desktop Productivity Enforcement Tool

A Pomodoro-based focus timer with hard application blocking.
Applications remain blocked until daily focus goal is met.
"""

__version__ = "0.1.0"
__author__ = "TimerKiller Team"

from . import state_manager, pomodoro, blocker
from .ui import TimerKillerUI
from .main import main

__all__ = [
    "state_manager",
    "pomodoro",
    "blocker",
    "TimerKillerUI",
    "main"
]
