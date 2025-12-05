"""Reset IDE Data tab for SurfManager."""
import os
import json
import uuid
import shutil
import platform
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QLabel, QPushButton, QLineEdit, QTextEdit, QScrollArea, QProgressBar,
    QMessageBox, QSizePolicy
)
from PyQt6.QtCore import Qt
import qtawesome as qta
from app.core import app_configs


class ResetTab(QWidget):
    """Reset data tab widget - dynamically loads from App Configuration."""
    MAX_PROGRAMS = 8

    def __init__(self, status_bar, log_callback=None):
        super().__init__()
        self.status_bar = status_bar
        self.log_callback = log_callback
        self.program_widgets = []
        self.app_widgets = {}  # Store widgets by app name
        self.auto_backup_enabled = True  # Auto-backup toggle state
        self._init_ui()
        self._load_apps_from_config()

    def log(self, msg: str):
        """Log message to local output."""
        self.log_output.append(msg)

    def clear_log(self):
        self.log_output.clear()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(6)
        layout.setContentsMargins(8, 8, 8, 8)
        self.setLayout(layout)

        # Programs section (compact, max 8 with scroll)
        self._create_programs_section(layout)

        # Log section
        log_section = QGroupBox("Log")
        log_main = QVBoxLayout()
        log_main.setSpacing(6)
        log_main.setContentsMargins(6, 6, 6, 6)
        log_section.setLayout(log_main)
        
        # Log output (full width)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        self.log_output.setMinimumHeight(150)
        self.log_output.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #e0e0e0;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                font-family: Consolas, monospace;
                font-size: 11px;
            }
        """)
        log_main.addWidget(self.log_output, 1)
        
        # Bottom row: Progress bar | Actions
        bottom_row = QHBoxLayout()
        bottom_row.setSpacing(6)
        
        # Progress bar (left, stretch)
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(24)
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
        bottom_row.addWidget(self.progress_bar, 1)
        
        # Actions (right side, horizontal)
        self._create_actions(bottom_row)
        
        log_main.addLayout(bottom_row)
        layout.addWidget(log_section, 1)

    def _create_programs_section(self, layout):
        self.programs_group = QGroupBox("Programs")
        programs_layout = QVBoxLayout()
        programs_layout.setSpacing(2)  # Compact spacing
        programs_layout.setContentsMargins(6, 8, 6, 6)
        self.programs_group.setLayout(programs_layout)

        # Empty placeholder
        self.empty_placeholder = QWidget()
        ph_layout = QHBoxLayout()
        ph_layout.setContentsMargins(0, 4, 0, 4)
        self.empty_placeholder.setLayout(ph_layout)

        icon = QLabel()
        icon.setPixmap(qta.icon('fa5s.inbox', color='#555').pixmap(24, 24))
        ph_layout.addStretch()
        ph_layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(1)
        title = QLabel("No Programs Configured")
        title.setStyleSheet("color: #777; font-weight: bold; font-size: 11px;")
        desc = QLabel("Add programs in App Configuration")
        desc.setStyleSheet("color: #555; font-size: 10px;")
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        ph_layout.addLayout(text_layout)
        ph_layout.addStretch()

        programs_layout.addWidget(self.empty_placeholder)

        # Scroll area for programs (dynamic height based on content)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #2d2d2d; width: 8px; border-radius: 4px; }
            QScrollBar::handle:vertical { background: #4a4a4a; border-radius: 4px; min-height: 20px; }
            QScrollBar::handle:vertical:hover { background: #5a5a5a; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        """)
        
        # Programs grid inside scroll
        self.programs_grid = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(2)  # Compact vertical spacing
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.programs_grid.setLayout(self.grid_layout)
        
        self.scroll_area.setWidget(self.programs_grid)
        self.scroll_area.hide()
        programs_layout.addWidget(self.scroll_area)

        layout.addWidget(self.programs_group)

    def add_program(self, display_name: str, app_key: str = "", detected_path: str = None):
        """Add program to grid.
        
        Args:
            display_name: Display name for the app
            app_key: Config key for the app (lowercase)
            detected_path: Detected data path (or None if not found)
        """
        self.empty_placeholder.hide()
        self.scroll_area.show()
        row = len(self.program_widgets)

        name_lbl = QLabel(f"<b>{display_name}</b>")
        name_lbl.setMinimumWidth(70)
        name_lbl.setMaximumHeight(24)
        name_lbl.setStyleSheet("font-size: 11px;")

        path_input = QLineEdit()
        path_input.setReadOnly(True)
        path_input.setMaximumHeight(24)
        
        if detected_path:
            path_input.setText(detected_path)
            path_input.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 3px; padding: 2px 4px; color: #FFFF00; font-size: 10px;")
        else:
            path_input.setPlaceholderText("Not detected")
            path_input.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 3px; padding: 2px 4px; color: #888; font-size: 10px;")

        btns = QHBoxLayout()
        btns.setSpacing(3)
        btns.setContentsMargins(0, 0, 0, 0)
        
        # Button style with icon + text
        btn_style = """
            QPushButton {
                background-color: #2d2d30;
                border: 1px solid #3d3d3d;
                border-radius: 3px;
                padding: 2px 6px;
                font-size: 10px;
                color: #ccc;
            }
            QPushButton:hover { background-color: #3d3d3d; border-color: #4d4d4d; }
        """

        folder_btn = QPushButton(" Folder")
        folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#ffb74d'))
        folder_btn.setToolTip("Open data folder")
        folder_btn.setFixedHeight(22)
        folder_btn.setStyleSheet(btn_style)
        folder_btn.clicked.connect(lambda checked, k=app_key: self._open_folder(k))

        reset_btn = QPushButton(" Reset")
        reset_btn.setIcon(qta.icon('fa5s.redo-alt', color='#ef5350'))
        reset_btn.setToolTip("Reset application data")
        reset_btn.setFixedHeight(22)
        reset_btn.setStyleSheet(btn_style)
        reset_btn.clicked.connect(lambda checked, k=app_key: self._reset_app(k))

        newid_btn = QPushButton(" NewID")
        newid_btn.setIcon(qta.icon('fa5s.fingerprint', color='#ffd54f'))
        newid_btn.setToolTip("Generate new Machine ID")
        newid_btn.setFixedHeight(22)
        newid_btn.setStyleSheet(btn_style)
        newid_btn.clicked.connect(lambda checked, k=app_key: self._generate_new_id_for_app(k))

        launch_btn = QPushButton(" Launch")
        launch_btn.setIcon(qta.icon('fa5s.play', color='#81c784'))
        launch_btn.setToolTip("Launch application")
        launch_btn.setFixedHeight(22)
        launch_btn.setStyleSheet(btn_style)
        launch_btn.clicked.connect(lambda checked, k=app_key: self._launch_app(k))

        btns.addWidget(folder_btn)
        btns.addWidget(reset_btn)
        btns.addWidget(newid_btn)
        btns.addWidget(launch_btn)

        self.grid_layout.addWidget(name_lbl, row, 0)
        self.grid_layout.addWidget(path_input, row, 1)
        self.grid_layout.addLayout(btns, row, 2)
        self.grid_layout.setColumnStretch(1, 1)

        self.program_widgets.append({'name': display_name, 'path': path_input, 'key': app_key})
        self.app_widgets[app_key] = {'path_input': path_input}

    def _open_folder(self, app_key: str):
        """Open app data folder."""
        config = app_configs.get_app(app_key)
        display_name = config.get('display_name', app_key.title())
        
        # Find existing data path
        data_paths = config.get('paths', {}).get('data_paths', [])
        for path in data_paths:
            if os.path.exists(path):
                try:
                    if platform.system() == "Windows":
                        os.startfile(path)
                    elif platform.system() == "Darwin":
                        subprocess.run(["open", path])
                    else:
                        subprocess.run(["xdg-open", path])
                    self.log(f"Opened folder: {path}")
                    return
                except Exception as e:
                    self.log(f"Error opening folder: {e}")
                    return
        
        self.log(f"No folder found for {display_name}")

    def _reset_app(self, app_key: str):
        """Reset app data - FORCE CLOSE first, then delete data."""
        from app.core.process_killer import ProcessKiller
        
        config = app_configs.get_app(app_key)
        display_name = config.get('display_name', app_key.title())
        data_paths = config.get('paths', {}).get('data_paths', [])
        exe_paths = config.get('paths', {}).get('exe_paths', [])
        process_names = [os.path.basename(p) for p in exe_paths if p]
        
        # Find existing data path
        data_path = None
        for path in data_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if not data_path:
            self.log(f"[Reset] {display_name} - No data folder found")
            return
        
        # STEP 1: FORCE CLOSE APP IF RUNNING
        killer = ProcessKiller(log_callback=self.log)
        procs = killer.get_running_processes(process_names)
        
        if procs:
            self.log(f"[SMART CLOSE] {display_name} is running ({len(procs)} process) - closing...")
            self.progress_bar.setFormat(f"Closing {display_name}...")
            self.progress_bar.setValue(5)
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("App Running")
            msg.setText(f"{display_name} will be closed before reset")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
            
            if msg.exec() != QMessageBox.StandardButton.Ok:
                self.log(f"[Reset] Cancelled")
                return
            
            # FORCE KILL
            success, message = killer.smart_close(display_name, process_names)
            self.log(f"[SMART CLOSE] {message}")
            self.progress_bar.setValue(15)
        
        # STEP 2: Auto-backup if enabled
        if self.auto_backup_enabled:
            self.log(f"[AutoBackup] Creating backup before reset...")
            self.progress_bar.setFormat(f"Creating auto-backup...")
            self.progress_bar.setValue(20)
            
            # Create auto-backup folder
            import datetime
            backup_name = f"auto-reset-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"
            auto_backup_path = os.path.join(os.path.expanduser("~"), "Documents", "SurfManager", "auto-backups", app_key.lower())
            backup_folder = os.path.join(auto_backup_path, backup_name)
            
            try:
                os.makedirs(backup_folder, exist_ok=True)
                shutil.copytree(data_path, backup_folder, dirs_exist_ok=True)
                self.log(f"[AutoBackup] Saved: {backup_name}")
            except Exception as e:
                self.log(f"[AutoBackup] Failed: {e}")
        
        # STEP 3: Confirm reset
        msg = QMessageBox(self)
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.setWindowTitle("Confirm Reset")
        msg.setText(f"Reset {display_name}?")
        auto_text = " (Auto-backup created)" if self.auto_backup_enabled else ""
        msg.setInformativeText(f"Delete all data in:\n{data_path}{auto_text}")
        msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        
        if msg.exec() != QMessageBox.StandardButton.Yes:
            self.log(f"[Reset] Cancelled")
            return
        
        # STEP 4: Delete and recreate
        try:
            self.progress_bar.setFormat(f"Resetting {display_name}...")
            self.progress_bar.setValue(30)
            
            self.log(f"[Reset] Deleting {data_path}...")
            
            if os.path.exists(data_path):
                shutil.rmtree(data_path, ignore_errors=True)
            
            self.progress_bar.setValue(70)
            os.makedirs(data_path, exist_ok=True)
            
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("Reset completed!")
            self.log(f"[Reset] {display_name} - Complete!")
            
        except Exception as e:
            self.log(f"[Reset] {display_name} - Failed: {e}")
            self.progress_bar.setFormat("Reset failed!")

    def _generate_new_id_for_app(self, app_key: str):
        """Generate new Machine ID for a specific app."""
        config = app_configs.get_app(app_key)
        display_name = config.get('display_name', app_key.title())
        data_paths = config.get('paths', {}).get('data_paths', [])
        
        # Find data path
        data_path = None
        for path in data_paths:
            if os.path.exists(path):
                data_path = path
                break
        
        if not data_path:
            self.log(f"[NewID] {display_name} - No data folder found")
            return
        
        # Generate new IDs
        new_machine_id = str(uuid.uuid4())
        new_session_id = str(uuid.uuid4())
        
        self.progress_bar.setFormat(f"NewID: {display_name}...")
        self.progress_bar.setValue(20)
        
        self.log(f"[NewID] {display_name} - Generating...")
        
        total_updated = 0
        total_files = 0
        
        # Find and update JSON files
        for root, dirs, files in os.walk(data_path):
            for file in files:
                if file.endswith('.json'):
                    json_path = os.path.join(root, file)
                    try:
                        with open(json_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        modified = False
                        if isinstance(data, dict):
                            if 'machineId' in data:
                                data['machineId'] = new_machine_id
                                modified = True
                                total_updated += 1
                            
                            if 'telemetry.machineId' in data:
                                data['telemetry.machineId'] = new_machine_id
                                modified = True
                                total_updated += 1
                            
                            if 'sessionId' in data:
                                data['sessionId'] = new_session_id
                                modified = True
                                total_updated += 1
                            
                            # Force add to storage.json
                            if file == 'storage.json' and 'machineId' not in data:
                                data['machineId'] = new_machine_id
                                data['telemetry.machineId'] = new_machine_id
                                modified = True
                                total_updated += 2
                        
                        if modified:
                            with open(json_path, 'w', encoding='utf-8') as f:
                                json.dump(data, f, indent=2)
                            total_files += 1
                            
                    except (json.JSONDecodeError, IOError):
                        continue
        
        self.progress_bar.setValue(100)
        
        if total_files > 0:
            self.progress_bar.setFormat(f"Updated {total_updated} keys")
            self.log(f"[NewID] {display_name} - Updated {total_updated} keys in {total_files} files")
        else:
            self.progress_bar.setFormat("No ID files found")
            self.log(f"[NewID] {display_name} - No ID files found")
        

    def _launch_app(self, app_key: str):
        """Launch app executable."""
        config = app_configs.get_app(app_key)
        display_name = config.get('display_name', app_key.title())
        
        # Find exe path
        exe_paths = config.get('paths', {}).get('exe_paths', [])
        for exe_path in exe_paths:
            if os.path.exists(exe_path):
                try:
                    subprocess.Popen([exe_path], shell=True)
                    self.log(f"Launched: {display_name}")
                    return
                except Exception as e:
                    self.log(f"Error launching {display_name}: {e}")
                    return
        
        self.log(f"Executable not found for {display_name}")

    def _create_actions(self, parent):
        """Create action buttons (horizontal, bottom right)."""
        btn_style = """
            QPushButton {
                background-color: #2d2d30;
                color: #ccc;
                border: 1px solid #3d3d3d;
                border-radius: 4px;
                padding: 4px 10px;
                font-size: 11px;
            }
            QPushButton:hover { background-color: #3d3d3d; border-color: #0d7377; }
        """
        
        # AutoBackup toggle button
        self.auto_backup_btn = QPushButton("AutoBackup [ON]")
        self.auto_backup_btn.setToolTip("Toggle auto-backup before reset")
        self.auto_backup_btn.setFixedHeight(24)
        self.auto_backup_btn.setFixedWidth(130)
        self.auto_backup_btn.clicked.connect(self.toggle_auto_backup)
        self._update_auto_backup_style()
        parent.addWidget(self.auto_backup_btn)
        
        # Clear Log button
        clear_btn = QPushButton("Clear")
        clear_btn.setIcon(qta.icon('fa5s.eraser', color='#aaa'))
        clear_btn.setToolTip("Clear log output")
        clear_btn.setFixedHeight(24)
        clear_btn.setStyleSheet(btn_style)
        clear_btn.clicked.connect(self.clear_log)
        parent.addWidget(clear_btn)

        # Refresh button
        refresh_btn = QPushButton("Refresh")
        refresh_btn.setIcon(qta.icon('fa5s.sync', color='#4fc3f7'))
        refresh_btn.setToolTip("Refresh programs list")
        refresh_btn.setFixedHeight(24)
        refresh_btn.setStyleSheet(btn_style)
        refresh_btn.clicked.connect(self.refresh_ui)
        parent.addWidget(refresh_btn)
    
    def toggle_auto_backup(self):
        """Toggle auto-backup state."""
        self.auto_backup_enabled = not self.auto_backup_enabled
        self._update_auto_backup_style()
        status = "ENABLED" if self.auto_backup_enabled else "DISABLED"
        self.log(f"[AutoBackup] {status}")
    
    def _update_auto_backup_style(self):
        """Update auto-backup button style."""
        if self.auto_backup_enabled:
            self.auto_backup_btn.setText("AutoBackup [ON]")
            self.auto_backup_btn.setStyleSheet("""
                QPushButton {
                    background-color: #2d5016;
                    color: #90EE90;
                    font-weight: bold;
                    border: 1px solid #4CAF50;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #3d6020; }
            """)
        else:
            self.auto_backup_btn.setText("AutoBackup [OFF]")
            self.auto_backup_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4a2020;
                    color: #FF6B6B;
                    font-weight: bold;
                    border: 1px solid #8B0000;
                    border-radius: 4px;
                    padding: 4px 10px;
                    font-size: 11px;
                }
                QPushButton:hover { background-color: #5a3030; }
            """)

    def _load_apps_from_config(self):
        """Load apps from App Configuration (only active apps)."""
        # Clear existing programs
        self._clear_programs()
        
        # Get active apps from config
        active_apps = app_configs.get_active_apps()
        
        if not active_apps:
            # Show empty placeholder
            self.empty_placeholder.show()
            self.scroll_area.hide()
            self._update_scroll_height()
            return
        
        # Add each active app
        for app_name in sorted(active_apps):
            config = app_configs.get_app(app_name)
            display_name = config.get('display_name', app_name.title())
            
            # Detect data path from config
            detected_path = None
            data_paths = config.get('paths', {}).get('data_paths', [])
            for path in data_paths:
                if os.path.exists(path):
                    detected_path = path
                    break
            
            self.add_program(display_name, app_name, detected_path)
        
        # Update scroll area height to fit content
        self._update_scroll_height()
    
    def _clear_programs(self):
        """Clear all program widgets from grid."""
        # Clear grid layout
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()
        
        self.program_widgets = []
        self.app_widgets = {}
        
        # Reset visibility state
        self.scroll_area.hide()
        self.empty_placeholder.show()
    
    def _update_scroll_height(self):
        """Update scroll area height based on number of programs."""
        num_programs = len(self.program_widgets)
        
        if num_programs == 0:
            self.scroll_area.setFixedHeight(0)
            return
        
        # Each row is ~30px (24px widget + 6px spacing)
        row_height = 30
        max_visible = 8  # Max rows before scrolling
        
        if num_programs <= max_visible:
            # Fit exactly to content (no scroll needed)
            height = num_programs * row_height + 10  # +10 for padding
            self.scroll_area.setFixedHeight(height)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        else:
            # Enable scrolling for many programs
            height = max_visible * row_height + 10
            self.scroll_area.setFixedHeight(height)
            self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
    
    def refresh_ui(self):
        """Refresh UI when app configs change."""
        # Force reload from disk
        app_configs.reload_configs()
        
        # Rebuild UI
        self._load_apps_from_config()
        
        # Force update layout and geometry
        self.programs_grid.updateGeometry()
        self.scroll_area.updateGeometry()
        self.programs_group.updateGeometry()
        
        # Process events to ensure UI updates immediately
        from PyQt6.QtWidgets import QApplication
        QApplication.processEvents()
        
        self.log("[Refresh] Programs list updated")
