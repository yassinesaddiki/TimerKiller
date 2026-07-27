"""
Main Window Module — app/ui/main_window.py

CONTEXT:
- Top-level PySide6 window: goal editing, Pomodoro controls, task list,
  blocked-apps list. Resizable (header bar + two-column card layout,
  right column scrollable) instead of the old fixed-size single stack.
- Also hosts ProcessSelectorDialog (pick games/processes to block) and
  TimerCircle (custom-painted circular progress widget).
- Polls state every 1s via QTimer and re-renders; also drains blocker's
  notification queue and pops BlockingNotificationDialog when needed.
- Depends on: app.core (state_manager, pomodoro, task_manager),
  app.enforcement (blocker, game_detection), app.system (startup),
  app.ui.notifications, app.ui.close_dialog, app.ui.task_widget.
- Close (X) button never quits the process: it opens CloseConfirmDialog
  (5s forced wait) and, if confirmed, hides to a QSystemTrayIcon. The tray
  menu's "Quit" is the only real exit path. The enforcer thread is tied to
  the process, not the window, so it keeps running either way until the
  process actually exits.
"""

import sys
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem, QFrame,
    QInputDialog, QMessageBox, QSpinBox, QDialog, QComboBox, QCheckBox,
    QSystemTrayIcon, QMenu, QScrollArea, QSizePolicy
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont, QColor, QPainter, QBrush, QPen, QIcon, QPixmap, QAction

from ..core import state_manager, pomodoro
from ..enforcement import blocker, game_detection
from ..system import startup
from .notifications import BlockingNotificationDialog
from .close_dialog import CloseConfirmDialog
from .task_widget import TaskListWidget

logger = logging.getLogger(__name__)

# Clean dark theme applied to the whole window. Cards give each section a
# visually distinct surface so the layout reads as organized regions rather
# than one long stack of controls.
STYLESHEET = """
QMainWindow, QDialog { background-color: #0f0f18; }
QWidget#centralWidget { background-color: #0f0f18; }
QLabel { color: #eaeaf0; font-family: 'Segoe UI'; }
QLabel#sectionHeader {
    color: #9a9ab0;
    font-size: 11px;
    font-weight: bold;
    letter-spacing: 1px;
}
QLabel#appTitle { color: #ffffff; font-size: 20px; font-weight: bold; }
QLabel#appSubtitle { color: #75758c; font-size: 11px; }
QLabel#cardTitle {
    color: #eaeaf0;
    font-size: 13px;
    font-weight: bold;
}
QFrame#card {
    background-color: #181826;
    border: 1px solid #26263a;
    border-radius: 10px;
}
QFrame#headerBar {
    background-color: #14141f;
    border-bottom: 1px solid #24243a;
}
QFrame#hline { background-color: #26263a; max-height: 1px; }
QPushButton {
    background-color: #2a2a40;
    color: #eaeaf0;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-family: 'Segoe UI';
    font-weight: bold;
}
QPushButton:hover { background-color: #35354f; }
QPushButton:disabled { background-color: #1a1a28; color: #55556a; }
QPushButton#primaryButton {
    background-color: #e74c3c;
    color: white;
}
QPushButton#primaryButton:hover { background-color: #ef5a4a; }
QPushButton#primaryButton:disabled { background-color: #3a2a28; color: #7a5a55; }
QListWidget {
    background-color: #12121c;
    color: #eaeaf0;
    border: 1px solid #26263a;
    border-radius: 6px;
}
QLineEdit {
    background-color: #12121c;
    color: #eaeaf0;
    border: 1px solid #26263a;
    border-radius: 6px;
    padding: 6px;
}
QCheckBox { color: #eaeaf0; }
QComboBox {
    background-color: #12121c;
    color: #eaeaf0;
    border: 1px solid #26263a;
    border-radius: 6px;
    padding: 4px;
}
QScrollArea { border: none; background: transparent; }
"""


def _make_card(title=None):
    """Build a QFrame('card') with an optional bold title row + vlayout body.

    Returns (card_frame, content_layout) — callers add their widgets to
    content_layout, keeping consistent card padding/spacing everywhere.
    """
    card = QFrame()
    card.setObjectName("card")
    outer = QVBoxLayout(card)
    outer.setContentsMargins(16, 14, 16, 16)
    outer.setSpacing(10)
    if title:
        title_label = QLabel(title)
        title_label.setObjectName("cardTitle")
        outer.addWidget(title_label)
    return card, outer


def _build_tray_icon():
    """Generate a small circular tray icon (no external asset dependency)."""
    pixmap = QPixmap(32, 32)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QBrush(QColor("#e74c3c")))
    painter.setPen(Qt.NoPen)
    painter.drawEllipse(2, 2, 28, 28)
    painter.setPen(QPen(QColor("white")))
    painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
    painter.drawText(pixmap.rect(), Qt.AlignCenter, "TK")
    painter.end()
    return QIcon(pixmap)


class TimerKillerUI(QMainWindow):
    """
    Main application window.

    CONTEXT:
    - Resizable window (min 760x560, opens at 1040x720, supports maximize/
      full screen); single instance, created once in app.main.
    - Layout: a header bar (title + live goal readout) over a two-column
      body — left column is a "Focus" card (TimerCircle, start/pause,
      startup toggle), right column stacks a "Tasks" card and a
      "Blocked Applications" card, both scrollable so the window can shrink
      without clipping content.
    - Polls state every 1s (self.refresh_timer) and re-renders from state_manager
      + pomodoro; also drains blocker's notification queue each tick.
    - closeEvent() intentionally does NOT stop the enforcer thread.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimerKiller")
        self.setMinimumSize(760, 560)
        self.resize(1040, 720)
        self.setStyleSheet(STYLESHEET)
        self._tray_icon_pixmap = _build_tray_icon()
        self.setWindowIcon(self._tray_icon_pixmap)
        self._force_quit = False

        # Create central widget and main layout
        central_widget = QWidget()
        central_widget.setObjectName("centralWidget")
        self.setCentralWidget(central_widget)
        root_layout = QVBoxLayout(central_widget)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # ===== HEADER BAR =====
        header_bar = QFrame()
        header_bar.setObjectName("headerBar")
        header_layout = QHBoxLayout(header_bar)
        header_layout.setContentsMargins(24, 16, 24, 16)

        title_block = QVBoxLayout()
        title_block.setSpacing(2)
        app_title = QLabel("TimerKiller")
        app_title.setObjectName("appTitle")
        title_block.addWidget(app_title)
        app_subtitle = QLabel("Hit your goal, or the apps stay locked.")
        app_subtitle.setObjectName("appSubtitle")
        title_block.addWidget(app_subtitle)
        header_layout.addLayout(title_block)
        header_layout.addStretch()

        self.goal_label = QLabel()
        self.goal_label.setFont(QFont("Segoe UI", 12, QFont.Bold))
        header_layout.addWidget(self.goal_label)

        self.edit_goal_button = QPushButton("✏️ Edit Goal")
        self.edit_goal_button.clicked.connect(self.on_edit_goal_clicked)
        header_layout.addWidget(self.edit_goal_button)

        root_layout.addWidget(header_bar)

        # ===== BODY (two columns) =====
        body = QWidget()
        body_layout = QHBoxLayout(body)
        body_layout.setContentsMargins(24, 20, 24, 24)
        body_layout.setSpacing(20)
        root_layout.addWidget(body, stretch=1)

        # ----- Left column: Focus card -----
        focus_card, focus_layout = _make_card("Focus Session")
        focus_card.setMinimumWidth(320)

        self.timer_display = TimerCircle()
        self.timer_display.setMinimumHeight(220)
        focus_layout.addWidget(self.timer_display, stretch=1)

        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Bold))
        focus_layout.addWidget(self.status_label)

        button_layout = QHBoxLayout()
        self.start_button = QPushButton("▶ Start Focus")
        self.start_button.setObjectName("primaryButton")
        self.start_button.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(self.start_button)

        self.pause_button = QPushButton("⏸ Pause")
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        focus_layout.addLayout(button_layout)

        divider = QFrame()
        divider.setObjectName("hline")
        divider.setFixedHeight(1)
        focus_layout.addWidget(divider)

        settings_layout = QHBoxLayout()
        self.startup_checkbox = QCheckBox("Start on Windows Startup")
        self.startup_checkbox.setChecked(startup.is_startup_enabled())
        self.startup_checkbox.stateChanged.connect(self.on_startup_toggled)
        settings_layout.addWidget(self.startup_checkbox)
        settings_layout.addStretch()
        focus_layout.addLayout(settings_layout)

        body_layout.addWidget(focus_card, stretch=2)

        # ----- Right column: Tasks + Blocked Apps, scrollable -----
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        right_column = QWidget()
        right_layout = QVBoxLayout(right_column)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(20)

        # ===== TASK LIST SECTION =====
        tasks_card, tasks_layout = _make_card("Tasks")
        self.task_widget = TaskListWidget()
        tasks_layout.addWidget(self.task_widget)
        right_layout.addWidget(tasks_card)

        # ===== BLOCKED APPS SECTION =====
        apps_card, apps_layout = _make_card("Blocked Applications")

        self.apps_list = QListWidget()
        self.apps_list.setMinimumHeight(140)
        apps_layout.addWidget(self.apps_list)

        app_buttons_layout = QHBoxLayout()
        self.add_app_button = QPushButton("+ Add App")
        self.add_app_button.clicked.connect(self.on_add_app_clicked)
        app_buttons_layout.addWidget(self.add_app_button)

        self.process_selector_button = QPushButton("🎮 Select Games")
        self.process_selector_button.clicked.connect(self.on_process_selector_clicked)
        app_buttons_layout.addWidget(self.process_selector_button)

        self.remove_app_button = QPushButton("- Remove App")
        self.remove_app_button.clicked.connect(self.on_remove_app_clicked)
        app_buttons_layout.addWidget(self.remove_app_button)
        apps_layout.addLayout(app_buttons_layout)

        right_layout.addWidget(apps_card)
        right_layout.addStretch()

        right_scroll.setWidget(right_column)
        body_layout.addWidget(right_scroll, stretch=3)

        # ===== SYSTEM TRAY =====
        self._setup_tray_icon()

        # ===== REFRESH TIMER =====
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(1000)  # Update every 1 second

        # Initial display update
        self.refresh_display()
        self.update_blocked_apps_list()

        logger.info("UI initialized")

    def _setup_tray_icon(self):
        """Create the system tray icon + menu (Open / Quit)."""
        self.tray_icon = QSystemTrayIcon(self._tray_icon_pixmap, self)
        self.tray_icon.setToolTip("TimerKiller — still enforcing")

        tray_menu = QMenu()

        open_action = QAction("Open TimerKiller", self)
        open_action.triggered.connect(self._restore_from_tray)
        tray_menu.addAction(open_action)

        quit_action = QAction("Quit (stops blocking)", self)
        quit_action.triggered.connect(self._quit_from_tray)
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self._on_tray_activated)
        self.tray_icon.show()

    def _on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.Trigger:
            self._restore_from_tray()

    def _restore_from_tray(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def _quit_from_tray(self):
        """Explicit, deliberate exit — the only path that stops the enforcer."""
        confirm = QMessageBox.question(
            self,
            "Quit TimerKiller",
            "This fully exits TimerKiller — blocking stops completely.\n"
            "Are you sure?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        if confirm == QMessageBox.Yes:
            self._force_quit = True
            self.tray_icon.hide()
            from PySide6.QtWidgets import QApplication
            QApplication.quit()
    
    def refresh_display(self):
        """Update all UI elements from current state."""
        try:
            # Check for pending notifications from blocker
            self.process_notifications()

            # Keep task timers ticking on screen
            self.task_widget.refresh()

            # Update goal and progress
            goal = state_manager.get_daily_goal()
            focused = state_manager.get_focused_minutes()
            self.goal_label.setText(f"Daily Goal: {focused} / {goal} minutes")
            
            # Update timer display
            if pomodoro.is_session_active():
                elapsed = pomodoro.get_formatted_elapsed()
                elapsed_sec = pomodoro.get_elapsed_seconds()
                self.timer_display.update_timer(elapsed, elapsed_sec)
                self.status_label.setText("Status: Running")
                self.start_button.setEnabled(False)
                self.pause_button.setEnabled(True)
            else:
                self.timer_display.update_timer("00:00:00", 0)
                self.status_label.setText("Status: Paused")
                self.start_button.setEnabled(True)
                self.pause_button.setEnabled(False)
            
            # Check if goal is met
            if state_manager.is_goal_met():
                self.goal_label.setStyleSheet("color: green; font-weight: bold;")
                self.status_label.setText("Status: Goal Met! ✓")
            else:
                self.goal_label.setStyleSheet("")
        
        except Exception as e:
            logger.error(f"Error refreshing display: {e}")
    
    def process_notifications(self):
        """Process and display pending notifications from blocker."""
        try:
            notifications = blocker.get_pending_notifications()
            for notif_type, data in notifications:
                if notif_type == "block":
                    # Show blocking notification
                    dialog = BlockingNotificationDialog(data, self)
                    dialog.show_modal()
        except Exception as e:
            logger.error(f"Error processing notifications: {e}")
    
    def on_startup_toggled(self):
        """Handle startup checkbox toggle."""
        try:
            if self.startup_checkbox.isChecked():
                success = startup.enable_startup()
                if success:
                    logger.info("Startup enabled")
                else:
                    self.startup_checkbox.setChecked(False)
                    QMessageBox.warning(self, "Error", "Failed to enable startup. Run as administrator?")
            else:
                success = startup.disable_startup()
                if success:
                    logger.info("Startup disabled")
                else:
                    self.startup_checkbox.setChecked(True)
                    QMessageBox.warning(self, "Error", "Failed to disable startup")
        except Exception as e:
            logger.error(f"Error toggling startup: {e}")
            QMessageBox.critical(self, "Error", f"Failed to toggle startup: {e}")
    
    def on_start_clicked(self):
        """Start focus session button clicked."""
        try:
            pomodoro.start_focus_session()
            self.refresh_display()
            logger.info("Start button clicked")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to start session: {e}")
            logger.error(f"Error starting session: {e}")
    
    def on_pause_clicked(self):
        """Pause focus session button clicked."""
        try:
            pomodoro.pause_session()
            self.refresh_display()
            logger.info("Pause button clicked")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to pause session: {e}")
            logger.error(f"Error pausing session: {e}")
    
    def on_add_app_clicked(self):
        """Add blocked app button clicked."""
        try:
            app_name, ok = QInputDialog.getText(
                self,
                "Add Blocked App",
                "Enter process name (e.g., steam.exe):"
            )
            
            if ok and app_name:
                state_manager.add_blocked_app(app_name)
                self.update_blocked_apps_list()
                logger.info(f"Added app: {app_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add app: {e}")
            logger.error(f"Error adding app: {e}")
    
    def on_remove_app_clicked(self):
        """Remove blocked app button clicked."""
        try:
            current_item = self.apps_list.currentItem()
            if not current_item:
                QMessageBox.warning(self, "No Selection", "Please select an app to remove")
                return
            
            app_name = current_item.text()
            state_manager.remove_blocked_app(app_name)
            self.update_blocked_apps_list()
            logger.info(f"Removed app: {app_name}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove app: {e}")
            logger.error(f"Error removing app: {e}")
    
    def on_edit_goal_clicked(self):
        """Edit daily focus goal button clicked."""
        try:
            current_goal = state_manager.get_daily_goal()
            new_goal, ok = QInputDialog.getInt(
                self,
                "Edit Daily Goal",
                "Enter your daily focus goal (in minutes):",
                value=current_goal,
                minValue=1,
                maxValue=1440,
                step=15
            )
            
            if ok:
                state_manager.set_daily_goal(new_goal)
                self.refresh_display()
                QMessageBox.information(
                    self,
                    "Goal Updated",
                    f"Daily goal updated to {new_goal} minutes!"
                )
                logger.info(f"Daily goal changed to: {new_goal} minutes")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to edit goal: {e}")
            logger.error(f"Error editing goal: {e}")
    
    def on_process_selector_clicked(self):
        """Open process selector dialog for easy game blocking."""
        try:
            dialog = ProcessSelectorDialog(self)
            dialog.exec()
            self.update_blocked_apps_list()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to open process selector: {e}")
            logger.error(f"Error in process selector: {e}")
    
    def update_blocked_apps_list(self):
        """Sync UI list with state_manager."""
        try:
            self.apps_list.clear()
            blocked_apps = state_manager.get_blocked_apps()
            
            for app in blocked_apps:
                item = QListWidgetItem(app)
                self.apps_list.addItem(item)
        except Exception as e:
            logger.error(f"Error updating blocked apps list: {e}")
    
    def closeEvent(self, event):
        """
        Handle the window's close (X) button.

        Never actually exits the app: shows CloseConfirmDialog (5s forced
        wait); if confirmed, hides to the system tray instead of closing.
        Quitting for real only happens via the tray menu's "Quit".
        """
        if self._force_quit:
            event.accept()
            return

        event.ignore()
        dialog = CloseConfirmDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.hide()
            self.tray_icon.showMessage(
                "TimerKiller is still running",
                "Blocking stays active in the background. Open it again from the tray.",
                QSystemTrayIcon.Information,
                4000
            )
            logger.info("UI hidden to tray. Enforcer thread continues in background.")


class ProcessSelectorDialog(QDialog):
    """
    Dialog for easy process/game selection.

    CONTEXT:
    - Modal dialog opened from the "Select Games" button on TimerKillerUI.
    - Three views (category combo): All / Common Games / Running Processes,
      backed by app.enforcement.game_detection for categorization.
    - Add/Remove Selected buttons write directly through state_manager
      (add_blocked_app/remove_blocked_app); caller refreshes its own list after.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Select Games to Block")
        self.setGeometry(150, 150, 500, 400)
        self.blocked_apps = set(state_manager.get_blocked_apps())
        
        layout = QVBoxLayout()
        
        # Category selector
        category_layout = QHBoxLayout()
        category_layout.addWidget(QLabel("Category:"))
        
        self.category_combo = QComboBox()
        self.category_combo.addItems(["All", "Common Games", "Running Processes"])
        self.category_combo.currentTextChanged.connect(self.on_category_changed)
        category_layout.addWidget(self.category_combo)
        layout.addLayout(category_layout)
        
        # Process list
        self.process_list = QListWidget()
        layout.addWidget(self.process_list)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        add_selected_btn = QPushButton("✅ Add Selected")
        add_selected_btn.clicked.connect(self.on_add_selected)
        button_layout.addWidget(add_selected_btn)
        
        remove_selected_btn = QPushButton("❌ Remove Selected")
        remove_selected_btn.clicked.connect(self.on_remove_selected)
        button_layout.addWidget(remove_selected_btn)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Load initial list
        self.on_category_changed("All")
    
    def on_category_changed(self, category):
        """Update process list based on selected category."""
        self.process_list.clear()
        
        if category == "All":
            self.populate_all_processes()
        elif category == "Common Games":
            self.populate_common_games()
        elif category == "Running Processes":
            self.populate_running_processes()
    
    def populate_common_games(self):
        """Populate list with common game executables."""
        common_games = game_detection.get_common_games()
        for game in sorted(common_games):
            self.add_process_item(game)
    
    def populate_running_processes(self):
        """Populate list with currently running processes."""
        try:
            import psutil
            processes = []
            for proc in psutil.process_iter(['name']):
                try:
                    processes.append(proc.name())
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Categorize and display
            categorized = game_detection.categorize_processes(processes)
            
            for category, procs in categorized.items():
                if procs:
                    header = QListWidgetItem(f"--- {category} ---")
                    header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
                    self.process_list.addItem(header)
                    
                    for proc in sorted(set(procs)):
                        self.add_process_item(proc)
        
        except Exception as e:
            logger.error(f"Error fetching running processes: {e}")
    
    def populate_all_processes(self):
        """Populate with both common games and running processes."""
        # First add common games
        common_games = game_detection.get_common_games()
        header = QListWidgetItem("--- Common Games ---")
        header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
        self.process_list.addItem(header)
        
        for game in sorted(common_games):
            self.add_process_item(game)
        
        # Then add running processes
        try:
            import psutil
            running_games = []
            for proc in psutil.process_iter(['name']):
                try:
                    name = proc.name()
                    if game_detection.is_game_process(name):
                        running_games.append(name)
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            if running_games:
                header = QListWidgetItem("--- Running Games ---")
                header.setFlags(header.flags() & ~Qt.ItemIsSelectable)
                self.process_list.addItem(header)
                
                for game in sorted(set(running_games)):
                    self.add_process_item(game)
        except Exception as e:
            logger.error(f"Error fetching running games: {e}")
    
    def add_process_item(self, process_name):
        """Add a process to the list with checkbox styling."""
        item = QListWidgetItem(process_name)
        item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
        
        # Check if already blocked
        if process_name.lower() in [app.lower() for app in self.blocked_apps]:
            item.setText(f"✓ {process_name}")
            item.setSelected(True)
        
        self.process_list.addItem(item)
    
    def on_add_selected(self):
        """Add selected processes to blocked list."""
        try:
            selected_items = self.process_list.selectedItems()
            for item in selected_items:
                app_name = item.text().replace("✓ ", "")
                if app_name.startswith("---"):
                    continue
                
                state_manager.add_blocked_app(app_name)
                item.setText(f"✓ {app_name}")
            
            logger.info(f"Added {len(selected_items)} apps to blocked list")
            QMessageBox.information(self, "Success", f"Added {len(selected_items)} app(s)!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to add apps: {e}")
            logger.error(f"Error adding apps: {e}")
    
    def on_remove_selected(self):
        """Remove selected processes from blocked list."""
        try:
            selected_items = self.process_list.selectedItems()
            for item in selected_items:
                app_name = item.text().replace("✓ ", "")
                if app_name.startswith("---"):
                    continue
                
                state_manager.remove_blocked_app(app_name)
                item.setText(app_name)
            
            logger.info(f"Removed {len(selected_items)} apps from blocked list")
            QMessageBox.information(self, "Success", f"Removed {len(selected_items)} app(s)!")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to remove apps: {e}")
            logger.error(f"Error removing apps: {e}")


class TimerCircle(QWidget):
    """
    Custom circular timer display with progress animation.

    CONTEXT:
    - Pure presentation widget: no state_manager/pomodoro access of its own.
    - Caller (TimerKillerUI.refresh_display) pushes formatted time + elapsed
      seconds via update_timer(); paintEvent() draws the ring + centered text.
    - max_seconds = 25 min (one Pomodoro) is the 100% reference for the arc.
    """
    
    def __init__(self):
        super().__init__()
        self.time_str = "00:00:00"
        self.elapsed_seconds = 0
        self.max_seconds = 25 * 60  # 25 minutes in seconds
        self.setStyleSheet("background-color: transparent;")
    
    def update_timer(self, time_str, elapsed_sec):
        """Update timer display with time string and elapsed seconds."""
        self.time_str = time_str
        self.elapsed_seconds = elapsed_sec
        # Cap at max to avoid over-filling circle
        if elapsed_sec > self.max_seconds:
            self.elapsed_seconds = self.max_seconds
        self.update()  # Trigger repaint
    
    def paintEvent(self, event):
        """Draw circular timer with progress."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # Get widget dimensions
        rect = self.rect()
        center_x = rect.width() // 2
        center_y = rect.height() // 2
        radius = min(rect.width(), rect.height()) // 2 - 20
        
        # Draw background circle
        bg_color = QColor("#2a2a4e")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(QPen(QColor("#3a3a5e"), 2))
        painter.drawEllipse(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # Draw progress arc
        progress = self.elapsed_seconds / self.max_seconds if self.max_seconds > 0 else 0
        progress = min(progress, 1.0)  # Cap at 100%
        
        progress_color = QColor("#e74c3c") if progress > 0 else QColor("#3498db")
        painter.setPen(QPen(progress_color, 4))
        painter.setBrush(Qt.NoBrush)
        
        # Draw arc (16ths of degree = 1/360th)
        start_angle = 90 * 16  # Start at top
        span_angle = int(-progress * 360 * 16)  # Clockwise
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            start_angle, span_angle
        )
        
        # Draw center text
        painter.setFont(QFont("Arial", 32, QFont.Bold))
        painter.setPen(QPen(QColor("white")))
        painter.drawText(
            rect,
            Qt.AlignCenter,
            self.time_str
        )
        
        painter.end()

