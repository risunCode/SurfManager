"""Theme loader for SurfManager - Loads styles from external QSS file."""
from pathlib import Path
from app.core.core_utils import get_resource_path, debug_print


def load_stylesheet() -> str:
    """Load main stylesheet from external QSS file.
    
    Returns:
        Stylesheet string or empty string if file not found
    """
    try:
        qss_path = get_resource_path('app/gui/styles.qss')
        if qss_path.exists():
            debug_print(f"Loading stylesheet from: {qss_path}")
            return qss_path.read_text(encoding='utf-8')
        else:
            debug_print(f"Stylesheet not found: {qss_path}")
            return ""
    except Exception as e:
        debug_print(f"Error loading stylesheet: {e}")
        return ""


# Load stylesheet on import
COMPACT_DARK_STYLE = load_stylesheet()

# Fallback dialog style (minimal, kept inline)
DARK_DIALOG_STYLE = """
    QMessageBox, QDialog, QInputDialog {
        background-color: #252526;
        color: #cccccc;
    }
    QPushButton {
        background-color: #404040;
        color: #e0e0e0;
        border: 1px solid #555555;
        padding: 8px 16px;
        border-radius: 4px;
        min-width: 80px;
    }
    QPushButton:hover {
        background-color: #505050;
    }
"""


def apply_dark_theme(dialog):
    """Apply dark theme to dialog."""
    dialog.setStyleSheet(DARK_DIALOG_STYLE)
