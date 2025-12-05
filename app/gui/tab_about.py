"""About tab for SurfManager."""
import os
import platform
from datetime import datetime, timezone
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout
)
from PyQt6.QtCore import Qt
from app import __version__


def get_time_ago(release_date):
    """Calculate time ago from release date."""
    now = datetime.now(timezone.utc)
    diff = now - release_date
    
    days = diff.days
    weeks = days / 7
    months = days / 30
    years = days / 365
    
    if years >= 1:
        count = int(years)
        return f"{count} year{'s' if count > 1 else ''} ago"
    elif months >= 1:
        count = int(months)
        return f"{count} month{'s' if count > 1 else ''} ago"
    elif weeks >= 1:
        count = int(weeks)
        return f"{count} week{'s' if count > 1 else ''} ago"
    elif days >= 1:
        count = int(days)
        return f"{count} day{'s' if count > 1 else ''} ago"
    else:
        return "today"


class AboutTab(QWidget):
    """About App tab with hacker style."""
    
    def __init__(self):
        super().__init__()
        self._init_ui()
    
    def _init_ui(self):
        """Initialize About UI."""
        layout = QVBoxLayout()
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)
        self.setLayout(layout)
        
        # Add stretch at top for vertical centering
        layout.addStretch()
        
        # ASCII Art Title
        ascii_title = QLabel("""<pre style='color: #0d7377; font-family: Consolas, monospace; font-size: 9px;'>
███████╗██╗   ██╗██████╗ ███████╗███╗   ███╗ █████╗ ███╗   ██╗ █████╗  ██████╗ ███████╗██████╗ 
██╔════╝██║   ██║██╔══██╗██╔════╝████╗ ████║██╔══██╗████╗  ██║██╔══██╗██╔════╝ ██╔════╝██╔══██╗
███████╗██║   ██║██████╔╝█████╗  ██╔████╔██║███████║██╔██╗ ██║███████║██║  ███╗█████╗  ██████╔╝
╚════██║██║   ██║██╔══██╗██╔══╝  ██║╚██╔╝██║██╔══██║██║╚██╗██║██╔══██║██║   ██║██╔══╝  ██╔══██╗
███████║╚██████╔╝██║  ██║██║     ██║ ╚═╝ ██║██║  ██║██║ ╚████║██║  ██║╚██████╔╝███████╗██║  ██║
╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝     ╚═╝     ╚═╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═╝
</pre>""")
        ascii_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(ascii_title)
        
        # Version
        version_label = QLabel(f"<h2 style='color: #0d7377;'>Version {__version__}</h2>")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)
        
        # Release Date with time ago
        release_date = datetime(2025, 12, 5, 22, 0, 0, tzinfo=timezone.utc)
        time_ago = get_time_ago(release_date)
        release_label = QLabel(
            f"<p style='color: #888; font-size: 12px;'>"
            f"Released: 12/05/2025 "
            f"<span style='color: #666;'>({time_ago})</span>"
            f"</p>"
        )
        release_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(release_label)
        
        # Description
        desc_label = QLabel("""<p style='color: #cccccc; font-size: 14px;'>
        Advanced Session and Data Management Tool<br>
        for VSCode-based AI Editors
        </p>""")
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(desc_label)
        
        # Info Grid
        info_widget = QWidget()
        info_layout = QGridLayout()
        info_layout.setSpacing(15)
        info_widget.setLayout(info_layout)
        
        info_items = [
            ("Author:", "risunCode"),
            ("License:", "MIT"),
            ("Build:", "Stable"),
            ("Platform:", platform.system())
        ]
        
        for i, (label, value) in enumerate(info_items):
            lbl = QLabel(f"<span style='color: #0d7377; font-weight: bold;'>{label}</span>")
            lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
            val = QLabel(f"<span style='color: #cccccc;'>{value}</span>")
            val.setAlignment(Qt.AlignmentFlag.AlignLeft)
            
            row = i // 2
            col = (i % 2) * 2
            info_layout.addWidget(lbl, row, col)
            info_layout.addWidget(val, row, col + 1)
        
        # Center the info widget
        info_container = QWidget()
        info_container_layout = QHBoxLayout()
        info_container_layout.addStretch()
        info_container_layout.addWidget(info_widget)
        info_container_layout.addStretch()
        info_container.setLayout(info_container_layout)
        
        layout.addWidget(info_container)
        
        # Features
        features_label = QLabel("""<p style='color: #888; font-size: 11px; text-align: center;'>
        Session Backup • Data Reset • Process Management<br>
        Dynamic Configuration • Cross-platform Ready
        </p>""")
        features_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(features_label)
        
        # Repository link
        repo_label = QLabel("""<p style='color: #666; font-size: 10px;'>
        <a href='https://github.com/risunCode/SurfManager' style='color: #0d7377;'>
        github.com/risunCode/SurfManager
        </a>
        </p>""")
        repo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        repo_label.setOpenExternalLinks(True)
        layout.addWidget(repo_label)
        
        # Add stretch at bottom
        layout.addStretch()
