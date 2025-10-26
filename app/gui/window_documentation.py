"""Documentation tab for MinimalSurfGUI."""
import os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QTextEdit,
    QLabel, QSplitter
)
from PyQt6.QtCore import Qt


class DocumentationTab(QWidget):
    """Documentation tab widget."""
    
    def __init__(self):
        super().__init__()
        self.documentation_data = self.load_documentation()
        self.init_ui()
    
    def load_documentation(self):
        """Load documentation from JSON file."""
        try:
            config_path = os.path.join(
                os.path.dirname(os.path.dirname(__file__)),
                'config',
                'documentation.json'
            )
            
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"[Documentation] Failed to load: {e}")
        
        # Fallback default
        return {
            "title": "MinimalSurfGUI Documentation",
            "version": "1.0.0",
            "sections": [
                {
                    "title": "Welcome",
                    "content": "Documentation not found."
                }
            ]
        }
    
    def init_ui(self):
        """Initialize the documentation UI."""
        main_layout = QHBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        self.setLayout(main_layout)
        
        # Create splitter for resizable layout
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side - Table of Contents
        toc_widget = QWidget()
        toc_layout = QVBoxLayout()
        toc_layout.setContentsMargins(10, 10, 10, 10)
        toc_widget.setLayout(toc_layout)
        
        # TOC Header
        toc_header = QLabel("📚 Table of Contents")
        toc_header.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        toc_layout.addWidget(toc_header)
        
        # TOC List
        self.toc_list = QListWidget()
        self.toc_list.setMaximumWidth(250)
        for section in self.documentation_data.get('sections', []):
            self.toc_list.addItem(section['title'])
        
        self.toc_list.currentRowChanged.connect(self.display_section)
        toc_layout.addWidget(self.toc_list)
        
        splitter.addWidget(toc_widget)
        
        # Right side - Content Display
        content_widget = QWidget()
        content_layout = QVBoxLayout()
        content_layout.setContentsMargins(10, 10, 10, 10)
        content_widget.setLayout(content_layout)
        
        # Content Header
        title = self.documentation_data.get('title', 'Documentation')
        version = self.documentation_data.get('version', '1.0.0')
        header = QLabel(f"<h2>{title}</h2><p style='color: #888;'>Version {version}</p>")
        header.setTextFormat(Qt.TextFormat.RichText)
        content_layout.addWidget(header)
        
        # Content Area
        self.content_display = QTextEdit()
        self.content_display.setReadOnly(True)
        content_layout.addWidget(self.content_display)
        
        splitter.addWidget(content_widget)
        
        # Set splitter sizes (25% TOC, 75% Content)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
        
        # Display first section by default
        if self.toc_list.count() > 0:
            self.toc_list.setCurrentRow(0)
    
    def display_section(self, index):
        """Display selected documentation section."""
        if index < 0:
            return
        
        sections = self.documentation_data.get('sections', [])
        if index < len(sections):
            section = sections[index]
            content = f"<h3>{section['title']}</h3><p>{section['content']}</p>"
            self.content_display.setHtml(content)
