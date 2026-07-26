"""
Windows Startup Manager Module — app/system/startup.py

CONTEXT:
- Registers/unregisters TimerKiller in the Windows "Run on login" registry key.
- Isolated in app.system because it is Windows-only (winreg) and not domain logic.
- Exposes: is_startup_enabled, enable_startup, disable_startup, toggle_startup.
- Used by: app.ui.main_window (startup checkbox in the main window).
- Depends on: nothing internal — stdlib only (os, sys, winreg).
"""

import logging
import os
import sys
import winreg

logger = logging.getLogger(__name__)


def get_exe_path():
    """Get the path to TimerKiller.exe"""
    # If running as compiled exe
    if getattr(sys, 'frozen', False):
        return sys.executable
    # If running as script, return the run.py path (project root, two levels up)
    else:
        return os.path.join(os.path.dirname(__file__), '..', '..', 'run.py')


def is_startup_enabled():
    """Check if TimerKiller is registered in Windows startup."""
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
                           r'Software\Microsoft\Windows\CurrentVersion\Run') as key:
            value, _ = winreg.QueryValueEx(key, 'TimerKiller')
            return True
    except (FileNotFoundError, OSError):
        return False


def enable_startup():
    """Register TimerKiller to start on Windows startup."""
    try:
        exe_path = get_exe_path()
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Run',
                            0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, 'TimerKiller', 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        
        logger.info(f"Startup enabled: {exe_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to enable startup: {e}")
        return False


def disable_startup():
    """Remove TimerKiller from Windows startup."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Run',
                            0, winreg.KEY_WRITE)
        winreg.DeleteValue(key, 'TimerKiller')
        winreg.CloseKey(key)
        
        logger.info("Startup disabled")
        return True
    except Exception as e:
        logger.error(f"Failed to disable startup: {e}")
        return False


def toggle_startup():
    """Toggle startup on/off."""
    if is_startup_enabled():
        return disable_startup()
    else:
        return enable_startup()
