"""
State Manager Module — app/core/state_manager.py

CONTEXT:
- Single source of truth for all persisted app state (state.json).
- Responsibilities:
  - Load/save state atomically (temp file + rename) with a thread lock.
  - Fill in missing keys with defaults (forward-compatible schema).
  - Daily reset of focused minutes when the calendar day changes.
  - CRUD helpers for: daily goal, focused minutes, blocked apps, pomodoro state.
- Depended on by: app.core.pomodoro, app.enforcement.blocker, app.ui.main_window.
- Has NO dependency on UI, threading beyond its own lock, or OS-specific APIs.
- State file lives at app/data/state.json (see STATE_FILE below).
"""

import json
import logging
import threading
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# State file path (app/data/state.json)
STATE_FILE = Path(__file__).parent.parent / "data" / "state.json"

# Default state structure
DEFAULT_STATE = {
    "daily_goal_minutes": 180,
    "focused_minutes_today": 0,
    "pomodoro_active": False,
    "pomodoro_start_ts": None,
    "blocked_apps": [],
    "last_reset_date": datetime.now().strftime("%Y-%m-%d")
}

# Thread lock for state access
_state_lock = threading.Lock()
_state_cache = None


def _get_default_state():
    """Return a fresh copy of default state."""
    return DEFAULT_STATE.copy()


def load_state():
    """
    Load state from disk or create with defaults if missing.
    
    Returns:
        dict: Current application state
    """
    global _state_cache
    
    with _state_lock:
        # Try to load from disk
        if STATE_FILE.exists():
            try:
                with open(STATE_FILE, 'r') as f:
                    state = json.load(f)
                    
                # Validate and fill missing keys
                for key, value in DEFAULT_STATE.items():
                    if key not in state:
                        state[key] = value
                
                _state_cache = state
                logger.info("State loaded from disk")
                return state
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Error loading state.json: {e}. Creating default state.")
                state = _get_default_state()
        else:
            state = _get_default_state()
            logger.info("state.json not found. Creating with defaults.")
        
        # Save default/repaired state
        _save_to_disk(state)
        _state_cache = state
        return state


def save_state(state):
    """
    Save state to disk atomically.
    
    Args:
        state (dict): State dictionary to save
    """
    with _state_lock:
        _save_to_disk(state)
        _state_cache = state


def _save_to_disk(state):
    """Internal atomic write to disk."""
    try:
        # Write to temporary file first
        temp_file = STATE_FILE.with_suffix('.json.tmp')
        with open(temp_file, 'w') as f:
            json.dump(state, f, indent=2)
        
        # Atomic rename
        temp_file.replace(STATE_FILE)
        logger.debug("State saved to disk")
    except IOError as e:
        logger.error(f"Failed to save state: {e}")


def get_focused_minutes():
    """
    Get total focused minutes for today.
    
    Returns:
        int: Focused minutes
    """
    state = load_state()
    return state['focused_minutes_today']


def set_focused_minutes(minutes):
    """
    Set focused minutes for today.
    
    Args:
        minutes (int): Minutes to set
    """
    state = load_state()
    state['focused_minutes_today'] = max(0, minutes)
    save_state(state)


def add_focused_minutes(minutes):
    """
    Add minutes to today's total.
    
    Args:
        minutes (int): Minutes to add
    """
    state = load_state()
    state['focused_minutes_today'] += max(0, minutes)
    save_state(state)


def add_blocked_app(app_name):
    """
    Add application to blocked list.
    
    Args:
        app_name (str): Process name (e.g., 'steam.exe')
    """
    state = load_state()
    if app_name.lower() not in [app.lower() for app in state['blocked_apps']]:
        state['blocked_apps'].append(app_name)
        save_state(state)
        logger.info(f"Added blocked app: {app_name}")


def remove_blocked_app(app_name):
    """
    Remove application from blocked list.
    
    Args:
        app_name (str): Process name to remove
    """
    state = load_state()
    original_length = len(state['blocked_apps'])
    state['blocked_apps'] = [app for app in state['blocked_apps'] 
                             if app.lower() != app_name.lower()]
    
    if len(state['blocked_apps']) < original_length:
        save_state(state)
        logger.info(f"Removed blocked app: {app_name}")


def get_blocked_apps():
    """
    Get list of blocked applications.
    
    Returns:
        list: Application names
    """
    state = load_state()
    return state['blocked_apps'].copy()


def get_daily_goal():
    """
    Get daily focus goal in minutes.
    
    Returns:
        int: Goal in minutes
    """
    state = load_state()
    return state['daily_goal_minutes']


def set_daily_goal(minutes):
    """
    Set daily focus goal.
    
    Args:
        minutes (int): Goal in minutes
    """
    state = load_state()
    state['daily_goal_minutes'] = max(1, minutes)
    save_state(state)
    logger.info(f"Daily goal set to {minutes} minutes")


def is_goal_met():
    """
    Check if daily goal is met.
    
    Returns:
        bool: True if focused_minutes_today >= daily_goal_minutes
    """
    state = load_state()
    return state['focused_minutes_today'] >= state['daily_goal_minutes']


def reset_if_day_changed():
    """
    Reset focused minutes if calendar day has changed.
    Call this periodically to maintain daily reset logic.
    """
    state = load_state()
    today = datetime.now().strftime("%Y-%m-%d")
    
    if state['last_reset_date'] != today:
        logger.info(f"Day changed. Resetting focused minutes. Old date: {state['last_reset_date']}")
        state['focused_minutes_today'] = 0
        state['last_reset_date'] = today
        save_state(state)


def get_pomodoro_state():
    """
    Get pomodoro timer state.
    
    Returns:
        tuple: (is_active, start_timestamp)
    """
    state = load_state()
    return state['pomodoro_active'], state['pomodoro_start_ts']


def set_pomodoro_state(is_active, start_ts=None):
    """
    Update pomodoro timer state.
    
    Args:
        is_active (bool): Whether session is active
        start_ts (float): Unix timestamp when session started
    """
    state = load_state()
    state['pomodoro_active'] = is_active
    state['pomodoro_start_ts'] = start_ts
    save_state(state)
