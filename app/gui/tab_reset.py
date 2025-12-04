"""Reset IDE Data tab for SurfManager."""
import os
import platform
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, 
    QLabel, QPushButton, QLineEdit, QTextEdit
)
from PyQt6.QtCore import Qt
import qtawesome as qta
from app.core import app_configs


class ResetTab(QWidget):
    """Reset data tab widget - dynamically loads from App Configuration."""
    MAX_PROGRAMS = 8

    def __init__(self, status_bar, log_callback):
        super().__init__()
        self.status_bar = status_bar
        self.log_callback = log_callback
        self.program_widgets = []
        self.app_widgets = {}  # Store widgets by app name
        self._init_ui()
        self._load_apps_from_config()

    def log(self, msg: str):
        """Log message to output."""
        if self.log_callback:
            self.log_callback(msg)
        if hasattr(self, 'log_output'):
            self.log_output.append(msg)

    def clear_log(self):
        self.log_output.clear()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)

        # Programs section
        self._create_programs_section(layout)

        # Bottom: Log + Actions
        bottom = QHBoxLayout()
        bottom.setSpacing(8)

        # Log
        log_group = QGroupBox("Log")
        log_layout = QVBoxLayout()
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_group.setLayout(log_layout)
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        bottom.addWidget(log_group, 2)

        # Actions
        self._create_actions(bottom)
        layout.addLayout(bottom, 1)

    def _create_programs_section(self, layout):
        self.programs_group = QGroupBox("Programs")
        programs_layout = QVBoxLayout()
        programs_layout.setSpacing(6)
        programs_layout.setContentsMargins(8, 12, 8, 8)
        self.programs_group.setLayout(programs_layout)

        # Empty placeholder
        self.empty_placeholder = QWidget()
        ph_layout = QHBoxLayout()
        ph_layout.setContentsMargins(0, 8, 0, 8)
        self.empty_placeholder.setLayout(ph_layout)

        icon = QLabel()
        icon.setPixmap(qta.icon('fa5s.inbox', color='#555').pixmap(32, 32))
        ph_layout.addStretch()
        ph_layout.addWidget(icon)

        text_layout = QVBoxLayout()
        text_layout.setSpacing(2)
        title = QLabel("No Programs Configured")
        title.setStyleSheet("color: #777; font-weight: bold;")
        desc = QLabel("Add programs in settings")
        desc.setStyleSheet("color: #555; font-size: 11px;")
        text_layout.addWidget(title)
        text_layout.addWidget(desc)
        ph_layout.addLayout(text_layout)
        ph_layout.addStretch()

        programs_layout.addWidget(self.empty_placeholder)

        # Programs grid (hidden)
        self.programs_grid = QWidget()
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(6)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.programs_grid.setLayout(self.grid_layout)
        self.programs_grid.hide()
        programs_layout.addWidget(self.programs_grid)

        layout.addWidget(self.programs_group)

    def add_program(self, display_name: str, app_key: str = "", detected_path: str = None):
        """Add program to grid (max 8).
        
        Args:
            display_name: Display name for the app
            app_key: Config key for the app (lowercase)
            detected_path: Detected data path (or None if not found)
        """
        if len(self.program_widgets) >= self.MAX_PROGRAMS:
            return

        self.empty_placeholder.hide()
        self.programs_grid.show()
        row = len(self.program_widgets)

        name_lbl = QLabel(f"<b>{display_name}</b>")
        name_lbl.setMinimumWidth(80)

        path_input = QLineEdit()
        path_input.setReadOnly(True)
        
        if detected_path:
            path_input.setText(detected_path)
            path_input.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 3px; padding: 4px; color: #FFFF00; font-weight: bold;")
        else:
            path_input.setPlaceholderText("Not detected")
            path_input.setStyleSheet("background-color: #2a2a2a; border: 1px solid #3a3a3a; border-radius: 3px; padding: 4px; color: #888;")

        btns = QHBoxLayout()
        btns.setSpacing(4)
        btns.setContentsMargins(0, 0, 0, 0)

        folder_btn = QPushButton()
        folder_btn.setIcon(qta.icon('fa5s.folder-open', color='#ffb74d'))
        folder_btn.setToolTip("Open Folder")
        folder_btn.setFixedSize(28, 28)
        folder_btn.clicked.connect(lambda checked, k=app_key: self._open_folder(k))

        reset_btn = QPushButton()
        reset_btn.setIcon(qta.icon('fa5s.redo-alt', color='#ef5350'))
        reset_btn.setToolTip("Reset")
        reset_btn.setFixedSize(28, 28)
        reset_btn.clicked.connect(lambda checked, k=app_key: self._reset_app(k))

        launch_btn = QPushButton()
        launch_btn.setIcon(qta.icon('fa5s.play', color='#81c784'))
        launch_btn.setToolTip("Launch")
        launch_btn.setFixedSize(28, 28)
        launch_btn.clicked.connect(lambda checked, k=app_key: self._launch_app(k))

        btns.addWidget(folder_btn)
        btns.addWidget(reset_btn)
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
        """Reset app data (placeholder - implement in next version)."""
        config = app_configs.get_app(app_key)
        display_name = config.get('display_name', app_key.title())
        self.log(f"[Reset] {display_name} - Feature coming soon")

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
        actions = QGroupBox("Actions")
        layout = QVBoxLayout()
        layout.setSpacing(8)
        layout.setContentsMargins(8, 12, 8, 8)
        actions.setLayout(layout)

        grid = QGridLayout()
        grid.setSpacing(6)

        clear_btn = QPushButton(" Clear")
        clear_btn.setIcon(qta.icon('fa5s.eraser', color='#e0e0e0'))
        clear_btn.clicked.connect(self.clear_log)
        grid.addWidget(clear_btn, 0, 0)

        id_btn = QPushButton(" New ID")
        id_btn.setIcon(qta.icon('fa5s.fingerprint', color='#ffd54f'))
        id_btn.clicked.connect(lambda: self.log("Generating new ID..."))
        grid.addWidget(id_btn, 0, 1)

        layout.addLayout(grid)
        layout.addStretch()
        parent.addWidget(actions, 1)

    def _load_apps_from_config(self):
        """Load apps from App Configuration (only active apps)."""
        # Clear existing programs
        self._clear_programs()
        
        # Get active apps from config
        active_apps = app_configs.get_active_apps()
        
        if not active_apps:
            # Show empty placeholder
            self.empty_placeholder.show()
            self.programs_grid.hide()
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
    
    def refresh_ui(self):
        """Refresh UI when app configs change."""
        app_configs.reload_configs()
        self._load_apps_from_config()
        self.log("Programs list refreshed")
