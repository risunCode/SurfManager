"""Account Manager tab functionality for SurfManager."""
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QComboBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QMessageBox, QInputDialog, QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont


class AccountTab(QWidget):
    """Account Manager tab widget."""
    
    def __init__(self, app_manager, log_callback):
        super().__init__()
        self.app_manager = app_manager
        self.log = log_callback
        
        self.init_ui()
        self.init_session_manager()
    
    def init_ui(self):
        """Initialize the account tab UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Account Manager header
        header = QLabel("👤 Account Manager")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        header.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0; margin: 10px;")
        layout.addWidget(header)
        
        # Description
        desc = QLabel("Manage multiple user sessions and profiles for Cursor and Windsurf")
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setStyleSheet("color: #aaa; margin-bottom: 15px;")
        layout.addWidget(desc)
        
        # Action buttons row
        buttons_row = QHBoxLayout()
        
        # Session backup buttons
        self.create_cursor_session_btn = QPushButton("📁 Create Cursor Session")
        self.create_cursor_session_btn.clicked.connect(lambda: self.create_session_backup("cursor"))
        buttons_row.addWidget(self.create_cursor_session_btn)
        
        self.create_windsurf_session_btn = QPushButton("📁 Create Windsurf Session")
        self.create_windsurf_session_btn.clicked.connect(lambda: self.create_session_backup("windsurf"))
        buttons_row.addWidget(self.create_windsurf_session_btn)
        
        buttons_row.addStretch()
        
        # Utility buttons
        self.refresh_sessions_btn = QPushButton("🔄 Refresh")
        self.refresh_sessions_btn.clicked.connect(self.refresh_session_list)
        buttons_row.addWidget(self.refresh_sessions_btn)
        
        self.info_btn = QPushButton("ℹ️ Info")
        self.info_btn.clicked.connect(self.show_info_dialog)
        buttons_row.addWidget(self.info_btn)
        
        layout.addLayout(buttons_row)
        
        # Session table
        self.session_table = QTableWidget()
        self.session_table.setColumnCount(4)
        self.session_table.setHorizontalHeaderLabels(["#", "App", "Backup Name", "Date Created"])
        
        # Show row numbers and enable sorting
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setSortingEnabled(True)
        
        # Set column widths
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.session_table.setColumnWidth(0, 40)
        self.session_table.setColumnWidth(1, 80)
        
        # Enable context menu
        self.session_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_table.customContextMenuRequested.connect(self.show_session_context_menu)
        
        layout.addWidget(self.session_table)
        
        # Session backup path info
        session_info = QLabel("📂 Session backups stored in: Documents/SurfManager/Session Backup")
        session_info.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 10px;")
        layout.addWidget(session_info)
    
    def init_session_manager(self):
        """Initialize session manager."""
        self.session_backup_path = os.path.join(os.path.expanduser("~"), "Documents", "SurfManager", "Session Backup")
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
    
    def apply_dark_theme_to_dialog(self, dialog):
        """Apply dark theme to any dialog."""
        dialog.setStyleSheet("""
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
        """)
    
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

<b>Storage Location:</b> Documents/SurfManager/Session Backup
        """
        
        info_dialog.setText(info_text)
        info_dialog.setTextFormat(Qt.TextFormat.RichText)
        self.apply_dark_theme_to_dialog(info_dialog)
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
            self.apply_dark_theme_to_dialog(warning_box)
            warning_box.exec()
            return
        
        # Get backup name from user
        default_name = f"{app_name}-session-{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Create Session Backup")
        input_dialog.setLabelText(f"Enter name for {app_name.title()} session backup:")
        input_dialog.setTextValue(default_name)
        self.apply_dark_theme_to_dialog(input_dialog)
        
        ok = input_dialog.exec()
        backup_name = input_dialog.textValue() if ok else ""
        
        if not ok or not backup_name.strip():
            return
        
        backup_name = backup_name.strip()
        
        # Check if name already exists
        if backup_name in self.session_data.get(app_name, {}):
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("Name Exists")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText(f"Session backup '{backup_name}' already exists!")
            self.apply_dark_theme_to_dialog(warning_box)
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
                self.apply_dark_theme_to_dialog(success_box)
                success_box.exec()
                self.refresh_session_list()
            else:
                error_box = QMessageBox(self)
                error_box.setWindowTitle("Error")
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setText(f"Failed to create session backup '{backup_name}'")
                self.apply_dark_theme_to_dialog(error_box)
                error_box.exec()
        except Exception as e:
            self.log(f"❌ Error during backup creation: {e}")
            error_box = QMessageBox(self)
            error_box.setWindowTitle("Error")
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setText(f"An error occurred while creating backup: {str(e)}")
            self.apply_dark_theme_to_dialog(error_box)
            error_box.exec()
    
    def backup_session_data(self, app_name, backup_name, app_path):
        """Backup session-specific data."""
        try:
            # Create backup folder
            backup_folder = os.path.join(self.session_backup_path, app_name, backup_name)
            os.makedirs(backup_folder, exist_ok=True)
            
            # Session-specific files to backup (including telemetry data)
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
                "User/globalStorage/telemetry.json",
                "User/machineId",
                "User/globalStorage/ms-vscode.vscode-account",
                "User/globalStorage/ms-vscode-remote.remote-containers",
                "User/globalStorage/ms-vscode.remote-repositories"
            ]
            
            backed_up_files = 0
            for file_path in session_files:
                source = os.path.join(app_path, file_path)
                if os.path.exists(source):
                    dest = os.path.join(backup_folder, file_path)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    
                    if os.path.isfile(source):
                        shutil.copy2(source, dest)
                    else:
                        shutil.copytree(source, dest, dirs_exist_ok=True)
                    backed_up_files += 1
            
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
            
            # Session-specific files to restore
            session_files = [
                "User/settings.json",
                "User/keybindings.json", 
                "User/snippets",
                "User/globalStorage/state.vscdb",
                "User/workspaceStorage",
                "Network",
                "Local State",
                "Preferences"
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
        # Collect all sessions from both apps
        all_sessions = []
        
        for app_name in ['cursor', 'windsurf']:
            sessions = self.session_data.get(app_name, {})
            for name, data in sessions.items():
                all_sessions.append((app_name, name, data))
        
        # Sort sessions: current first, then by app name, then by date created (latest first)
        sorted_sessions = sorted(
            all_sessions,
            key=lambda x: (
                not x[2].get('is_current', False),  # Current sessions first
                x[0],  # Then by app name (cursor, windsurf)
                -(datetime.fromisoformat(x[2].get('created', '1900-01-01T00:00:00')).timestamp() if x[2].get('created') else 0)  # Then by date (latest first)
            )
        )
        
        # Clear the table completely and disable sorting temporarily
        self.session_table.setSortingEnabled(False)
        self.session_table.clear()
        self.session_table.setHorizontalHeaderLabels(["#", "App", "Backup Name", "Date Created"])
        self.session_table.setRowCount(len(sorted_sessions))
        
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
            if data.get('is_current', False):
                display_name = f"⭐ {name} (Current) - {backup_size}"
                name_item = QTableWidgetItem(display_name)
                # Highlight current session
                name_item.setBackground(QBrush(QColor("#404040")))
                name_item.setForeground(QBrush(QColor("#e0e0e0")))
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
        try:
            backup_folder = os.path.join(self.session_backup_path, app_name, session_name)
            if os.path.exists(backup_folder):
                os.startfile(backup_folder)
                self.log(f"📁 Opened backup folder: {session_name}")
            else:
                self.log(f"❌ Backup folder not found: {backup_folder}")
        except Exception as e:
            self.log(f"❌ Failed to open backup folder: {e}")
    
    def show_session_context_menu(self, position):
        """Show context menu for session table."""
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
        session_name = name_item.text().replace("⭐ ", "").replace(" (Current)", "").split(" - ")[0]
        
        # Create context menu
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #252526;
                color: #cccccc;
                border: 1px solid #3d3d3d;
            }
            QMenu::item {
                padding: 8px 16px;
            }
            QMenu::item:selected {
                background-color: #404040;
            }
        """)
        
        # Menu actions
        restore_action = menu.addAction("🔄 Restore this backup")
        replace_action = menu.addAction("💾 Replace backup with current data")
        menu.addSeparator()
        open_folder_action = menu.addAction("📁 Open backup folder")
        menu.addSeparator()
        rename_action = menu.addAction("✏️ Rename backup")
        set_current_action = menu.addAction("⭐ Set as current active")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete backup")
        
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
        # Confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Restore")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(f"Restore session backup '{session_name}'?\n\nThis will overwrite current {app_name.title()} settings.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.apply_dark_theme_to_dialog(msg_box)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.log(f"🔄 Restoring session: {session_name}")
            success = self.restore_session_data(app_name, session_name)
            if success:
                self.log(f"✅ Session restored: {session_name}")
                # Update last used time
                self.session_data[app_name][session_name]['last_used'] = datetime.now().isoformat()
                self.save_session_config()
                self.refresh_session_list()
            else:
                self.log(f"❌ Failed to restore session: {session_name}")
    
    def replace_session_backup(self, app_name, session_name):
        """Replace session backup with current data."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Replace")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(f"Replace backup '{session_name}' with current {app_name.title()} data?")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        self.apply_dark_theme_to_dialog(msg_box)
        
        if msg_box.exec() == QMessageBox.StandardButton.Yes:
            self.log(f"💾 Replacing session backup: {session_name}")
            app_info = self.app_manager.get_app_info(app_name)
            if app_info and app_info["installed"]:
                success = self.backup_session_data(app_name, session_name, app_info["path"])
                if success:
                    self.log(f"✅ Session backup replaced: {session_name}")
                    self.refresh_session_list()
                else:
                    self.log(f"❌ Failed to replace session backup: {session_name}")
            else:
                self.log(f"❌ {app_name.title()} not found or not installed")
    
    def rename_session_backup(self, app_name, session_name):
        """Rename a session backup."""
        input_dialog = QInputDialog(self)
        input_dialog.setWindowTitle("Rename Session Backup")
        input_dialog.setLabelText(f"Enter new name for '{session_name}':")
        input_dialog.setTextValue(session_name)
        self.apply_dark_theme_to_dialog(input_dialog)
        
        ok = input_dialog.exec()
        new_name = input_dialog.textValue() if ok else ""
        
        if ok and new_name.strip() and new_name.strip() != session_name:
            new_name = new_name.strip()
            if new_name in self.session_data[app_name]:
                warning_box = QMessageBox(self)
                warning_box.setWindowTitle("Name Exists")
                warning_box.setIcon(QMessageBox.Icon.Warning)
                warning_box.setText(f"Session backup '{new_name}' already exists!")
                self.apply_dark_theme_to_dialog(warning_box)
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
        self.apply_dark_theme_to_dialog(msg_box)
        
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
