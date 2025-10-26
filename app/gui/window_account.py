"""Account Manager tab functionality for SurfManager."""
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QMenu, QLineEdit, QGroupBox, QGridLayout, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont
from app.core.config_manager import ConfigManager
from app.gui.theme_utils import apply_dark_theme
from app.core.path_utils import open_folder_in_explorer, get_resource_path


class AccountTab(QWidget):
    """Account Manager tab widget."""
    
    def __init__(self, app_manager, log_callback):
        super().__init__()
        self.app_manager = app_manager
        self.log_callback = log_callback  # Keep main window log
        self.config_manager = ConfigManager()
        
        self.init_ui()
        self.init_session_manager()
    
    def log(self, message: str):
        """Log to both activity log and main window."""
        # Add to local log output
        if hasattr(self, 'log_output'):
            self.log_output.append(message)
        
        # Also log to main window
        if self.log_callback:
            self.log_callback(message)
    
    def init_ui(self):
        """Initialize the account tab UI with grid layout."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Top toolbar
        self.create_top_toolbar(main_layout)
        
        # Main content: Table + Actions (side by side)
        content_layout = QHBoxLayout()
        
        # Left side - Session Table Group
        table_group = QGroupBox("📅 Sessions")
        table_layout = QVBoxLayout()
        table_group.setLayout(table_layout)
        
        # Top bar: Session count + Search + Refresh
        table_top = QHBoxLayout()
        self.session_count_label = QLabel("")
        self.session_count_label.setStyleSheet("color: #aaa; font-size: 11px;")
        table_top.addWidget(self.session_count_label)
        
        table_top.addStretch()
        
        # Search on right side
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search sessions...")
        self.search_input.setMaximumWidth(200)
        self.search_input.textChanged.connect(self.filter_sessions)
        table_top.addWidget(self.search_input)
        
        # Refresh button after search
        self.refresh_sessions_btn = QPushButton("🔄 Refresh")
        self.refresh_sessions_btn.setMaximumWidth(90)
        self.refresh_sessions_btn.setToolTip("Refresh session list")
        self.refresh_sessions_btn.clicked.connect(self.refresh_session_list)
        table_top.addWidget(self.refresh_sessions_btn)
        
        table_layout.addLayout(table_top)
        
        # Session table
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(5)
        self.session_table.setHorizontalHeaderLabels(["#", "App", "Session Name", "Created", "Status"])
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setSortingEnabled(True)
        self.session_table.setAlternatingRowColors(True)
        self.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        # Column widths
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)  # App
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)  # Session Name
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Created
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)  # Status
        self.session_table.setColumnWidth(0, 35)
        self.session_table.setColumnWidth(1, 80)
        
        # Context menu
        self.session_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_table.customContextMenuRequested.connect(self.show_session_context_menu)
        
        table_layout.addWidget(self.session_table)
        content_layout.addWidget(table_group, 2)  # 66% width
        
        # Right side - Actions
        self.create_actions_panel(content_layout)
        
        main_layout.addLayout(content_layout)
        
        # Bottom - Activity Log
        log_group = QGroupBox("📋 Activity Log")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(5, 5, 5, 5)
        log_layout.setSpacing(0)
        log_group.setLayout(log_layout)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMaximumHeight(120)
        log_layout.addWidget(self.log_output)
        
        main_layout.addWidget(log_group)
    
    def create_top_toolbar(self, layout):
        """Create compact top toolbar - removed, toolbar now empty."""
        pass
    
    def create_actions_panel(self, parent_layout):
        """Create actions panel with grid-style buttons and tips."""
        actions_group = QGroupBox("⚡ Quick Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        actions_group.setLayout(actions_layout)
        
        # Grid for buttons
        button_grid = QGridLayout()
        button_grid.setSpacing(8)
        
        # Row 0 - Backup buttons
        self.backup_cursor_btn = QPushButton("💾 Backup Cursor")
        self.backup_cursor_btn.clicked.connect(lambda: self.create_session_backup("cursor"))
        button_grid.addWidget(self.backup_cursor_btn, 0, 0)
        
        self.backup_windsurf_btn = QPushButton("💾 Backup Windsurf")
        self.backup_windsurf_btn.clicked.connect(lambda: self.create_session_backup("windsurf"))
        button_grid.addWidget(self.backup_windsurf_btn, 0, 1)
        
        # Row 1 - Backup Claude & Open Folder
        self.backup_claude_btn = QPushButton("💾 Backup Claude")
        self.backup_claude_btn.clicked.connect(lambda: self.create_session_backup("claude"))
        button_grid.addWidget(self.backup_claude_btn, 1, 0)
        
        self.open_folder_btn = QPushButton("📁 Open Folder")
        self.open_folder_btn.clicked.connect(self.open_session_backup_folder)
        button_grid.addWidget(self.open_folder_btn, 1, 1)
        
        actions_layout.addLayout(button_grid)
        
        # Tips section (larger font, better spacing)
        tips_label = QLabel(
            "<b style='font-size: 12px;'>💡 Tips:</b><br><br>"
            "• Right-click sessions for more actions<br>"
            "• Active sessions are highlighted in green<br>"
            "• Use search to filter sessions quickly<br>"
            "• Backups stored in Documents/SurfManager"
        )
        tips_label.setStyleSheet("""
            QLabel {
                color: #bbb;
                font-size: 11px;
                padding: 12px;
                background-color: #2a2a2a;
                border-radius: 5px;
                border: 1px solid #3a3a3a;
                line-height: 1.6;
            }
        """)
        tips_label.setWordWrap(True)
        actions_layout.addWidget(tips_label)
        
        parent_layout.addWidget(actions_group, 1)  # 33% width
    
    def init_session_manager(self):
        """Initialize session manager."""
        # Use ConfigManager to get session backup path
        backup_location = self.config_manager.get('backup_location')
        if backup_location:
            self.session_backup_path = os.path.join(os.path.expanduser("~"), backup_location)
        else:
            # Fallback
            self.session_backup_path = os.path.join(os.path.expanduser("~"), "Documents", "SurfManager")
        
        # Session config file
        self.session_config_file = os.path.join(self.session_backup_path, "sessions.json")
        
        # Create session backup directory
        os.makedirs(self.session_backup_path, exist_ok=True)
        
        # Load or create session config
        self.session_data = self.load_session_config()
        
        # Refresh the session list
        self.refresh_session_list()
    
    def load_session_config(self):
        """Load session configuration."""
        if os.path.exists(self.session_config_file):
            try:
                with open(self.session_config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception:
                pass
        return {"cursor": {}, "windsurf": {}}
    
    def save_session_config(self):
        """Save session configuration."""
        try:
            with open(self.session_config_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"❌ Failed to save session config: {e}")
    
    def show_info_dialog(self):
        """Show information dialog about session backup functionality."""
        info_dialog = QMessageBox(self)
        info_dialog.setWindowTitle("Session Backup Information")
        info_dialog.setIcon(QMessageBox.Icon.Information)
        
        info_text = """
<b>📁 Session Backup Manager</b><br><br>

<b>Function:</b> • Create and manage multiple user sessions for Cursor and Windsurf • Switch between different user profiles and settings • Backup and restore application configurations<br><br>

<b>Data Backed Up:</b> • User settings and preferences • Key bindings and shortcuts • Code snippets and templates • Workspace configurations • Extension settings • Network and authentication data<br><br>

<b>Recommendations:</b> • Create backups before major updates • Use descriptive names for easy identification • Regularly backup your current active session • Test restore functionality with non-critical sessions • Keep backups of different development environments<br><br>

<b>Storage Location:</b> Documents/SurfManager
        """
        
        info_dialog.setText(info_text)
        info_dialog.setTextFormat(Qt.TextFormat.RichText)
        apply_dark_theme(info_dialog)
        info_dialog.exec()
    
    def create_session_backup(self, app_name=None):
        """Create a new session backup."""
        if app_name is None:
            app_name = "cursor"  # Default fallback
        app_info = self.app_manager.get_app_info(app_name)
        
        if not app_info or not app_info["installed"]:
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("Not Found")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText(f"{app_name.title()} is not installed or not detected.")
            apply_dark_theme(warning_box)
            warning_box.exec()
            return
        
        # Check if app is running
        if app_info["running"]:
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Application Running")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(f"⚠️ {app_name.title()} is currently running.\n\nPlease close and save your progress before creating a backup.\n\nDo you want to continue?")
            
            # Add custom buttons
            kill_btn = msg_box.addButton("Kill & Continue", QMessageBox.ButtonRole.YesRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(cancel_btn)
            apply_dark_theme(msg_box)
            
            msg_box.exec()
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == cancel_btn:
                return
            elif clicked_button == kill_btn:
                # Kill the application
                self.log(f"⛔ Killing {app_name.title()} processes...")
                success, msg = self.app_manager.kill_app_process(app_name)
                self.log(msg)
                if not success:
                    error_box = QMessageBox(self)
                    error_box.setWindowTitle("Error")
                    error_box.setIcon(QMessageBox.Icon.Critical)
                    error_box.setText(f"Failed to kill {app_name.title()}: {msg}")
                    apply_dark_theme(error_box)
                    error_box.exec()
                    return
        
        # Get backup name from user (user-defined name only)
        default_name = ""
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Create Session Backup")
        input_dialog.setLabelText(f"Enter name for {app_name.title()} session backup:")
        input_dialog.setTextValue(default_name)
        apply_dark_theme(input_dialog)
        
        ok = input_dialog.exec()
        user_name = input_dialog.textValue() if ok else ""
        
        if not ok or not user_name.strip():
            return
        
        user_name = user_name.strip()
        # Create backup name with format: appname-userdefine
        backup_name = f"{app_name}-{user_name}"
        
        # Check if name already exists
        if backup_name in self.session_data.get(app_name, {}):
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("Name Exists")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText(f"Session backup '{backup_name}' already exists!")
            apply_dark_theme(warning_box)
            warning_box.exec()
            return
        
        # Create session backup
        self.log(f"📁 Creating session backup: {backup_name}")
        
        try:
            success = self.backup_session_data(app_name, backup_name, app_info["path"])
            
            if success:
                success_box = QMessageBox(self)
                success_box.setWindowTitle("Success")
                success_box.setIcon(QMessageBox.Icon.Information)
                success_box.setText(f"Session backup '{backup_name}' created successfully!")
                apply_dark_theme(success_box)
                success_box.exec()
                self.refresh_session_list()
            else:
                error_box = QMessageBox(self)
                error_box.setWindowTitle("Error")
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setText(f"Failed to create session backup '{backup_name}'")
                apply_dark_theme(error_box)
                error_box.exec()
        except Exception as e:
            self.log(f"❌ Error during backup creation: {e}")
            error_box = QMessageBox(self)
            error_box.setWindowTitle("Error")
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setText(f"An error occurred while creating backup: {str(e)}")
            apply_dark_theme(error_box)
            error_box.exec()
    
    def _load_backup_items_from_config(self, app_name):
        """Load backup items from reset.json config."""
        try:
            config_path = get_resource_path('app/config/reset.json')
            with open(config_path, 'r', encoding='utf-8') as f:
                reset_config = json.load(f)
            
            app_config = reset_config.get(app_name.lower(), {})
            backup_items = app_config.get('backup_items', [])
            
            if backup_items:
                self.log(f"📋 Loaded {len(backup_items)} backup items from config")
                return backup_items
            else:
                self.log(f"⚠️ No backup items in config, using defaults")
                # Fallback to basic items
                return ["Network", "User", "Local State", "Preferences"]
                
        except Exception as e:
            self.log(f"⚠️ Failed to load backup config: {e}")
            # Fallback to basic items
            return ["Network", "User", "Local State", "Preferences"]
    
    def backup_session_data(self, app_name, backup_name, app_path):
        """Backup session-specific data."""
        def ignore_permission_errors(dir, files):
            """Ignore files that cause permission errors."""
            ignored = []
            for file in files:
                file_path = os.path.join(dir, file)
                # Skip files that commonly cause permission errors
                if any(skip in file.lower() for skip in ['cookies', 'lockfile', '.lock', 'tmp']):
                    ignored.append(file)
                    continue
                # Test if we can access the file
                try:
                    if os.path.isfile(file_path):
                        with open(file_path, 'rb') as f:
                            pass  # Just test read access
                except (PermissionError, OSError):
                    ignored.append(file)
            return ignored
        
        try:
            # Create backup folder
            backup_folder = os.path.join(self.session_backup_path, app_name, backup_name)
            os.makedirs(backup_folder, exist_ok=True)
            
            # Load session files from reset.json config
            session_files = self._load_backup_items_from_config(app_name)
            
            backed_up_files = 0
            found_items = []
            missing_items = []
            
            self.log(f"📦 Scanning {len(session_files)} items...")
            
            for file_path in session_files:
                source = os.path.join(app_path, file_path)
                if os.path.exists(source):
                    try:
                        dest = os.path.join(backup_folder, file_path)
                        os.makedirs(os.path.dirname(dest), exist_ok=True)
                        
                        if os.path.isfile(source):
                            shutil.copy2(source, dest)
                            backed_up_files += 1
                            found_items.append(file_path)
                            self.log(f"✅ Backed up: {file_path}")
                        else:
                            # Count files in directory
                            file_count = sum(len(files) for _, _, files in os.walk(source))
                            shutil.copytree(source, dest, dirs_exist_ok=True, ignore=ignore_permission_errors)
                            backed_up_files += 1
                            found_items.append(file_path)
                            self.log(f"✅ Backed up: {file_path} ({file_count} files)")
                    except (PermissionError, OSError) as e:
                        self.log(f"❌ Failed: {file_path} - {str(e)}")
                        continue
                else:
                    missing_items.append(file_path)
                    self.log(f"⚠️ Not found: {file_path}")
            
            # Summary
            self.log(f"📊 Summary: {len(found_items)} items backed up, {len(missing_items)} not found")
            
            # Ensure app_name key exists in session_data
            if app_name not in self.session_data:
                self.session_data[app_name] = {}
            
            # Update session data
            current_time = datetime.now().isoformat()
            self.session_data[app_name][backup_name] = {
                "created": current_time,
                "last_used": current_time,
                "files_count": backed_up_files,
                "is_current": False
            }
            
            self.save_session_config()
            self.log(f"✅ Session backup created: {backup_name} ({backed_up_files} items)")
            return True
            
        except Exception as e:
            self.log(f"❌ Session backup failed: {e}")
            return False
    
    def restore_session_data(self, app_name, session_name):
        """Restore session data from backup."""
        try:
            app_info = self.app_manager.get_app_info(app_name)
            if not app_info or not app_info["installed"]:
                self.log(f"❌ {app_name.title()} not found or not installed")
                return False
            
            backup_folder = os.path.join(self.session_backup_path, app_name, session_name)
            if not os.path.exists(backup_folder):
                self.log(f"❌ Backup folder not found: {backup_folder}")
                return False
            
            app_path = app_info["path"]
            
            # Get restore files from config
            session_files = self.config_manager.get_restore_files(app_name, 'session_files')
            if not session_files:
                # Fallback to hardcoded list
                session_files = [
                    "User/settings.json",
                    "User/keybindings.json", 
                    "User/snippets",
                    "User/globalStorage/state.vscdb",
                    "User/globalStorage/storage.json",
                    "User/workspaceStorage",
                    "Network",
                    "Local State",
                    "Preferences",
                    "storage.json"
                ]
            
            restored_files = 0
            for file_path in session_files:
                source = os.path.join(backup_folder, file_path)
                if os.path.exists(source):
                    dest = os.path.join(app_path, file_path)
                    
                    # Create destination directory if needed
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    
                    # Remove existing file/folder if it exists
                    if os.path.exists(dest):
                        if os.path.isfile(dest):
                            os.remove(dest)
                        else:
                            shutil.rmtree(dest, ignore_errors=True)
                    
                    # Copy from backup
                    if os.path.isfile(source):
                        shutil.copy2(source, dest)
                    else:
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    restored_files += 1
            
            self.log(f"✅ Session data restored: {session_name} ({restored_files} items)")
            return True
            
        except Exception as e:
            self.log(f"❌ Session restore failed: {e}")
            return False
    
    def refresh_session_list(self):
        """Refresh the session list table."""
        # Collect all sessions from all apps
        all_sessions = []
        app_counts = {'cursor': 0, 'windsurf': 0, 'claude': 0}
        
        for app_name in ['cursor', 'windsurf', 'claude']:
            sessions = self.session_data.get(app_name, {})
            app_counts[app_name] = len(sessions)
            for name, data in sessions.items():
                all_sessions.append((app_name, name, data))
        
        # Sort sessions: Active first, then by app name, then by date created (latest first)
        sorted_sessions = sorted(
            all_sessions,
            key=lambda x: (
                not x[2].get('is_current', False),  # Active sessions first
                x[0],  # Then by app name
                -(datetime.fromisoformat(x[2].get('created', '1900-01-01T00:00:00')).timestamp() if x[2].get('created') else 0)
            )
        )
        
        # Clear the table and disable sorting temporarily
        self.session_table.setSortingEnabled(False)
        self.session_table.clear()
        self.session_table.setHorizontalHeaderLabels(["#", "App", "Session Name", "Created", "Status"])
        self.session_table.setRowCount(len(sorted_sessions))
        
        # Update session count with breakdown
        count_text = f"Total: {len(sorted_sessions)} | Cursor: {app_counts['cursor']} | Windsurf: {app_counts['windsurf']} | Claude: {app_counts['claude']}"
        self.session_count_label.setText(count_text)
        
        for row, (app_name, name, data) in enumerate(sorted_sessions):
            # Row number
            number_item = QTableWidgetItem(str(row + 1))
            if data.get('is_current', False):
                number_item.setBackground(QBrush(QColor("#404040")))
                number_item.setForeground(QBrush(QColor("#e0e0e0")))
                font = QFont()
                font.setBold(True)
                number_item.setFont(font)
            self.session_table.setItem(row, 0, number_item)
            
            # App name
            app_item = QTableWidgetItem(app_name.title())
            font = QFont()
            font.setBold(True)
            app_item.setFont(font)
            self.session_table.setItem(row, 1, app_item)
            
            # Backup name with size
            backup_size = self.get_backup_size(app_name, name)
            is_active = data.get('is_current', False)
            
            if is_active:
                display_name = f"⭐ {name} - {backup_size}"
                name_item = QTableWidgetItem(display_name)
                name_item.setBackground(QBrush(QColor("#2d4a2e")))  # Dark green
                name_item.setForeground(QBrush(QColor("#a8e6a3")))  # Light green
                font = QFont()
                font.setBold(True)
                name_item.setFont(font)
            else:
                display_name = f"{name} - {backup_size}"
                name_item = QTableWidgetItem(display_name)
            self.session_table.setItem(row, 2, name_item)
            
            # Date created
            created = data.get('created', '')
            if created:
                try:
                    dt = datetime.fromisoformat(created)
                    created_str = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    created_str = created
            else:
                created_str = "Unknown"
            date_item = QTableWidgetItem(created_str)
            self.session_table.setItem(row, 3, date_item)
            
            # Status column
            if is_active:
                status_item = QTableWidgetItem("✅ Active")
                status_item.setBackground(QBrush(QColor("#2d4a2e")))
                status_item.setForeground(QBrush(QColor("#a8e6a3")))
                font = QFont()
                font.setBold(True)
                status_item.setFont(font)
            else:
                status_item = QTableWidgetItem("⚪ Deactivated")
                status_item.setForeground(QBrush(QColor("#888")))
            self.session_table.setItem(row, 4, status_item)
        
        # Re-enable sorting after populating
        self.session_table.setSortingEnabled(True)
    
    def get_backup_size(self, app_name, session_name):
        """Get the size of a backup folder."""
        try:
            backup_folder = os.path.join(self.session_backup_path, app_name, session_name)
            if not os.path.exists(backup_folder):
                return "0 KB"
            
            total_size = 0
            for dirpath, dirnames, filenames in os.walk(backup_folder):
                for filename in filenames:
                    filepath = os.path.join(dirpath, filename)
                    if os.path.exists(filepath):
                        total_size += os.path.getsize(filepath)
            
            # Convert to appropriate unit
            if total_size < 1024:
                return f"{total_size} B"
            elif total_size < 1024 * 1024:
                return f"{total_size / 1024:.1f} KB"
            else:
                return f"{total_size / (1024 * 1024):.1f} MB"
        except Exception:
            return "Unknown"
    
    def open_backup_folder(self, app_name, session_name):
        """Open the backup folder in file explorer."""
        backup_folder = os.path.join(self.session_backup_path, app_name, session_name)
        if open_folder_in_explorer(backup_folder):
            self.log(f"📁 Opened backup folder: {session_name}")
        else:
            self.log(f"❌ Failed to open backup folder: {backup_folder}")
    
    def show_session_context_menu(self, position):
        """Show beautiful context menu for session table."""
        if self.session_table.itemAt(position) is None:
            return
        
        row = self.session_table.rowAt(position.y())
        if row < 0:
            return
        
        # Get app name and session name
        app_item = self.session_table.item(row, 1)
        name_item = self.session_table.item(row, 2)
        if not app_item or not name_item:
            return
        
        app_name = app_item.text().lower()
        session_name = name_item.text().replace("⭐ ", "").split(" - ")[0]
        
        # Create beautiful context menu
        menu = QMenu(self)
        menu.setStyleSheet("""
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
        """)
        
        # ===== PRIMARY ACTIONS =====
        restore_action = menu.addAction("🔄  Load Backup")
        restore_action.setToolTip("Restore this session to application")
        
        replace_action = menu.addAction("💾  Update Backup")
        replace_action.setToolTip("Update this backup with current data")
        
        menu.addSeparator()
        
        # ===== STATUS MANAGEMENT =====
        set_current_action = menu.addAction("⭐  Set as Active")
        set_current_action.setToolTip("Mark this session as active")
        
        rename_action = menu.addAction("✏️  Rename Session")
        rename_action.setToolTip("Change session name")
        
        menu.addSeparator()
        
        # ===== UTILITIES =====
        open_folder_action = menu.addAction("📂  Open Folder")
        open_folder_action.setToolTip("Open backup folder in explorer")
        
        menu.addSeparator()
        
        # ===== DANGER ZONE =====
        delete_action = menu.addAction("🗑️  Delete Session")
        delete_action.setToolTip("Permanently delete this backup")
        
        # Execute menu
        action = menu.exec(self.session_table.mapToGlobal(position))
        
        if action == restore_action:
            self.restore_session_backup(app_name, session_name)
        elif action == replace_action:
            self.replace_session_backup(app_name, session_name)
        elif action == open_folder_action:
            self.open_backup_folder(app_name, session_name)
        elif action == rename_action:
            self.rename_session_backup(app_name, session_name)
        elif action == set_current_action:
            self.set_current_session(app_name, session_name)
        elif action == delete_action:
            self.delete_session_backup(app_name, session_name)
    
    def restore_session_backup(self, app_name, session_name):
        """Restore a session backup."""
        app_info = self.app_manager.get_app_info(app_name)
        
        # Try to kill app anyway without checking if running
        if app_info:
            self.log(f"⛔ Closing {app_name.title()} processes...")
            success, message = self.app_manager.kill_app_process(app_name)
            if success or "not running" in message.lower():
                self.log(message)
            else:
                self.log(f"⚠️ Warning: {message}")
        
        # Confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Restore")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(f"Restore session backup '{session_name}'?\n\nThis will overwrite current {app_name.title()} settings.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        apply_dark_theme(msg_box)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.log(f"🔄 Restoring session: {session_name}")
            success = self.restore_session_data(app_name, session_name)
            if success:
                self.log(f"✅ Session restored: {session_name}")
                
                # Auto set as current active session
                self.set_current_session(app_name, session_name)
                self.log(f"⭐ Set as current active session: {session_name}")
                
                # Update last used time
                self.session_data[app_name][session_name]['last_used'] = datetime.now().isoformat()
                self.save_session_config()
                self.refresh_session_list()
            else:
                self.log(f"❌ Failed to restore session: {session_name}")
    
    def replace_session_backup(self, app_name, session_name):
        """Replace session backup with current data."""
        app_info = self.app_manager.get_app_info(app_name)
        
        # Check if app is running
        if app_info and app_info.get("running", False):
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Application Running")
            msg_box.setIcon(QMessageBox.Icon.Warning)
            msg_box.setText(f"⚠️ {app_name.title()} is currently running.\n\nPlease close the application before updating the backup.\n\nDo you want to close it now?")
            
            # Add custom buttons
            kill_btn = msg_box.addButton("Close Application", QMessageBox.ButtonRole.YesRole)
            cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.NoRole)
            msg_box.setDefaultButton(cancel_btn)
            apply_dark_theme(msg_box)
            
            msg_box.exec()
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == cancel_btn:
                return
            elif clicked_button == kill_btn:
                # Kill the application
                self.log(f"⛔ Closing {app_name.title()} processes...")
                success, msg = self.app_manager.kill_app_process(app_name)
                self.log(msg)
                if not success:
                    error_box = QMessageBox(self)
                    error_box.setWindowTitle("Error")
                    error_box.setIcon(QMessageBox.Icon.Critical)
                    error_box.setText(f"Failed to close {app_name.title()}: {msg}")
                    apply_dark_theme(error_box)
                    error_box.exec()
                    return
        
        # Confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Update")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(f"Update backup '{session_name}' with current {app_name.title()} data?\n\nThis will overwrite the existing backup.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        apply_dark_theme(msg_box)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.log(f"💾 Updating session backup: {session_name}")
            if app_info and app_info["installed"]:
                success = self.backup_session_data(app_name, session_name, app_info["path"])
                if success:
                    self.log(f"✅ Session backup updated: {session_name}")
                    self.refresh_session_list()
                else:
                    self.log(f"❌ Failed to update session backup: {session_name}")
            else:
                self.log(f"❌ {app_name.title()} not found or not installed")
    
    def rename_session_backup(self, app_name, session_name):
        """Rename a session backup."""
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Rename Session Backup")
        input_dialog.setLabelText(f"Enter new name for '{session_name}':")
        input_dialog.setTextValue(session_name)
        apply_dark_theme(input_dialog)
        
        ok = input_dialog.exec()
        new_name = input_dialog.textValue() if ok else ""
        
        if ok and new_name.strip() and new_name.strip() != session_name:
            new_name = new_name.strip()
            if new_name in self.session_data[app_name]:
                warning_box = QMessageBox(self)
                warning_box.setWindowTitle("Name Exists")
                warning_box.setIcon(QMessageBox.Icon.Warning)
                warning_box.setText(f"Session backup '{new_name}' already exists!")
                apply_dark_theme(warning_box)
                warning_box.exec()
                return
            
            # Rename in config
            self.session_data[app_name][new_name] = self.session_data[app_name].pop(session_name)
            
            # Rename folder
            old_folder = os.path.join(self.session_backup_path, app_name, session_name)
            new_folder = os.path.join(self.session_backup_path, app_name, new_name)
            if os.path.exists(old_folder):
                os.rename(old_folder, new_folder)
            
            self.save_session_config()
            self.refresh_session_list()
            self.log(f"✏️ Session renamed: {session_name} → {new_name}")
    
    def set_current_session(self, app_name, session_name):
        """Set a session as current active."""
        # Clear current flag from all sessions
        for name in self.session_data[app_name]:
            self.session_data[app_name][name]['is_current'] = False
        
        # Set new current
        self.session_data[app_name][session_name]['is_current'] = True
        self.session_data[app_name][session_name]['last_used'] = datetime.now().isoformat()
        
        self.save_session_config()
        self.refresh_session_list()
        self.log(f"⭐ Set as current: {session_name}")
    
    def delete_session_backup(self, app_name, session_name):
        """Delete a session backup."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Delete")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"Delete session backup '{session_name}'?\n\nThis action cannot be undone.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        apply_dark_theme(msg_box)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            # Remove from config
            if session_name in self.session_data[app_name]:
                del self.session_data[app_name][session_name]
            
            # Remove folder
            backup_folder = os.path.join(self.session_backup_path, app_name, session_name)
            if os.path.exists(backup_folder):
                shutil.rmtree(backup_folder, ignore_errors=True)
            
            self.save_session_config()
            self.refresh_session_list()
            self.log(f"🗑️ Session deleted: {session_name}")
    
    def open_session_backup_folder(self):
        """Open the session backup folder in file explorer."""
        # Ensure the folder exists
        os.makedirs(self.session_backup_path, exist_ok=True)
        
        if open_folder_in_explorer(self.session_backup_path):
            self.log(f"📁 Opened session backup folder: {self.session_backup_path}")
        else:
            self.log(f"❌ Failed to open session backup folder")
    
    def filter_sessions(self, search_text: str):
        """Filter session table based on search text."""
        search_text = search_text.lower()
        
        for row in range(self.session_table.rowCount()):
            # Get backup name from column 2
            backup_name_item = self.session_table.item(row, 2)
            if backup_name_item:
                backup_name = backup_name_item.text().lower()
                # Show row if search text is in backup name
                should_show = search_text in backup_name
                self.session_table.setRowHidden(row, not should_show)
    
    def clear_search(self):
        """Clear search input and show all rows."""
        self.search_input.clear()
    
    def update_detected_apps(self, apps: dict):
        """Update detected applications."""
        # Update app selector dropdown if it exists
        if hasattr(self, 'app_selector'):
            current_selection = self.app_selector.currentText()
            self.app_selector.clear()
            
            for app_name, app_info in apps.items():
                if app_info.get('installed'):
                    display_name = app_info.get('display_name', app_name.title())
                    self.app_selector.addItem(display_name, app_name)
            
            # Restore selection if possible
            index = self.app_selector.findText(current_selection)
            if index >= 0:
                self.app_selector.setCurrentIndex(index)
        
        self.log(f"📊 Account tab updated with {len(apps)} applications")
        # Show all rows
        for row in range(self.session_table.rowCount()):
            self.session_table.setRowHidden(row, False)
