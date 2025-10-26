"""Reset tab functionality for SurfManager."""
import os
import json
import subprocess
import shutil
from pathlib import Path
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout, QGroupBox, QLabel,
    QPushButton, QLineEdit, QProgressBar, QTextEdit, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from app.core.reset_thread import ResetThread
from app.core.id_manager import IdManager
from app.core.path_utils import open_folder_in_explorer


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
                self.toggle_audio_btn.setStyleSheet("QPushButton { background-color: #4CAF50; }")
            else:
                self.toggle_audio_btn.setText("🔊 Enable Audio")
                self.toggle_audio_btn.setStyleSheet("QPushButton { background-color: #f44336; }")
    
    def init_ui(self):
        """Initialize the reset tab UI."""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(10)
        main_layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(main_layout)
        
        # Programs grid with status
        self.create_programs_grid(main_layout)
        
        # Bottom row: Log and Actions side by side
        bottom_layout = QHBoxLayout()
        
        # Log output (full height)
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
        
        bottom_layout.addWidget(log_group, 2)
        
        # Actions
        self.create_actions_compact(bottom_layout)
        
        main_layout.addLayout(bottom_layout)
    
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
        self.open_windsurf_btn = QPushButton("📁 Open Folder")
        self.open_windsurf_btn.setToolTip("Open Windsurf data folder")
        self.open_windsurf_btn.setMaximumWidth(110)
        self.open_windsurf_btn.clicked.connect(lambda: self.open_program_folder("windsurf"))
        windsurf_actions.addWidget(self.open_windsurf_btn)
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
        self.open_cursor_btn = QPushButton("📁 Open Folder")
        self.open_cursor_btn.setToolTip("Open Cursor data folder")
        self.open_cursor_btn.setMaximumWidth(110)
        self.open_cursor_btn.clicked.connect(lambda: self.open_program_folder("cursor"))
        cursor_actions.addWidget(self.open_cursor_btn)
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
        self.open_claude_btn = QPushButton("📁 Open Folder")
        self.open_claude_btn.setToolTip("Open Claude data folder")
        self.open_claude_btn.setMaximumWidth(110)
        self.open_claude_btn.clicked.connect(lambda: self.open_program_folder("claude"))
        claude_actions.addWidget(self.open_claude_btn)
        claude_actions.addStretch()
        grid.addLayout(claude_actions, 2, 2)
        
        # Set column stretch
        grid.setColumnStretch(0, 0)  # Name column - fixed
        grid.setColumnStretch(1, 1)  # Path column - stretch
        grid.setColumnStretch(2, 0)  # Actions column - fixed
        
        layout.addWidget(programs_group)
    
    def create_actions_compact(self, parent_layout):
        """Create compact actions section with 3x2 grid layout."""
        actions_group = QGroupBox("⚡ Actions")
        actions_main_layout = QVBoxLayout()
        actions_main_layout.setSpacing(5)
        actions_main_layout.setContentsMargins(10, 10, 10, 10)
        actions_group.setLayout(actions_main_layout)
        
        # Grid for buttons
        actions_layout = QGridLayout()
        actions_layout.setSpacing(5)
        actions_layout.setContentsMargins(0, 0, 0, 0)
        
        # Row 1 - Reset buttons
        self.reset_windsurf_btn = QPushButton("🔄 Reset Windsurf")
        self.reset_windsurf_btn.clicked.connect(lambda: self.reset_app_placeholder("windsurf"))
        actions_layout.addWidget(self.reset_windsurf_btn, 0, 0)
        
        self.reset_cursor_btn = QPushButton("🔄 Reset Cursor")
        self.reset_cursor_btn.clicked.connect(lambda: self.reset_app_placeholder("cursor"))
        actions_layout.addWidget(self.reset_cursor_btn, 0, 1)
        
        # Row 2 - Reset Claude & Clear Log
        self.reset_claude_btn = QPushButton("🔄 Reset Claude")
        self.reset_claude_btn.clicked.connect(lambda: self.reset_app_placeholder("claude"))
        actions_layout.addWidget(self.reset_claude_btn, 1, 0)
        
        self.clear_log_btn = QPushButton("🗑 Clear Log")
        self.clear_log_btn.clicked.connect(self.clear_log_with_sound)
        actions_layout.addWidget(self.clear_log_btn, 1, 1)
        
        # Row 3 - Utility buttons
        self.cleanup_btn = QPushButton("🧹 Cleanup")
        self.cleanup_btn.clicked.connect(self.run_cleanup_placeholder)
        actions_layout.addWidget(self.cleanup_btn, 2, 0)
        
        self.gen_new_id_btn = QPushButton("🔑 Generate New ID")
        self.gen_new_id_btn.clicked.connect(self.show_generate_id_placeholder)
        actions_layout.addWidget(self.gen_new_id_btn, 2, 1)
        
        # Row 4 - Refresh App List
        self.refresh_apps_btn = QPushButton("🔄 Refresh App List")
        self.refresh_apps_btn.clicked.connect(self.refresh_app_list)
        actions_layout.addWidget(self.refresh_apps_btn, 3, 0, 1, 2)  # Span 2 columns
        
        # Row 5 - Audio toggle (span 2 columns for emphasis)
        self.toggle_audio_btn = QPushButton("🔇 Disable Audio")
        self.toggle_audio_btn.clicked.connect(self.toggle_audio_enabled)
        self.update_audio_button_text()
        actions_layout.addWidget(self.toggle_audio_btn, 4, 0, 1, 2)  # Span 2 columns
        
        actions_main_layout.addLayout(actions_layout)
        
        # Add tips section below buttons
        tips_group = QGroupBox("💡 Tips")
        tips_layout = QVBoxLayout()
        tips_layout.setSpacing(3)
        tips_layout.setContentsMargins(8, 8, 8, 8)
        tips_group.setLayout(tips_layout)
        
        tips = [
            "⚠️ BACKUP in Account tab BEFORE reset!",
            "🔊 Disable audio to mute all sound effects",
            "🔄 Close apps before resetting for best results",
            "🔑 Generate new ID if you need fresh device identity"
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
        
        actions_main_layout.addWidget(tips_group)
        actions_main_layout.addStretch()
        
        parent_layout.addWidget(actions_group, 1)  # 33% width
    
    # ACTION FUNCTIONS
    
    def open_program_folder(self, app_name: str):
        """Open program data folder."""
        app_info = self.detected_apps.get(app_name)
        if app_info and app_info.get('installed'):
            path = app_info['path']
            
            if open_folder_in_explorer(path):
                self.log(f"📁 Opened {app_name.title()} folder: {path}")
                if self.audio_manager:
                    self.audio_manager.play_action_sound('open_folder')
            else:
                self.log(f"❌ Failed to open folder: {path}")
        else:
            self.log(f"❌ {app_name.title()} not detected")
    
    def reset_app_placeholder(self, app_name: str):
        """Reset application data."""
        app_info = self.detected_apps.get(app_name)
        if not app_info or not app_info.get('installed'):
            self.log(f"❌ {app_name.title()} not detected")
            return
        
        # Confirmation dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Reset")
        msg_box.setIcon(QMessageBox.Icon.Warning)
        msg_box.setText(f"⚠️ Reset {app_info['display_name']}?\n\n"
                       f"This will DELETE all application data.\n\n"
                       f"💾 Make sure to backup in Account tab first if needed!")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        
        if msg_box.exec() != QMessageBox.StandardButton.Yes:
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
                except:
                    pass
            
            self.log(f"✅ Cleaned {cleaned} cache directories")
            if self.audio_manager:
                self.audio_manager.play_action_sound('cleanup')
        except Exception as e:
            self.log(f"❌ Cleanup failed: {e}")
    
    def show_generate_id_placeholder(self):
        """Generate new machine ID."""
        # Show app selection dialog
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Generate New Device ID")
        msg_box.setText("Select application to generate new device ID:")
        
        windsurf_btn = msg_box.addButton("Windsurf", QMessageBox.ButtonRole.ActionRole)
        cursor_btn = msg_box.addButton("Cursor", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg_box.addButton("Cancel", QMessageBox.ButtonRole.RejectRole)
        
        msg_box.exec()
        clicked = msg_box.clickedButton()
        
        if clicked == windsurf_btn:
            app_key = 'windsurf'
        elif clicked == cursor_btn:
            app_key = 'cursor'
        else:
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
            self.log("✅ Application list refreshed")
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
        self.detected_apps = apps
        
        if log_details:
            installed_count = sum(1 for app in apps.values() if app.get('installed', False))
            self.log(f"📊 Detected {installed_count} installed applications")
        
        # Update UI elements based on detected apps
        for app_name, app_info in apps.items():
            if app_info.get('installed'):
                path = app_info.get('path', 'N/A')
                
                if log_details:
                    self.log(f"  ✓ {app_info.get('display_name', app_name)}: {path}")
                
                # Update path inputs
                if app_name == 'windsurf' and hasattr(self, 'windsurf_path_input'):
                    self.windsurf_path_input.setText(path)
                    self.windsurf_path_input.setStyleSheet("QLineEdit { color: #FFFF00; font-weight: bold; }")
                elif app_name == 'cursor' and hasattr(self, 'cursor_path_input'):
                    self.cursor_path_input.setText(path)
                    self.cursor_path_input.setStyleSheet("QLineEdit { color: #FFFF00; font-weight: bold; }")
                elif app_name == 'claude' and hasattr(self, 'claude_path_input'):
                    self.claude_path_input.setText(path)
                    self.claude_path_input.setStyleSheet("QLineEdit { color: #FFFF00; font-weight: bold; }")
