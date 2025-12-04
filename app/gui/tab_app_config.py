"""App Configuration tab for SurfManager - VSCode based apps management."""
import os
import json
import shutil
import platform
import subprocess
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QGroupBox, QFileDialog,
    QHeaderView, QMessageBox, QMenu, QGridLayout, QDialog,
    QLineEdit, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor
import qtawesome as qta


class AddManualConfigDialog(QDialog):
    """Dialog to add application configuration manually."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Application Configuration")
        self.setMinimumWidth(550)
        self.setMinimumHeight(450)
        self.exe_folder = None
        self.data_folder = None
        self.addon_folders = []  # List of additional folders to backup
        self._init_ui()
    
    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)
        self.setLayout(layout)
        
        # Apply dark theme
        self.setStyleSheet("""
            QDialog { background-color: #252526; color: #ccc; }
            QLabel { color: #ccc; }
            QLineEdit { background-color: #3c3c3c; color: #ccc; border: 1px solid #555; padding: 6px; border-radius: 3px; }
            QPushButton { background-color: #404040; color: #e0e0e0; border: 1px solid #555; padding: 6px 12px; border-radius: 3px; }
            QPushButton:hover { background-color: #505050; }
            QGroupBox { border: 1px solid #3d3d3d; border-radius: 4px; margin-top: 8px; padding-top: 8px; color: #ccc; }
            QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }
        """)
        
        form = QFormLayout()
        form.setSpacing(12)
        
        # App name (auto-filled from exe)
        self.app_name = QLineEdit()
        self.app_name.setPlaceholderText("Auto-filled from .exe file name")
        self.app_name.setReadOnly(True)
        self.app_name.setStyleSheet("QLineEdit { background-color: #2a2a2a; color: #888; }")
        form.addRow("App Name (auto-filled):", self.app_name)
        
        # Exe path selector
        exe_layout = QHBoxLayout()
        self.exe_path_label = QLabel("Not selected")
        self.exe_path_label.setStyleSheet("color: #888;")
        exe_layout.addWidget(self.exe_path_label, 1)
        exe_browse = QPushButton("Select .exe...")
        exe_browse.clicked.connect(self._browse_exe)
        exe_layout.addWidget(exe_browse)
        form.addRow("Program Executable*:", exe_layout)
        
        # Data folder selector
        data_layout = QHBoxLayout()
        self.data_path_label = QLabel("Not selected")
        self.data_path_label.setStyleSheet("color: #888;")
        data_layout.addWidget(self.data_path_label, 1)
        data_browse = QPushButton("Browse...")
        data_browse.clicked.connect(self._browse_data)
        data_layout.addWidget(data_browse)
        form.addRow("Program Data Folder*:", data_layout)
        
        # Example hint
        example_label = QLabel("Example: VSCode uses Code.exe -> Data folder: Code")
        example_label.setStyleSheet("color: #888; font-size: 10px; font-style: italic;")
        form.addRow("", example_label)
        
        layout.addLayout(form)
        
        # Auto-generated config info
        backup_group = QGroupBox("Auto-Generated Configuration")
        backup_layout = QVBoxLayout()
        backup_layout.setSpacing(8)
        
        info_label = QLabel("Essential backup items (auto-included):")
        info_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        backup_layout.addWidget(info_label)
        
        items_label = QLabel(
            "  Folders: User, Local Storage, Session Storage, Network\n"
            "  Files: Preferences, Local State, DIPS, machineid, languagepacks.json"
        )
        items_label.setStyleSheet("color: #888; font-size: 10px; margin-left: 10px;")
        backup_layout.addWidget(items_label)
        
        # Registry keys info
        registry_label = QLabel("Windows Registry keys (auto-included for cleanup):")
        registry_label.setStyleSheet("color: #4CAF50; font-size: 11px; margin-top: 8px;")
        backup_layout.addWidget(registry_label)
        
        registry_items = QLabel(
            "  • HKEY_CURRENT_USER\\Software\\[AppName]\n"
            "  • HKEY_CURRENT_USER\\Software\\Classes\\[AppName]\n"
            "  • Uninstall entries (HKCU & HKLM)"
        )
        registry_items.setStyleSheet("color: #888; font-size: 10px; margin-left: 10px;")
        backup_layout.addWidget(registry_items)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Optional: Addon Backup Folders
        addon_group = QGroupBox("Optional: Additional Backup Folders")
        addon_layout = QVBoxLayout()
        addon_layout.setSpacing(8)
        
        addon_info = QLabel("📁 Add extra folders to backup (e.g., ~/.aws, ~/.ssh, config folders)")
        addon_info.setStyleSheet("color: #FFC107; font-size: 11px;")
        addon_layout.addWidget(addon_info)
        
        # Addon folders list
        self.addon_list_widget = QVBoxLayout()
        self.addon_list_widget.setSpacing(4)
        addon_layout.addLayout(self.addon_list_widget)
        
        # Add folder button
        add_addon_btn = QPushButton("+ Add Folder")
        add_addon_btn.setIcon(qta.icon('fa5s.folder-plus', color='#4CAF50'))
        add_addon_btn.setStyleSheet("QPushButton { background-color: #2d4a2e; color: #90EE90; border: 1px solid #3d6030; } QPushButton:hover { background-color: #3d6030; }")
        add_addon_btn.clicked.connect(self._add_addon_folder)
        addon_layout.addWidget(add_addon_btn)
        
        addon_group.setLayout(addon_layout)
        layout.addWidget(addon_group)
        
        layout.addStretch()
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)
    
    def _browse_exe(self):
        """Browse for executable file and auto-fill app name."""
        start_dir = os.path.join(os.path.expanduser("~"), "AppData", "Local", "Programs")
        
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Select Program Executable",
            start_dir,
            "Executable Files (*.exe);;All Files (*.*)"
        )
        
        if file_path:
            self.exe_folder = os.path.dirname(file_path)
            exe_filename = os.path.basename(file_path)
            
            # Extract app name from exe filename
            app_name = os.path.splitext(exe_filename)[0]
            
            self.app_name.setText(app_name)
            self.app_name.setStyleSheet("QLineEdit { background-color: #2a2a2a; color: #FFFF00; font-weight: bold; }")
            
            self.exe_path_label.setText(exe_filename)
            self.exe_path_label.setStyleSheet("color: #4CAF50;")
    
    def _browse_data(self):
        """Browse for data folder."""
        start_dir = os.path.join(os.path.expanduser("~"), "AppData", "Roaming")
        folder_path = QFileDialog.getExistingDirectory(self, "Select Data Folder", start_dir)
        if folder_path:
            self.data_folder = folder_path
            self.data_path_label.setText(folder_path)
            self.data_path_label.setStyleSheet("color: #4CAF50;")
    
    def _add_addon_folder(self):
        """Add an addon folder to backup list."""
        # Start from user home directory
        start_dir = os.path.expanduser("~")
        folder_path = QFileDialog.getExistingDirectory(self, "Select Additional Folder to Backup", start_dir)
        
        if folder_path and folder_path not in self.addon_folders:
            self.addon_folders.append(folder_path)
            self._refresh_addon_list()
    
    def _remove_addon_folder(self, folder_path):
        """Remove addon folder from list."""
        if folder_path in self.addon_folders:
            self.addon_folders.remove(folder_path)
            self._refresh_addon_list()
    
    def _refresh_addon_list(self):
        """Refresh the addon folders display list."""
        # Clear existing widgets
        while self.addon_list_widget.count():
            item = self.addon_list_widget.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add current addon folders
        for folder in self.addon_folders:
            row_widget = QWidget()
            row_layout = QHBoxLayout()
            row_layout.setContentsMargins(0, 0, 0, 0)
            row_layout.setSpacing(4)
            
            # Folder path label
            folder_label = QLabel(folder)
            folder_label.setStyleSheet("color: #4FC3F7; font-size: 10px; background-color: #2a2a2a; padding: 4px; border-radius: 3px;")
            row_layout.addWidget(folder_label, 1)
            
            # Remove button
            remove_btn = QPushButton("✕")
            remove_btn.setFixedSize(20, 20)
            remove_btn.setStyleSheet("QPushButton { background-color: #4a2020; color: #FF6B6B; border: none; border-radius: 3px; font-size: 10px; } QPushButton:hover { background-color: #6a3030; }")
            remove_btn.clicked.connect(lambda checked, f=folder: self._remove_addon_folder(f))
            row_layout.addWidget(remove_btn)
            
            row_widget.setLayout(row_layout)
            self.addon_list_widget.addWidget(row_widget)
    
    def _validate_and_accept(self):
        if not self.app_name.text().strip():
            QMessageBox.warning(self, "Validation Error", "Please select an executable file (.exe) first")
            return
        if not self.exe_folder:
            QMessageBox.warning(self, "Validation Error", "Program Executable is required")
            return
        if not self.data_folder:
            QMessageBox.warning(self, "Validation Error", "Program Data folder is required")
            return
        self.accept()
    
    def get_config_data(self):
        """Generate VSCode-based app configuration."""
        app_name = self.app_name.text().strip()
        display_name = app_name.capitalize()
        process_name = f"{display_name}.exe"
        exe_path = os.path.join(self.exe_folder, process_name)
        
        config = {
            "app_name": app_name,
            "display_name": display_name,
            "version": "1.0",
            "active": True,
            "description": f"{display_name} - AI Code Editor",
            "metadata": {
                "color": "#4CAF50",
                "icon": f"{display_name}.ico",
                "process_name": process_name
            },
            "paths": {
                "data_paths": [self.data_folder],
                "exe_paths": [exe_path],
                "reset_folder": self.data_folder
            },
            "backup_items": [
                # Essential folders
                {"type": "folder", "path": "User", "description": "User settings and data"},
                {"type": "folder", "path": "Local Storage", "description": "Local storage data"},
                {"type": "folder", "path": "Session Storage", "description": "Session storage"},
                {"type": "folder", "path": "Network", "description": "Network data"},
                # Essential files
                {"type": "file", "path": "Preferences", "description": "App preferences"},
                {"type": "file", "path": "Local State", "description": "Local app state"},
                {"type": "file", "path": "DIPS", "description": "Authentication data"},
                {"type": "file", "path": "machineid", "description": "Machine ID", "optional": True},
                {"type": "file", "path": "languagepacks.json", "description": "Language packs", "optional": True},
            ],
            "cache_dirs": [
                "Cache", "CachedData", "CachedExtensions", "CachedExtensionVSIXs",
                "Code Cache", "GPUCache", "Service Worker",
                "User/workspaceStorage", "User/History", "logs", "blob_storage", "IndexedDB"
            ],
            "registry_keys": [
                {"root": "HKEY_CURRENT_USER", "path": f"Software\\{display_name}", "description": "Main app settings"},
                {"root": "HKEY_CURRENT_USER", "path": f"Software\\Classes\\{display_name}", "description": "File associations"},
                {"root": "HKEY_CURRENT_USER", "path": f"Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\{display_name}", "description": "Uninstall entry"}
            ],
            "addon_backup_paths": self.addon_folders if self.addon_folders else []
        }
        
        return config


class AppConfigTab(QWidget):
    """App Configuration tab for managing application configurations."""
    
    # Signal emitted when apps configuration changes
    apps_changed = pyqtSignal()
    
    def __init__(self, log_callback):
        super().__init__()
        self.log_callback = log_callback
        self.config_dir = Path.home() / ".surfmanager" / "AppConfigs"
        self._ensure_config_dir()
        self._init_ui()
        self.refresh_apps_list()
    
    def _ensure_config_dir(self):
        """Ensure AppConfigs directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def log(self, msg: str):
        """Log message to main window."""
        if self.log_callback:
            self.log_callback(msg)
    
    def _init_ui(self):
        """Initialize UI."""
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)
        
        # Application Configurations section
        self._create_app_configs_section(layout)
    
    def _create_app_configs_section(self, layout):
        """Create Application Configurations section."""
        configs_group = QGroupBox("Application Configurations")
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(6)
        main_h_layout.setContentsMargins(6, 6, 6, 6)
        configs_group.setLayout(main_h_layout)
        
        # Left side: Table
        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(4)
        left_widget.setLayout(left_layout)
        
        # Info label
        info_label = QLabel("Configured Applications")
        info_label.setStyleSheet("color: #aaa; font-size: 11px;")
        left_layout.addWidget(info_label)
        
        # Apps table
        self.apps_table = QTableWidget()
        self.apps_table.setColumnCount(4)
        self.apps_table.setHorizontalHeaderLabels(["NO", "Name", "Status", "Actions"])
        self.apps_table.verticalHeader().setVisible(False)
        self.apps_table.setAlternatingRowColors(True)
        self.apps_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.apps_table.setMinimumHeight(200)
        
        # Dark table styling (match Sessions table)
        self.apps_table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                color: #e0e0e0;
            }
            QTableWidget::item {
                padding: 4px;
                border-bottom: 1px solid #2d2d2d;
            }
            QTableWidget::item:selected {
                background-color: #0d7377;
                color: #fff;
            }
            QHeaderView::section {
                background-color: #2d2d30;
                color: #ccc;
                font-weight: bold;
                padding: 6px;
                border: none;
                border-bottom: 2px solid #3d3d3d;
                border-right: 1px solid #3d3d3d;
            }
        """)
        
        # Column widths
        header = self.apps_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        
        self.apps_table.setColumnWidth(0, 35)
        self.apps_table.setColumnWidth(3, 220)  # Actions column - normal buttons
        
        # Context menu
        self.apps_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.apps_table.customContextMenuRequested.connect(self._show_context_menu)
        
        left_layout.addWidget(self.apps_table)
        main_h_layout.addWidget(left_widget)
        
        # Right side: Actions panel
        self._create_actions_panel(main_h_layout)
        
        layout.addWidget(configs_group)
    
    def _create_actions_panel(self, main_layout):
        """Create actions panel."""
        actions_widget = QWidget()
        actions_widget.setMaximumWidth(200)
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(4)
        actions_layout.setContentsMargins(6, 6, 6, 6)
        actions_widget.setLayout(actions_layout)
        
        # Quick Actions label
        actions_label = QLabel("Quick Actions")
        actions_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 12px;")
        actions_layout.addWidget(actions_label)
        
        # Actions grid (2 columns)
        actions_grid = QGridLayout()
        actions_grid.setSpacing(4)
        
        # Row 1: Import Config | Add Manual
        import_btn = QPushButton(" Import")
        import_btn.setIcon(qta.icon('fa5s.file-import', color='#4fc3f7'))
        import_btn.setMinimumHeight(30)
        import_btn.clicked.connect(self._import_configs)
        actions_grid.addWidget(import_btn, 0, 0)
        
        add_manual_btn = QPushButton(" Add")
        add_manual_btn.setIcon(qta.icon('fa5s.plus', color='#81c784'))
        add_manual_btn.setMinimumHeight(30)
        add_manual_btn.clicked.connect(self._add_manual_config)
        actions_grid.addWidget(add_manual_btn, 0, 1)
        
        # Row 2: Export All | Open Folder
        export_btn = QPushButton(" Export")
        export_btn.setIcon(qta.icon('fa5s.file-export', color='#ce93d8'))
        export_btn.setMinimumHeight(30)
        export_btn.clicked.connect(self._export_configs)
        actions_grid.addWidget(export_btn, 1, 0)
        
        folder_btn = QPushButton(" Folder")
        folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#ffb74d'))
        folder_btn.setMinimumHeight(30)
        folder_btn.clicked.connect(self._open_config_folder)
        actions_grid.addWidget(folder_btn, 1, 1)
        
        # Row 3: Delete All (spanning both columns)
        delete_all_btn = QPushButton(" Delete All")
        delete_all_btn.setIcon(qta.icon('fa5s.trash', color='#fff'))
        delete_all_btn.setMinimumHeight(30)
        delete_all_btn.clicked.connect(self._delete_all_configs)
        delete_all_btn.setStyleSheet("""
            QPushButton { background-color: #c72e0f; border: 1px solid #e03e1c; }
            QPushButton:hover { background-color: #e03e1c; }
        """)
        actions_grid.addWidget(delete_all_btn, 2, 0, 1, 2)
        
        actions_layout.addLayout(actions_grid)
        actions_layout.addSpacing(20)
        
        # Instructions
        instructions = QLabel(
            "Instructions\n\n"
            "• Import: Add from JSON\n"
            "• Add: Quick VSCode setup\n"
            "• Export: Backup all configs\n"
            "• Folder: Browse config dir\n\n"
            "Right-click row for options\n\n"
            "Toggle Active/Inactive to\n"
            "   enable/disable apps"
        )
        instructions.setStyleSheet(
            "color: #888; font-size: 10px; "
            "background: rgba(255,255,255,0.05); "
            "padding: 10px; border-radius: 4px; "
            "line-height: 1.5;"
        )
        instructions.setWordWrap(True)
        instructions.setMaximumWidth(200)
        actions_layout.addWidget(instructions)
        
        actions_layout.addStretch()
        main_layout.addWidget(actions_widget)
    
    def refresh_apps_list(self):
        """Refresh the list of configured applications."""
        if not hasattr(self, 'apps_table'):
            return
        
        self.apps_table.setRowCount(0)
        
        if not self.config_dir.exists():
            self.log("Config directory not found")
            return
        
        configs = list(self.config_dir.glob("*.json"))
        
        if not configs:
            self.log("No application configurations found")
            return
        
        for idx, config_path in enumerate(sorted(configs)):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                app_name = config.get('app_name', config_path.stem)
                is_installed = self._check_app_installed(config)
                is_active = config.get('active', True)
                
                # Status text
                if is_installed and not is_active:
                    status = "Installed (Inactive)"
                    status_color = "#FFA500"
                elif is_installed:
                    status = "Installed"
                    status_color = "#4CAF50"
                else:
                    status = "Not Found"
                    status_color = "#888"
                
                # Add row
                row = self.apps_table.rowCount()
                self.apps_table.insertRow(row)
                
                # Column 0: Number
                number_item = QTableWidgetItem(str(row + 1))
                number_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.apps_table.setItem(row, 0, number_item)
                
                # Column 1: App name
                name_item = QTableWidgetItem(app_name)
                name_item.setData(Qt.ItemDataRole.UserRole, str(config_path))
                self.apps_table.setItem(row, 1, name_item)
                
                # Column 2: Status
                status_item = QTableWidgetItem(status)
                status_item.setForeground(QBrush(QColor(status_color)))
                self.apps_table.setItem(row, 2, status_item)
                
                # Column 3: Action buttons (normal size)
                actions_widget = QWidget()
                actions_layout = QHBoxLayout()
                actions_layout.setSpacing(4)
                actions_layout.setContentsMargins(4, 2, 4, 2)
                
                btn_style = "QPushButton { padding: 4px 8px; font-size: 11px; border-radius: 3px; }"
                
                edit_btn = QPushButton("Edit")
                edit_btn.setFixedHeight(26)
                edit_btn.setStyleSheet(btn_style + "QPushButton { background-color: #3d3d3d; } QPushButton:hover { background-color: #4d4d4d; }")
                edit_btn.clicked.connect(lambda checked, path=config_path: self._edit_app_config(path))
                actions_layout.addWidget(edit_btn)
                
                remove_btn = QPushButton("Delete")
                remove_btn.setFixedHeight(26)
                remove_btn.setStyleSheet(btn_style + "QPushButton { background-color: #c72e0f; color: white; } QPushButton:hover { background-color: #e03e1c; }")
                remove_btn.clicked.connect(lambda checked, path=config_path: self._delete_app_config(path))
                actions_layout.addWidget(remove_btn)
                
                # Toggle Active/Inactive
                toggle_text = "Active" if is_active else "Inactive"
                toggle_btn = QPushButton(toggle_text)
                toggle_btn.setFixedHeight(26)
                toggle_btn.clicked.connect(lambda checked, path=config_path: self._toggle_app_active(path))
                if is_active:
                    toggle_btn.setStyleSheet(btn_style + "QPushButton { background-color: #4CAF50; color: white; font-weight: bold; } QPushButton:hover { background-color: #45a049; }")
                else:
                    toggle_btn.setStyleSheet(btn_style + "QPushButton { background-color: #555; color: #999; } QPushButton:hover { background-color: #666; }")
                actions_layout.addWidget(toggle_btn)
                
                actions_widget.setLayout(actions_layout)
                self.apps_table.setCellWidget(row, 3, actions_widget)
                
                # Set row height for normal buttons
                self.apps_table.setRowHeight(row, 34)
                
            except Exception as e:
                self.log(f"ERROR: Failed to load {config_path.name}: {e}")
    
    def _check_app_installed(self, config):
        """Check if application is installed by checking exe paths."""
        exe_paths = config.get('paths', {}).get('exe_paths', [])
        for exe_path in exe_paths:
            if os.path.exists(exe_path):
                return True
        return False
    
    def _import_configs(self):
        """Import application configurations from JSON files."""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Import Application Configurations",
            "",
            "JSON Files (*.json);;All Files (*)"
        )
        
        if not file_paths:
            return
        
        imported_count = 0
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # Validate
                if not all(key in config for key in ['app_name', 'display_name']):
                    self.log(f"ERROR: Invalid config structure in {Path(file_path).name}")
                    continue
                
                app_name = config['app_name']
                dest_path = self.config_dir / f"{app_name}.json"
                
                if dest_path.exists():
                    reply = QMessageBox.warning(
                        self, "Config Exists",
                        f"Configuration for '{app_name}' already exists.\n\nOverwrite?",
                        QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                    )
                    if reply != QMessageBox.StandardButton.Yes:
                        continue
                
                with open(dest_path, 'w', encoding='utf-8') as f:
                    json.dump(config, f, indent=2)
                
                imported_count += 1
                self.log(f"Imported: {app_name}")
                
            except Exception as e:
                self.log(f"ERROR: Failed to import {Path(file_path).name}: {e}")
        
        if imported_count > 0:
            self.log(f"Successfully imported {imported_count} configuration(s)")
            self.refresh_apps_list()
            self.apps_changed.emit()
        else:
            QMessageBox.warning(self, "Import Failed", "No configurations were imported.")
    
    def _add_manual_config(self):
        """Add manual application configuration."""
        dialog = AddManualConfigDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            try:
                config_data = dialog.get_config_data()
                app_name = config_data['app_name']
                
                config_path = self.config_dir / f"{app_name}.json"
                self.config_dir.mkdir(parents=True, exist_ok=True)
                
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(config_data, f, indent=2, ensure_ascii=False)
                
                self.log(f"Manual config '{app_name}' added successfully")
                self.refresh_apps_list()
                self.apps_changed.emit()
                
            except Exception as e:
                self.log(f"ERROR: Failed to save config: {e}")
                QMessageBox.critical(self, "Error", f"Failed to save configuration:\n{e}")
    
    def _export_configs(self):
        """Export all configurations to a folder."""
        folder_path = QFileDialog.getExistingDirectory(self, "Select Export Folder", "")
        
        if not folder_path:
            return
        
        configs = list(self.config_dir.glob("*.json"))
        if not configs:
            QMessageBox.warning(self, "No Configurations", "No configurations to export.")
            return
        
        export_folder = Path(folder_path) / "SurfManager_Configs"
        export_folder.mkdir(exist_ok=True)
        
        exported_count = 0
        for config_path in configs:
            try:
                dest_path = export_folder / config_path.name
                shutil.copy2(config_path, dest_path)
                exported_count += 1
            except Exception as e:
                self.log(f"ERROR: Failed to export {config_path.name}: {e}")
        
        if exported_count > 0:
            self.log(f"Exported {exported_count} configurations to {export_folder}")
            QMessageBox.information(self, "Export Complete", f"Exported {exported_count} configurations to:\n{export_folder}")
    
    def _open_config_folder(self):
        """Open the configuration folder in file explorer."""
        try:
            if platform.system() == "Windows":
                os.startfile(str(self.config_dir))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(self.config_dir)])
            else:
                subprocess.run(["xdg-open", str(self.config_dir)])
            self.log(f"Opened config folder: {self.config_dir}")
        except Exception as e:
            self.log(f"ERROR: Failed to open config folder: {e}")
    
    def _delete_all_configs(self):
        """Delete all configurations after confirmation."""
        configs = list(self.config_dir.glob("*.json"))
        
        if not configs:
            QMessageBox.information(self, "Already Clean", "No configurations to remove.")
            return
        
        reply = QMessageBox.warning(
            self, "Reset to Factory",
            f"This will DELETE ALL {len(configs)} application configurations.\n\nThis action cannot be undone!\n\nContinue?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        deleted_count = 0
        for config_path in configs:
            try:
                config_path.unlink()
                deleted_count += 1
                self.log(f"Deleted: {config_path.name}")
            except Exception as e:
                self.log(f"ERROR: Failed to delete {config_path.name}: {e}")
        
        self.log(f"Factory reset complete - deleted {deleted_count} configurations")
        self.refresh_apps_list()
        self.apps_changed.emit()
        
        QMessageBox.information(self, "Reset Complete", f"Deleted {deleted_count} configurations.")
    
    def _show_context_menu(self, position):
        """Show right-click context menu."""
        item = self.apps_table.itemAt(position)
        if not item:
            return
        
        row = item.row()
        config_path_item = self.apps_table.item(row, 1)
        if not config_path_item:
            return
        
        config_path = Path(config_path_item.data(Qt.ItemDataRole.UserRole))
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #404040; border-radius: 6px; padding: 4px; }
            QMenu::item { padding: 8px 20px; border-radius: 3px; }
            QMenu::item:selected { background-color: #0d7377; }
            QMenu::separator { height: 1px; background: #404040; margin: 4px 8px; }
        """)
        
        edit_action = menu.addAction(qta.icon('fa5s.edit', color='#4fc3f7'), "Edit Configuration")
        edit_action.triggered.connect(lambda: self._edit_app_config(config_path))
        
        remove_action = menu.addAction(qta.icon('fa5s.trash', color='#ef5350'), "Delete Configuration")
        remove_action.triggered.connect(lambda: self._delete_app_config(config_path))
        
        menu.addSeparator()
        
        copy_path_action = menu.addAction(qta.icon('fa5s.copy', color='#888'), "Copy Path")
        copy_path_action.triggered.connect(lambda: self._copy_to_clipboard(str(config_path)))
        
        open_folder_action = menu.addAction(qta.icon('fa5s.folder', color='#ffb74d'), "Open Folder")
        open_folder_action.triggered.connect(lambda: self._open_file_location(config_path))
        
        menu.exec(self.apps_table.mapToGlobal(position))
    
    def _copy_to_clipboard(self, text):
        """Copy text to clipboard."""
        try:
            from PyQt6.QtWidgets import QApplication
            clipboard = QApplication.clipboard()
            clipboard.setText(text)
            self.log(f"Copied to clipboard: {text}")
        except Exception as e:
            self.log(f"ERROR: Failed to copy to clipboard: {e}")
    
    def _open_file_location(self, file_path):
        """Open the folder containing the file."""
        try:
            folder = file_path.parent if isinstance(file_path, Path) else Path(file_path).parent
            if platform.system() == "Windows":
                os.startfile(str(folder))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(folder)])
            else:
                subprocess.run(["xdg-open", str(folder)])
            self.log(f"Opened location: {folder}")
        except Exception as e:
            self.log(f"ERROR: Failed to open file location: {e}")
    
    def _edit_app_config(self, config_path):
        """Edit application configuration (opens in default editor)."""
        try:
            if platform.system() == "Windows":
                os.startfile(str(config_path))
            elif platform.system() == "Darwin":
                subprocess.run(["open", str(config_path)])
            else:
                subprocess.run(["xdg-open", str(config_path)])
            
            self.log(f"Opened config in editor: {config_path.name}")
        except Exception as e:
            self.log(f"ERROR: Failed to open config: {e}")
            QMessageBox.critical(self, "Open Failed", f"Failed to open configuration file:\n{e}")
    
    def _delete_app_config(self, config_path):
        """Delete application configuration."""
        app_name = config_path.stem
        
        reply = QMessageBox.warning(
            self, "Delete Configuration",
            f"Delete configuration for '{app_name}'?\n\nThis will remove the app from the list.\n\nThis action cannot be undone.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        try:
            config_path.unlink()
            self.log(f"Deleted configuration: {app_name}")
            QMessageBox.information(self, "Deleted", f"Configuration for '{app_name}' has been removed")
            self.refresh_apps_list()
            self.apps_changed.emit()
        except Exception as e:
            QMessageBox.critical(self, "Delete Failed", f"Failed to delete configuration:\n{e}")
    
    def _toggle_app_active(self, config_path):
        """Toggle active/inactive status for an app."""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            current_status = config.get('active', True)
            config['active'] = not current_status
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=4)
            
            app_name = config.get('app_name', Path(config_path).stem)
            new_status = "active" if config['active'] else "inactive"
            self.log(f"{app_name} is now {new_status}")
            
            self.refresh_apps_list()
            self.apps_changed.emit()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to toggle status:\n{e}")
