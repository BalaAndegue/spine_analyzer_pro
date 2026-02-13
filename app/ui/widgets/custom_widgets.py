
from PySide6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel, 
    QGraphicsDropShadowEffect, QSizePolicy
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QColor, QPalette

class ModernCard(QFrame):
    """
    A reusable card-style container with consistent styling, 
    optional title, and shadow effect.
    """
    def __init__(self, title: str = None, parent=None):
        super().__init__(parent)
        self.setObjectName("ModernCard")
        
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(10)
        
        # Style
        self.setStyleSheet("""
            #ModernCard {
                background-color: #1e1e1e;
                border: 1px solid #333333;
                border-radius: 8px;
            }
        """)
        
        # Add Shadow
        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(15)
        shadow.setColor(QColor(0, 0, 0, 100))
        shadow.setOffset(0, 4)
        self.setGraphicsEffect(shadow)
        
        # Title Section
        if title:
            self.title_label = QLabel(title)
            self.title_label.setStyleSheet("""
                font-weight: bold;
                font-size: 11pt;
                color: #2196f3;
                border-bottom: 2px solid #2d2d2d;
                padding-bottom: 6px;
            """)
            self.layout.addWidget(self.title_label)
            
        # Content Container (so users can add widgets to this)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        self.layout.addWidget(self.content_widget)
        
    def add_widget(self, widget: QWidget):
        """Add a widget to the card's content area"""
        self.content_layout.addWidget(widget)
        
    def add_layout(self, layout):
        """Add a layout to the card's content area"""
        self.content_layout.addLayout(layout)

class StatusLed(QWidget):
    """
    Circular LED indicator for status
    """
    def __init__(self, size=16, color="#4caf50", parent=None):
        super().__init__(parent)
        self.setFixedSize(size, size)
        self._color = color
        self._active = False
        self.update_style()
        
    def set_status(self, active: bool, color: str = None):
        if color:
            self._color = color
        self._active = active
        self.update_style()
        
    def update_style(self):
        color = self._color if self._active else "#444444"
        border = self._color if self._active else "#666666"
        
        self.setStyleSheet(f"""
            background-color: {color};
            border: 1px solid {border};
            border-radius: {self.width() // 2}px;
        """)

class InfoRow(QWidget):
    """
    A simple row with Label: Value
    """
    def __init__(self, label: str, value: str = "-", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.lbl_key = QLabel(label)
        self.lbl_key.setStyleSheet("color: #888888; font-weight: 500;")
        
        self.lbl_value = QLabel(value)
        self.lbl_value.setStyleSheet("color: #e0e0e0; font-weight: bold;")
        self.lbl_value.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        layout.addWidget(self.lbl_key)
        layout.addStretch()
        layout.addWidget(self.lbl_value)
        
    def set_value(self, value: str):
        self.lbl_value.setText(str(value))
