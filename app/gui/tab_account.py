"""Account Manager tab for SurfManager."""
import os
import json
import shutil
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QInputDialog, QMenu, QFrame, QDialog, QScrollArea, QProgressBar
)
from PyQt6.QtCore import Qt, QTimer, QThread
from PyQt6.QtGui import QBrush, QColor, QFont, QAction, QKeySequence, QShortcut
import qtawesome as qta
from app.core.config import ConfigManager
from app.core import app_configs
from app.core.workers import BackupWorker, RestoreWorker, run_in_thread


class AllAppsDialog(QDialog):
    """Dialog showing all applications."""
    
    def __init__(self, apps, on_click_callback, parent=None):
        super().__init__(parent)
        self.setWindowTitle("All Applications")
        self.setMinimumSize(300, 200)
        self.on_click = on_click_callback
        self._init_ui(apps)
    
    def _init_ui(self, apps):
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)
        
        label = QLabel(f"Select application ({len(apps)} total)")
        label.setStyleSheet("font-weight: bold; color: #ccc;")
        layout.addWidget(label)
        
        # Scroll area for apps
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        
        grid_widget = QWidget()
        grid = QGridLayout()
        grid.setSpacing(4)
        grid.setContentsMargins(0, 0, 0, 0)
        grid_widget.setLayout(grid)
        
        for i, app_name in enumerate(sorted(apps)):
            btn = QPushButton(f" {app_name}")
            btn.setIcon(qta.icon('fa5s.cube', color='#ccc'))
            btn.setStyleSheet("""
                QPushButton { 
                    background-color: #333; 
                    border: 1px solid #444; 
                    border-radius: 4px; 
                    padding: 8px;
                    text-align: left;
                }
                QPushButton:hover { background-color: #404040; border-color: #0d7377; }
            """)
            btn.clicked.connect(lambda checked, n=app_name: self._on_click(n))
            grid.addWidget(btn, i // 2, i % 2)
        
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll, 1)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        layout.addWidget(close_btn)
    
    def _on_click(self, app_name):
        self.on_click(app_name)
        self.close()


class AccountTab(QWidget):
    """Account Manager tab widget - dynamically loads from App Configuration."""
    MAX_APPS = 8
    MAX_VISIBLE_APPS = 5  # Show max 5 apps, then "Show more" button

    def __init__(self, app_manager, log_callback):
        super().__init__()
        self.app_manager = app_manager
        self.log_callback = log_callback
        self.config = ConfigManager()
        self.current_filter = "All"
        self.app_list = []
        self.app_widgets = []
        self.show_auto_backups = False  # Toggle for auto-backups view
        self._init_ui()
        self._init_sessions()
        self._setup_shortcuts()
        self._load_apps_from_config()

    def log(self, msg: str):
        """Log to local output only."""
        self.log_output.append(msg)

    def clear_log(self):
        self.log_output.clear()

    def _setup_shortcuts(self):
        """Setup keyboard shortcuts."""
        del_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Delete), self)
        del_shortcut.activated.connect(self._delete_selected)

    def _delete_selected(self):
        """Delete selected row with Delete key."""
        row = self.table.currentRow()
        if row >= 0:
            app = self.table.item(row, 1).text().lower()
            name = self.table.item(row, 2).text()
            self._delete(app, name)

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Main content: Sessions (left) + Sidebar (right)
        content = QHBoxLayout()
        content.setSpacing(8)

        # Left: Sessions (Table + Log)
        self._create_sessions_section(content)

        # Right: Applications + Actions
        self._create_sidebar(content)

        layout.addLayout(content, 1)

    def _create_sidebar(self, parent):
        """Create sidebar with Applications + Actions."""
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout()
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(8)
        sidebar.setLayout(sidebar_layout)

        # Applications section
        self.apps_group = QGroupBox("Applications")
        apps_layout = QVBoxLayout()
        apps_layout.setSpacing(6)
        apps_layout.setContentsMargins(8, 12, 8, 8)
        self.apps_group.setLayout(apps_layout)

        # Empty placeholder
        self.empty_placeholder = QWidget()
        ph_layout = QVBoxLayout()
        ph_layout.setContentsMargins(0, 8, 0, 8)
        self.empty_placeholder.setLayout(ph_layout)

        icon = QLabel()
        icon.setPixmap(qta.icon('fa5s.inbox', color='#555').pixmap(24, 24))
        icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.addWidget(icon)

        title = QLabel("No apps configured")
        title.setStyleSheet("color: #555; font-size: 10px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ph_layout.addWidget(title)

        apps_layout.addWidget(self.empty_placeholder)

        # Apps grid (hidden)
        self.apps_grid = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.apps_grid.setLayout(self.grid_layout)
        self.apps_grid.hide()
        apps_layout.addWidget(self.apps_grid)

        sidebar_layout.addWidget(self.apps_group)

        # Actions section
        actions = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(8)
        actions_layout.setContentsMargins(8, 12, 8, 8)
        actions.setLayout(actions_layout)

        grid = QGridLayout()
        grid.setSpacing(6)

        clear_btn = QPushButton(" Clear")
        clear_btn.setIcon(qta.icon('fa5s.eraser', color='#e0e0e0'))
        clear_btn.clicked.connect(self.clear_log)
        grid.addWidget(clear_btn, 0, 0)

        refresh_btn = QPushButton(" Refresh")
        refresh_btn.setIcon(qta.icon('fa5s.sync-alt', color='#4fc3f7'))
        refresh_btn.clicked.connect(self._refresh)
        grid.addWidget(refresh_btn, 0, 1)

        folder_btn = QPushButton(" Folder")
        folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#ffb74d'))
        folder_btn.clicked.connect(self._open_backup_folder)
        grid.addWidget(folder_btn, 1, 0)

        delete_btn = QPushButton(" Delete")
        delete_btn.setIcon(qta.icon('fa5s.trash', color='#ef5350'))
        delete_btn.clicked.connect(self._delete_selected_multi)
        grid.addWidget(delete_btn, 1, 1)

        actions_layout.addLayout(grid)

        sidebar_layout.addWidget(actions)

        # Log section
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_group.setLayout(log_layout)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setStyleSheet("background-color: #1a1a1a; border: 1px solid #333; border-radius: 3px;")
        log_layout.addWidget(self.log_output)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(20)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setFormat("Ready")
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                text-align: center;
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-size: 10px;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d7377, stop:1 #14ffec);
                border-radius: 3px;
            }
        """)
        log_layout.addWidget(self.progress_bar)

        sidebar_layout.addWidget(log_group, 1)

        parent.addWidget(sidebar)

    def add_app(self, name: str, icon_name: str = 'fa5s.globe'):
        """Add application button to grid (max 8)."""
        if len(self.app_widgets) >= self.MAX_APPS:
            return

        self.empty_placeholder.hide()
        self.apps_grid.show()

        btn = QPushButton(f" {name}")
        btn.setIcon(qta.icon(icon_name, color='#ccc'))
        btn.setToolTip(f"Filter: {name}")
        btn.setStyleSheet("""
            QPushButton { 
                background-color: #333; 
                border: 1px solid #444; 
                border-radius: 4px; 
                padding: 6px 8px;
                text-align: left;
            }
            QPushButton:hover { background-color: #404040; border-color: #0d7377; }
        """)
        btn.clicked.connect(lambda checked, n=name: self._on_app_click(n))

        # Add to grid (2 columns)
        count = len(self.app_widgets)
        row, col = count // 2, count % 2
        self.grid_layout.addWidget(btn, row, col)

        self.app_widgets.append({'name': name, 'btn': btn})
        
        # Also add to filter
        self.add_app_filter(name)

    def _on_app_click(self, app_name: str):
        """Handle app button click - backup with smart app close."""
        from app.core.process_killer import ProcessKiller
        
        # Find app config
        active_apps = app_configs.get_active_apps()
        app_key = None
        config = None
        for a in active_apps:
            config = app_configs.get_app(a)
            if config.get('display_name', a.title()) == app_name:
                app_key = a
                break
        
        if not app_key or not config:
            self.log(f"App not found: {app_name}")
            return
        
        exe_paths = config.get('paths', {}).get('exe_paths', [])
        process_names = [os.path.basename(p) for p in exe_paths if p]
        
        # STEP 1: FORCE CLOSE APP IF RUNNING
        killer = ProcessKiller(log_callback=self.log)
        self._force_close_app(killer, app_name, process_names)
        
        # STEP 2: Ask for backup name
        name, ok = QInputDialog.getText(self, f"Backup {app_name}", "Enter session name:", text="main")
        if not ok or not name.strip():
            return
        
        backup_name = f"{app_key}-{name.strip()}"
        
        # Check for duplicate session name
        existing_sessions = self._get_existing_sessions_for_app(app_key)
        if backup_name in existing_sessions:
            QMessageBox.warning(self, "Duplicate Name", 
                f"Session '{backup_name}' already exists!\n\nPlease use a different name.")
            return
        
        # STEP 3: Create backup
        self._create_backup(app_key, backup_name)
        
        # Keep filter as "All" - don't change filter after backup
    
    def _force_close_app(self, killer, app_name: str, process_names: list):
        """Force close app if running - NO QUESTIONS ASKED."""
        if not process_names:
            return
        
        # Check if running
        procs = killer.get_running_processes(process_names)
        if not procs:
            return
        
        # App is running - FORCE CLOSE
        self.log(f"[SMART CLOSE] {app_name} is running - closing...")
        self.progress_bar.setFormat(f"Closing {app_name}...")
        self.progress_bar.setValue(5)
        
        # Show brief warning
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("App Running")
        msg.setText(f"{app_name} will be closed")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        if msg.exec() != QMessageBox.StandardButton.Ok:
            return
        
        # KILL IT
        success, message = killer.smart_close(app_name, process_names)
        self.log(f"[SMART CLOSE] {message}")
        self.progress_bar.setValue(20)



    def _create_sessions_section(self, parent):
        """Create sessions table section."""
        sessions_group = QGroupBox("Sessions")
        sessions_layout = QVBoxLayout()
        sessions_layout.setContentsMargins(8, 12, 8, 8)
        sessions_layout.setSpacing(6)
        sessions_group.setLayout(sessions_layout)

        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)

        self.filter_combo = QComboBox()
        self.filter_combo.addItem(qta.icon('fa5s.layer-group', color='#888'), "All")
        self.filter_combo.setFixedWidth(120)
        self.filter_combo.currentTextChanged.connect(self._on_filter)
        toolbar.addWidget(self.filter_combo)

        self.count_label = QLabel()
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        toolbar.addWidget(self.count_label)
        
        toolbar.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.setMaximumWidth(160)
        self.search.textChanged.connect(self._filter_table)
        toolbar.addWidget(self.search)
        
        # Auto-backups toggle button
        self.auto_backup_toggle_btn = QPushButton("Show Auto-Backup")
        self.auto_backup_toggle_btn.setFixedWidth(140)
        self.auto_backup_toggle_btn.setFixedHeight(24)
        self.auto_backup_toggle_btn.setCheckable(True)
        self.auto_backup_toggle_btn.setToolTip("Click to show auto-backups only")
        self.auto_backup_toggle_btn.clicked.connect(self._toggle_auto_backups_view)
        self._update_auto_backup_btn()
        toolbar.addWidget(self.auto_backup_toggle_btn)

        sessions_layout.addLayout(toolbar)

        # Table (multi-select enabled)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["#", "App", "Session Name", "Size", "Created", "Modified", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(False)  # Keep creation order
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        
        # Dark theme styling with standard font
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: #1e1e1e;
                alternate-background-color: #252526;
                gridline-color: #3d3d3d;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                color: #e0e0e0;
                font-family: "Segoe UI", sans-serif;
                font-size: 11px;
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
                font-family: "Segoe UI", sans-serif;
                font-size: 11px;
            }
        """)

        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(6, QHeaderView.ResizeMode.ResizeToContents)
        self.table.setColumnWidth(0, 35)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.doubleClicked.connect(self._on_double_click)

        sessions_layout.addWidget(self.table)
        
        # Add tip label
        tip_label = QLabel("Tip: Right-click on sessions for quick actions (Load, Update, Set Active, Rename, Browse, Delete)")
        tip_label.setStyleSheet("""
            QLabel {
                color: #888;
                font-size: 11px;
                font-style: italic;
                padding: 4px 8px;
                margin-top: 2px;
                background-color: rgba(255, 193, 7, 0.1);
                border-left: 3px solid #FFC107;
                border-radius: 3px;
            }
        """)
        tip_label.setWordWrap(True)
        sessions_layout.addWidget(tip_label)

        parent.addWidget(sessions_group, 2)


    def _on_double_click(self, index):
        """Load backup on double-click."""
        row = index.row()
        if row >= 0:
            app = self.table.item(row, 1).text().lower()
            name = self.table.item(row, 2).text()
            self._load_session(app, name)

    def _delete_selected_multi(self):
        """Delete selected rows (multi-select support)."""
        selected_rows = self.table.selectionModel().selectedRows()
        if not selected_rows:
            self.log("No items selected")
            return

        # Collect items to delete
        items_to_delete = []
        for index in selected_rows:
            row = index.row()
            app = self.table.item(row, 1).text().lower()
            name = self.table.item(row, 2).text()
            items_to_delete.append((app, name))

        count = len(items_to_delete)
        
        # Confirmation dialog
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete Sessions")
        msg.setIcon(QMessageBox.Icon.Warning)
        if count == 1:
            msg.setText(f"Delete '{items_to_delete[0][1]}'?")
        else:
            msg.setText(f"Delete {count} selected sessions?")
            msg.setInformativeText("This action cannot be undone.")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("QMessageBox { background-color: #252526; color: #ccc; } QPushButton { background-color: #404040; color: #e0e0e0; border: 1px solid #555; padding: 6px 14px; border-radius: 3px; } QPushButton:hover { background-color: #505050; }")

        if msg.exec() == QMessageBox.StandardButton.Yes:
            deleted = 0
            for app, name in items_to_delete:
                folder = os.path.join(self.backup_path, app, name)
                if os.path.exists(folder):
                    shutil.rmtree(folder, ignore_errors=True)
                    deleted += 1
            
            self._refresh()
            self.log(f"Deleted {deleted} session(s)")

    def _open_backup_folder(self):
        """Open backup folder."""
        if os.path.exists(self.backup_path):
            os.startfile(self.backup_path)
            self.log(f"Opened: {self.backup_path}")
        else:
            self.log("Backup folder not found")

    def add_app_filter(self, name: str):
        # Skip auto-backups from filter dropdown
        if name.lower() == "auto-backups":
            return
        if self.filter_combo.findText(name) == -1:
            self.filter_combo.addItem(name)
            self.app_list.append(name.lower())

    def _on_filter(self, text):
        self.current_filter = text
        self._refresh()

    def _init_sessions(self):
        # Use cross-platform backup path
        self.backup_path = str(self.config.get_platform_path("backup"))
        os.makedirs(self.backup_path, exist_ok=True)
        self._refresh()

    def _refresh(self):
        """Refresh sessions by scanning backup folders (filesystem-based)."""
        all_sessions = []
        
        if self.show_auto_backups:
            # Show auto-backups from Documents/SurfManager/auto-backupss/app_name/auto-xxx
            docs = self.config.documents_path
            auto_backup_base = os.path.join(docs, "SurfManager", "auto-backups")
            
            if os.path.exists(auto_backup_base):
                for app_name in os.listdir(auto_backup_base):
                    app_folder = os.path.join(auto_backup_base, app_name)
                    if not os.path.isdir(app_folder):
                        continue
                    
                    # Skip if not in filter
                    if self.current_filter != "All" and self.current_filter.lower() != app_name.lower():
                        continue
                    
                    try:
                        for item in os.listdir(app_folder):
                            item_path = os.path.join(app_folder, item)
                            if os.path.isdir(item_path) and item.startswith("auto-"):
                                # Get creation time
                                try:
                                    created_time = os.path.getctime(item_path)
                                    created_dt = datetime.fromtimestamp(created_time)
                                except:
                                    created_dt = datetime.now()
                                
                                all_sessions.append((app_name.lower(), item, created_dt))
                    except (PermissionError, OSError):
                        pass
        else:
            # Show regular manual sessions
            if os.path.exists(self.backup_path):
                for app_name in os.listdir(self.backup_path):
                    app_folder = os.path.join(self.backup_path, app_name)
                    if not os.path.isdir(app_folder):
                        continue
                    
                    # Skip special folders
                    if app_name.lower() in ("auto-backups", "sessions"):
                        continue
                    
                    # Skip if not in filter
                    if self.current_filter != "All" and self.current_filter.lower() != app_name.lower():
                        continue
                    
                    # Scan for backup folders in app directory (exclude auto- prefixed sessions)
                    try:
                        for item in os.listdir(app_folder):
                            item_path = os.path.join(app_folder, item)
                            if os.path.isdir(item_path) and not item.startswith("auto-") and not item.startswith("."):
                                # Get creation time
                                try:
                                    created_time = os.path.getctime(item_path)
                                    created_dt = datetime.fromtimestamp(created_time)
                                except:
                                    created_dt = datetime.now()
                                
                                all_sessions.append((app_name.lower(), item, created_dt))
                    except (PermissionError, OSError):
                        pass
        
        # Keep creation order (filesystem order)
        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(all_sessions))

        # Update count label
        total = len(all_sessions)
        if self.show_auto_backups:
            self.count_label.setText(f"{total} auto-backup(s)")
        else:
            self.count_label.setText(f"{total} session(s)")
        
        # Update auto-backup button badge
        self._update_auto_backup_btn()

        for row, (app, name, created_dt) in enumerate(all_sessions):
            # Row number
            num = QTableWidgetItem(str(row + 1))
            num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, num)

            # App name
            app_item = QTableWidgetItem(app.title())
            font = app_item.font()
            font.setBold(True)
            app_item.setFont(font)
            self.table.setItem(row, 1, app_item)

            # Session name
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 2, name_item)

            # Size
            size = self._get_size(app, name)
            size_item = QTableWidgetItem(size)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            size_item.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 3, size_item)

            # Created date
            created_str = created_dt.strftime('%m/%d %H:%M')
            created_item = QTableWidgetItem(created_str)
            created_item.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 4, created_item)

            # Modified (same as created for now)
            modified_item = QTableWidgetItem(created_str)
            modified_item.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 5, modified_item)

            # Status - different for auto-backups vs regular sessions
            if self.show_auto_backups:
                status = QTableWidgetItem("Auto")
                status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                status.setForeground(QBrush(QColor("#FFA726")))  # Orange for auto-backups
            else:
                is_active = self._is_session_active(app, name)
                if is_active:
                    status = QTableWidgetItem("Active")
                    status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    status.setBackground(QBrush(QColor("#2d4a2e")))
                    status.setForeground(QBrush(QColor("#a8e6a3")))
                    font = status.font()
                    font.setBold(True)
                    status.setFont(font)
                else:
                    status = QTableWidgetItem("Ready")
                    status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                    status.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 6, status)

        # Keep original order - no automatic sorting
        self.table.setSortingEnabled(False)

    def _get_size(self, app, name):
        try:
            if self.show_auto_backups:
                # Auto-backups path: Documents/SurfManager/auto-backups/app/name
                docs = self.config.documents_path
                folder = os.path.join(docs, "SurfManager", "auto-backups", app, name)
            else:
                # Regular sessions path
                folder = os.path.join(self.backup_path, app, name)
                
            if not os.path.exists(folder):
                return "0 KB"
            total = sum(os.path.getsize(os.path.join(dp, f)) for dp, _, files in os.walk(folder) for f in files if os.path.exists(os.path.join(dp, f)))
            if total < 1024:
                return f"{total} B"
            elif total < 1024 * 1024:
                return f"{total / 1024:.1f} KB"
            return f"{total / (1024 * 1024):.1f} MB"
        except:
            return "—"

    def _filter_table(self, text):
        """Filter table by search text."""
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)  # Session Name column
            if item:
                self.table.setRowHidden(row, text not in item.text().lower())

    def _toggle_auto_backups_view(self, checked):
        """Toggle between normal sessions and auto-backups view."""
        self.show_auto_backups = checked
        self._refresh()  # Refresh will update button and show different data
        
        # Clear search when switching views
        self.search.clear()
    
    def _count_auto_backups(self) -> int:
        """Count total auto-backups across all apps."""
        count = 0
        # Auto-backups are stored in Documents/SurfManager/auto-backups/app_name/auto-xxx
        docs = self.config.documents_path
        auto_backup_base = os.path.join(docs, "SurfManager", "auto-backups")
        
        if os.path.exists(auto_backup_base):
            for app_name in os.listdir(auto_backup_base):
                app_folder = os.path.join(auto_backup_base, app_name)
                if os.path.isdir(app_folder):
                    try:
                        for item in os.listdir(app_folder):
                            item_path = os.path.join(app_folder, item)
                            if os.path.isdir(item_path) and item.startswith("auto-"):
                                count += 1
                    except (PermissionError, OSError):
                        pass
        return count
        
    def _update_auto_backup_btn(self):
        """Update auto-backup toggle button text and style."""
        count = self._count_auto_backups()
        
        if self.show_auto_backups:
            self.auto_backup_toggle_btn.setText("← Back to Sessions")
            self.auto_backup_toggle_btn.setToolTip("Click to go back to manual sessions")
            self.auto_backup_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0d7377;
                    color: white;
                    font-weight: bold;
                    border: 1px solid #14a085;
                    border-radius: 3px;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background-color: #14a085;
                }
            """)
        else:
            if count > 0:
                self.auto_backup_toggle_btn.setText(f"Show Auto-Backup ({count})")
            else:
                self.auto_backup_toggle_btn.setText("Show Auto-Backup")
            self.auto_backup_toggle_btn.setToolTip("Click to show auto-backups only")
            self.auto_backup_toggle_btn.setStyleSheet("""
                QPushButton {
                    background-color: #3d3d3d;
                    color: #ccc;
                    border: 1px solid #555;
                    border-radius: 3px;
                    padding: 2px 8px;
                }
                QPushButton:hover {
                    background-color: #4d4d4d;
                }
            """)

    def _context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        row = self.table.row(item)
        app = self.table.item(row, 1).text().lower()
        name = self.table.item(row, 2).text()
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background-color: #2b2b2b; color: #e0e0e0; border: 1px solid #404040; border-radius: 6px; padding: 4px; } QMenu::item { padding: 8px 20px; border-radius: 3px; } QMenu::item:selected { background-color: #0d7377; } QMenu::separator { height: 1px; background: #404040; margin: 4px 8px; }")

        load_act = QAction(qta.icon('fa5s.download', color='#4fc3f7'), "Load", self)
        save_act = QAction(qta.icon('fa5s.upload', color='#81c784'), "Update", self)
        star_act = QAction(qta.icon('fa5s.star', color='#ffd54f'), "Set Active", self)
        rename_act = QAction(qta.icon('fa5s.pen', color='#ce93d8'), "Rename", self)
        folder_act = QAction(qta.icon('fa5s.folder', color='#ffb74d'), "Browse", self)
        del_act = QAction(qta.icon('fa5s.trash', color='#ef5350'), "Delete", self)

        menu.addAction(load_act)
        menu.addAction(save_act)
        menu.addSeparator()
        menu.addAction(star_act)
        menu.addAction(rename_act)
        menu.addSeparator()
        menu.addAction(folder_act)
        menu.addSeparator()
        menu.addAction(del_act)

        action = menu.exec(self.table.mapToGlobal(pos))

        if action == load_act:
            self._load_session(app, name)
        elif action == save_act:
            self._update_session(app, name)
        elif action == star_act:
            self._set_active(app, name)
        elif action == rename_act:
            self._rename(app, name)
        elif action == folder_act:
            self._open_folder(app, name)
        elif action == del_act:
            self._delete(app, name)

    def _is_session_active(self, app: str, name: str) -> bool:
        """Check if session is marked as active via marker file."""
        marker_file = os.path.join(self.backup_path, app, '.active')
        if not os.path.exists(marker_file):
            return False
        try:
            with open(marker_file, 'r') as f:
                active_name = f.read().strip()
                return active_name == name
        except:
            return False
    
    def _set_active(self, app, name):
        """Set session as active via marker file."""
        marker_file = os.path.join(self.backup_path, app, '.active')
        os.makedirs(os.path.dirname(marker_file), exist_ok=True)
        
        try:
            with open(marker_file, 'w') as f:
                f.write(name)
            self.log(f"Set active: {name}")
            self._refresh()  # Refresh to show updated status
        except Exception as e:
            self.log(f"Failed to set active: {e}")

    def _rename(self, app, old):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rename")
        dialog.setLabelText("New name:")
        dialog.setTextValue(old)
        dialog.setStyleSheet("QInputDialog { background-color: #252526; color: #ccc; } QLineEdit { background-color: #3c3c3c; color: #ccc; border: 1px solid #555; padding: 4px; border-radius: 3px; }")

        if dialog.exec():
            new = dialog.textValue().strip()
            if new and new != old:
                old_path = os.path.join(self.backup_path, app, old)
                new_path = os.path.join(self.backup_path, app, new)
                if os.path.exists(old_path) and not os.path.exists(new_path):
                    os.rename(old_path, new_path)
                    self._refresh()
                    self.log(f"Renamed: {old} → {new}")
                else:
                    self.log(f"Cannot rename: target exists or source not found")

    def _open_folder(self, app, name):
        folder = os.path.join(self.backup_path, app, name)
        if os.path.exists(folder):
            os.startfile(folder)
            self.log(f"Opened: {name}")
        else:
            self.log(f"Not found: {folder}")

    def _delete(self, app, name):
        msg = QMessageBox(self)
        msg.setWindowTitle("Delete")
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setText(f"Delete '{name}'?")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg.setStyleSheet("QMessageBox { background-color: #252526; color: #ccc; } QPushButton { background-color: #404040; color: #e0e0e0; border: 1px solid #555; padding: 6px 14px; border-radius: 3px; } QPushButton:hover { background-color: #505050; }")

        if msg.exec() == QMessageBox.StandardButton.Yes:
            folder = os.path.join(self.backup_path, app, name)
            if os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)
            self._refresh()
            self.log(f"Deleted: {name}")

    def _create_backup_dialog(self):
        """Show dialog to create new backup."""
        # Get active apps
        active_apps = app_configs.get_active_apps()
        if not active_apps:
            QMessageBox.warning(self, "No Apps", "No applications configured. Add apps in App Configuration first.")
            return
        
        # Select app dialog
        app_names = [app_configs.get_app(a).get('display_name', a.title()) for a in sorted(active_apps)]
        app, ok = QInputDialog.getItem(self, "Select Application", "Choose app to backup:", app_names, 0, False)
        if not ok or not app:
            return
        
        # Find app key
        app_key = None
        for a in active_apps:
            if app_configs.get_app(a).get('display_name', a.title()) == app:
                app_key = a
                break
        
        if not app_key:
            return
        
        # Session name dialog
        default_name = f"{app}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        name, ok = QInputDialog.getText(self, "Backup Name", "Enter session name:", text=default_name)
        if not ok or not name.strip():
            return
        
        name = name.strip()
        
        # Check for duplicate session name
        existing_sessions = self._get_existing_sessions_for_app(app_key)
        if name in existing_sessions:
            QMessageBox.warning(self, "Duplicate Name", 
                f"Session '{name}' already exists for {app_key.title()}!\n\n"
                f"Existing sessions:\n" + "\n".join(f"• {s}" for s in existing_sessions[:5]))
            return
        
        self._create_backup(app_key, name)
    
    def _get_existing_sessions_for_app(self, app_key: str) -> list:
        """Get list of existing session names for an app."""
        existing = []
        app_folder = os.path.join(self.backup_path, app_key.lower())
        
        if os.path.exists(app_folder):
            try:
                for item in os.listdir(app_folder):
                    item_path = os.path.join(app_folder, item)
                    if os.path.isdir(item_path) and not item.startswith("auto-") and not item.startswith("."):
                        existing.append(item)
            except (PermissionError, OSError):
                pass
        
        return existing
    
    def _create_backup(self, app_key: str, name: str):
        """Create backup of app data in background thread (no UI freeze)."""
        config = app_configs.get_app(app_key)
        display_name = config.get('display_name', app_key.title())
        data_paths = config.get('paths', {}).get('data_paths', [])
        
        # Find source path
        source_path = None
        for path in data_paths:
            if os.path.exists(path):
                source_path = path
                break
        
        if not source_path:
            self.log(f"No data found for {display_name}")
            return
        
        # Progress: Start backup
        self.progress_bar.setFormat(f"Backing up {display_name}...")
        self.progress_bar.setValue(10)
        self.log(f"Backing up {display_name}...")
        
        # Get backup config
        backup_folder = os.path.join(self.backup_path, app_key.lower(), name)
        backup_items = config.get('backup_items', [])
        addon_paths = config.get('addon_backup_paths', [])
        
        # Create worker and thread
        self._backup_worker = BackupWorker(source_path, backup_folder, backup_items, addon_paths)
        self._backup_thread = run_in_thread(self._backup_worker)
        
        # Connect signals
        self._backup_worker.progress.connect(self._on_backup_progress)
        self._backup_worker.log.connect(self.log)
        self._backup_worker.finished.connect(lambda success, msg: self._on_backup_finished(success, msg, name))
        
        # Start background thread
        self._backup_thread.start()
    
    def _on_backup_progress(self, percent: int, message: str):
        """Handle backup progress update."""
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(message)
    
    def _on_backup_finished(self, success: bool, message: str, name: str):
        """Handle backup completion."""
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Backup complete!")
            self.log(f"Backup created: {name}")
            self._refresh()
        else:
            self.progress_bar.setFormat(f"Backup failed: {message}")
            self.log(f"Backup failed: {message}")
    
    def _load_session(self, app: str, name: str):
        """Restore session - FORCE CLOSE app first, then restore in background."""
        from app.core.process_killer import ProcessKiller
        
        config = app_configs.get_app(app)
        if not config:
            self.log(f"App config not found: {app}")
            return
        
        display_name = config.get('display_name', app.title())
        data_paths = config.get('paths', {}).get('data_paths', [])
        exe_paths = config.get('paths', {}).get('exe_paths', [])
        process_names = [os.path.basename(p) for p in exe_paths if p]
        
        # Find target path
        target_path = None
        for path in data_paths:
            target_path = path
            break
        
        if not target_path:
            self.log(f"No data path for {display_name}")
            return
        
        # Backup source
        backup_folder = os.path.join(self.backup_path, app.lower(), name)
        if not os.path.exists(backup_folder):
            self.log(f"Backup not found: {name}")
            return
        
        # STEP 1: FORCE CLOSE APP IF RUNNING
        killer = ProcessKiller(log_callback=self.log)
        procs = killer.get_running_processes(process_names)
        
        if procs:
            self.log(f"[SMART CLOSE] {display_name} running - closing...")
            self.progress_bar.setFormat(f"Closing {display_name}...")
            self.progress_bar.setValue(5)
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("App Running")
            msg.setText(f"{display_name} will be closed before restore")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            
            if msg.exec() != QMessageBox.StandardButton.Ok:
                self.log(f"[Restore] Cancelled")
                return
            
            success, message = killer.smart_close(display_name, process_names)
            self.log(f"[SMART CLOSE] {message}")
            self.progress_bar.setValue(15)
        
        # STEP 2: Start restore in background thread
        self.progress_bar.setFormat(f"Restoring {name}...")
        self.progress_bar.setValue(20)
        self.log(f"Restoring {name}...")
        
        addon_paths = config.get('addon_backup_paths', [])
        
        # Store app info for callback
        self._restore_app = app
        self._restore_name = name
        
        # Create worker and thread
        self._restore_worker = RestoreWorker(backup_folder, target_path, addon_paths)
        self._restore_thread = run_in_thread(self._restore_worker)
        
        # Connect signals
        self._restore_worker.progress.connect(self._on_restore_progress)
        self._restore_worker.log.connect(self.log)
        self._restore_worker.finished.connect(self._on_restore_finished)
        
        # Start background thread
        self._restore_thread.start()
    
    def _on_restore_progress(self, percent: int, message: str):
        """Handle restore progress update."""
        self.progress_bar.setValue(percent)
        self.progress_bar.setFormat(message)
    
    def _on_restore_finished(self, success: bool, message: str):
        """Handle restore completion."""
        if success:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Restore complete!")
            self.log(f"Restored: {self._restore_name}")
            # Auto-set as active after successful restore
            self._set_active(self._restore_app.lower(), self._restore_name)
        else:
            self.progress_bar.setFormat(f"Restore failed: {message}")
            self.log(f"Restore failed: {message}")
    
    def _update_session(self, app: str, name: str):
        """Update existing session with current app data."""
        config = app_configs.get_app(app)
        if not config:
            self.log(f"App config not found: {app}")
            return
        
        display_name = config.get('display_name', app.title())
        data_paths = config.get('paths', {}).get('data_paths', [])
        
        # Find source path
        source_path = None
        for path in data_paths:
            if os.path.exists(path):
                source_path = path
                break
        
        if not source_path:
            self.log(f"No data found for {display_name}")
            return
        
        # Backup folder
        backup_folder = os.path.join(self.backup_path, app.lower(), name)
        
        try:
            self.log(f"Updating {name}...")
            
            # Clear existing backup
            if os.path.exists(backup_folder):
                shutil.rmtree(backup_folder)
            os.makedirs(backup_folder, exist_ok=True)
            
            # Copy data
            for item in os.listdir(source_path):
                src = os.path.join(source_path, item)
                dst = os.path.join(backup_folder, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            
            self._refresh()
            self.log(f"Updated: {name}")
            
        except Exception as e:
            self.log(f"Update failed: {e}")

    def _load_apps_from_config(self):
        """Load apps from App Configuration (only active apps)."""
        # Clear existing app widgets
        self._clear_app_widgets()
        
        # Get active apps from config
        active_apps = app_configs.get_active_apps()
        self._all_active_apps = []  # Store for "Show more" dialog
        
        if not active_apps:
            # Show empty placeholder
            self.empty_placeholder.show()
            self.apps_grid.hide()
            return
        
        # Build display names list
        for app_name in sorted(active_apps):
            config = app_configs.get_app(app_name)
            display_name = config.get('display_name', app_name.title())
            self._all_active_apps.append(display_name)
            
            # Add to app_list for sessions filtering
            if app_name.lower() not in self.app_list:
                self.app_list.append(app_name.lower())
        
        # Show max 5 apps, then "Show more" button
        visible_apps = self._all_active_apps[:self.MAX_VISIBLE_APPS]
        for display_name in visible_apps:
            self.add_app(display_name)
        
        # Add "Show more" button if there are more apps
        if len(self._all_active_apps) > self.MAX_VISIBLE_APPS:
            self._add_show_more_button()
    
    def _add_show_more_button(self):
        """Add 'Show more' button when there are more than MAX_VISIBLE_APPS."""
        remaining = len(self._all_active_apps) - self.MAX_VISIBLE_APPS
        btn = QPushButton(f" +{remaining} more...")
        btn.setIcon(qta.icon('fa5s.ellipsis-h', color='#888'))
        btn.setToolTip(f"Show all {len(self._all_active_apps)} applications")
        btn.setStyleSheet("""
            QPushButton { 
                background-color: #2a2a2a; 
                border: 1px dashed #555; 
                border-radius: 4px; 
                padding: 6px 8px;
                text-align: left;
                color: #888;
            }
            QPushButton:hover { background-color: #333; border-color: #0d7377; color: #ccc; }
        """)
        btn.clicked.connect(self._show_all_apps_dialog)
        
        # Add to grid
        count = len(self.app_widgets)
        row, col = count // 2, count % 2
        self.grid_layout.addWidget(btn, row, col)
    
    def _show_all_apps_dialog(self):
        """Show dialog with all applications."""
        dialog = AllAppsDialog(self._all_active_apps, self._on_app_click, self)
        dialog.exec()
    
    def _clear_app_widgets(self):
        """Clear all app widgets from grid."""
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.app_widgets = []
        self.app_list = []  # Clear app_list to prevent duplicates
        
        # Also clear filter combo except "All"
        while self.filter_combo.count() > 1:
            self.filter_combo.removeItem(1)

    def refresh_ui(self):
        """Refresh UI when app configs change."""
        app_configs.reload_configs()
        self._load_apps_from_config()
        self._refresh()
