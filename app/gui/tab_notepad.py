"""Notepad tab for SurfManager - Quick notes management."""
import os
import json
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QListWidget, QListWidgetItem, QTextEdit, QPushButton,
    QLabel, QLineEdit, QMessageBox, QInputDialog, QFrame,
    QMenu
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QAction
import qtawesome as qta
from app.core.config import ConfigManager


class NotepadTab(QWidget):
    """Notepad tab for quick notes management."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = ConfigManager()
        self.notes_dir = os.path.join(self.config.surfmanager_path, "notes")
        os.makedirs(self.notes_dir, exist_ok=True)
        
        self.current_note = None
        self.unsaved_changes = False
        
        self._init_ui()
        self._load_notes_list()
    
    def _init_ui(self):
        """Initialize the UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Create splitter for sidebar and content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # === SIDEBAR ===
        sidebar = QFrame()
        sidebar.setFixedWidth(250)
        sidebar.setStyleSheet("""
            QFrame {
                background-color: #1e1e1e;
                border-right: 1px solid #333;
            }
        """)
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(10, 10, 10, 10)
        sidebar_layout.setSpacing(10)
        
        # Sidebar header
        header = QLabel("Notes")
        header.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        header.setStyleSheet("color: #fff; padding: 5px 0;")
        sidebar_layout.addWidget(header)
        
        # Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(5)
        
        self.btn_new = QPushButton()
        self.btn_new.setIcon(qta.icon('fa5s.plus', color='#4CAF50'))
        self.btn_new.setToolTip("New Note")
        self.btn_new.setFixedSize(32, 32)
        self.btn_new.clicked.connect(self._new_note)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        toolbar.addWidget(self.btn_new)
        
        self.btn_save = QPushButton()
        self.btn_save.setIcon(qta.icon('fa5s.save', color='#2196F3'))
        self.btn_save.setToolTip("Save Note")
        self.btn_save.setFixedSize(32, 32)
        self.btn_save.clicked.connect(self._save_note)
        self.btn_save.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        toolbar.addWidget(self.btn_save)
        
        self.btn_delete = QPushButton()
        self.btn_delete.setIcon(qta.icon('fa5s.trash', color='#f44336'))
        self.btn_delete.setToolTip("Delete Note")
        self.btn_delete.setFixedSize(32, 32)
        self.btn_delete.clicked.connect(self._delete_note)
        self.btn_delete.setStyleSheet("""
            QPushButton {
                background-color: #2d2d2d;
                border: 1px solid #444;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #3d3d3d;
            }
        """)
        toolbar.addWidget(self.btn_delete)
        
        toolbar.addStretch()
        sidebar_layout.addLayout(toolbar)
        
        # Notes list
        self.notes_list = QListWidget()
        self.notes_list.setStyleSheet("""
            QListWidget {
                background-color: #252525;
                border: 1px solid #333;
                border-radius: 4px;
                padding: 5px;
            }
            QListWidget::item {
                color: #ddd;
                padding: 8px;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:selected {
                background-color: #0d47a1;
                color: #fff;
            }
            QListWidget::item:hover {
                background-color: #333;
            }
        """)
        self.notes_list.itemClicked.connect(self._on_note_selected)
        self.notes_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.notes_list.customContextMenuRequested.connect(self._show_context_menu)
        sidebar_layout.addWidget(self.notes_list)
        
        # Notes count
        self.count_label = QLabel("0 notes")
        self.count_label.setStyleSheet("color: #888; font-size: 11px;")
        sidebar_layout.addWidget(self.count_label)
        
        splitter.addWidget(sidebar)
        
        # === CONTENT AREA ===
        content = QFrame()
        content.setStyleSheet("""
            QFrame {
                background-color: #1a1a1a;
            }
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(10)
        
        # Title bar
        title_bar = QHBoxLayout()
        
        self.title_input = QLineEdit()
        self.title_input.setPlaceholderText("Note title...")
        self.title_input.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        self.title_input.setStyleSheet("""
            QLineEdit {
                background-color: transparent;
                border: none;
                border-bottom: 2px solid #333;
                color: #fff;
                padding: 10px 0;
            }
            QLineEdit:focus {
                border-bottom: 2px solid #2196F3;
            }
        """)
        self.title_input.textChanged.connect(self._on_content_changed)
        title_bar.addWidget(self.title_input)
        
        content_layout.addLayout(title_bar)
        
        # Modified label
        self.modified_label = QLabel("")
        self.modified_label.setStyleSheet("color: #666; font-size: 11px;")
        content_layout.addWidget(self.modified_label)
        
        # Editor
        self.editor = QTextEdit()
        self.editor.setPlaceholderText("Start writing your note here...")
        self.editor.setFont(QFont("Consolas", 12))
        self.editor.setStyleSheet("""
            QTextEdit {
                background-color: #252525;
                border: 1px solid #333;
                border-radius: 8px;
                color: #ddd;
                padding: 15px;
                selection-background-color: #0d47a1;
            }
        """)
        self.editor.textChanged.connect(self._on_content_changed)
        content_layout.addWidget(self.editor)
        
        # Status bar
        status_bar = QHBoxLayout()
        
        self.char_count = QLabel("0 characters")
        self.char_count.setStyleSheet("color: #666; font-size: 11px;")
        status_bar.addWidget(self.char_count)
        
        status_bar.addStretch()
        
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #4CAF50; font-size: 11px;")
        status_bar.addWidget(self.status_label)
        
        content_layout.addLayout(status_bar)
        
        splitter.addWidget(content)
        
        # Set splitter sizes
        splitter.setSizes([250, 750])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        
        layout.addWidget(splitter)
        
        # Clear editor on start
        self._clear_editor()
    
    def _load_notes_list(self):
        """Load all notes from the notes directory."""
        self.notes_list.clear()
        
        notes = []
        if os.path.exists(self.notes_dir):
            for filename in os.listdir(self.notes_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.notes_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            notes.append({
                                'id': filename[:-5],  # Remove .json
                                'title': data.get('title', 'Untitled'),
                                'modified': data.get('modified', ''),
                                'preview': data.get('content', '')[:50]
                            })
                    except:
                        pass
        
        # Sort by modified date (newest first)
        notes.sort(key=lambda x: x['modified'], reverse=True)
        
        for note in notes:
            item = QListWidgetItem(note['title'])
            item.setData(Qt.ItemDataRole.UserRole, note['id'])
            item.setToolTip(f"Modified: {note['modified']}\n{note['preview']}...")
            self.notes_list.addItem(item)
        
        self.count_label.setText(f"{len(notes)} notes")
    
    def _new_note(self):
        """Create a new note."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before creating new note?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_note()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        self._clear_editor()
        self.current_note = None
        self.title_input.setFocus()
        self.status_label.setText("New note")
    
    def _save_note(self):
        """Save the current note."""
        title = self.title_input.text().strip()
        content = self.editor.toPlainText()
        
        if not title:
            title = "Untitled"
        
        # Generate ID if new note
        if not self.current_note:
            self.current_note = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save note
        note_data = {
            'title': title,
            'content': content,
            'created': datetime.now().isoformat() if not self.current_note else self._get_note_created(),
            'modified': datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        filepath = os.path.join(self.notes_dir, f"{self.current_note}.json")
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(note_data, f, indent=2, ensure_ascii=False)
            
            self.unsaved_changes = False
            self.modified_label.setText(f"Saved: {note_data['modified']}")
            self.status_label.setText("Saved!")
            self._load_notes_list()
            
            # Select the saved note
            for i in range(self.notes_list.count()):
                item = self.notes_list.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == self.current_note:
                    self.notes_list.setCurrentItem(item)
                    break
                    
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save note: {e}")
    
    def _get_note_created(self):
        """Get the created date of current note."""
        if self.current_note:
            filepath = os.path.join(self.notes_dir, f"{self.current_note}.json")
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return data.get('created', datetime.now().isoformat())
                except:
                    pass
        return datetime.now().isoformat()
    
    def _delete_note(self):
        """Delete the current note."""
        if not self.current_note:
            return
        
        reply = QMessageBox.question(
            self, "Delete Note",
            f"Are you sure you want to delete '{self.title_input.text()}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            filepath = os.path.join(self.notes_dir, f"{self.current_note}.json")
            try:
                os.remove(filepath)
                self._clear_editor()
                self.current_note = None
                self._load_notes_list()
                self.status_label.setText("Note deleted")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")
    
    def _on_note_selected(self, item):
        """Handle note selection."""
        if self.unsaved_changes:
            reply = QMessageBox.question(
                self, "Unsaved Changes",
                "You have unsaved changes. Save before switching?",
                QMessageBox.StandardButton.Save | 
                QMessageBox.StandardButton.Discard | 
                QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Save:
                self._save_note()
            elif reply == QMessageBox.StandardButton.Cancel:
                return
        
        note_id = item.data(Qt.ItemDataRole.UserRole)
        self._load_note(note_id)
    
    def _load_note(self, note_id):
        """Load a note by ID."""
        filepath = os.path.join(self.notes_dir, f"{note_id}.json")
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.current_note = note_id
            self.title_input.setText(data.get('title', ''))
            self.editor.setPlainText(data.get('content', ''))
            self.modified_label.setText(f"Modified: {data.get('modified', 'Unknown')}")
            self.unsaved_changes = False
            self.status_label.setText("")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load note: {e}")
    
    def _on_content_changed(self):
        """Handle content changes."""
        self.unsaved_changes = True
        char_count = len(self.editor.toPlainText())
        self.char_count.setText(f"{char_count} characters")
        self.status_label.setText("Unsaved changes")
        self.status_label.setStyleSheet("color: #FFA500; font-size: 11px;")
    
    def _clear_editor(self):
        """Clear the editor."""
        self.title_input.clear()
        self.editor.clear()
        self.modified_label.setText("")
        self.char_count.setText("0 characters")
        self.status_label.setText("")
        self.unsaved_changes = False
        self.notes_list.clearSelection()
    
    def _show_context_menu(self, pos):
        """Show context menu for notes list."""
        item = self.notes_list.itemAt(pos)
        if not item:
            return
        
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #2d2d2d;
                border: 1px solid #444;
                padding: 5px;
            }
            QMenu::item {
                color: #ddd;
                padding: 8px 20px;
            }
            QMenu::item:selected {
                background-color: #0d47a1;
            }
        """)
        
        open_action = QAction("Open", self)
        open_action.triggered.connect(lambda: self._on_note_selected(item))
        menu.addAction(open_action)
        
        rename_action = QAction("Rename", self)
        rename_action.triggered.connect(lambda: self._rename_note(item))
        menu.addAction(rename_action)
        
        menu.addSeparator()
        
        delete_action = QAction("Delete", self)
        delete_action.triggered.connect(lambda: self._delete_note_by_id(item.data(Qt.ItemDataRole.UserRole)))
        menu.addAction(delete_action)
        
        menu.exec(self.notes_list.mapToGlobal(pos))
    
    def _rename_note(self, item):
        """Rename a note."""
        note_id = item.data(Qt.ItemDataRole.UserRole)
        current_title = item.text()
        
        new_title, ok = QInputDialog.getText(
            self, "Rename Note", 
            "Enter new title:",
            text=current_title
        )
        
        if ok and new_title.strip():
            filepath = os.path.join(self.notes_dir, f"{note_id}.json")
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                data['title'] = new_title.strip()
                data['modified'] = datetime.now().strftime("%Y-%m-%d %H:%M")
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                
                self._load_notes_list()
                
                if self.current_note == note_id:
                    self.title_input.setText(new_title.strip())
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to rename: {e}")
    
    def _delete_note_by_id(self, note_id):
        """Delete a note by ID."""
        reply = QMessageBox.question(
            self, "Delete Note",
            "Are you sure you want to delete this note?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            filepath = os.path.join(self.notes_dir, f"{note_id}.json")
            try:
                os.remove(filepath)
                if self.current_note == note_id:
                    self._clear_editor()
                    self.current_note = None
                self._load_notes_list()
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to delete: {e}")
