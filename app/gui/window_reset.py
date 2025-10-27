"""Reset tab functionality for SurfManager."""
import os
import json
import subprocess
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QLineEdit, QProgressBar, QTextEdit, QCheckBox
)
from app.gui.ui_helpers import DialogHelper, StyleHelper
from PyQt6.QtCore import Qt, QMutex, QMutexLocker
from PyQt6.QtGui import QShortcut, QKeySequence
import threading
from app.core.reset_thread import ResetThread
from app.core.id_manager import IdManager
from app.core.core_utils import open_folder_in_explorer, AppOperations


class ResetTab(QWidget):
    """Reset data tab widget."""
    
    def __init__(self, app_manager, status_bar, log_callback, 
                 refresh_callback=None, audio_manager=None):
        super().__init__()
        self.app_manager = app_manager
        self.audio_manager = audio_manager
        self.status_bar = status_bar
        self.log = log_callback
        self.refresh_callback = refresh_callback
        self.detected_apps = {}
        
        # Thread safety
        self.reset_mutex = QMutex()
        self.detected_apps_lock = threading.Lock()
        
        self.init_ui()
        self.log("✅ Reset tab initialized")
    
    def log_with_smooth_scroll(self, text: str):
        """Log to output."""
        self.log_output.append(text)
    
    def update_log_progress(self, percentage: int):
        """Update log progress bar."""
        if hasattr(self, 'log_progress_bar'):
            self.log_progress_bar.setValue(percentage)
    
    def clear_log_with_sound(self):
        """Clear log output and play clear sound."""
        self.log_output.clear()
        # Reset progress bar to Ready state
        if hasattr(self, 'log_progress_bar'):
            self.log_progress_bar.setValue(0)
            self.log_progress_bar.setFormat("Ready")
        if self.audio_manager:
            self.audio_manager.play_action_sound('clear_data')
    
    def toggle_audio_enabled(self):
        """Toggle audio enabled/disabled and update config."""
        if self.audio_manager:
            current_state = self.audio_manager.audio_config.get('audio_enabled', True)
            new_state = not current_state
            
            # Update config
            self.audio_manager.audio_config['audio_enabled'] = new_state
            
            # Save to file
            try:
                import json
                with open(self.audio_manager.config_path, 'w', encoding='utf-8') as f:
                    json.dump(self.audio_manager.audio_config, f, indent=2)
                
                self.log(f"🔊 Audio {'enabled' if new_state else 'disabled'}")
                self.update_audio_button_text()
                
                # Play startup sound if enabling
                if new_state:
                    self.audio_manager.play_sound('startup')
                    
            except Exception as e:
                self.log(f"❌ Failed to save audio settings: {e}")
    
    def update_audio_button_text(self):
        """Update audio button text based on current state."""
        if self.audio_manager:
            is_enabled = self.audio_manager.audio_config.get('audio_enabled', True)
            if is_enabled:
                self.toggle_audio_btn.setText("🔇 Disable Audio")
                StyleHelper.apply_button_style(self.toggle_audio_btn, 'success')
            else:
                self.toggle_audio_btn.setText("🔊 Enable Audio")
                StyleHelper.apply_button_style(self.toggle_audio_btn, 'disabled')
    
    def init_ui(self):
        """Initialize the reset tab UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Programs grid with status
        self.create_programs_grid(main_layout)
        
        # Log output with utilities
        log_group = QGroupBox("📋 Log")
        log_layout = QVBoxLayout()
        log_layout.setSpacing(5)
        log_layout.setContentsMargins(8, 8, 8, 8)
        log_group.setLayout(log_layout)
        
        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        # Progress bar inside log group (at bottom)
        self.log_progress_bar = QProgressBar()
        self.log_progress_bar.setMaximumHeight(20)
        self.log_progress_bar.setTextVisible(True)
        self.log_progress_bar.setFormat("Ready")
        self.log_progress_bar.setValue(0)
        self.log_progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #3d3d3d;
                border-radius: 5px;
                text-align: center;
                background-color: #1e1e1e;
                color: #e0e0e0;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0d7377, stop:1 #14ffec);
                border-radius: 3px;
            }
        """)
        log_layout.addWidget(self.log_progress_bar)
        
        # Utility buttons row
        utils_layout = QHBoxLayout()
        utils_layout.setSpacing(5)
        
        self.clear_log_btn = QPushButton("🗑️ Clear Log")
        self.clear_log_btn.setMaximumWidth(110)
        self.clear_log_btn.setToolTip("Clear log output (Ctrl+L)")
        self.clear_log_btn.clicked.connect(self.clear_log_with_sound)
        utils_layout.addWidget(self.clear_log_btn)
        
        self.generate_id_btn = QPushButton("🔑 Generate ID")
        self.generate_id_btn.setToolTip("Generate new device ID for app (Ctrl+G)")
        self.generate_id_btn.setMaximumWidth(120)
        self.generate_id_btn.clicked.connect(self.show_generate_id_placeholder)
        utils_layout.addWidget(self.generate_id_btn)
        
        utils_layout.addStretch()
        
        self.toggle_audio_btn = QPushButton("🔇 Disable Audio")
        self.toggle_audio_btn.setMaximumWidth(130)
        self.toggle_audio_btn.setToolTip("Toggle sound effects (Ctrl+M)")
        self.toggle_audio_btn.clicked.connect(self.toggle_audio_enabled)
        utils_layout.addWidget(self.toggle_audio_btn)
        self.update_audio_button_text()
        
        self.refresh_btn = QPushButton("🔄 Refresh List")
        self.refresh_btn.setMaximumWidth(120)
        self.refresh_btn.setToolTip("Refresh app detection list (F5)")
        self.refresh_btn.clicked.connect(self.refresh_app_list)
        utils_layout.addWidget(self.refresh_btn)
        
        log_layout.addLayout(utils_layout)
        
        main_layout.addWidget(log_group)
        
        # Setup keyboard shortcuts
        self.setup_shortcuts()
    
    def setup_shortcuts(self):
        """Setup keyboard shortcuts for common actions."""
        # Ctrl+L: Clear log
        QShortcut(QKeySequence("Ctrl+L"), self).activated.connect(self.clear_log_with_sound)
        
        # F5: Refresh app list
        QShortcut(QKeySequence("F5"), self).activated.connect(self.refresh_app_list)
        
        # Ctrl+M: Toggle audio
        QShortcut(QKeySequence("Ctrl+M"), self).activated.connect(self.toggle_audio_enabled)
        
        # Ctrl+G: Generate ID
        QShortcut(QKeySequence("Ctrl+G"), self).activated.connect(self.show_generate_id_placeholder)
    
    def create_programs_grid(self, layout):
        """Create programs as 3-column grid."""
        programs_group = QGroupBox("💻 Programs")
        grid = QGridLayout()
        grid.setSpacing(10)
        programs_group.setLayout(grid)
        
        # Windsurf (row 0)
        grid.addWidget(QLabel("<b>Windsurf</b>"), 0, 0)
        
        self.windsurf_path_input = QLineEdit()
        self.windsurf_path_input.setReadOnly(True)
        self.windsurf_path_input.setPlaceholderText("Not detected")
        grid.addWidget(self.windsurf_path_input, 0, 1)
        windsurf_actions = QHBoxLayout()
        windsurf_actions.setSpacing(5)
        windsurf_actions.setContentsMargins(0, 0, 0, 0)
        self.launch_windsurf_btn = QPushButton("🚀 Launch")
        self.launch_windsurf_btn.setToolTip("Launch Windsurf")
        self.launch_windsurf_btn.setMaximumWidth(85)
        self.launch_windsurf_btn.clicked.connect(lambda: self.launch_app("windsurf"))
        windsurf_actions.addWidget(self.launch_windsurf_btn)
        self.open_windsurf_btn = QPushButton("📁 Open")
        self.open_windsurf_btn.setToolTip("Open Windsurf data folder")
        self.open_windsurf_btn.setMaximumWidth(75)
        self.open_windsurf_btn.clicked.connect(lambda: self.open_program_folder("windsurf"))
        windsurf_actions.addWidget(self.open_windsurf_btn)
        self.reset_windsurf_btn = QPushButton("🔄 Reset")
        self.reset_windsurf_btn.setToolTip("Reset Windsurf data (delete all settings)")
        self.reset_windsurf_btn.setMaximumWidth(75)
        self.reset_windsurf_btn.clicked.connect(lambda: self.reset_app_placeholder("windsurf"))
        StyleHelper.apply_button_style(self.reset_windsurf_btn, 'danger')
        windsurf_actions.addWidget(self.reset_windsurf_btn)
        windsurf_actions.addStretch()
        grid.addLayout(windsurf_actions, 0, 2)
        
        # Cursor (row 1)
        grid.addWidget(QLabel("<b>Cursor</b>"), 1, 0)
        self.cursor_path_input = QLineEdit()
        self.cursor_path_input.setReadOnly(True)
        self.cursor_path_input.setPlaceholderText("Not detected")
        grid.addWidget(self.cursor_path_input, 1, 1)
        cursor_actions = QHBoxLayout()
        cursor_actions.setSpacing(5)
        cursor_actions.setContentsMargins(0, 0, 0, 0)
        self.launch_cursor_btn = QPushButton("🚀 Launch")
        self.launch_cursor_btn.setToolTip("Launch Cursor")
        self.launch_cursor_btn.setMaximumWidth(85)
        self.launch_cursor_btn.clicked.connect(lambda: self.launch_app("cursor"))
        cursor_actions.addWidget(self.launch_cursor_btn)
        self.open_cursor_btn = QPushButton("📁 Open")
        self.open_cursor_btn.setToolTip("Open Cursor data folder")
        self.open_cursor_btn.setMaximumWidth(75)
        self.open_cursor_btn.clicked.connect(lambda: self.open_program_folder("cursor"))
        cursor_actions.addWidget(self.open_cursor_btn)
        self.reset_cursor_btn = QPushButton("🔄 Reset")
        self.reset_cursor_btn.setToolTip("Reset Cursor data (delete all settings)")
        self.reset_cursor_btn.setMaximumWidth(75)
        self.reset_cursor_btn.clicked.connect(lambda: self.reset_app_placeholder("cursor"))
        StyleHelper.apply_button_style(self.reset_cursor_btn, 'danger')
        cursor_actions.addWidget(self.reset_cursor_btn)
        cursor_actions.addStretch()
        grid.addLayout(cursor_actions, 1, 2)
        
        # Claude (row 2)
        grid.addWidget(QLabel("<b>Claude</b>"), 2, 0)
        
        self.claude_path_input = QLineEdit()
        self.claude_path_input.setReadOnly(True)
        self.claude_path_input.setPlaceholderText("Not detected")
        grid.addWidget(self.claude_path_input, 2, 1)
        claude_actions = QHBoxLayout()
        claude_actions.setSpacing(5)
        claude_actions.setContentsMargins(0, 0, 0, 0)
        self.launch_claude_btn = QPushButton("🚀 Launch")
        self.launch_claude_btn.setToolTip("Launch Claude")
        self.launch_claude_btn.setMaximumWidth(85)
        self.launch_claude_btn.clicked.connect(lambda: self.launch_app("claude"))
        claude_actions.addWidget(self.launch_claude_btn)
        self.open_claude_btn = QPushButton("📁 Open")
        self.open_claude_btn.setToolTip("Open Claude data folder")
        self.open_claude_btn.setMaximumWidth(75)
        self.open_claude_btn.clicked.connect(lambda: self.open_program_folder("claude"))
        claude_actions.addWidget(self.open_claude_btn)
        self.reset_claude_btn = QPushButton("🔄 Reset")
        self.reset_claude_btn.setToolTip("Reset Claude data (delete all settings)")
        self.reset_claude_btn.setMaximumWidth(75)
        self.reset_claude_btn.clicked.connect(lambda: self.reset_app_placeholder("claude"))
        StyleHelper.apply_button_style(self.reset_claude_btn, 'danger')
        claude_actions.addWidget(self.reset_claude_btn)
        claude_actions.addStretch()
        grid.addLayout(claude_actions, 2, 2)
        
        # Set column stretch
        grid.setColumnStretch(0, 0)  # Name column - fixed
        grid.setColumnStretch(1, 1)  # Path column - stretch
        grid.setColumnStretch(2, 0)  # Actions column - fixed
        
        layout.addWidget(programs_group)
    
    # ACTION FUNCTIONS
    
    def launch_app(self, app_name: str):
        """Launch application executable."""
        with self.detected_apps_lock:
            apps_copy = self.detected_apps.copy()
        
        AppOperations.launch_app(app_name, apps_copy, self.log, self.audio_manager)
    
    def open_program_folder(self, app_name: str):
        """Open program data folder."""
        with self.detected_apps_lock:
            apps_copy = self.detected_apps.copy()
        
        AppOperations.open_app_folder(app_name, apps_copy, self.log, self.audio_manager)
    
    def reset_app_placeholder(self, app_name: str):
        """Reset application data."""
        # Thread-safe check for running reset
        locker = QMutexLocker(self.reset_mutex)
        if hasattr(self, 'reset_thread') and self.reset_thread and self.reset_thread.isRunning():
            self.log("❌ Reset operation already in progress")
            return
        locker.unlock()
        
        with self.detected_apps_lock:
            app_info = self.detected_apps.get(app_name)
        
        if not app_info or not app_info.get('installed'):
            self.log(f"❌ {app_name.title()} not detected")
            return
        
        # Confirmation dialog
        if not DialogHelper.confirm_warning(
            self, "Confirm Reset",
            f"⚠️ Reset {app_info['display_name']}?\n\n"
            f"This will DELETE all application data.\n\n"
            f"💾 Make sure to backup in Account tab first if needed!"
        ):
            self.log(f"❌ Reset cancelled for {app_info['display_name']}")
            return
        
        # Proceed with reset
        self.log(f"🔄 Starting reset for {app_info['display_name']}...")
        
        # Start reset thread
        self.reset_thread = ResetThread(
            self.app_manager,
            app_name
        )
        self.reset_thread.progress.connect(self.log_with_smooth_scroll)
        self.reset_thread.progress_percent.connect(self.update_log_progress)
        self.reset_thread.finished.connect(self.on_reset_finished)
        self.reset_thread.start()
        
        # Start progress bar
        if hasattr(self, 'log_progress_bar'):
            self.log_progress_bar.setValue(0)
            self.log_progress_bar.setMaximum(100)
            self.log_progress_bar.setFormat("%p% - Processing...")
    
    def on_reset_finished(self, success: bool, message: str):
        """Handle reset completion."""
        # Set progress bar to Completed/Failed state
        if hasattr(self, 'log_progress_bar'):
            if success:
                self.log_progress_bar.setFormat("✅ Completed")
            else:
                self.log_progress_bar.setFormat("❌ Failed")
        
        if success:
            self.log(f"✅ {message}")
            if self.audio_manager:
                # Determine which reset action based on app name
                if hasattr(self, 'reset_thread') and self.reset_thread:
                    app_name = getattr(self.reset_thread, 'app_name', '')
                    if 'windsurf' in app_name.lower():
                        self.audio_manager.play_action_sound('reset_windsurf')
                    elif 'cursor' in app_name.lower():
                        self.audio_manager.play_action_sound('reset_cursor')
                    elif 'claude' in app_name.lower():
                        self.audio_manager.play_action_sound('reset_claude')
                    else:
                        self.audio_manager.play_action_sound('clear_data')
            
            # Refresh app list (silent refresh - no logging)
            if self.refresh_callback:
                self.refresh_callback(force_rescan=False)
        else:
            self.log(f"❌ {message}")
    
    def run_cleanup_placeholder(self):
        """Run cleanup operations."""
        self.log("🧹 Running cleanup...")
        
        try:
            # Clean __pycache__
            cleaned = 0
            for pycache in Path('.').rglob('__pycache__'):
                try:
                    shutil.rmtree(pycache)
                    cleaned += 1
                except (OSError, PermissionError):
                    pass  # Expected - folder may be in use
            
            self.log(f"✅ Cleaned {cleaned} cache directories")
            if self.audio_manager:
                self.audio_manager.play_action_sound('cleanup')
        except Exception as e:
            self.log(f"❌ Cleanup failed: {e}")
    
    def show_generate_id_placeholder(self):
        """Generate new machine ID."""
        # Show app selection dialog
        app_key = DialogHelper.choose_app(
            self,
            "Generate New Device ID",
            "Select application to generate new device ID:"
        )
        
        if not app_key:
            return
        
        self.log(f"🔑 Generating new device ID for {app_key.title()}...")
        
        try:
            id_manager = IdManager()
            success, msg, new_ids = id_manager.reset_device_ids(app_key, backup=True)
            
            if success:
                self.log(f"✅ {msg}")
                self.log(f"   New IDs generated: {len(new_ids or {})}")
                if self.audio_manager:
                    self.audio_manager.play_action_sound('generate_new_id')
            else:
                self.log(f"❌ {msg}")
        except Exception as e:
            self.log(f"❌ Failed to generate device ID: {e}")
    
    def refresh_app_list(self):
        """Refresh application list with full rescan."""
        self.log("🔄 Refreshing application list...")
        
        if self.refresh_callback:
            self.refresh_callback(force_rescan=True)
            if self.audio_manager:
                self.audio_manager.play_sound('startup')
        else:
            self.log("❌ Refresh callback not available")
    
    def update_detected_apps(self, apps: dict, log_details: bool = False):
        """Update detected applications.
        
        Args:
            apps: Dictionary of detected applications
            log_details: If True, log detailed information. Otherwise just update UI silently.
        """
        # Thread-safe update
        with self.detected_apps_lock:
            self.detected_apps = apps.copy()
        
        # Clear all path inputs first (clean state)
        if hasattr(self, 'windsurf_path_input'):
            self.windsurf_path_input.setText("")
            self.windsurf_path_input.setStyleSheet("QLineEdit { color: #888; }")
        if hasattr(self, 'cursor_path_input'):
            self.cursor_path_input.setText("")
            self.cursor_path_input.setStyleSheet("QLineEdit { color: #888; }")
        if hasattr(self, 'claude_path_input'):
            self.claude_path_input.setText("")
            self.claude_path_input.setStyleSheet("QLineEdit { color: #888; }")
        
        # Update UI elements based on detected apps
        for app_name, app_info in apps.items():
            if app_info.get('installed'):
                path = app_info.get('path', 'N/A')
                
                # Update path inputs for installed apps only
                if app_name == 'windsurf' and hasattr(self, 'windsurf_path_input'):
                    self.windsurf_path_input.setText(path)
                    self.windsurf_path_input.setStyleSheet("QLineEdit { color: #FFFF00; font-weight: bold; }")
                elif app_name == 'cursor' and hasattr(self, 'cursor_path_input'):
                    self.cursor_path_input.setText(path)
                    self.cursor_path_input.setStyleSheet("QLineEdit { color: #FFFF00; font-weight: bold; }")
                elif app_name == 'claude' and hasattr(self, 'claude_path_input'):
                    self.claude_path_input.setText(path)
                    self.claude_path_input.setStyleSheet("QLineEdit { color: #FFFF00; font-weight: bold; }")
            else:
                # App not installed - ensure path is cleared and styled as not available
                if app_name == 'windsurf' and hasattr(self, 'windsurf_path_input'):
                    self.windsurf_path_input.setText("Not installed for current user")
                    self.windsurf_path_input.setStyleSheet("QLineEdit { color: #888; font-style: italic; }")
                elif app_name == 'cursor' and hasattr(self, 'cursor_path_input'):
                    self.cursor_path_input.setText("Not installed for current user")
                    self.cursor_path_input.setStyleSheet("QLineEdit { color: #888; font-style: italic; }")
                elif app_name == 'claude' and hasattr(self, 'claude_path_input'):
                    self.claude_path_input.setText("Not installed for current user")
                    self.claude_path_input.setStyleSheet("QLineEdit { color: #888; font-style: italic; }")
