"""Splash screen for SurfManager."""
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen


class SplashScreen(QSplashScreen):
    """Custom splash screen with loading animation."""
    
    def __init__(self):
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(30, 30, 40))
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        self.progress = 0
        self.message = "Initializing..."
        
        self.timer = QTimer()
        self.timer.timeout.connect(self._animate)
        self.timer.start(50)  # 50ms is smooth enough, saves CPU
        
    def _animate(self):
        if self.progress < 100:
            self.progress = min(self.progress + 0.5, 100)
        self.repaint()
    
    def drawContents(self, painter: QPainter):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(30, 30, 40))
        
        # Title
        painter.setFont(QFont("Segoe UI", 32, QFont.Weight.Bold))
        painter.setPen(QColor(100, 180, 255))
        painter.drawText(self.rect().adjusted(0, 60, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "SurfManager")
        
        # Slogan
        painter.setFont(QFont("Segoe UI", 11))
        painter.setPen(QColor(180, 180, 200))
        painter.drawText(self.rect().adjusted(0, 120, 0, 0), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop, "Advanced Session & Data Manager")
        
        # Progress bar
        bar = self.rect().adjusted(100, 180, -100, -80)
        painter.setPen(QPen(QColor(60, 60, 70), 2))
        painter.setBrush(QColor(40, 40, 50))
        painter.drawRoundedRect(bar, 5, 5)
        
        fill_width = int((bar.width() - 4) * (self.progress / 100))
        fill = bar.adjusted(2, 2, -bar.width() + fill_width + 2, -2)
        painter.setBrush(QColor(100, 180, 255))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(fill, 3, 3)
        
        # Message
        painter.setFont(QFont("Segoe UI", 9))
        painter.setPen(QColor(150, 150, 170))
        painter.drawText(self.rect().adjusted(0, 0, 0, -30), Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self.message)
    
    def set_message(self, msg: str):
        self.message = msg
        self.repaint()
    
    def finish_loading(self, window):
        self.timer.stop()
        self.finish(window)
