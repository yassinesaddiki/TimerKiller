"""
Pomodoro Timer Module — app/core/pomodoro.py

CONTEXT:
- Manages the focus-session lifecycle: start, pause, elapsed/remaining time.
- Timestamp-based (not a running counter) so it survives app restarts/crashes.
- Persists session + accumulated minutes via app.core.state_manager (no local state).
- Depended on by: app.ui.main_window (drives the on-screen timer + buttons).
- Depends on: app.core.state_manager only.
"""

import time
import logging
from . import state_manager

logger = logging.getLogger(__name__)

# Pomodoro constants (in seconds)
FOCUS_DURATION = 1500  # 25 minutes
BREAK_DURATION = 300   # 5 minutes


def start_focus_session():
    """
    Start a new focus session.
    Records the start timestamp and marks session as active.
    """
    start_ts = time.time()
    state_manager.set_pomodoro_state(is_active=True, start_ts=start_ts)
    logger.info("Focus session started")


def pause_session():
    """
    Pause the current focus session.
    Accumulates elapsed time into focused_minutes_today.
    """
    is_active, start_ts = state_manager.get_pomodoro_state()
    
    if not is_active or start_ts is None:
        logger.warning("Attempted to pause session that is not active")
        return
    
    elapsed_seconds = time.time() - start_ts
    elapsed_minutes = elapsed_seconds / 60
    
    # Add to daily total
    state_manager.add_focused_minutes(int(elapsed_minutes))
    
    # Deactivate session
    state_manager.set_pomodoro_state(is_active=False, start_ts=None)
    
    logger.info(f"Session paused. Added {int(elapsed_minutes)} minutes to daily total")
    
    # Check if goal is met
    if state_manager.is_goal_met():
        logger.info("Daily goal reached! All apps unblocked.")


def get_elapsed_seconds():
    """
    Get elapsed seconds in current session.
    Handles pause state gracefully.
    
    Returns:
        int: Elapsed seconds (0 if not active)
    """
    is_active, start_ts = state_manager.get_pomodoro_state()
    
    if not is_active or start_ts is None:
        return 0
    
    return int(time.time() - start_ts)


def is_session_active():
    """
    Check if a focus session is currently active.
    
    Returns:
        bool: True if session is running
    """
    is_active, _ = state_manager.get_pomodoro_state()
    return is_active


def get_remaining_seconds():
    """
    Get remaining seconds in current focus session.
    
    Returns:
        int: Remaining seconds (0 if not active or time exceeded)
    """
    elapsed = get_elapsed_seconds()
    remaining = max(0, FOCUS_DURATION - elapsed)
    return remaining


def format_time(seconds):
    """
    Format seconds as HH:MM:SS.
    
    Args:
        seconds (int): Seconds to format
        
    Returns:
        str: Formatted time string
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def get_formatted_elapsed():
    """
    Get formatted elapsed time for display.
    
    Returns:
        str: "HH:MM:SS" format
    """
    return format_time(get_elapsed_seconds())


def get_formatted_remaining():
    """
    Get formatted remaining time for display.
    
    Returns:
        str: "HH:MM:SS" format
    """
    return format_time(get_remaining_seconds())


def reset_for_new_session():
    """
    Prepare state for next Pomodoro session.
    This would be called after a break or manual reset.
    """
    state_manager.set_pomodoro_state(is_active=False, start_ts=None)
    logger.info("Session reset for new Pomodoro")
