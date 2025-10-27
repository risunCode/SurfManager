"""Account Manager tab - Consistent style with Reset tab."""
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QGroupBox,
    QMenu, QTextEdit, QGridLayout, QLabel
)
from app.gui.ui_helpers import DialogHelper, StyleHelper
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QBrush, QColor, QFont, QShortcut, QKeySequence
from app.core.config_manager import ConfigManager
from app.core.core_utils import open_folder_in_explorer, get_resource_path


class AccountTab(QWidget):
    """Account Manager with session backup functionality."""
    
    def __init__(self, app_manager, log_callback):
        super().__init__()
        self.app_manager = app_manager
        self.log_callback = log_callback
        self.config_manager = ConfigManager()
        self.session_backup_path = ""
        self.current_user = None
        self.init_ui()
        self.init_sessions()
        
    def log(self, msg):
        """Log only to Account Manager's own log output."""
        if hasattr(self, 'log_output'):
            self.log_output.append(msg)
    
    def init_ui(self):
        """Initialize UI - consistent with Reset tab style."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Top: Session Table
        self.create_session_table(main_layout)
        
        # Log output (full width)
        log_group = QGroupBox("📋 Log")
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_group.setLayout(log_layout)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(120)  # Comfortable height for log
        log_layout.addWidget(self.log_output)
        
        main_layout.addWidget(log_group)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions."""
        # F5: Refresh session list
        QShortcut(QKeySequence("F5"), self).activated.connect(self.refresh_list)
        
        # Ctrl+O: Open backup folder
        QShortcut(QKeySequence("Ctrl+O"), self).activated.connect(self.open_folder)
        
        # Ctrl+F: Focus search
        QShortcut(QKeySequence("Ctrl+F"), self).activated.connect(lambda: self.search_input.setFocus())
        
        # Ctrl+1/2/3: Quick backup shortcuts
        QShortcut(QKeySequence("Ctrl+1"), self).activated.connect(lambda: self.create_backup("cursor"))
        QShortcut(QKeySequence("Ctrl+2"), self).activated.connect(lambda: self.create_backup("windsurf"))
        QShortcut(QKeySequence("Ctrl+3"), self).activated.connect(lambda: self.create_backup("claude"))
        
        # Delete: Delete selected sessions
        QShortcut(QKeySequence("Delete"), self).activated.connect(self.batch_delete_sessions)
        
        # Ctrl+A: Select all
        QShortcut(QKeySequence("Ctrl+A"), self).activated.connect(lambda: self.session_table.selectAll())
    
    def create_session_table(self, layout):
        """Create session table group."""
        table_group = QGroupBox("📅 Sessions")
        main_h_layout = QHBoxLayout()
        main_h_layout.setSpacing(10)
        main_h_layout.setContentsMargins(8, 8, 8, 8)
        table_group.setLayout(main_h_layout)
        
        # Left side: Table with search
        left_layout = QVBoxLayout()
        left_layout.setSpacing(8)
        
        # Stats and search bar
        top_bar = QHBoxLayout()
        top_bar.setSpacing(8)
        
        self.session_count_label = QLabel("")
        self.session_count_label.setStyleSheet("color: #aaa; font-size: 11px;")
        top_bar.addWidget(self.session_count_label)
        
        self.selection_count_label = QLabel("")
        self.selection_count_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-weight: bold;")
        top_bar.addWidget(self.selection_count_label)
        
        top_bar.addStretch()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔍 Search sessions...")
        self.search_input.setToolTip("Search sessions (Ctrl+F to focus)")
        self.search_input.setMaximumWidth(250)
        self.search_input.textChanged.connect(self.filter_sessions)
        top_bar.addWidget(self.search_input)
        
        left_layout.addLayout(top_bar)
        
        # Session Table
        self.session_table = QTableWidget()
        self.session_table.setMinimumHeight(350)
        self.session_table.setColumnCount(5)
        self.session_table.setHorizontalHeaderLabels(["#", "App", "Session Name", "Created", "Status"])
        
        # Add tooltips to headers
        self.session_table.horizontalHeaderItem(0).setToolTip("Row number")
        self.session_table.horizontalHeaderItem(1).setToolTip("Application name (Cursor, Windsurf, Claude)")
        self.session_table.horizontalHeaderItem(2).setToolTip("Backup session name - Right-click for actions")
        self.session_table.horizontalHeaderItem(3).setToolTip("Backup creation timestamp")
        self.session_table.horizontalHeaderItem(4).setToolTip("⭐ = Active session")
        
        self.session_table.verticalHeader().setVisible(False)
        self.session_table.setSortingEnabled(True)
        self.session_table.setAlternatingRowColors(True)
        self.session_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.session_table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.session_table.itemSelectionChanged.connect(self.update_selection_count)
        
        # Column widths
        header = self.session_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self.session_table.setColumnWidth(0, 35)
        self.session_table.setColumnWidth(1, 80)
        
        # Context menu
        self.session_table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.session_table.customContextMenuRequested.connect(self.show_context_menu)
        
        left_layout.addWidget(self.session_table)
        main_h_layout.addLayout(left_layout, stretch=4)
        
        # Right side: Actions in vertical layout with spacing
        right_layout = QVBoxLayout()
        right_layout.setSpacing(8)
        
        # Backup Actions Section
        backup_label = QLabel("💾 Create Backup")
        backup_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 12px;")
        right_layout.addWidget(backup_label)
        
        self.backup_cursor_btn = QPushButton("Cursor")
        self.backup_cursor_btn.setToolTip("Create backup for Cursor (Ctrl+1)")
        self.backup_cursor_btn.setMinimumWidth(120)
        self.backup_cursor_btn.setMinimumHeight(40)
        self.backup_cursor_btn.clicked.connect(lambda: self.create_backup("cursor"))
        right_layout.addWidget(self.backup_cursor_btn)
        
        right_layout.addSpacing(5)
        
        self.backup_windsurf_btn = QPushButton("Windsurf")
        self.backup_windsurf_btn.setToolTip("Create backup for Windsurf (Ctrl+2)")
        self.backup_windsurf_btn.setMinimumWidth(120)
        self.backup_windsurf_btn.setMinimumHeight(40)
        self.backup_windsurf_btn.clicked.connect(lambda: self.create_backup("windsurf"))
        right_layout.addWidget(self.backup_windsurf_btn)
        
        right_layout.addSpacing(5)
        
        self.backup_claude_btn = QPushButton("Claude")
        self.backup_claude_btn.setToolTip("Create backup for Claude (Ctrl+3)")
        self.backup_claude_btn.setMinimumWidth(120)
        self.backup_claude_btn.setMinimumHeight(40)
        self.backup_claude_btn.clicked.connect(lambda: self.create_backup("claude"))
        right_layout.addWidget(self.backup_claude_btn)
        
        right_layout.addSpacing(15)
        
        # Actions Section
        actions_label = QLabel("⚙️ Actions")
        actions_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 12px;")
        right_layout.addWidget(actions_label)
        
        refresh_btn = QPushButton("🔄 Refresh")
        refresh_btn.setMinimumWidth(120)
        refresh_btn.setMinimumHeight(40)
        refresh_btn.setToolTip("Refresh session list (F5)")
        refresh_btn.clicked.connect(self.refresh_list)
        right_layout.addWidget(refresh_btn)
        
        right_layout.addSpacing(5)
        
        self.open_folder_btn = QPushButton("📁 Folder")
        self.open_folder_btn.setMinimumWidth(120)
        self.open_folder_btn.setMinimumHeight(40)
        self.open_folder_btn.setToolTip("Open backup folder (Ctrl+O)")
        self.open_folder_btn.clicked.connect(self.open_folder)
        right_layout.addWidget(self.open_folder_btn)
        
        right_layout.addSpacing(15)
        
        # Delete All button
        delete_all_label = QLabel("🗑️ Delete")
        delete_all_label.setStyleSheet("font-weight: bold; color: #4CAF50; font-size: 12px;")
        right_layout.addWidget(delete_all_label)
        
        self.delete_all_btn = QPushButton("Delete All")
        self.delete_all_btn.setMinimumWidth(120)
        self.delete_all_btn.setMinimumHeight(40)
        self.delete_all_btn.setToolTip("Delete ALL backup sessions")
        self.delete_all_btn.setStyleSheet("""
            QPushButton {
                background-color: #8B0000;
                color: white;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #A52A2A;
            }
            QPushButton:disabled {
                background-color: #555;
                color: #888;
            }
        """)
        self.delete_all_btn.clicked.connect(self.delete_all_sessions)
        self.delete_all_btn.setEnabled(False)
        right_layout.addWidget(self.delete_all_btn)
        
        right_layout.addStretch()
        
        main_h_layout.addLayout(right_layout, stretch=1)
        layout.addWidget(table_group)
    
    def init_sessions(self):
        """Initialize session manager with proper path handling."""
        backup_loc = self.config_manager.get('backup_location')
        
        # Use backup_location directly if it's already an absolute path
        if backup_loc and os.path.isabs(backup_loc):
            self.session_backup_path = backup_loc
        elif backup_loc:
            self.session_backup_path = os.path.join(os.path.expanduser("~"), backup_loc)
        else:
            self.session_backup_path = os.path.join(os.path.expanduser("~"), "Documents", "SurfManager", "Backups")
        
        # Create directory with error handling
        try:
            os.makedirs(self.session_backup_path, exist_ok=True)
        except PermissionError:
            self.log(f"⚠️ Cannot create backup folder: {self.session_backup_path}")
            self.log(f"⚠️ Using fallback location...")
            # Fallback to current user's Documents
            self.session_backup_path = os.path.join(os.path.expanduser("~"), "Documents", "SurfManager", "Backups")
            os.makedirs(self.session_backup_path, exist_ok=True)
        
        # Get current user from environment
        import getpass
        self.current_user = getpass.getuser()
        
        QTimer.singleShot(100, self.refresh_list)
    
    def refresh_list(self):
        """Refresh session list by scanning backup folders."""
        all_sessions = []
        counts = {'cursor': 0, 'windsurf': 0, 'claude': 0}
        
        # Scan backup folders for each app
        for app in ['cursor', 'windsurf', 'claude']:
            app_folder = os.path.join(self.session_backup_path, app)
            
            if os.path.exists(app_folder):
                try:
                    for session_name in os.listdir(app_folder):
                        session_path = os.path.join(app_folder, session_name)
                        
                        # Only include directories
                        if os.path.isdir(session_path):
                            # Get folder creation time
                            try:
                                created_time = os.path.getctime(session_path)
                                created_dt = datetime.fromtimestamp(created_time)
                            except (OSError, ValueError) as e:
                                self.log(f"Warning: Could not get creation time for {session}: {e}")
                                created_dt = datetime.now()
                            
                            # Check if this is active session (has .active marker file)
                            is_active = os.path.exists(os.path.join(session_path, '.active'))
                            
                            all_sessions.append((app, session_name, created_dt, is_active))
                            counts[app] += 1
                except PermissionError:
                    pass  # Skip if can't access folder
        
        # Sort: active first, then by date (newest first)
        all_sessions.sort(key=lambda x: (not x[3], -x[2].timestamp()))
        
        # Update count label
        total = len(all_sessions)
        count_text = f"Total: {total} | Cursor: {counts['cursor']} | Windsurf: {counts['windsurf']} | Claude: {counts['claude']}"
        self.session_count_label.setText(count_text)
        
        # Enable/disable Delete All button based on total sessions
        self.delete_all_btn.setEnabled(total > 0)
        
        # Update table
        self.session_table.setSortingEnabled(False)
        self.session_table.setRowCount(len(all_sessions))
        
        for row, (app, name, created_dt, is_active) in enumerate(all_sessions):
            # Row number
            number_item = QTableWidgetItem(str(row + 1))
            if is_active:
                number_item.setBackground(QBrush(QColor("#404040")))
                number_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.session_table.setItem(row, 0, number_item)
            
            # App name
            app_item = QTableWidgetItem(app.title())
            app_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.session_table.setItem(row, 1, app_item)
            
            # Session name with size
            size = self.get_size(app, name)
            display_name = f"⭐ {name} - {size}" if is_active else f"{name} - {size}"
            
            name_item = QTableWidgetItem(display_name)
            if is_active:
                name_item.setBackground(QBrush(QColor("#2d4a2e")))
                name_item.setForeground(QBrush(QColor("#a8e6a3")))
                name_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.session_table.setItem(row, 2, name_item)
            
            # Created date
            created_str = created_dt.strftime('%Y-%m-%d %H:%M')
            self.session_table.setItem(row, 3, QTableWidgetItem(created_str))
            
            # Status
            if is_active:
                status_item = QTableWidgetItem("✅ Active")
                status_item.setBackground(QBrush(QColor("#2d4a2e")))
                status_item.setForeground(QBrush(QColor("#a8e6a3")))
                status_item.setFont(QFont("", -1, QFont.Weight.Bold))
            else:
                status_item = QTableWidgetItem("⚪ Ready")
                status_item.setForeground(QBrush(QColor("#888")))
            self.session_table.setItem(row, 4, status_item)
        
        self.session_table.setSortingEnabled(True)
    
    def get_size(self, app, name):
        """Get backup size."""
        try:
            path = os.path.join(self.session_backup_path, app, name)
            if not os.path.exists(path):
                return "0 KB"
            total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, files in os.walk(path) for f in files)
            if total < 1024:
                return f"{total} B"
            elif total < 1024 * 1024:
                return f"{total / 1024:.1f} KB"
            else:
                return f"{total / (1024 * 1024):.1f} MB"
        except (OSError, PermissionError) as e:
            self.log(f"Warning: Could not calculate folder size: {e}")
            return "Unknown"
    
    def filter_sessions(self, text):
        """Filter sessions by search text."""
        text = text.lower()
        for row in range(self.session_table.rowCount()):
            item = self.session_table.item(row, 2)
            if item:
                self.session_table.setRowHidden(row, text not in item.text().lower())
    
    def show_context_menu(self, pos):
        """Show context menu."""
        item = self.session_table.itemAt(pos)
        if not item:
            return
        
        row = self.session_table.row(item)
        selected_rows = self.session_table.selectionModel().selectedRows()
        
        menu = QMenu(self)
        menu.setStyleSheet(StyleHelper.CONTEXT_MENU)
        
        # Check if multiple items are selected
        if len(selected_rows) > 1:
            # Multiple selection menu - only show delete
            delete_action = menu.addAction(f"🗑️ Delete {len(selected_rows)} Sessions")
            action = menu.exec(self.session_table.mapToGlobal(pos))
            
            if action == delete_action:
                self.batch_delete_sessions()
        else:
            # Single selection menu - full options
            app_item = self.session_table.item(row, 1)
            name_item = self.session_table.item(row, 2)
            
            if not app_item or not name_item:
                return
            
            app = app_item.text().lower()
            session = name_item.text().replace("⭐ ", "").split(" - ")[0]
            
            restore = menu.addAction("🔄 Restore Session")
            update = menu.addAction("💾 Update Backup")
            menu.addSeparator()
            activate = menu.addAction("⭐ Set as Active")
            rename = menu.addAction("✏️ Rename")
            menu.addSeparator()
            open_f = menu.addAction("📂 Open Folder")
            menu.addSeparator()
            delete = menu.addAction("🗑️ Delete")
            
            action = menu.exec(self.session_table.mapToGlobal(pos))
            
            if action == restore:
                self.restore_session(app, session)
            elif action == update:
                self.update_backup(app, session)
            elif action == activate:
                self.set_active(app, session)
            elif action == rename:
                self.rename_session(app, session)
            elif action == open_f:
                path = os.path.join(self.session_backup_path, app, session)
                open_folder_in_explorer(path)
                self.log(f"📂 Opened: {session}")
            elif action == delete:
                self.delete_session(app, session)
    
    def create_backup(self, app_name):
        """Create new backup."""
        app_info = self.app_manager.get_app_info(app_name)
        
        if not app_info or not app_info["installed"]:
            DialogHelper.show_warning(self, "Not Found", f"{app_name.title()} not installed.")
            return
        
        if app_info.get("running"):
            if DialogHelper.confirm_warning(
                self, "Application Running",
                f"⚠️ {app_name.title()} is currently running.\n\n"
                f"For a safe backup, the application should be closed first.\n"
                f"This ensures all data is properly saved.\n\n"
                f"Do you want to close {app_name.title()} now?"
            ):
                self.log(f"⛔ Closing {app_name.title()} processes...")
                success, message = self.app_manager.kill_app_process(app_name)
                self.log(message)
                if not success:
                    DialogHelper.show_error(self, "Error", f"Failed to close {app_name.title()}:\n{message}")
                    return
            else:
                self.log(f"❌ Backup cancelled for {app_name.title()}")
                return
        
        name, ok = DialogHelper.get_text(self, "Create Backup", f"Enter name for {app_name.title()} backup:")
        if not ok or not name:
            return
        
        backup_name = f"{app_name}-{name.strip()}"
        
        # Check if backup already exists
        backup_path = os.path.join(self.session_backup_path, app_name, backup_name)
        if os.path.exists(backup_path):
            DialogHelper.show_warning(self, "Exists", "Backup name already exists!")
            return
        
        self.log(f"💾 Creating backup: {backup_name}")
        
        try:
            if self.backup_data(app_name, backup_name, app_info["path"]):
                DialogHelper.show_info(self, "Success", f"Backup '{backup_name}' created!")
                self.refresh_list()
        except Exception as e:
            self.log(f"❌ Failed: {e}")
    
    def backup_data(self, app, name, path):
        """Perform backup."""
        try:
            backup_path = os.path.join(self.session_backup_path, app, name)
            os.makedirs(backup_path, exist_ok=True)
            
            config_path = get_resource_path('app/config/reset.json')
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            items = config.get(app, {}).get('backup_items', [])
            backed_up = 0
            
            for item in items:
                source = os.path.join(path, item)
                if os.path.exists(source):
                    dest = os.path.join(backup_path, item)
                    os.makedirs(os.path.dirname(dest), exist_ok=True)
                    
                    try:
                        if os.path.isfile(source):
                            shutil.copy2(source, dest)
                        else:
                            shutil.copytree(source, dest, dirs_exist_ok=True)
                        backed_up += 1
                        self.log(f"✅ Backed up: {item}")
                    except Exception as e:
                        self.log(f"⚠️ Skip {item}: {e}")
            
            self.log(f"✅ Backup complete: {backed_up} items")
            return True
            
        except Exception as e:
            self.log(f"❌ Error: {e}")
            return False
    
    def restore_session(self, app, session):
        """Restore session."""
        if not DialogHelper.confirm(self, "Confirm Restore", f"Restore session '{session}'?\n\nThis will overwrite current {app.title()} settings."):
            return
        
        self.log(f"🔄 Restoring: {session}")
        
        app_info = self.app_manager.get_app_info(app)
        if not app_info:
            return
        
        self.app_manager.kill_app_process(app)
        
        backup_path = os.path.join(self.session_backup_path, app, session)
        app_path = app_info["path"]
        
        try:
            for item in os.listdir(backup_path):
                source = os.path.join(backup_path, item)
                dest = os.path.join(app_path, item)
                
                if os.path.exists(dest):
                    if os.path.isfile(dest):
                        os.remove(dest)
                    else:
                        shutil.rmtree(dest, ignore_errors=True)
                
                if os.path.isfile(source):
                    shutil.copy2(source, dest)
                else:
                    shutil.copytree(source, dest)
            
            self.set_active(app, session)
            self.log(f"✅ Restored: {session}")
            DialogHelper.show_info(self, "Success", "Session restored successfully!")
            
        except Exception as e:
            self.log(f"❌ Restore failed: {e}")
    
    def update_backup(self, app, session):
        """Update existing backup."""
        if DialogHelper.confirm(self, "Update Backup", f"Update backup '{session}' with current {app.title()} data?", default_no=False):
            app_info = self.app_manager.get_app_info(app)
            if app_info:
                self.backup_data(app, session, app_info["path"])
                self.log(f"✅ Updated: {session}")
    
    def set_active(self, app, session):
        """Set session as active using .active marker file."""
        app_folder = os.path.join(self.session_backup_path, app)
        
        # Remove all .active markers for this app
        if os.path.exists(app_folder):
            for folder_name in os.listdir(app_folder):
                marker_file = os.path.join(app_folder, folder_name, '.active')
                if os.path.exists(marker_file):
                    try:
                        os.remove(marker_file)
                    except (OSError, PermissionError):
                        pass  # Expected - file may be in use
        
        # Set new active session
        session_path = os.path.join(app_folder, session)
        if os.path.exists(session_path):
            marker_file = os.path.join(session_path, '.active')
            try:
                with open(marker_file, 'w') as f:
                    f.write(datetime.now().isoformat())
            except (OSError, PermissionError):
                pass  # Expected - permission issues
        
        self.refresh_list()
        self.log(f"⭐ Active: {session}")
    
    def rename_session(self, app, old_name):
        """Rename session."""
        new_name, ok = DialogHelper.get_text(self, "Rename Session", "New name:", default=old_name)
        
        if ok and new_name and new_name != old_name:
            old_path = os.path.join(self.session_backup_path, app, old_name)
            new_path = os.path.join(self.session_backup_path, app, new_name)
            
            # Check if new name already exists
            if os.path.exists(new_path):
                DialogHelper.show_warning(self, "Exists", "Name already exists!")
                return
            
            # Rename folder
            if os.path.exists(old_path):
                try:
                    os.rename(old_path, new_path)
                    self.refresh_list()
                    self.log(f"✏️ Renamed: {old_name} → {new_name}")
                except Exception as e:
                    self.log(f"❌ Rename failed: {e}")
    
    def update_selection_count(self):
        """Update selection count label."""
        selected_rows = self.session_table.selectionModel().selectedRows()
        count = len(selected_rows)
        
        if count > 0:
            self.selection_count_label.setText(f"Selected: {count}")
        else:
            self.selection_count_label.setText("")
    
    def delete_all_sessions(self):
        """Delete ALL backup sessions (wipe all data)."""
        # Count total sessions
        total = 0
        for app in ['cursor', 'windsurf', 'claude']:
            app_folder = os.path.join(self.session_backup_path, app)
            if os.path.exists(app_folder):
                try:
                    total += len([d for d in os.listdir(app_folder) if os.path.isdir(os.path.join(app_folder, d))])
                except PermissionError:
                    pass
        
        if total == 0:
            DialogHelper.show_info(self, "No Sessions", "No backup sessions found.")
            return
        
        # Confirm deletion
        if not DialogHelper.confirm(
            self, 
            "⚠️ DELETE ALL SESSIONS", 
            f"⚠️ WARNING: This will delete ALL {total} backup session(s)!\n\n"
            f"This action cannot be undone.\n\n"
            f"Are you absolutely sure you want to delete everything?"
        ):
            return
        
        self.log(f"🗑️ Deleting ALL sessions...")
        
        # Delete all sessions
        deleted_count = 0
        failed_count = 0
        
        for app in ['cursor', 'windsurf', 'claude']:
            app_folder = os.path.join(self.session_backup_path, app)
            if os.path.exists(app_folder):
                try:
                    for session_name in os.listdir(app_folder):
                        session_path = os.path.join(app_folder, session_name)
                        if os.path.isdir(session_path):
                            try:
                                shutil.rmtree(session_path)
                                deleted_count += 1
                            except Exception as e:
                                failed_count += 1
                                self.log(f"❌ Failed to delete {session_name}: {e}")
                except PermissionError:
                    self.log(f"⚠️ Cannot access {app} folder")
        
        # Show summary
        if deleted_count > 0:
            self.log(f"✅ Successfully deleted {deleted_count} session(s)")
            DialogHelper.show_info(self, "Success", f"Deleted {deleted_count} session(s)")
        if failed_count > 0:
            self.log(f"⚠️ Failed to delete {failed_count} session(s)")
        
        # Refresh list
        self.refresh_list()
    
    def batch_delete_sessions(self):
        """Delete multiple selected sessions."""
        selected_rows = self.session_table.selectionModel().selectedRows()
        
        if not selected_rows:
            return
        
        count = len(selected_rows)
        
        # Confirm deletion
        if not DialogHelper.confirm(
            self, 
            "Confirm Batch Delete", 
            f"Delete {count} selected session(s)?\n\nThis action cannot be undone."
        ):
            return
        
        # Collect sessions to delete
        sessions_to_delete = []
        for index in selected_rows:
            row = index.row()
            app_item = self.session_table.item(row, 1)
            name_item = self.session_table.item(row, 2)
            
            if app_item and name_item:
                app = app_item.text().lower()
                session = name_item.text().replace("⭐ ", "").split(" - ")[0]
                sessions_to_delete.append((app, session))
        
        # Delete sessions
        deleted_count = 0
        failed_count = 0
        
        for app, session in sessions_to_delete:
            path = os.path.join(self.session_backup_path, app, session)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    deleted_count += 1
                    self.log(f"🗑️ Deleted: {session}")
                except Exception as e:
                    failed_count += 1
                    self.log(f"❌ Delete failed for {session}: {e}")
        
        # Show summary
        if deleted_count > 0:
            self.log(f"✅ Successfully deleted {deleted_count} session(s)")
        if failed_count > 0:
            self.log(f"⚠️ Failed to delete {failed_count} session(s)")
        
        # Refresh list
        self.refresh_list()
    
    def delete_session(self, app, session):
        """Delete single session."""
        if DialogHelper.confirm(self, "Confirm Delete", f"Delete session '{session}'?\n\nThis action cannot be undone."):
            path = os.path.join(self.session_backup_path, app, session)
            if os.path.exists(path):
                try:
                    shutil.rmtree(path)
                    self.refresh_list()
                    self.log(f"🗑️ Deleted: {session}")
                except Exception as e:
                    self.log(f"❌ Delete failed: {e}")
    
    def open_folder(self):
        """Open backup folder."""
        os.makedirs(self.session_backup_path, exist_ok=True)
        if open_folder_in_explorer(self.session_backup_path):
            self.log(f"📁 Opened backup folder")
    
    def update_detected_apps(self, apps):
        """Update detected apps."""
        pass
    
    def set_current_user(self, username):
        """Set current user and update paths accordingly."""
        try:
            # Always construct path for selected user (don't use config backup_location)
            if username != os.environ.get('USERNAME'):
                profile = os.path.join(os.getenv('SystemDrive', 'C:'), 'Users', username)
            else:
                profile = os.path.expanduser("~")
            self.session_backup_path = os.path.join(profile, "Documents", "SurfManager", "Backups")
            
            # Update current user
            self.current_user = username
            
            # Try to create directory with permission handling
            try:
                os.makedirs(self.session_backup_path, exist_ok=True)
                self.log(f"📂 Backup path updated for user: {username}")
                self.log(f"   Path: {self.session_backup_path}")
            except PermissionError:
                self.log(f"⚠️ Cannot access: {self.session_backup_path}")
                self.log(f"⚠️ You may need administrator privileges to access this user's folder")
                # Use current user's path as fallback
                import getpass
                self.current_user = getpass.getuser()
                self.session_backup_path = os.path.join(os.path.expanduser("~"), "Documents", "SurfManager", "Backups")
                os.makedirs(self.session_backup_path, exist_ok=True)
                self.log(f"   Using fallback: {self.session_backup_path}")
            
            self.refresh_list()
        except Exception as e:
            self.log(f"❌ Error setting user: {e}")
