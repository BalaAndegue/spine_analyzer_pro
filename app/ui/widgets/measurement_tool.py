
import math
from PySide6.QtCore import Qt, QPoint, Signal
from PySide6.QtGui import QPainter, QPen, QColor, QMouseEvent
from .annotation_tool import Tool

class MeasurementTool(Tool):
    """Outil pour mesurer des distances"""
    
    measurement_completed = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.current_pos = None
        self.is_measuring = False
        self.color = QColor(0, 255, 255) # Cyan
        self.pixel_spacing = (1.0, 1.0) # mm par pixel (x, y)
        
    def set_pixel_spacing(self, spacing_x: float, spacing_y: float):
        self.pixel_spacing = (spacing_x, spacing_y)
        
    def handle_mouse_press(self, event: QMouseEvent):
        if not self.is_active: return
        if event.button() == Qt.LeftButton:
            self.start_pos = event.position()
            self.current_pos = event.position()
            self.is_measuring = True
            
    def handle_mouse_move(self, event: QMouseEvent):
        if not self.is_active or not self.is_measuring: return
        self.current_pos = event.position()
        
    def handle_mouse_release(self, event: QMouseEvent):
        if not self.is_active or not self.is_measuring: return
        if event.button() == Qt.LeftButton:
            self.is_measuring = False
            self.current_pos = event.position()
            
            # Calculer la distance
            p1 = self.start_pos
            p2 = self.current_pos
            
            dx = (p2.x() - p1.x()) * self.pixel_spacing[0]
            dy = (p2.y() - p1.y()) * self.pixel_spacing[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            if distance > 0:
                measurement = {
                    'type': 'distance',
                    'start': (p1.x(), p1.y()),
                    'end': (p2.x(), p2.y()),
                    'value': distance,
                    'unit': 'mm'
                }
                self.measurement_completed.emit(measurement)
            
            self.start_pos = None
            self.current_pos = None
            
    def draw(self, painter: QPainter):
        if self.is_active and self.is_measuring and self.start_pos and self.current_pos:
            painter.setPen(QPen(self.color, 2))
            
            p1 = self.start_pos.toPoint()
            p2 = self.current_pos.toPoint()
            painter.drawLine(p1, p2)
            
            # Afficher la distance en temps réel
            dx = (p2.x() - p1.x()) * self.pixel_spacing[0]
            dy = (p2.y() - p1.y()) * self.pixel_spacing[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            mid_x = (p1.x() + p2.x()) // 2
            mid_y = (p1.y() + p2.y()) // 2
            
            painter.drawText(mid_x + 10, mid_y, f"{distance:.1f} mm")
