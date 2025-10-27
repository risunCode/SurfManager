"""UI Helper utilities to reduce duplicate code across GUI modules."""
from PyQt6.QtWidgets import QMessageBox, QInputDialog
from app.gui.theme import apply_dark_theme


class DialogHelper:
    """Centralized dialog utilities to reduce QMessageBox duplication."""
    
    @staticmethod
    def show_info(parent, title: str, message: str):
        """Show information dialog."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setWindowTitle(title)
        msg.setText(message)
        apply_dark_theme(msg)
        msg.exec()
    
    @staticmethod
    def show_warning(parent, title: str, message: str):
        """Show warning dialog."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        apply_dark_theme(msg)
        msg.exec()
    
    @staticmethod
    def show_error(parent, title: str, message: str):
        """Show error dialog."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Critical)
        msg.setWindowTitle(title)
        msg.setText(message)
        apply_dark_theme(msg)
        msg.exec()
    
    @staticmethod
    def confirm(parent, title: str, message: str, default_no: bool = True) -> bool:
        """Show confirmation dialog. Returns True if Yes clicked."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Question)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(
            QMessageBox.StandardButton.No if default_no else QMessageBox.StandardButton.Yes
        )
        apply_dark_theme(msg)
        return msg.exec() == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def confirm_warning(parent, title: str, message: str, default_no: bool = True) -> bool:
        """Show warning confirmation dialog."""
        msg = QMessageBox(parent)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle(title)
        msg.setText(message)
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setDefaultButton(
            QMessageBox.StandardButton.No if default_no else QMessageBox.StandardButton.Yes
        )
        apply_dark_theme(msg)
        return msg.exec() == QMessageBox.StandardButton.Yes
    
    @staticmethod
    def get_text(parent, title: str, label: str, default: str = "") -> tuple:
        """Show input dialog. Returns (text, ok)."""
        text, ok = QInputDialog.getText(parent, title, label, text=default)
        return text.strip() if ok else "", ok
    
    @staticmethod
    def choose_app(parent, title: str, message: str) -> str:
        """Show app selection dialog. Returns 'windsurf', 'cursor', or empty string."""
        from PyQt6.QtWidgets import QMessageBox
        
        msg = QMessageBox(parent)
        msg.setWindowTitle(title)
        msg.setText(message)
        
        windsurf_btn = msg.addButton("Windsurf", QMessageBox.ButtonRole.ActionRole)
        cursor_btn = msg.addButton("Cursor", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        from app.gui.theme import apply_dark_theme
        apply_dark_theme(msg)
        
        msg.exec()
        clicked = msg.clickedButton()
        
        if clicked == windsurf_btn:
            return 'windsurf'
        elif clicked == cursor_btn:
            return 'cursor'
        else:
            return ""


class StyleHelper:
    """Centralized style utilities."""
    
    # Common button styles
    DANGER_BUTTON = """
        QPushButton {
            background-color: #c72e0f;
            border: 1px solid #e03e1c;
        }
        QPushButton:hover {
            background-color: #e03e1c;
        }
    """
    
    SUCCESS_BUTTON = """
        QPushButton {
            background-color: #4CAF50;
            border: 1px solid #45a049;
        }
        QPushButton:hover {
            background-color: #45a049;
        }
    """
    
    WARNING_BUTTON = """
        QPushButton {
            background-color: #8B4513;
            border: 1px solid #A0522D;
        }
        QPushButton:hover {
            background-color: #A0522D;
        }
    """
    
    DISABLED_BUTTON = """
        QPushButton {
            background-color: #f44336;
        }
        QPushButton:hover {
            background-color: #d32f2f;
        }
    """
    
    CONTEXT_MENU = """
        QMenu {
            background-color: #2b2b2b;
            color: #e0e0e0;
            border: 2px solid #404040;
            border-radius: 8px;
            padding: 8px;
        }
        QMenu::item {
            padding: 10px 24px;
            border-radius: 4px;
            margin: 2px 4px;
        }
        QMenu::item:selected {
            background-color: #0d7377;
            color: #ffffff;
        }
        QMenu::separator {
            height: 2px;
            background: #404040;
            margin: 6px 12px;
        }
    """
    
    @staticmethod
    def apply_button_style(button, style_type: str):
        """Apply predefined button style.
        
        Args:
            button: QPushButton instance
            style_type: 'danger', 'success', 'warning', 'disabled'
        """
        styles = {
            'danger': StyleHelper.DANGER_BUTTON,
            'success': StyleHelper.SUCCESS_BUTTON,
            'warning': StyleHelper.WARNING_BUTTON,
            'disabled': StyleHelper.DISABLED_BUTTON
        }
        
        style = styles.get(style_type.lower())
        if style:
            button.setStyleSheet(style)


class LogHelper:
    """Base class for components that need logging."""
    
    def __init__(self, log_callback=None, log_widget=None):
        """Initialize logger.
        
        Args:
            log_callback: Optional callback function for logging
            log_widget: Optional QTextEdit/QPlainTextEdit widget
        """
        self._log_callback = log_callback
        self._log_widget = log_widget
    
    def log(self, message: str):
        """Log message to callback and/or widget."""
        if self._log_callback:
            self._log_callback(message)
        
        if self._log_widget and hasattr(self._log_widget, 'append'):
            self._log_widget.append(message)
    
    def set_log_callback(self, callback):
        """Update log callback."""
        self._log_callback = callback
    
    def set_log_widget(self, widget):
        """Update log widget."""
        self._log_widget = widget


class ValidationHelper:
    """Common validation utilities."""
    
    @staticmethod
    def validate_not_empty(text: str, field_name: str = "Field") -> tuple:
        """Validate text is not empty.
        
        Returns:
            (is_valid, error_message)
        """
        text = text.strip() if text else ""
        if not text:
            return False, f"{field_name} cannot be empty"
        return True, ""
    
    @staticmethod
    def validate_no_special_chars(text: str, field_name: str = "Field") -> tuple:
        """Validate text contains no special characters.
        
        Returns:
            (is_valid, error_message)
        """
        import re
        if re.search(r'[<>:"/\\|?*]', text):
            return False, f"{field_name} contains invalid characters"
        return True, ""
    
    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename by removing invalid characters."""
        import re
        # Remove invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove control characters
        sanitized = ''.join(char for char in sanitized if ord(char) >= 32)
        # Trim whitespace
        sanitized = sanitized.strip()
        return sanitized if sanitized else "unnamed"
