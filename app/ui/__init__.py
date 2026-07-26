"""
UI Package
----------
- Owns all PySide6 presentation code: main window and popup dialogs.
- Talks to core/enforcement/system packages only through their public functions.
- Modules: main_window (TimerKillerUI, ProcessSelectorDialog, TimerCircle), notifications (BlockingNotificationDialog).
"""

from .main_window import TimerKillerUI

__all__ = ["TimerKillerUI"]
