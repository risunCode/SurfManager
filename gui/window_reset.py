"""Reset tab functionality for SurfManager."""
import os
import subprocess
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, 
    QPushButton, QLineEdit, QProgressBar, QTextEdit, QMessageBox, QCheckBox
)
from PyQt6.QtCore import Qt
from core.reset_thread import ResetThread
from datetime import datetime

# Debug mode configuration
DEBUG_MODE = os.environ.get('SURFMANAGER_DEBUG', 'NO').upper() == 'YES'

def debug_print(message):
    """Print debug message only if DEBUG_MODE is enabled."""
    if DEBUG_MODE:
        print(message)


class ResetTab(QWidget):
    """Reset data tab widget."""
    
    def __init__(self, app_manager, backup_manager, status_bar, log_callback, refresh_callback=None):
        super().__init__()
        self.app_manager = app_manager
        self.backup_manager = backup_manager
        self.status_bar = status_bar
        self.log = log_callback
        self.refresh_callback = refresh_callback
        self.detected_apps = {}
        
        self.init_ui()
    
    def init_ui(self):
        """Initialize the reset tab UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)
        
        # Programs section
        self.create_programs_section(layout)
        
        # Backup options section
        self.create_backup_section(layout)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setMaximumHeight(8)
        layout.addWidget(self.progress_bar)
        
        # Log output
        log_group = QGroupBox("📋 Log Output")
        log_layout = QVBoxLayout()
        log_group.setLayout(log_layout)
        
        self.log_output = QTextEdit()
        self.log_output.setMaximumHeight(200)
        self.log_output.setReadOnly(True)
        log_layout.addWidget(self.log_output)
        
        # Actions
        actions_group = QGroupBox("⚡ Actions")
        actions_layout = QHBoxLayout()
        actions_group.setLayout(actions_layout)
        
        self.reset_windsurf_btn = QPushButton("🔄 Reset Windsurf")
        self.reset_windsurf_btn.clicked.connect(lambda: self.reset_app_with_confirm("windsurf"))
        actions_layout.addWidget(self.reset_windsurf_btn)
        
        self.reset_cursor_btn = QPushButton("🔄 Reset Cursor")
        self.reset_cursor_btn.clicked.connect(lambda: self.reset_app_with_confirm("cursor"))
        actions_layout.addWidget(self.reset_cursor_btn)
        
        self.clear_log_btn = QPushButton("🗑 Clear Log")
        self.clear_log_btn.clicked.connect(self.log_output.clear)
        actions_layout.addWidget(self.clear_log_btn)
        
        actions_layout.addStretch()
        
        layout.addWidget(log_group)
        layout.addWidget(actions_group)
    
    def create_programs_section(self, layout):
        """Create programs section."""
        programs_group = QGroupBox("💻 Programs")
        programs_layout = QVBoxLayout()
        programs_group.setLayout(programs_layout)
        
        # Windsurf
        windsurf_row = QHBoxLayout()
        windsurf_row.addWidget(QLabel("Windsurf:"))
        self.windsurf_path_input = QLineEdit()
        self.windsurf_path_input.setReadOnly(True)
        self.windsurf_path_input.setPlaceholderText("Not detected")
        windsurf_row.addWidget(self.windsurf_path_input, 1)
        self.open_windsurf_btn = QPushButton("📁 Open Data Folder")
        self.open_windsurf_btn.setMaximumWidth(130)
        self.open_windsurf_btn.clicked.connect(lambda: self.open_program_folder("windsurf"))
        windsurf_row.addWidget(self.open_windsurf_btn)
        self.kill_windsurf_program_btn = QPushButton("Kill App")
        self.kill_windsurf_program_btn.setMaximumWidth(80)
        self.kill_windsurf_program_btn.setObjectName("dangerButton")
        self.kill_windsurf_program_btn.clicked.connect(lambda: self.kill_program("windsurf"))
        windsurf_row.addWidget(self.kill_windsurf_program_btn)
        self.open_windsurf_program_btn = QPushButton("Open Program")
        self.open_windsurf_program_btn.setMaximumWidth(100)
        self.open_windsurf_program_btn.clicked.connect(lambda: self.open_program_executable("windsurf"))
        windsurf_row.addWidget(self.open_windsurf_program_btn)
        programs_layout.addLayout(windsurf_row)
        
        # Cursor
        cursor_row = QHBoxLayout()
        cursor_row.addWidget(QLabel("Cursor:"))
        self.cursor_path_input = QLineEdit()
        self.cursor_path_input.setReadOnly(True)
        self.cursor_path_input.setPlaceholderText("Not detected")
        cursor_row.addWidget(self.cursor_path_input, 1)
        self.open_cursor_btn = QPushButton("📁 Open Data Folder")
        self.open_cursor_btn.setMaximumWidth(130)
        self.open_cursor_btn.clicked.connect(lambda: self.open_program_folder("cursor"))
        cursor_row.addWidget(self.open_cursor_btn)
        self.kill_cursor_program_btn = QPushButton("Kill App")
        self.kill_cursor_program_btn.setMaximumWidth(80)
        self.kill_cursor_program_btn.setObjectName("dangerButton")
        self.kill_cursor_program_btn.clicked.connect(lambda: self.kill_program("cursor"))
        cursor_row.addWidget(self.kill_cursor_program_btn)
        self.open_cursor_program_btn = QPushButton("Open Program")
        self.open_cursor_program_btn.setMaximumWidth(100)
        self.open_cursor_program_btn.clicked.connect(lambda: self.open_program_executable("cursor"))
        cursor_row.addWidget(self.open_cursor_program_btn)
        programs_layout.addLayout(cursor_row)
        layout.addWidget(programs_group)
    
    def create_backup_section(self, layout):
        """Create backup options section."""
        backup_group = QGroupBox("💾 Backup Options")
        backup_layout = QVBoxLayout()
        backup_group.setLayout(backup_layout)
        
        # Backup toggle with spacing
        backup_toggle_row = QHBoxLayout()
        backup_toggle_row.addStretch()  # Push checkbox to the right
        self.backup_enabled_checkbox = QCheckBox("Create backup before reset (optional)")
        self.backup_enabled_checkbox.setChecked(False)  # Default disabled
        self.backup_enabled_checkbox.stateChanged.connect(self.on_backup_toggle_changed)
        backup_toggle_row.addWidget(self.backup_enabled_checkbox)
        backup_layout.addLayout(backup_toggle_row)
        
        # Info note when backup is enabled
        self.backup_info_label = QLabel(
            "📝 Backup keeps: settings, extensions, workspaces, user data\n"
            "💡 Note: Backup is not necessary but recommended for safety"
        )
        self.backup_info_label.setStyleSheet("color: #888; font-size: 11px; padding: 5px;")
        self.backup_info_label.setVisible(False)  # Hidden by default
        backup_layout.addWidget(self.backup_info_label)
        
        # Cursor backup
        self.cursor_backup_row = QHBoxLayout()
        self.cursor_backup_label = QLabel("Cursor:")
        self.cursor_backup_row.addWidget(self.cursor_backup_label)
        backup_base = self.backup_manager.get_backup_path()
        # Show example format: backup_cursor_YYYYMMDD_HHMMSS
        example_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        cursor_backup_example = f"backup_cursor_{example_time}.zip"
        cursor_backup_path = os.path.join(backup_base, cursor_backup_example)
        self.cursor_backup_input = QLineEdit(cursor_backup_path)
        self.cursor_backup_input.setReadOnly(True)
        self.cursor_backup_input.setPlaceholderText("Folder created when backup is performed")
        self.cursor_backup_row.addWidget(self.cursor_backup_input, 1)
        self.open_cursor_backup_btn = QPushButton("📁 Select Folder")
        self.open_cursor_backup_btn.setMaximumWidth(110)
        self.open_cursor_backup_btn.clicked.connect(lambda: self.open_backup_folder("cursor"))
        self.cursor_backup_row.addWidget(self.open_cursor_backup_btn)
        backup_layout.addLayout(self.cursor_backup_row)
        
        # Windsurf backup
        self.windsurf_backup_row = QHBoxLayout()
        self.windsurf_backup_label = QLabel("Windsurf:")
        self.windsurf_backup_row.addWidget(self.windsurf_backup_label)
        windsurf_backup_example = f"backup_windsurf_{example_time}.zip"
        windsurf_backup_path = os.path.join(backup_base, windsurf_backup_example)
        self.windsurf_backup_input = QLineEdit(windsurf_backup_path)
        self.windsurf_backup_input.setReadOnly(True)
        self.windsurf_backup_input.setPlaceholderText("Folder created when backup is performed")
        self.windsurf_backup_row.addWidget(self.windsurf_backup_input, 1)
        self.open_windsurf_backup_btn = QPushButton("📁 Select Folder")
        self.open_windsurf_backup_btn.setMaximumWidth(110)
        self.open_windsurf_backup_btn.clicked.connect(lambda: self.open_backup_folder("windsurf"))
        self.windsurf_backup_row.addWidget(self.open_windsurf_backup_btn)
        backup_layout.addLayout(self.windsurf_backup_row)
        
        # Initially hide backup paths and info since checkbox is unchecked
        self.set_backup_paths_visibility(False)
        
        layout.addWidget(backup_group)
    
    def on_backup_toggle_changed(self, state):
        """Handle backup checkbox state change."""
        is_checked = state == 2  # Qt.CheckState.Checked
        self.set_backup_paths_visibility(is_checked)
    
    def set_backup_paths_visibility(self, visible: bool):
        """Show or hide backup path widgets."""
        # Hide/show info label
        self.backup_info_label.setVisible(visible)
        
        # Hide/show cursor backup widgets
        self.cursor_backup_label.setVisible(visible)
        self.cursor_backup_input.setVisible(visible)
        self.open_cursor_backup_btn.setVisible(visible)
        
        # Hide/show windsurf backup widgets
        self.windsurf_backup_label.setVisible(visible)
        self.windsurf_backup_input.setVisible(visible)
        self.open_windsurf_backup_btn.setVisible(visible)
    
    def apply_dark_theme_to_dialog(self, dialog):
        """Apply dark theme to any dialog."""
        dialog.setStyleSheet("""
            QMessageBox, QDialog {
                background-color: #2b2b2b;
                color: #ffffff;
            }
            QMessageBox QLabel, QDialog QLabel {
                color: #ffffff;
                background-color: transparent;
            }
            QMessageBox QPushButton, QDialog QPushButton {
                background-color: #404040;
                color: #ffffff;
                border: 1px solid #555555;
                padding: 8px 16px;
                border-radius: 4px;
                min-width: 80px;
            }
            QMessageBox QPushButton:hover, QDialog QPushButton:hover {
                background-color: #505050;
            }
            QMessageBox QPushButton:pressed, QDialog QPushButton:pressed {
                background-color: #353535;
            }
        """)
    
    def open_program_folder(self, app_name: str):
        """Open program data folder in explorer."""
        path = self.windsurf_path_input.text() if app_name == "windsurf" else self.cursor_path_input.text()
        if path and path != "Not detected" and os.path.exists(path):
            os.startfile(path)
            self.log(f"📂 Opened {app_name.title()} folder: {path}")
        else:
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("No Path")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText(f"{app_name.title()} path not detected or doesn't exist")
            self.apply_dark_theme_to_dialog(warning_box)
            warning_box.exec()
    
    def open_program_executable(self, app_name: str):
        """Launch the program executable without admin privileges."""
        # Common executable paths
        if app_name == "windsurf":
            exe_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Windsurf\Windsurf.exe"),
                os.path.expandvars(r"%APPDATA%\Codeium\Windsurf\Windsurf.exe"),
                r"C:\Program Files\Windsurf\Windsurf.exe"
            ]
        elif app_name == "cursor":
            exe_paths = [
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\cursor\Cursor.exe"),
                os.path.expandvars(r"%APPDATA%\Cursor\Cursor.exe"),
                r"C:\Program Files\Cursor\Cursor.exe"
            ]
        else:
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("Unknown App")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText(f"Unknown application: {app_name}")
            self.apply_dark_theme_to_dialog(warning_box)
            warning_box.exec()
            return
        
        # Try to find and launch the executable without admin privileges
        for exe_path in exe_paths:
            if os.path.exists(exe_path):
                try:
                    # Launch without admin privileges using subprocess
                    import subprocess
                    # Use CREATE_NEW_PROCESS_GROUP to avoid inheriting admin privileges
                    subprocess.Popen([exe_path], creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
                    self.log(f"🚀 Launched {app_name.title()} (non-admin) from: {exe_path}")
                    return
                except Exception as e:
                    self.log(f"❌ Failed to launch {app_name.title()}: {e}")
                    continue
        
        # If no executable found
        warning_box = QMessageBox(self)
        warning_box.setWindowTitle("Not Found")
        warning_box.setIcon(QMessageBox.Icon.Warning)
        warning_box.setText(f"{app_name.title()} executable not found in common locations")
        self.apply_dark_theme_to_dialog(warning_box)
        warning_box.exec()
    
    def kill_program(self, app_name: str):
        """Kill program processes with confirmation."""
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Kill")
        msg_box.setIcon(QMessageBox.Icon.Question)
        msg_box.setText(f"⚠ Kill {app_name.title()} processes?\n\nThis will forcefully close the application.")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        self.apply_dark_theme_to_dialog(msg_box)
        
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            self.log(f"⛔ Killing {app_name.title()} processes...")
            success, msg = self.app_manager.kill_app_process(app_name)
            self.log(msg)
            if success:
                success_box = QMessageBox(self)
                success_box.setWindowTitle("Success")
                success_box.setIcon(QMessageBox.Icon.Information)
                success_box.setText(msg)
                self.apply_dark_theme_to_dialog(success_box)
                success_box.exec()
            else:
                error_box = QMessageBox(self)
                error_box.setWindowTitle("Error")
                error_box.setIcon(QMessageBox.Icon.Critical)
                error_box.setText(msg)
                self.apply_dark_theme_to_dialog(error_box)
                error_box.exec()
            # Refresh app status
            if self.refresh_callback:
                self.refresh_callback()
    
    def open_backup_folder(self, app_name: str):
        """Open backup base folder in explorer."""
        backup_base = self.backup_manager.get_backup_path()
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(backup_base):
            os.makedirs(backup_base, exist_ok=True)
        
        os.startfile(backup_base)
        self.log(f"📂 Opened backup folder: {backup_base}")
    
    def restore_backup_with_dialog(self, app_name: str, backup_path: str):
        """Restore backup and show launch dialog."""
        app_info = self.app_manager.get_app_info(app_name)
        if not app_info or not app_info.get("installed", False):
            self.log(f"⚠️ Cannot restore: {app_name} not found")
            return
        
        target_path = app_info.get("path", "")
        if not target_path or not os.path.exists(target_path):
            self.log(f"⚠️ Cannot restore: Invalid target path for {app_name}")
            return
        
        # Perform restore
        self.log(f"🔄 Restoring backup for {app_name}...")
        success, message = self.backup_manager.restore_backup(backup_path, target_path)
        
        if success:
            self.log(f"✓ {message}")
            
            # Safely update status bar
            try:
                if self.status_bar and not self.status_bar.isHidden():
                    self.status_bar.showMessage("Backup restored successfully", 5000)
            except RuntimeError:
                debug_print("[DEBUG] Status bar already deleted")
            
            # Show launch dialog after successful restore
            self.show_launch_dialog_after_restore(app_name)
        else:
            self.log(f"✗ {message}")
            
            # Safely update status bar
            try:
                if self.status_bar and not self.status_bar.isHidden():
                    self.status_bar.showMessage("Restore failed", 5000)
            except RuntimeError:
                debug_print("[DEBUG] Status bar already deleted")
            
            # Show error dialog
            error_box = QMessageBox(self)
            error_box.setWindowTitle("Restore Failed")
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setText("Failed to restore backup")
            error_box.setInformativeText(message)
            self.apply_dark_theme_to_dialog(error_box)
            error_box.exec()
    
    def reset_app_with_confirm(self, app_name: str):
        """Reset application with confirmation and auto-kill."""
        app_info = self.app_manager.get_app_info(app_name)
        
        if not app_info or not app_info["installed"]:
            warning_box = QMessageBox(self)
            warning_box.setWindowTitle("Not Found")
            warning_box.setIcon(QMessageBox.Icon.Warning)
            warning_box.setText(f"{app_name.title()} is not installed or not detected.")
            self.apply_dark_theme_to_dialog(warning_box)
            warning_box.exec()
            return
        
        # Check if running
        is_running = app_info["running"]
        running_status = f"{app_name.title()} is currently running.\n\n" if is_running else ""
        
        # Create custom message box
        msg_box = QMessageBox(self)
        msg_box.setWindowTitle("Confirm Reset")
        msg_box.setIcon(QMessageBox.Icon.Question)
        
        backup_status = "Create backup in Backups/ResetData" + app_name.title() if self.backup_enabled_checkbox.isChecked() else "Skip backup (backup disabled)"
        
        message = (
            f"Reset {app_name.title()}?\n\n"
            f"{running_status}"
            f"This action will:\n"
            f"  • Kill {app_name.title()} if running\n"
            f"  • {backup_status}\n"
            f"  • Clear all application data\n\n"
            f"Continue?"
        )
        
        msg_box.setText(message)
        msg_box.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        msg_box.setDefaultButton(QMessageBox.StandardButton.No)
        self.apply_dark_theme_to_dialog(msg_box)
        
        reply = msg_box.exec()
        
        if reply == QMessageBox.StandardButton.Yes:
            self.perform_reset(app_name)
    
    def perform_reset(self, app_name: str):
        """Perform reset operation in background thread."""
        debug_print(f"[DEBUG] perform_reset called for {app_name}")
        self.log(f"\n{'='*50}")
        self.log(f"Starting reset for {app_name.title()}...")
        self.log(f"{'='*50}")
        
        # Store app name for dialog
        self.last_reset_app = app_name
        debug_print(f"[DEBUG] Stored last_reset_app: {self.last_reset_app}")
        
        # Disable buttons during reset
        self.disable_all_buttons()
        
        # Show progress bar
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Get backup settings
        create_backup = self.backup_enabled_checkbox.isChecked()
        backup_folder = None
        if create_backup and hasattr(self, 'backup_folder_input'):
            backup_folder = self.backup_folder_input.text().strip()
            if not backup_folder:
                backup_folder = None
        
        # Create and start reset thread
        self.reset_thread = ResetThread(
            self.app_manager, 
            self.backup_manager, 
            app_name, 
            create_backup, 
            backup_folder
        )
        self.reset_thread.progress.connect(self.log)
        self.reset_thread.finished.connect(self.on_reset_finished)
        self.reset_thread.start()
    
    def on_reset_finished(self, success: bool, message: str):
        """Handle reset completion."""
        debug_print(f"[DEBUG] on_reset_finished called - success: {success}, message: {message}")
        
        try:
            self.progress_bar.setVisible(False)
        except RuntimeError:
            debug_print("[DEBUG] Progress bar already deleted")
        
        try:
            self.enable_all_buttons()
        except RuntimeError:
            debug_print("[DEBUG] Buttons already deleted")
        
        if success:
            self.log(f"✓ {message}")
            
            # Safely update status bar
            try:
                if self.status_bar and not self.status_bar.isHidden():
                    self.status_bar.showMessage("Reset completed successfully", 5000)
            except RuntimeError:
                debug_print("[DEBUG] Status bar already deleted, skipping status update")
            
            debug_print("[DEBUG] Reset successful, showing launch dialog...")
            
            # Show launch dialog after successful reset
            self.show_launch_dialog_after_reset()
            debug_print("[DEBUG] Launch dialog completed")
        else:
            self.log(f"✗ {message}")
            
            # Safely update status bar
            try:
                if self.status_bar and not self.status_bar.isHidden():
                    self.status_bar.showMessage("Reset failed", 5000)
            except RuntimeError:
                debug_print("[DEBUG] Status bar already deleted, skipping status update")
            
            debug_print(f"[DEBUG] Reset failed: {message}")
            error_box = QMessageBox(self)
            error_box.setWindowTitle("Error")
            error_box.setIcon(QMessageBox.Icon.Critical)
            error_box.setText(message)
            self.apply_dark_theme_to_dialog(error_box)
            error_box.exec()
            debug_print("[DEBUG] Error dialog closed")
    
    def show_launch_dialog_after_reset(self):
        """Show dialog to launch application after reset completion."""
        debug_print("[DEBUG] show_launch_dialog_after_reset called")
        # Get the app name from the last reset operation
        app_name = getattr(self, 'last_reset_app', None)
        debug_print(f"[DEBUG] last_reset_app: {app_name}")
        if not app_name:
            debug_print("[DEBUG] No app_name found, returning early")
            return
        
        app_info = self.app_manager.get_app_info(app_name)
        display_name = app_info.get('display_name', app_name.title()) if app_info else app_name.title()
        debug_print(f"[DEBUG] Creating launch dialog for {display_name}")
        
        # Create custom dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("✅ Clear Data Complete")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(f"🎉 {display_name} data cleared successfully!")
        dialog.setInformativeText(f"Would you like to open {display_name} now?")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        # Apply dark theme
        self.apply_dark_theme_to_dialog(dialog)
        
        debug_print("[DEBUG] Showing launch dialog...")
        # Show dialog and handle response
        reply = dialog.exec()
        debug_print(f"[DEBUG] Dialog reply: {reply}")
        
        if reply == QMessageBox.StandardButton.Yes:
            debug_print(f"[DEBUG] User chose Yes, launching {display_name}")
            self.launch_application(app_name, display_name)
        else:
            debug_print("[DEBUG] User chose No or closed dialog")
    
    def show_launch_dialog_after_restore(self, app_name: str):
        """Show dialog to launch application after backup restoration."""
        app_info = self.app_manager.get_app_info(app_name)
        display_name = app_info.get('display_name', app_name.title()) if app_info else app_name.title()
        
        # Create custom dialog
        dialog = QMessageBox(self)
        dialog.setWindowTitle("✅ Restore Complete")
        dialog.setIcon(QMessageBox.Icon.Question)
        dialog.setText(f"🎉 {display_name} backup restored successfully!")
        dialog.setInformativeText(f"Would you like to open {display_name} now?")
        dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
        
        # Apply dark theme
        self.apply_dark_theme_to_dialog(dialog)
        
        # Show dialog and handle response
        reply = dialog.exec()
        if reply == QMessageBox.StandardButton.Yes:
            self.launch_application(app_name, display_name)
    
    def launch_application(self, app_name: str, display_name: str):
        """Launch the specified application."""
        debug_print(f"[DEBUG] launch_application called for {app_name} ({display_name})")
        try:
            debug_print(f"[DEBUG] Calling app_manager.launch_application({app_name})")
            success, message = self.app_manager.launch_application(app_name)
            debug_print(f"[DEBUG] Launch result - success: {success}, message: {message}")
            if success:
                self.log(f"🚀 {message}")
                
                # Safely update status bar
                try:
                    if self.status_bar and not self.status_bar.isHidden():
                        self.status_bar.showMessage(f"Launched {display_name}", 3000)
                except RuntimeError:
                    debug_print("[DEBUG] Status bar already deleted")
                
                debug_print(f"[DEBUG] Application {display_name} launched successfully")
            else:
                self.log(f"⚠️ {message}")
                debug_print(f"[DEBUG] Launch failed: {message}")
                error_dialog = QMessageBox(self)
                error_dialog.setWindowTitle("Launch Failed")
                error_dialog.setIcon(QMessageBox.Icon.Warning)
                error_dialog.setText(f"Could not launch {display_name}")
                error_dialog.setInformativeText(message)
                self.apply_dark_theme_to_dialog(error_dialog)
                error_dialog.exec()
                debug_print("[DEBUG] Launch failed dialog closed")
        except Exception as e:
            debug_print(f"[DEBUG] Exception in launch_application: {str(e)}")
            if DEBUG_MODE:
                import traceback
                traceback.print_exc()
            self.log(f"❌ Failed to launch {display_name}: {str(e)}")
    
    def enable_all_buttons(self):
        """Enable all action buttons."""
        self.reset_windsurf_btn.setEnabled(True)
        self.reset_cursor_btn.setEnabled(True)
        self.clear_log_btn.setEnabled(True)
        self.open_windsurf_program_btn.setEnabled(True)
        self.open_windsurf_btn.setEnabled(True)
        self.kill_windsurf_program_btn.setEnabled(True)
        self.open_cursor_program_btn.setEnabled(True)
        self.open_cursor_btn.setEnabled(True)
        self.kill_cursor_program_btn.setEnabled(True)
    
    def disable_all_buttons(self):
        """Disable all action buttons."""
        self.reset_windsurf_btn.setEnabled(False)
        self.reset_cursor_btn.setEnabled(False)
        self.clear_log_btn.setEnabled(False)
        self.open_windsurf_program_btn.setEnabled(False)
        self.open_windsurf_btn.setEnabled(False)
        self.kill_windsurf_program_btn.setEnabled(False)
        self.open_cursor_program_btn.setEnabled(False)
        self.open_cursor_btn.setEnabled(False)
        self.kill_cursor_program_btn.setEnabled(False)
    
    def update_app_paths(self, detected_apps):
        """Update the application path displays."""
        self.detected_apps = detected_apps
        
        # Update Windsurf program path
        if 'windsurf' in detected_apps:
            app_info = detected_apps['windsurf']
            if app_info['installed'] and app_info['path']:
                self.windsurf_path_input.setText(app_info['path'])
            else:
                self.windsurf_path_input.setText("Not detected")
        
        # Update Cursor program path
        if 'cursor' in detected_apps:
            app_info = detected_apps['cursor']
            if app_info['installed'] and app_info['path']:
                self.cursor_path_input.setText(app_info['path'])
            else:
                self.cursor_path_input.setText("Not detected")
