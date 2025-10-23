"""Info tab with documentation and creator information for SurfManager."""
import webbrowser
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QScrollArea, QFrame, QTextEdit, QGroupBox, QGridLayout
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPixmap, QPalette


class InfoTab(QWidget):
    """Info tab widget with documentation and creator information."""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
    
    def init_ui(self):
        """Initialize the info tab UI."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)
        
        # Top section with title and GitHub button
        top_layout = QHBoxLayout()
        
        # Title section
        title_widget = QWidget()
        title_layout = QVBoxLayout()
        title_widget.setLayout(title_layout)
        
        # App title
        title_label = QLabel("🏄 SurfManager")
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #63b3ed; margin: 20px 0px 10px 0px;")
        title_layout.addWidget(title_label)
        
        # Creator info
        creator_label = QLabel("by risunCode")
        creator_font = QFont()
        creator_font.setPointSize(16)
        creator_label.setFont(creator_font)
        creator_label.setStyleSheet("color: #a0aec0; margin: 0px 0px 20px 0px;")
        title_layout.addWidget(creator_label)
        
        # Add title widget to left side
        top_layout.addWidget(title_widget)
        
        # Add stretch to push button to right
        top_layout.addStretch()
        
        # GitHub button on the right
        github_btn = QPushButton("🔗 GitHub")
        github_btn.setFixedSize(120, 40)
        github_btn.setStyleSheet("""
            QPushButton {
                background-color: #4299e1;
                color: white;
                border: none;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 14px;
                margin: 20px;
            }
            QPushButton:hover {
                background-color: #3182ce;
                transform: translateY(-1px);
            }
            QPushButton:pressed {
                background-color: #2c5282;
            }
        """)
        github_btn.clicked.connect(self.open_github)
        top_layout.addWidget(github_btn, 0, Qt.AlignmentFlag.AlignTop)
        
        main_layout.addLayout(top_layout)
        
        # Add stretch to center the content
        main_layout.addStretch()
    
    
    def open_github(self):
        """Open GitHub profile in browser."""
        try:
            webbrowser.open("https://github.com/risunCode/SurfManager")
        except Exception as e:
            print(f"Error opening GitHub: {e}")
