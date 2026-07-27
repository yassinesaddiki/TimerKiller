"""
Task List Widget — app/ui/task_widget.py

CONTEXT:
- Self-contained panel: add a task, check it off, start/pause a per-task timer,
  delete it. Embedded in app.ui.main_window.TimerKillerUI's central layout.
- Polled on the same 1s cadence as the rest of the window (refresh() is called
  by the parent's QTimer tick) so running task timers visibly tick.
- Depends on: app.core.task_manager, app.core.state_manager (read-only here).
- Does NOT touch app.enforcement directly — blocking picks up task completion
  via state_manager.is_unblocked() on its own poll cycle.
"""

import logging
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QListWidget, QListWidgetItem, QCheckBox
)
from PySide6.QtCore import Qt

from ..core import task_manager, state_manager

logger = logging.getLogger(__name__)


class TaskListWidget(QWidget):
    """
    CONTEXT:
    - One row per task: checkbox (done), name + accumulated time, ▶/⏸ timer
      toggle, 🗑 delete. Checking a task off stops its timer automatically.
    - refresh() rebuilds the list from state_manager.get_tasks() each tick;
      cheap enough at typical task-list sizes (rebuild, not diff).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        header = QLabel("Tasks (finish these or hit your goal to unlock apps)")
        header.setObjectName("sectionHeader")
        layout.addWidget(header)

        add_row = QHBoxLayout()
        self.new_task_input = QLineEdit()
        self.new_task_input.setPlaceholderText("Add a task…")
        self.new_task_input.returnPressed.connect(self.on_add_task)
        add_row.addWidget(self.new_task_input)

        add_button = QPushButton("+")
        add_button.setFixedWidth(32)
        add_button.clicked.connect(self.on_add_task)
        add_row.addWidget(add_button)
        layout.addLayout(add_row)

        self.list_widget = QListWidget()
        self.list_widget.setMaximumHeight(150)
        layout.addWidget(self.list_widget)

        self.setLayout(layout)
        self.refresh()

    def on_add_task(self):
        name = self.new_task_input.text().strip()
        if not name:
            return
        try:
            task_manager.new_task(name)
            self.new_task_input.clear()
            self.refresh()
        except Exception as e:
            logger.error(f"Error adding task: {e}")

    def refresh(self):
        """Rebuild the task rows from current state."""
        try:
            tasks = state_manager.get_tasks()
        except Exception as e:
            logger.error(f"Error loading tasks: {e}")
            return

        self.list_widget.clear()
        for task in tasks:
            self._add_row(task)

    def _add_row(self, task):
        item = QListWidgetItem(self.list_widget)
        row = QWidget()
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(4, 2, 4, 2)

        checkbox = QCheckBox()
        checkbox.setChecked(bool(task.get('done')))
        checkbox.stateChanged.connect(
            lambda state, tid=task['id']: self._on_toggle_done(tid, state)
        )
        row_layout.addWidget(checkbox)

        minutes = task.get('minutes_spent', 0)
        if task.get('timer_active'):
            minutes += task_manager.get_task_elapsed_seconds(task) // 60
        name_label = QLabel(f"{task['name']}  ·  {minutes}m")
        if task.get('done'):
            name_label.setStyleSheet("color: #6ecf6e; text-decoration: line-through;")
        row_layout.addWidget(name_label, stretch=1)

        timer_button = QPushButton("⏸" if task.get('timer_active') else "▶")
        timer_button.setFixedWidth(28)
        timer_button.setEnabled(not task.get('done'))
        timer_button.clicked.connect(
            lambda _, tid=task['id'], active=task.get('timer_active'): self._on_toggle_timer(tid, active)
        )
        row_layout.addWidget(timer_button)

        delete_button = QPushButton("🗑")
        delete_button.setFixedWidth(28)
        delete_button.clicked.connect(lambda _, tid=task['id']: self._on_delete(tid))
        row_layout.addWidget(delete_button)

        row.setLayout(row_layout)
        item.setSizeHint(row.sizeHint())
        self.list_widget.addItem(item)
        self.list_widget.setItemWidget(item, row)

    def _on_toggle_done(self, task_id, state):
        try:
            task_manager.toggle_done(task_id, done=bool(state))
            self.refresh()
        except Exception as e:
            logger.error(f"Error toggling task: {e}")

    def _on_toggle_timer(self, task_id, was_active):
        try:
            if was_active:
                task_manager.pause_task_timer(task_id)
            else:
                task_manager.start_task_timer(task_id)
            self.refresh()
        except Exception as e:
            logger.error(f"Error toggling task timer: {e}")

    def _on_delete(self, task_id):
        try:
            task_manager.delete_task(task_id)
            self.refresh()
        except Exception as e:
            logger.error(f"Error deleting task: {e}")
