"""
Application Blocker Module — app/enforcement/blocker.py

CONTEXT:
- Background enforcement loop: kills blocked processes while daily goal is unmet.
- Runs in a daemon thread started by app.main (must survive UI being closed).
- Polls every ~1.5s; cools down repeat notifications per-process (NOTIFICATION_COOLDOWN).
- Never raises out of the loop — all psutil errors are caught and logged.
- Exposes: start_enforcer (thread target), is_app_blocked, get_blocked_processes,
  get_pending_notifications (drains notification_queue for the UI to display).
- Depends on: app.core.state_manager (goal/blocked-apps source of truth).
"""

import time
import logging
import psutil
from queue import Queue
from ..core import state_manager

logger = logging.getLogger(__name__)

# Poll interval in seconds
POLL_INTERVAL = 1.5

# Notification queue for UI
notification_queue = Queue()

# Track recently killed processes to avoid spam notifications
recently_killed = {}
NOTIFICATION_COOLDOWN = 30  # seconds


def start_enforcer():
    """
    Start the continuous enforcement loop.
    
    This function runs in a background thread and continuously:
    1. Checks if daily goal is met
    2. Scans running processes
    3. Kills blocked apps if goal not met
    
    Runs forever until application exits.
    """
    logger.info("Blocker enforcer started")
    
    while True:
        try:
            # Check for daily reset
            state_manager.reset_if_day_changed()
            
            # Load current state
            state = state_manager.load_state()
            
            goal_met = state['focused_minutes_today'] >= state['daily_goal_minutes']
            
            if goal_met:
                # Goal met, all apps allowed
                logger.debug("Goal met. No blocking active.")
                time.sleep(2)
                continue
            
            # Goal NOT met, enforce blocking
            blocked_apps = state['blocked_apps']
            
            if not blocked_apps:
                # No apps to block
                time.sleep(POLL_INTERVAL)
                continue
            
            # Scan running processes
            try:
                for proc in psutil.process_iter(['pid', 'name']):
                    try:
                        proc_name = proc.name()
                        
                        # Check if process is in blocked list (case-insensitive)
                        if proc_name.lower() in [app.lower() for app in blocked_apps]:
                            # Kill the process immediately
                            proc.kill()
                            logger.warning(f"Killed blocked process: {proc_name} (PID: {proc.pid})")
                            
                            # Queue notification (avoid spam with cooldown)
                            current_time = time.time()
                            if proc_name not in recently_killed or \
                               (current_time - recently_killed[proc_name]) > NOTIFICATION_COOLDOWN:
                                notification_queue.put(("block", proc_name))
                                recently_killed[proc_name] = current_time
                    
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process disappeared or no permission to kill
                        # This is expected and not an error
                        pass
                    except Exception as e:
                        logger.error(f"Unexpected error checking process: {e}")
            
            except Exception as e:
                logger.error(f"Error scanning processes: {e}")
            
            time.sleep(POLL_INTERVAL)
        
        except Exception as e:
            logger.error(f"Critical error in enforcer loop: {e}")
            time.sleep(5)  # Back off if something goes wrong


def is_app_blocked(app_name):
    """
    Check if an app is currently blocked.
    
    Args:
        app_name (str): Application name to check
        
    Returns:
        bool: True if app is blocked and goal not met
    """
    state = state_manager.load_state()
    goal_met = state['focused_minutes_today'] >= state['daily_goal_minutes']
    
    if goal_met:
        return False
    
    return app_name.lower() in [app.lower() for app in state['blocked_apps']]


def get_blocked_processes():
    """
    Get list of currently running blocked processes.
    
    Returns:
        list: List of process names that are blocked
    """
    state = state_manager.load_state()
    goal_met = state['focused_minutes_today'] >= state['daily_goal_minutes']
    
    if goal_met:
        return []
    
    blocked_list = []
    blocked_apps = state['blocked_apps']
    
    try:
        for proc in psutil.process_iter(['name']):
            try:
                proc_name = proc.name()
                if proc_name.lower() in [app.lower() for app in blocked_apps]:
                    blocked_list.append(proc_name)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
    except Exception as e:
        logger.error(f"Error getting blocked processes: {e}")
    
    return blocked_list

def get_pending_notifications():
    """
    Get all pending notifications from the queue.
    
    Returns:
        list: List of (notification_type, data) tuples
    """
    notifications = []
    while not notification_queue.empty():
        try:
            notifications.append(notification_queue.get_nowait())
        except:
            break
    return notifications