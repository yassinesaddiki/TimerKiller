"""
Task Manager Module — app/core/task_manager.py

CONTEXT:
- Manages the task list: create/remove/toggle-done, and an optional
  per-task timer (start/pause), mirroring app.core.pomodoro's timestamp-based
  approach so it also survives app restarts/crashes.
- Persists everything via app.core.state_manager (no local state of its own).
- Depended on by: app.ui.task_widget (task list UI).
- Depends on: app.core.state_manager only.
"""

import time
import uuid
import logging
from . import state_manager

logger = logging.getLogger(__name__)


def new_task(name):
    """Create and persist a new task, return its id."""
    task_id = uuid.uuid4().hex
    task = {
        "id": task_id,
        "name": name,
        "done": False,
        "minutes_spent": 0,
        "timer_active": False,
        "timer_start_ts": None,
    }
    state_manager.add_task(task)
    logger.info(f"Task created: {name} ({task_id})")
    return task_id


def delete_task(task_id):
    """Remove a task entirely."""
    state_manager.remove_task(task_id)


def toggle_done(task_id, done):
    """Mark a task done/not done. Stops its timer if it was running."""
    state_manager.update_task(task_id, done=done, timer_active=False, timer_start_ts=None)
    logger.info(f"Task {task_id} marked done={done}")


def start_task_timer(task_id):
    """Start timing work on a task."""
    state_manager.update_task(task_id, timer_active=True, timer_start_ts=time.time())


def pause_task_timer(task_id):
    """Pause a task's timer, accumulating elapsed minutes."""
    tasks = state_manager.get_tasks()
    task = next((t for t in tasks if t['id'] == task_id), None)
    if not task or not task.get('timer_active') or task.get('timer_start_ts') is None:
        return

    elapsed_minutes = (time.time() - task['timer_start_ts']) / 60
    new_total = task.get('minutes_spent', 0) + int(elapsed_minutes)
    state_manager.update_task(task_id, timer_active=False, timer_start_ts=None, minutes_spent=new_total)


def get_task_elapsed_seconds(task):
    """
    Elapsed seconds for a task's current timer session (0 if not running).

    Args:
        task (dict): Task record as returned by state_manager.get_tasks()
    """
    if not task.get('timer_active') or task.get('timer_start_ts') is None:
        return 0
    return int(time.time() - task['timer_start_ts'])
