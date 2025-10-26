"""Splash screen with loading animation for SurfManager."""
import os
import sys
from PyQt6.QtWidgets import QSplashScreen
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPixmap, QPainter, QColor, QFont, QPen
from app.core.audio_manager import AudioManager


class SplashScreen(QSplashScreen):
    """Custom splash screen with loading animation."""
    
    def __init__(self):
        # Create a pixmap for the splash screen
        pixmap = QPixmap(500, 300)
        pixmap.fill(QColor(30, 30, 40))
        super().__init__(pixmap, Qt.WindowType.WindowStaysOnTopHint)
        
        self.setWindowFlag(Qt.WindowType.FramelessWindowHint)
        
        # Progress value
        self.progress = 0
        self.message = "Initializing..."
        
        # Timer for animation
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_progress)
        self.timer.start(30)
        
        # Audio manager
        self.audio_manager = AudioManager()
        
        # Try to load and play startup audio
        self.play_startup_audio()
        
    def update_progress(self):
        """Update progress animation - smooth continuous movement."""
        if self.progress < 100:
            self.progress += 0.5
            if self.progress > 100:
                self.progress = 100
        self.repaint()
    
    def play_startup_audio(self):
        """Play startup audio if available."""
        try:
            self.audio_manager.play_sound('startup', blocking=False)
        except Exception as e:
            print(f"[SplashScreen] Failed to play startup audio: {e}")
    
    
    def drawContents(self, painter: QPainter):
        """Draw custom splash screen contents."""
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Background gradient
        painter.fillRect(self.rect(), QColor(30, 30, 40))
        
        # Title
        title_font = QFont("Segoe UI", 32, QFont.Weight.Bold)
        painter.setFont(title_font)
        painter.setPen(QColor(100, 180, 255))
        painter.drawText(self.rect().adjusted(0, 60, 0, 0), 
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                        "SurfManager")
        
        # Slogan
        slogan_font = QFont("Segoe UI", 11)
        painter.setFont(slogan_font)
        painter.setPen(QColor(180, 180, 200))
        painter.drawText(self.rect().adjusted(0, 120, 0, 0),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop,
                        "Advanced Session & Data Manager")
        
        # Progress bar background
        bar_rect = self.rect().adjusted(100, 180, -100, -80)
        painter.setPen(QPen(QColor(60, 60, 70), 2))
        painter.setBrush(QColor(40, 40, 50))
        painter.drawRoundedRect(bar_rect, 5, 5)
        
        # Progress bar fill (animated)
        progress_width = int((bar_rect.width() - 4) * (self.progress / 100))
        fill_rect = bar_rect.adjusted(2, 2, -bar_rect.width() + progress_width + 2, -2)
        
        # Gradient for progress bar
        gradient_color = QColor(100, 180, 255)
        painter.setBrush(gradient_color)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(fill_rect, 3, 3)
        
        # Loading message
        msg_font = QFont("Segoe UI", 9)
        painter.setFont(msg_font)
        painter.setPen(QColor(150, 150, 170))
        painter.drawText(self.rect().adjusted(0, 0, 0, -30),
                        Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom,
                        self.message)
    
    def set_message(self, message: str):
        """Set loading message."""
        self.message = message
        self.repaint()
    
    def finish_loading(self, main_window):
        """Finish loading and show main window."""
        self.timer.stop()
        self.finish(main_window)
