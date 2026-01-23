"""
Blocking Notification Module

Displays motivational pop-ups when blocked apps are detected.
"""

import logging
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QFont, QMovie

logger = logging.getLogger(__name__)


class BlockingNotificationDialog(QDialog):
    """
    Pop-up notification when a blocked app is detected.
    Shows motivational message and optional GIF.
    """
    
    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.setWindowTitle("Stay Focused!")
        self.setGeometry(100, 100, 400, 300)
        self.setStyleSheet("""
            QDialog {
                background-color: #1a1a2e;
                color: white;
            }
            QLabel {
                color: white;
            }
            QPushButton {
                background-color: #e74c3c;
                color: white;
                font-weight: bold;
                border-radius: 5px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Main message
        message_label = QLabel("🎮 STAY FOCUSED, CHAMP! 🎮")
        message_label.setFont(QFont("Arial", 16, QFont.Bold))
        message_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(message_label)
        
        # App name
        app_label = QLabel(f"Tried to open: {app_name}")
        app_label.setFont(QFont("Arial", 12))
        app_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(app_label)
        
        # Motivational message
        motivation_label = QLabel(
            "You're so close to unlocking this app!\n\n"
            "Keep grinding. You've got this!\n\n"
            "💪 NEVER GIVE UP! 💪"
        )
        motivation_label.setFont(QFont("Arial", 11))
        motivation_label.setAlignment(Qt.AlignCenter)
        motivation_label.setStyleSheet("color: #f39c12;")
        layout.addWidget(motivation_label)
        
        # Close button
        close_button = QPushButton("Back to Work! 💻")
        close_button.setFont(QFont("Arial", 12, QFont.Bold))
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        
        # Auto-close after 5 seconds
        QTimer.singleShot(5000, self.accept)
        
        logger.info(f"Blocking notification shown for: {app_name}")
    
    def show_modal(self):
        """Show the dialog as modal."""
        self.exec()
