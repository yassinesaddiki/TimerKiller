"""
Close Confirmation Dialog — app/ui/close_dialog.py

CONTEXT:
- Modal shown when the user clicks the window's close (X) button.
- Purely presentational + a QTimer countdown; no core/enforcement imports.
- The "confirm" button stays disabled for CLOSE_DELAY_SECONDS so closing
  can never be a reflexive click — the user has to sit with the question.
- Confirming only hides the window to the system tray (app.ui.main_window
  wires the tray icon); it never terminates the process or the enforcer.
- Used by: app.ui.main_window.TimerKillerUI.closeEvent().
"""

from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

CLOSE_DELAY_SECONDS = 5


class CloseConfirmDialog(QDialog):
    """
    Asks "are you sure?" and forces a wait before the confirm button unlocks.

    CONTEXT:
    - result() is QDialog.Accepted if the user waited out the countdown and
      confirmed, QDialog.Rejected otherwise (including the window's own X).
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Wait a second.")
        self.setFixedSize(380, 260)
        self.setModal(True)
        self._seconds_left = CLOSE_DELAY_SECONDS

        self.setStyleSheet("""
            QDialog { background-color: #14141f; }
            QLabel { color: #eaeaf0; }
            QPushButton {
                border-radius: 6px;
                padding: 10px;
                font-weight: bold;
                font-size: 12px;
            }
        """)

        layout = QVBoxLayout()
        layout.setSpacing(14)

        title = QLabel("Are you sure you want this for your life?")
        title.setFont(QFont("Segoe UI", 13, QFont.Bold))
        title.setWordWrap(True)
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        subtitle = QLabel(
            "Closing this doesn't end your session — it just hides to the\n"
            "tray. Blocking keeps running. Take a breath before you decide."
        )
        subtitle.setWordWrap(True)
        subtitle.setAlignment(Qt.AlignCenter)
        subtitle.setStyleSheet("color: #9a9ab0; font-size: 11px;")
        layout.addWidget(subtitle)

        self.confirm_button = QPushButton()
        self._update_confirm_label()
        self.confirm_button.setEnabled(False)
        self.confirm_button.setStyleSheet(
            "background-color: #3a3a52; color: #7a7a90;"
        )
        self.confirm_button.clicked.connect(self.accept)
        layout.addWidget(self.confirm_button)

        cancel_button = QPushButton("Never mind, back to work")
        cancel_button.setStyleSheet("background-color: #2ecc71; color: #0d1a12;")
        cancel_button.clicked.connect(self.reject)
        layout.addWidget(cancel_button)

        self.setLayout(layout)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._tick)
        self._timer.start(1000)

    def _update_confirm_label(self):
        if self._seconds_left > 0:
            self.confirm_button.setText(f"Yes, minimize me ({self._seconds_left}s)")
        else:
            self.confirm_button.setText("Yes, minimize to tray")

    def _tick(self):
        self._seconds_left -= 1
        self._update_confirm_label()
        if self._seconds_left <= 0:
            self._timer.stop()
            self.confirm_button.setEnabled(True)
            self.confirm_button.setStyleSheet(
                "background-color: #e74c3c; color: white;"
            )
