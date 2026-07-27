"""
Main Entry Point — app/main.py

CONTEXT:
- Bootstraps the whole app; this is the only module allowed to wire the
  core/enforcement/ui packages together (keeps them decoupled from each other).
- Startup sequence: (1) init state, (2) start blocker enforcer as a daemon
  thread, (3) launch the PySide6 UI and block on the Qt event loop.
- Also contains add_to_windows_startup(), a registry helper kept here since
  it's invoked only at bootstrap (see app.system.startup for the toggle used by the UI).
- Logs to app/logs/timerkiller.log in addition to stdout.
"""

import sys
import logging
import threading
import winreg
from pathlib import Path

from PySide6.QtWidgets import QApplication

from .core import state_manager
from .enforcement import blocker
from .ui import TimerKillerUI

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(Path(__file__).parent / "logs" / "timerkiller.log")
    ]
)
logger = logging.getLogger(__name__)


def add_to_windows_startup():
    r"""
    Add TimerKiller to Windows startup registry.

    Creates entry in:
    HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run
    """
    try:
        # Get the path to the main.py (or compiled executable)
        script_path = Path(__file__).parent.parent / "run.py"
        if not script_path.exists():
            script_path = Path(__file__).absolute()
        
        # Open registry
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_SET_VALUE
            )
        except FileNotFoundError:
            logger.warning("Could not access Windows startup registry")
            return
        
        # Set value
        python_exe = sys.executable
        command = f'"{python_exe}" -m timerkiller'
        winreg.SetValueEx(key, "TimerKiller", 0, winreg.REG_SZ, command)
        winreg.CloseKey(key)
        
        logger.info("Added TimerKiller to Windows startup")
    except Exception as e:
        logger.error(f"Failed to add to Windows startup: {e}")


def main():
    """
    Main application entry point.
    
    Flow:
    1. Initialize state (create if missing)
    2. Start background enforcer thread
    3. Launch PySide6 UI
    4. Run event loop
    """
    logger.info("=" * 50)
    logger.info("TimerKiller Starting")
    logger.info("=" * 50)
    
    # Step 1: Initialize state
    try:
        state_manager.load_state()
        logger.info("State manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize state: {e}")
        sys.exit(1)
    
    # Step 2: Start background enforcer thread
    try:
        enforcer_thread = threading.Thread(
            target=blocker.start_enforcer,
            daemon=True,
            name="BlockerEnforcer"
        )
        enforcer_thread.start()
        logger.info("Background enforcer thread started")
    except Exception as e:
        logger.error(f"Failed to start enforcer thread: {e}")
        sys.exit(1)
    
    # Step 3: Launch PySide6 UI
    try:
        app = QApplication(sys.argv)
        app.setQuitOnLastWindowClosed(False)  # hiding to tray must not exit the app
        window = TimerKillerUI()
        window.show()
        logger.info("UI window shown")
        
        # Step 4: Run event loop (blocks until UI is closed)
        exit_code = app.exec()
        logger.info("Application exiting")
        sys.exit(exit_code)
    
    except Exception as e:
        logger.error(f"Failed to launch UI: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
