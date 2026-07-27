"""
Blocking Notification Dialog — app/ui/notifications.py

CONTEXT:
- Modal pop-up shown when a blocked process was killed; purely presentational.
- Picks a random line from MOTIVATION_MESSAGES each time, so it stays fresh.
- Falls back to emoji if no GIF is found under app/Media/.
- Exposes: BlockingNotificationDialog (QDialog subclass), .show_modal().
- Used by: app.ui.main_window.TimerKillerUI.process_notifications().
- Depends on: PySide6 only (no core/enforcement imports).
"""

import logging
import os
import random
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap, QFont, QMovie

logger = logging.getLogger(__name__)

# Rotated at random so the message doesn't go stale after the tenth time.
MOTIVATION_MESSAGES = [
    "You are working on your dreams.\nYou are not that man anymore.\nFinish what you started.",
    "This isn't the version of you that you're trying to become.\nGet back to it.",
    "Every minute here is a minute you're not becoming\nwho you said you'd be.",
    "You already know how this ends if you keep clicking this.\nClose it. Go work.",
    "Future you is watching. Don't let them down\nover a game.",
    "The goal isn't finished. You know that.\nSo why are you here?",
    "Discipline is choosing between what you want now\nand what you want most.",
]


class BlockingNotificationDialog(QDialog):
    """
    Pop-up notification when a blocked app is detected.

    CONTEXT:
    - Shows a motivational message + animated GIF (or emoji fallback).
    - User must click "Back to Work!" to dismiss — no auto-close by design.
    - Instantiated per kill event in TimerKillerUI.process_notifications().
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
        media_dir = os.path.join(os.path.dirname(__file__), "..", "Media")
        gif_paths = [
            os.path.join(media_dir, "never_give_up.gif"),
            os.path.join(media_dir, "motivation.gif"),
            os.path.join(media_dir, "cheering.gif"),
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
        
        # Motivational message (randomized so it doesn't go stale)
        motivation_label = QLabel(random.choice(MOTIVATION_MESSAGES))
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
