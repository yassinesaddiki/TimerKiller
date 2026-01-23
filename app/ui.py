"""
User Interface Module for TimerKiller

Enhanced PySide6-based UI with goal editing, process selector, and notifications.
"""

import sys
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QInputDialog, QMessageBox, QSpinBox, QDialog, QComboBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont

from . import state_manager, pomodoro, blocker, game_detection
from .notifications import BlockingNotificationDialog

logger = logging.getLogger(__name__)


class TimerKillerUI(QMainWindow):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TimerKiller")
        self.setGeometry(100, 100, 400, 500)
        
        # Create central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # ===== GOAL SECTION =====
        goal_layout = QHBoxLayout()
        self.goal_label = QLabel()
        self.goal_label.setFont(QFont("Arial", 11, QFont.Bold))
        goal_layout.addWidget(self.goal_label)
        
        # Edit goal button
        self.edit_goal_button = QPushButton("✏️ Edit Goal")
        self.edit_goal_button.setMaximumWidth(100)
        self.edit_goal_button.clicked.connect(self.on_edit_goal_clicked)
        goal_layout.addWidget(self.edit_goal_button)
        
        main_layout.addLayout(goal_layout)
        
        # ===== TIMER DISPLAY SECTION =====
        timer_layout = QVBoxLayout()
        self.timer_display = QLabel("00:00:00")
        self.timer_display.setFont(QFont("Arial", 36, QFont.Bold))
        self.timer_display.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.timer_display)
        
        self.status_label = QLabel("Status: Idle")
        self.status_label.setAlignment(Qt.AlignCenter)
        timer_layout.addWidget(self.status_label)
        
        main_layout.addLayout(timer_layout)
        
        # ===== TIMER CONTROL BUTTONS =====
        button_layout = QHBoxLayout()
        
        self.start_button = QPushButton("Start Focus")
        self.start_button.clicked.connect(self.on_start_clicked)
        button_layout.addWidget(self.start_button)
        
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.on_pause_clicked)
        self.pause_button.setEnabled(False)
        button_layout.addWidget(self.pause_button)
        
        main_layout.addLayout(button_layout)
        
        # ===== BLOCKED APPS SECTION =====
        apps_title = QLabel("Blocked Applications:")
        apps_title.setFont(QFont("Arial", 10, QFont.Bold))
        main_layout.addWidget(apps_title)
        
        self.apps_list = QListWidget()
        self.apps_list.setMaximumHeight(120)
        main_layout.addWidget(self.apps_list)
        
        # ===== APP MANAGEMENT BUTTONS =====
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
        
        main_layout.addLayout(app_buttons_layout)
        
        # ===== REFRESH TIMER =====
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_display)
        self.refresh_timer.start(1000)  # Update every 1 second
        
        # Initial display update
        self.refresh_display()
        self.update_blocked_apps_list()
        
        logger.info("UI initialized")
    
    def refresh_display(self):
        """Update all UI elements from current state."""
        try:
            # Check for pending notifications from blocker
            self.process_notifications()
            
            # Update goal and progress
            goal = state_manager.get_daily_goal()
            focused = state_manager.get_focused_minutes()
            self.goal_label.setText(f"Daily Goal: {focused} / {goal} minutes")
            
            # Update timer display
            if pomodoro.is_session_active():
                elapsed = pomodoro.get_formatted_elapsed()
                self.timer_display.setText(elapsed)
                self.status_label.setText("Status: Running")
                self.start_button.setEnabled(False)
                self.pause_button.setEnabled(True)
            else:
                self.timer_display.setText("00:00:00")
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
        Handle window close event.
        UI can close, but enforcer continues running.
        """
        logger.info("UI window closing. Enforcer thread continues in background.")
        event.accept()


class ProcessSelectorDialog(QDialog):
    """
    Dialog for easy process/game selection.
    Shows categorized list of running processes and common games.
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
