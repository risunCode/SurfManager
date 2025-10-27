"""Advanced Settings tab functionality for SurfManager."""
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QGroupBox, QGridLayout, QTextEdit, QLineEdit, QFileDialog,
    QTabWidget, QComboBox
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QSyntaxHighlighter, QTextCharFormat, QColor
from app.core.config_manager import ConfigManager
from app.core.core_utils import open_folder_in_explorer, get_resource_path
from app.core.path_validator import PathValidator
from app.gui.ui_helpers import DialogHelper, StyleHelper


class JsonSyntaxHighlighter(QSyntaxHighlighter):
    """Simple JSON syntax highlighter."""
    
    def __init__(self, document):
        super().__init__(document)
        
        # Define colors for dark theme
        self.keyword_color = QColor(86, 156, 214)      # Blue
        self.string_color = QColor(206, 145, 120)      # Orange
        self.number_color = QColor(181, 206, 168)      # Light green
        self.boolean_color = QColor(86, 156, 214)      # Blue
        self.null_color = QColor(128, 128, 128)        # Gray
        
    def highlightBlock(self, text):
        """Highlight JSON syntax."""
        # Strings (anything between quotes)
        string_format = QTextCharFormat()
        string_format.setForeground(self.string_color)
        
        i = 0
        while i < len(text):
            if text[i] == '"':
                start = i
                i += 1
                # Find closing quote
                while i < len(text) and text[i] != '"':
                    if text[i] == '\\' and i + 1 < len(text):
                        i += 2  # Skip escaped character
                    else:
                        i += 1
                if i < len(text):
                    i += 1  # Include closing quote
                self.setFormat(start, i - start, string_format)
            else:
                i += 1
        
        # Numbers
        number_format = QTextCharFormat()
        number_format.setForeground(self.number_color)
        
        import re
        for match in re.finditer(r'\b\d+\.?\d*\b', text):
            self.setFormat(match.start(), match.end() - match.start(), number_format)
        
        # Booleans and null
        bool_format = QTextCharFormat()
        bool_format.setForeground(self.boolean_color)
        
        null_format = QTextCharFormat()
        null_format.setForeground(self.null_color)
        
        for match in re.finditer(r'\b(true|false)\b', text):
            self.setFormat(match.start(), match.end() - match.start(), bool_format)
            
        for match in re.finditer(r'\bnull\b', text):
            self.setFormat(match.start(), match.end() - match.start(), null_format)


class AdvancedTab(QWidget):
    """Advanced Settings tab widget."""
    
    def __init__(self, app_manager, log_callback):
        super().__init__()
        self.app_manager = app_manager
        self.log_callback = log_callback
        self.config_manager = ConfigManager()
        self.current_user = None  # Track current selected user
        
        self.init_ui()
        self.load_current_config()
    
    def log(self, message: str):
        """Log message."""
        if self.log_callback:
            self.log_callback(message)
    
    def init_ui(self):
        """Initialize the advanced tab UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Title and description
        title_layout = QHBoxLayout()
        title_label = QLabel("⚙️ Advanced Settings")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #ffffff;")
        title_layout.addWidget(title_label)
        
        title_layout.addStretch()
        
        # Quick actions
        self.create_quick_actions(title_layout)
        main_layout.addLayout(title_layout)
        
        # Description
        desc_label = QLabel("Configure application paths, import/export settings, and edit configuration files.")
        desc_label.setStyleSheet("color: #aaa; font-size: 11px; margin-bottom: 10px;")
        main_layout.addWidget(desc_label)
        
        # Main content with tabs
        self.create_main_content(main_layout)
    
    def create_quick_actions(self, layout):
        """Create quick action buttons - now empty, moved to paths group."""
        pass
    
    def create_main_content(self, main_layout):
        """Create main content with tabbed interface."""
        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Paths Tab
        self.create_paths_tab()
        
        # Config Editor Tab
        self.create_config_editor_tab()
        
        # Apply tab styling
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #3d3d3d;
            }
            QTabBar::tab {
                padding: 8px 12px;
                margin-right: 1px;
                background-color: #2d2d2d;
                border: 1px solid #3d3d3d;
            }
            QTabBar::tab:selected {
                background-color: #3d3d3d;
            }
        """)
    
    
    def create_paths_tab(self):
        """Create paths and configuration management tab."""
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_widget.setLayout(main_layout)
        
        # Configuration Management
        paths_group = QGroupBox("⚙️ Configuration Management")
        paths_layout = QGridLayout()
        paths_layout.setSpacing(8)
        paths_layout.setContentsMargins(10, 10, 10, 10)
        paths_group.setLayout(paths_layout)
        
        # Backup location
        paths_layout.addWidget(QLabel("Backup:"), 0, 0)
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setReadOnly(True)
        self.backup_path_edit.setStyleSheet("background-color: #2d2d2d; font-size: 10px;")
        paths_layout.addWidget(self.backup_path_edit, 0, 1)
        
        # Open button only (auto follows Windows user)
        open_backup_btn = QPushButton("🔗 Open")
        open_backup_btn.clicked.connect(self.open_backup_folder)
        open_backup_btn.setMaximumHeight(30)
        open_backup_btn.setToolTip("Open backup folder (auto follows selected user)")
        paths_layout.addWidget(open_backup_btn, 0, 2)
        
        # Config location
        paths_layout.addWidget(QLabel("Config:"), 1, 0)
        self.config_path_edit = QLineEdit()
        self.config_path_edit.setReadOnly(True)
        self.config_path_edit.setStyleSheet("background-color: #2d2d2d; font-size: 10px;")
        paths_layout.addWidget(self.config_path_edit, 1, 1)
        
        open_config_btn = QPushButton("🔗 Open")
        open_config_btn.clicked.connect(self.open_config_folder)
        open_config_btn.setMaximumHeight(30)
        open_config_btn.setToolTip("Open config folder")
        paths_layout.addWidget(open_config_btn, 1, 2)
        
        # Separator line
        separator = QLabel()
        separator.setStyleSheet("background-color: #404040; max-height: 1px;")
        separator.setMaximumHeight(1)
        paths_layout.addWidget(separator, 2, 0, 1, 3)
        
        # Config Management Buttons
        config_label = QLabel("<b>Config Actions:</b>")
        config_label.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 5px;")
        paths_layout.addWidget(config_label, 3, 0, 1, 3)
        
        # Export button
        self.export_btn = QPushButton("📤 Export Config")
        self.export_btn.setToolTip("Export current configuration to file")
        self.export_btn.clicked.connect(self.export_config)
        paths_layout.addWidget(self.export_btn, 4, 0)
        
        # Import button
        self.import_btn = QPushButton("📥 Import Config")
        self.import_btn.setToolTip("Import configuration from file")
        self.import_btn.clicked.connect(self.import_config)
        paths_layout.addWidget(self.import_btn, 4, 1)
        
        # Reset button
        self.reset_btn = QPushButton("🔄 Reset Defaults")
        self.reset_btn.setToolTip("Reset all settings to default values")
        self.reset_btn.clicked.connect(self.reset_to_defaults)
        StyleHelper.apply_button_style(self.reset_btn, 'warning')
        paths_layout.addWidget(self.reset_btn, 4, 2)
        
        main_layout.addWidget(paths_group)
        
        # Tips Section
        tips_group = QGroupBox("💡 Tips")
        tips_layout = QVBoxLayout()
        tips_layout.setSpacing(3)
        tips_layout.setContentsMargins(8, 8, 8, 8)
        tips_group.setLayout(tips_layout)
        
        tips = [
            "<b>Backup Location:</b> Where session backups are stored",
            "<b>Config Location:</b> Where application configuration files are stored",
            "<b>Export/Import:</b> Save or load your configuration settings",
            "<b>Reset Defaults:</b> Restore all settings to factory defaults"
        ]
        
        for tip in tips:
            tip_label = QLabel(f"• <i>{tip}</i>")
            tip_label.setWordWrap(True)
            tip_label.setStyleSheet("""
                QLabel {
                    color: #888888;
                    font-size: 10px;
                    padding: 2px 0px;
                }
            """)
            tips_layout.addWidget(tip_label)
        
        tips_group.setStyleSheet("""
            QGroupBox {
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #404040;
                border-radius: 5px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """)
        
        main_layout.addWidget(tips_group)
        
        self.tabs.addTab(main_widget, "📁 Paths")
    
    def create_config_editor_tab(self):
        """Create configuration file editor tab."""
        editor_widget = QWidget()
        layout = QVBoxLayout()
        layout.setSpacing(10)
        editor_widget.setLayout(layout)
        
        # Editor toolbar
        toolbar_layout = QHBoxLayout()
        
        # Config file selector
        toolbar_layout.addWidget(QLabel("Config file:"))
        self.config_file_combo = QComboBox()
        self.config_file_combo.addItems([
            "config.json - Main configuration",
            "backup.json - Backup settings", 
            "reset.json - Reset configuration"
        ])
        self.config_file_combo.currentTextChanged.connect(self.load_selected_config)
        toolbar_layout.addWidget(self.config_file_combo)
        
        toolbar_layout.addStretch()
        
        # Editor buttons
        self.reload_btn = QPushButton("🔄 Reload")
        self.reload_btn.clicked.connect(self.reload_config_editor)
        self.reload_btn.setMaximumWidth(80)
        toolbar_layout.addWidget(self.reload_btn)
        
        self.save_config_btn = QPushButton("💾 Save")
        self.save_config_btn.clicked.connect(self.save_config_editor)
        self.save_config_btn.setMaximumWidth(80)
        self.save_config_btn.setStyleSheet("""
            QPushButton {
                background-color: #0d7377;
                color: white;
                border: 1px solid #0a5a5d;
            }
            QPushButton:hover {
                background-color: #0f8a8f;
            }
        """)
        toolbar_layout.addWidget(self.save_config_btn)
        
        layout.addLayout(toolbar_layout)
        
        # JSON Editor
        self.config_editor = QTextEdit()
        self.config_editor.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #3e3e3e;
                font-family: 'Consolas', 'Monaco', monospace;
                font-size: 11px;
                line-height: 1.4;
            }
        """)
        
        # Add syntax highlighter
        self.highlighter = JsonSyntaxHighlighter(self.config_editor.document())
        
        layout.addWidget(self.config_editor)
        
        # Status info
        status_layout = QHBoxLayout()
        self.editor_status_label = QLabel("Ready to edit configuration files")
        self.editor_status_label.setStyleSheet("color: #aaa; font-size: 10px;")
        status_layout.addWidget(self.editor_status_label)
        
        status_layout.addStretch()
        
        # Character count
        self.char_count_label = QLabel("0 chars")
        self.char_count_label.setStyleSheet("color: #aaa; font-size: 10px;")
        status_layout.addWidget(self.char_count_label)
        
        layout.addLayout(status_layout)
        
        # Connect text changed signal for character count
        self.config_editor.textChanged.connect(self.update_char_count)
        
        self.tabs.addTab(editor_widget, "📝 Config Editor")
    
    def load_current_config(self):
        """Load current configuration values into UI.
        
        Updates paths based on current selected user.
        """
        # Determine user profile path
        if self.current_user:
            # Multi-user mode - use selected user's path
            system_drive = os.getenv('SystemDrive', 'C:')
            if not system_drive.endswith('\\'):
                system_drive += '\\'
            user_home = os.path.join(system_drive, 'Users', self.current_user)
        else:
            # Default to current logged-in user
            user_home = os.path.expanduser("~")
        
        # Backup path - always construct from selected user
        backup_path = os.path.join(user_home, "Documents", "SurfManager", "Backups")
        self.backup_path_edit.setText(backup_path)
        
        # Config path - show user's .surfmanager folder
        config_path = os.path.join(user_home, ".surfmanager")
        self.config_path_edit.setText(config_path)
        
        # Load first config file
        self.load_selected_config()
    
    def load_selected_config(self):
        """Load the selected configuration file into editor."""
        selection = self.config_file_combo.currentText()
        config_file = selection.split(' - ')[0]
        
        try:
            config_path = get_resource_path(f'app/config/{config_file}')
            
            with open(config_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Pretty format JSON
            try:
                parsed = json.loads(content)
                formatted = json.dumps(parsed, indent=2, ensure_ascii=False)
                self.config_editor.setPlainText(formatted)
            except json.JSONDecodeError:
                self.config_editor.setPlainText(content)  # Show raw content if not valid JSON
            
            self.editor_status_label.setText(f"Loaded: {config_file}")
            
        except Exception as e:
            self.config_editor.setPlainText(f"Error loading {config_file}: {str(e)}")
            self.editor_status_label.setText(f"Error loading {config_file}")
    
    def update_char_count(self):
        """Update character count label."""
        text = self.config_editor.toPlainText()
        char_count = len(text)
        line_count = text.count('\n') + 1 if text else 0
        self.char_count_label.setText(f"{char_count} chars, {line_count} lines")
    
    def open_backup_folder(self):
        """Open backup folder in explorer."""
        path = self.backup_path_edit.text()
        
        # Validate path first
        is_valid, error, normalized = PathValidator.validate_path(path, must_exist=False)
        if not is_valid:
            DialogHelper.show_warning(self, "Invalid Path", f"Backup path is invalid:\n{error}")
            return
        
        if normalized.exists():
            open_folder_in_explorer(str(normalized))
        else:
            # Ask user if they want to create the folder
            if DialogHelper.confirm(
                self, "Create Backup Folder", 
                f"Backup folder does not exist:\n{path}\n\nWould you like to create it?",
                default_no=False
            ):
                try:
                    os.makedirs(path, exist_ok=True)
                    self.log(f"Created backup folder: {path}")
                    open_folder_in_explorer(path)
                except Exception as e:
                    DialogHelper.show_warning(self, "Create Folder Error", f"Failed to create backup folder:\n{str(e)}")
                    self.log(f"Error creating backup folder: {str(e)}")
    
    def open_config_folder(self):
        """Open config folder in explorer."""
        path = self.config_path_edit.text()
        
        # Validate path first
        is_valid, error, normalized = PathValidator.validate_path(path, must_exist=True)
        if not is_valid:
            DialogHelper.show_warning(self, "Invalid Path", f"Config path is invalid:\n{error}")
            return
        
        if normalized.exists():
            open_folder_in_explorer(str(normalized))
        else:
            DialogHelper.show_warning(self, "Path Not Found", f"Config folder does not exist:\n{path}")
    
    def reload_config_editor(self):
        """Reload configuration editor."""
        self.load_selected_config()
        self.log("Configuration editor reloaded")
    
    def save_config_editor(self):
        """Save configuration from editor."""
        try:
            content = self.config_editor.toPlainText()
            
            # Validate JSON
            parsed = json.loads(content)
            
            # Get selected file
            selection = self.config_file_combo.currentText()
            config_file = selection.split(' - ')[0]
            config_path = get_resource_path(f'app/config/{config_file}')
            
            # Save file
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(parsed, f, indent=2, ensure_ascii=False)
            
            self.editor_status_label.setText(f"Saved: {config_file}")
            self.log(f"Configuration file {config_file} saved successfully")
            
            # If it's the main config, reload it
            if config_file == 'config.json':
                self.config_manager._config = None
                self.config_manager = ConfigManager()
                self.load_current_config()
            
            DialogHelper.show_info(self, "Config Saved", f"Configuration file {config_file} has been saved successfully.")
            
        except json.JSONDecodeError as e:
            DialogHelper.show_warning(self, "JSON Error", f"Invalid JSON format:\n{str(e)}")
            self.editor_status_label.setText("Invalid JSON format")
        except Exception as e:
            DialogHelper.show_warning(self, "Save Error", f"Failed to save configuration:\n{str(e)}")
            self.editor_status_label.setText("Save failed")
    
    def export_config(self):
        """Export configuration to file."""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Export Configuration",
            f"surfmanager_config_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if filename:
            try:
                if self.config_manager.export_config(filename):
                    self.log(f"Configuration exported to: {filename}")
                    DialogHelper.show_info(self, "Export Success", f"Configuration exported successfully to:\n{filename}")
                else:
                    DialogHelper.show_warning(self, "Export Failed", "Failed to export configuration.")
            except Exception as e:
                DialogHelper.show_warning(self, "Export Error", f"Error exporting configuration:\n{str(e)}")
    
    def import_config(self):
        """Import configuration from file."""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Import Configuration", "",
            "JSON files (*.json);;All files (*.*)"
        )
        
        if filename:
            if DialogHelper.confirm(
                self, "Import Configuration",
                "This will replace your current configuration. Continue?"
            ):
                try:
                    if self.config_manager.import_config(filename):
                        self.load_current_config()
                        self.log(f"Configuration imported from: {filename}")
                        DialogHelper.show_info(self, "Import Success", "Configuration imported successfully.")
                    else:
                        DialogHelper.show_warning(self, "Import Failed", "Failed to import configuration.")
                except Exception as e:
                    DialogHelper.show_warning(self, "Import Error", f"Error importing configuration:\n{str(e)}")
    
    def reset_to_defaults(self):
        """Reset configuration to defaults."""
        if DialogHelper.confirm(
            self, "Reset to Defaults",
            "This will reset all settings to their default values. Continue?"
        ):
            try:
                self.config_manager.reset_to_defaults()
                self.load_current_config()
                self.log("Configuration reset to defaults")
                DialogHelper.show_info(self, "Reset Complete", "Configuration has been reset to default values.")
            except Exception as e:
                DialogHelper.show_warning(self, "Reset Error", f"Error resetting configuration:\n{str(e)}")
    
    def set_current_user(self, username: str):
        """Update current user and refresh paths.
        
        Args:
            username: Windows username
        """
        self.current_user = username
        self.load_current_config()
        self.log(f"Advanced Settings updated for user: {username}")
