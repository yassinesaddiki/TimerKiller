"""
User Interface Module for TimerKiller

Minimal PySide6-based UI for controlling timer and managing blocked apps.
"""

import sys
import logging
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QListWidget, QListWidgetItem,
    QInputDialog, QMessageBox
)
from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QFont

from . import state_manager, pomodoro, blocker

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
        self.apps_list.setMaximumHeight(150)
        main_layout.addWidget(self.apps_list)
        
        # ===== APP MANAGEMENT BUTTONS =====
        app_buttons_layout = QHBoxLayout()
        
        self.add_app_button = QPushButton("+ Add App")
        self.add_app_button.clicked.connect(self.on_add_app_clicked)
        app_buttons_layout.addWidget(self.add_app_button)
        
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
