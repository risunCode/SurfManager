"""Compact modern styling for MinimalSurfGUI."""

COMPACT_DARK_STYLE = """
/* Main Window */
QMainWindow {
    background-color: #1e1e1e;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #3d3d3d;
    background-color: #252526;
    border-radius: 4px;
}

QTabBar::tab {
    background-color: #2d2d30;
    color: #cccccc;
    padding: 6px 16px;
    margin-right: 2px;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    min-width: 100px;
}

QTabBar::tab:selected {
    background-color: #404040;
    color: #e0e0e0;
}

QTabBar::tab:hover:!selected {
    background-color: #3d3d3d;
}

/* Group Box */
QGroupBox {
    border: 1px solid #3d3d3d;
    border-radius: 4px;
    margin-top: 8px;
    padding-top: 8px;
    font-weight: bold;
    color: #cccccc;
    background-color: #252526;
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 8px;
    padding: 0 4px;
}

/* Labels */
QLabel {
    color: #cccccc;
    background-color: transparent;
    padding: 2px;
}

/* Buttons */
QPushButton {
    background-color: #404040;
    color: #e0e0e0;
    border: 1px solid #555555;
    padding: 6px 12px;
    border-radius: 3px;
    font-weight: bold;
    min-height: 24px;
}

QPushButton:hover {
    background-color: #505050;
}

QPushButton:pressed {
    background-color: #353535;
}

QPushButton:disabled {
    background-color: #3d3d3d;
    color: #666666;
}

QPushButton#dangerButton {
    background-color: #c72e0f;
}

QPushButton#dangerButton:hover {
    background-color: #e03e1c;
}

QPushButton#successButton {
    background-color: #0e7c0e;
}

QPushButton#successButton:hover {
    background-color: #128a12;
}

/* Text Edit / Plain Text Edit */
QTextEdit, QPlainTextEdit {
    background-color: #1e1e1e;
    color: #d4d4d4;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 4px;
    font-family: 'Consolas', 'Courier New', monospace;
    font-size: 9pt;
}

/* List Widget */
QListWidget {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 2px;
}

QListWidget::item {
    padding: 4px;
    border-radius: 2px;
}

QListWidget::item:selected {
    background-color: #404040;
}

QListWidget::item:hover {
    background-color: #2a2d2e;
}

/* Progress Bar */
QProgressBar {
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    text-align: center;
    background-color: #252526;
    color: white;
    height: 18px;
}

QProgressBar::chunk {
    background-color: #505050;
    border-radius: 2px;
}

/* Scroll Bar */
QScrollBar:vertical {
    background-color: #1e1e1e;
    width: 12px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background-color: #424242;
    min-height: 20px;
    border-radius: 6px;
}

QScrollBar::handle:vertical:hover {
    background-color: #4e4e4e;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

/* Status Bar */
QStatusBar {
    background-color: #404040;
    color: #e0e0e0;
    font-weight: bold;
}

QStatusBar::item {
    border: none;
}

/* Check Box */
QCheckBox {
    color: #cccccc;
    spacing: 6px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    background-color: #252526;
}

QCheckBox::indicator:checked {
    background-color: #505050;
    border-color: #505050;
}

QCheckBox::indicator:hover {
    border-color: #505050;
}

/* Line Edit */
QLineEdit {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 4px;
}

QLineEdit:focus {
    border-color: #505050;
}

/* Combo Box */
QComboBox {
    background-color: #3c3c3c;
    color: #cccccc;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    padding: 4px;
}

QComboBox:hover {
    border-color: #505050;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #252526;
    color: #cccccc;
    selection-background-color: #404040;
    border: 1px solid #3d3d3d;
}

/* Table Widget */
QTableWidget {
    background-color: #252526;
    color: #cccccc;
    border: 1px solid #3d3d3d;
    border-radius: 3px;
    gridline-color: #3d3d3d;
    alternate-background-color: #252526;
}

QTableWidget::item {
    padding: 4px;
    border: none;
    background-color: #252526;
    color: #cccccc;
}

QTableWidget::item:selected {
    background-color: #404040;
    color: #e0e0e0;
}

QTableWidget::item:hover {
    background-color: #2a2d2e;
}

QTableWidget::item:alternate {
    background-color: #252526;
}

QHeaderView::section {
    background-color: #2d2d30;
    color: #cccccc;
    border: 1px solid #3d3d3d;
    padding: 6px;
    font-weight: bold;
}

QHeaderView::section:hover {
    background-color: #3d3d3d;
}
"""
