"""Account Manager tab for SurfManager."""
import os
import json
import shutil
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox,
    QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox,
    QInputDialog, QMenu, QFrame, QDialog, QScrollArea
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QBrush, QColor, QFont, QAction, QKeySequence, QShortcut
import qtawesome as qta
from app.core.config import ConfigManager
from app.core import app_configs


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
        self._init_ui()
        self._init_sessions()
        self._setup_shortcuts()
        self._load_apps_from_config()

    def log(self, msg: str):
        """Log to both global and local log."""
        if self.log_callback:
            self.log_callback(msg)
        self._local_log(msg)

    def _local_log(self, msg: str):
        """Add message to local activity log (no timestamp)."""
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
            name = self.table.item(row, 2).text().replace("★ ", "")
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
        """Handle app button click - filter by app."""
        idx = self.filter_combo.findText(app_name)
        if idx >= 0:
            self.filter_combo.setCurrentIndex(idx)
        self.log(f"Filter: {app_name}")



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
        
        # Create Backup button
        backup_btn = QPushButton(" New Backup")
        backup_btn.setIcon(qta.icon('fa5s.plus', color='#81c784'))
        backup_btn.setStyleSheet("QPushButton { background-color: #2e7d32; color: white; padding: 4px 10px; border-radius: 4px; } QPushButton:hover { background-color: #388e3c; }")
        backup_btn.clicked.connect(self._create_backup_dialog)
        toolbar.addWidget(backup_btn)
        
        toolbar.addStretch()

        self.search = QLineEdit()
        self.search.setPlaceholderText("Search...")
        self.search.setMaximumWidth(160)
        self.search.textChanged.connect(self._filter_table)
        toolbar.addWidget(self.search)

        sessions_layout.addLayout(toolbar)

        # Table (multi-select enabled)
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["#", "App", "Session Name", "Size", "Created", "Modified", "Status"])
        self.table.verticalHeader().setVisible(False)
        self.table.setSortingEnabled(True)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.ExtendedSelection)
        self.table.setStyleSheet("QHeaderView::section { font-weight: bold; background-color: #333; }")

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

        parent.addWidget(sessions_group, 2)


    def _on_double_click(self, index):
        """Load backup on double-click."""
        row = index.row()
        if row >= 0:
            app = self.table.item(row, 1).text().lower()
            name = self.table.item(row, 2).text().replace("★ ", "")
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
            name = self.table.item(row, 2).text().replace("★ ", "")
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
                if name in self.sessions.get(app, {}):
                    del self.sessions[app][name]
                folder = os.path.join(self.backup_path, app, name)
                if os.path.exists(folder):
                    shutil.rmtree(folder, ignore_errors=True)
                deleted += 1
            
            self._save()
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
        if self.filter_combo.findText(name) == -1:
            self.filter_combo.addItem(name)
            self.app_list.append(name.lower())

    def _on_filter(self, text):
        self.current_filter = text
        self._refresh()

    def _init_sessions(self):
        self.backup_path = self.config.get_path('surfmanager_paths.session_backup') or os.path.join(os.path.expanduser("~"), "Documents", "SurfManager")
        self.config_file = self.config.get_path('session_config_file') or os.path.join(self.backup_path, "sessions.json")
        os.makedirs(self.backup_path, exist_ok=True)
        self.sessions = self._load()
        self._refresh()

    def _load(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save(self):
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.sessions, f, indent=2, ensure_ascii=False)
        except Exception as e:
            self.log(f"Save failed: {e}")

    def _refresh(self):
        all_sessions = []
        counts = {}

        for app in self.app_list:
            items = self.sessions.get(app, {})
            counts[app] = len(items)
            if self.current_filter == "All" or self.current_filter.lower() == app:
                for name, data in items.items():
                    all_sessions.append((app, name, data))

        all_sessions.sort(key=lambda x: (not x[2].get('is_current', False), -(datetime.fromisoformat(x[2].get('created', '1900-01-01')).timestamp() if x[2].get('created') else 0)))

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(all_sessions))

        total = sum(counts.values())
        self.count_label.setText(f"Total: {total}" if self.current_filter == "All" else f"{counts.get(self.current_filter.lower(), 0)} of {total}")

        for row, (app, name, data) in enumerate(all_sessions):
            active = data.get('is_current', False)

            num = QTableWidgetItem(str(row + 1))
            num.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table.setItem(row, 0, num)

            app_item = QTableWidgetItem(app.title())
            app_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(row, 1, app_item)

            name_item = QTableWidgetItem(f"{'★ ' if active else ''}{name}")
            if active:
                name_item.setBackground(QBrush(QColor("#2d4a2e")))
                name_item.setForeground(QBrush(QColor("#a8e6a3")))
                name_item.setFont(QFont("", -1, QFont.Weight.Bold))
            self.table.setItem(row, 2, name_item)

            size = self._get_size(app, name)
            size_item = QTableWidgetItem(size)
            size_item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
            size_item.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 3, size_item)

            created = data.get('created', '')
            created_str = datetime.fromisoformat(created).strftime('%m/%d %H:%M') if created else "—"
            created_item = QTableWidgetItem(created_str)
            created_item.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 4, created_item)

            modified = data.get('last_used', data.get('created', ''))
            modified_str = datetime.fromisoformat(modified).strftime('%m/%d %H:%M') if modified else "—"
            modified_item = QTableWidgetItem(modified_str)
            modified_item.setForeground(QBrush(QColor("#888")))
            self.table.setItem(row, 5, modified_item)

            status = QTableWidgetItem("Active" if active else "—")
            status.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            if active:
                status.setBackground(QBrush(QColor("#2d4a2e")))
                status.setForeground(QBrush(QColor("#a8e6a3")))
                status.setFont(QFont("", -1, QFont.Weight.Bold))
            else:
                status.setForeground(QBrush(QColor("#555")))
            self.table.setItem(row, 6, status)

        self.table.setSortingEnabled(True)

    def _get_size(self, app, name):
        try:
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
        text = text.lower()
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 2)
            self.table.setRowHidden(row, text not in item.text().lower() if item else False)

    def _context_menu(self, pos):
        item = self.table.itemAt(pos)
        if not item:
            return

        row = self.table.row(item)
        app = self.table.item(row, 1).text().lower()
        name = self.table.item(row, 2).text().replace("★ ", "")

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

    def _set_active(self, app, name):
        for n in self.sessions.get(app, {}):
            self.sessions[app][n]['is_current'] = False
        if app in self.sessions and name in self.sessions[app]:
            self.sessions[app][name]['is_current'] = True
        self._save()
        self._refresh()
        self.log(f"Active: {name}")

    def _rename(self, app, old):
        dialog = QInputDialog(self)
        dialog.setWindowTitle("Rename")
        dialog.setLabelText("New name:")
        dialog.setTextValue(old)
        dialog.setStyleSheet("QInputDialog { background-color: #252526; color: #ccc; } QLineEdit { background-color: #3c3c3c; color: #ccc; border: 1px solid #555; padding: 4px; border-radius: 3px; }")

        if dialog.exec():
            new = dialog.textValue().strip()
            if new and new != old and new not in self.sessions.get(app, {}):
                self.sessions[app][new] = self.sessions[app].pop(old)
                old_path = os.path.join(self.backup_path, app, old)
                new_path = os.path.join(self.backup_path, app, new)
                if os.path.exists(old_path):
                    os.rename(old_path, new_path)
                self._save()
                self._refresh()
                self.log(f"Renamed: {old} → {new}")

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
            if name in self.sessions.get(app, {}):
                del self.sessions[app][name]
            folder = os.path.join(self.backup_path, app, name)
            if os.path.exists(folder):
                shutil.rmtree(folder, ignore_errors=True)
            self._save()
            self._refresh()
            self.log(f"Deleted: {name}")

    def _create_backup_dialog(self):
        """Show dialog to create new backup."""
        from datetime import datetime
        
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
        self._create_backup(app_key, name)
    
    def _create_backup(self, app_key: str, name: str):
        """Create backup of app data."""
        from datetime import datetime
        
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
        
        # Create backup folder
        backup_folder = os.path.join(self.backup_path, app_key.lower(), name)
        os.makedirs(backup_folder, exist_ok=True)
        
        try:
            # Copy data
            self.log(f"Backing up {display_name}...")
            for item in os.listdir(source_path):
                src = os.path.join(source_path, item)
                dst = os.path.join(backup_folder, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst, dirs_exist_ok=True)
                else:
                    shutil.copy2(src, dst)
            
            # Update sessions
            if app_key.lower() not in self.sessions:
                self.sessions[app_key.lower()] = {}
            
            self.sessions[app_key.lower()][name] = {
                'created': datetime.now().isoformat(),
                'is_current': False
            }
            
            self._save()
            self._refresh()
            self.log(f"Backup created: {name}")
            
        except Exception as e:
            self.log(f"Backup failed: {e}")
    
    def _load_session(self, app: str, name: str):
        """Restore session data to app folder."""
        config = app_configs.get_app(app)
        if not config:
            self.log(f"App config not found: {app}")
            return
        
        display_name = config.get('display_name', app.title())
        data_paths = config.get('paths', {}).get('data_paths', [])
        
        # Find target path
        target_path = None
        for path in data_paths:
            # Use first path as target (create if needed)
            target_path = path
            break
        
        if not target_path:
            self.log(f"No data path configured for {display_name}")
            return
        
        # Backup source
        backup_folder = os.path.join(self.backup_path, app.lower(), name)
        if not os.path.exists(backup_folder):
            self.log(f"Backup not found: {name}")
            return
        
        try:
            self.log(f"Restoring {name} to {display_name}...")
            
            # Clear target folder
            if os.path.exists(target_path):
                shutil.rmtree(target_path)
            os.makedirs(target_path, exist_ok=True)
            
            # Copy backup to target
            for item in os.listdir(backup_folder):
                src = os.path.join(backup_folder, item)
                dst = os.path.join(target_path, item)
                if os.path.isdir(src):
                    shutil.copytree(src, dst)
                else:
                    shutil.copy2(src, dst)
            
            self.log(f"Restored: {name}")
            
        except Exception as e:
            self.log(f"Restore failed: {e}")
    
    def _update_session(self, app: str, name: str):
        """Update existing session with current app data."""
        from datetime import datetime
        
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
            
            # Update session info
            if app.lower() in self.sessions and name in self.sessions[app.lower()]:
                self.sessions[app.lower()][name]['last_used'] = datetime.now().isoformat()
            
            self._save()
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
        
        # Also clear filter combo except "All"
        while self.filter_combo.count() > 1:
            self.filter_combo.removeItem(1)
    
    def refresh_ui(self):
        """Refresh UI when app configs change."""
        app_configs.reload_configs()
        self._load_apps_from_config()
        self._refresh()
        self.log("Sessions list refreshed")
