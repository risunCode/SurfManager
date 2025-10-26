"""Theme utilities for SurfManager - Reusable styling functions."""

# Dark theme stylesheet for dialogs
DARK_DIALOG_STYLE = """
    QMessageBox, QDialog, QInputDialog {
        background-color: #252526;
        color: #cccccc;
    }
    QMessageBox QLabel, QDialog QLabel, QInputDialog QLabel {
        color: #cccccc;
        background-color: transparent;
    }
    QMessageBox QPushButton, QDialog QPushButton, QInputDialog QPushButton {
        background-color: #404040;
        color: #e0e0e0;
        border: 1px solid #555555;
        padding: 8px 16px;
        border-radius: 4px;
        min-width: 80px;
    }
    QMessageBox QPushButton:hover, QDialog QPushButton:hover, QInputDialog QPushButton:hover {
        background-color: #505050;
    }
    QMessageBox QPushButton:pressed, QDialog QPushButton:pressed, QInputDialog QPushButton:pressed {
        background-color: #353535;
    }
    QInputDialog QLineEdit {
        background-color: #3c3c3c;
        color: #cccccc;
        border: 1px solid #555555;
        padding: 5px;
        border-radius: 3px;
    }
"""


def apply_dark_theme(dialog):
    """Apply dark theme to any QDialog, QMessageBox, or QInputDialog.
    
    Args:
        dialog: PyQt6 dialog widget to apply theme to
    """
    dialog.setStyleSheet(DARK_DIALOG_STYLE)
