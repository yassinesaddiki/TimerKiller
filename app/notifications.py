"""
Blocking Notification Module

Displays motivational pop-ups when blocked apps are detected.
"""

import logging
import os
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QMovie

logger = logging.getLogger(__name__)


class BlockingNotificationDialog(QDialog):
    """
    Pop-up notification when a blocked app is detected.
    Shows motivational message and animated GIF.
    User must close it manually.
    """
    
    def __init__(self, app_name, parent=None):
        super().__init__(parent)
        self.app_name = app_name
        self.setWindowTitle("Stay Focused!")
        self.setGeometry(100, 100, 450, 550)
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
                padding: 10px;
                font-size: 13px;
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
        
        # Animated GIF
        self.gif_label = QLabel()
        self.gif_label.setAlignment(Qt.AlignCenter)
        self.gif_label.setMinimumHeight(200)
        
        # Try to load GIF - look for it in app/Media folder
        gif_paths = [
            os.path.join(os.path.dirname(__file__), "Media", "never_give_up.gif"),
            os.path.join(os.path.dirname(__file__), "Media", "motivation.gif"),
            os.path.join(os.path.dirname(__file__), "Media", "cheering.gif"),
        ]
        
        gif_found = False
        for gif_path in gif_paths:
            if os.path.exists(gif_path):
                try:
                    self.movie = QMovie(gif_path)
                    self.movie.setScaledSize(Qt.QSize(150, 150))
                    self.gif_label.setMovie(self.movie)
                    self.movie.start()
                    gif_found = True
                    logger.info(f"Loaded GIF from: {gif_path}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to load GIF from {gif_path}: {e}")
        
        # If no GIF found, show emoji animation
        if not gif_found:
            emoji_label = QLabel("💪\n🎮\n✨")
            emoji_label.setFont(QFont("Arial", 48))
            emoji_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(emoji_label)
            logger.info("No GIF found, showing emoji instead")
        else:
            layout.addWidget(self.gif_label)
        
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
        
        # Close button (user must click)
        close_button = QPushButton("Back to Work! 💻")
        close_button.setFont(QFont("Arial", 12, QFont.Bold))
        close_button.clicked.connect(self.accept)
        layout.addWidget(close_button)
        
        self.setLayout(layout)
        
        logger.info(f"Blocking notification shown for: {app_name}")
    
    def show_modal(self):
        """Show the dialog as modal."""
        self.exec()
