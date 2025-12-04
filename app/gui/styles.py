"""Dark theme styles for SurfManager."""

DARK_STYLE = """
QMainWindow { background-color: #1e1e1e; }

QTabWidget::pane { border: 1px solid #3d3d3d; background-color: #252526; border-radius: 4px; }
QTabBar::tab { background-color: #2d2d30; color: #ccc; padding: 6px 16px; margin-right: 2px; border-top-left-radius: 4px; border-top-right-radius: 4px; min-width: 100px; }
QTabBar::tab:selected { background-color: #404040; color: #e0e0e0; }
QTabBar::tab:hover:!selected { background-color: #3d3d3d; }

QGroupBox { border: 1px solid #3d3d3d; border-radius: 4px; margin-top: 8px; padding-top: 8px; font-weight: bold; color: #ccc; background-color: #252526; }
QGroupBox::title { subcontrol-origin: margin; left: 8px; padding: 0 4px; }

QLabel { color: #ccc; background-color: transparent; padding: 2px; }

QPushButton { background-color: #404040; color: #e0e0e0; border: 1px solid #555; padding: 6px 12px; border-radius: 3px; font-weight: bold; min-height: 24px; }
QPushButton:hover { background-color: #505050; }
QPushButton:pressed { background-color: #353535; }
QPushButton:disabled { background-color: #3d3d3d; color: #666; }

QTextEdit, QPlainTextEdit { background-color: #1e1e1e; color: #d4d4d4; border: 1px solid #3d3d3d; border-radius: 3px; padding: 4px; font-family: Consolas, monospace; font-size: 9pt; }

QLineEdit { background-color: #3c3c3c; color: #ccc; border: 1px solid #3d3d3d; border-radius: 3px; padding: 4px; }
QLineEdit:focus { border-color: #505050; }

QComboBox { background-color: #3c3c3c; color: #ccc; border: 1px solid #3d3d3d; border-radius: 3px; padding: 4px; }
QComboBox:hover { border-color: #505050; }
QComboBox::drop-down { border: none; }
QComboBox QAbstractItemView { background-color: #252526; color: #ccc; selection-background-color: #404040; border: 1px solid #3d3d3d; }

QTableWidget { background-color: #252526; color: #ccc; border: 1px solid #3d3d3d; border-radius: 3px; gridline-color: #3d3d3d; }
QTableWidget::item { padding: 4px; border: none; background-color: #252526; }
QTableWidget::item:selected { background-color: #404040; color: #e0e0e0; }
QTableWidget::item:hover { background-color: #2a2d2e; }
QHeaderView::section { background-color: #2d2d30; color: #ccc; border: 1px solid #3d3d3d; padding: 6px; font-weight: bold; }

QProgressBar { border: 1px solid #3d3d3d; border-radius: 3px; text-align: center; background-color: #252526; color: white; height: 18px; }
QProgressBar::chunk { background-color: #505050; border-radius: 2px; }

QScrollBar:vertical { background-color: #1e1e1e; width: 12px; }
QScrollBar::handle:vertical { background-color: #424242; min-height: 20px; border-radius: 6px; }
QScrollBar::handle:vertical:hover { background-color: #4e4e4e; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }

QStatusBar { background-color: #404040; color: #e0e0e0; font-weight: bold; }
QStatusBar::item { border: none; }

QCheckBox { color: #ccc; spacing: 6px; }
QCheckBox::indicator { width: 16px; height: 16px; border: 1px solid #3d3d3d; border-radius: 3px; background-color: #252526; }
QCheckBox::indicator:checked { background-color: #505050; border-color: #505050; }
"""

# Sub-tab style for nested tabs (Data Management sub-tabs)
SUB_TAB_STYLE = """
QTabWidget::pane {
    border: 1px solid #3d3d3d;
    background-color: #1e1e1e;
}
QTabBar::tab {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 6px 14px;
    margin-right: 1px;
}
QTabBar::tab:selected {
    background-color: #252526;
    color: #00ff41;
    border-bottom: 2px solid #00ff41;
}
QTabBar::tab:hover:!selected {
    background-color: #3d3d3d;
}
"""
