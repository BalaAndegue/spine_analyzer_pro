
from PySide6.QtCore import Qt, QPoint, QRect, Signal, QObject
from PySide6.QtGui import QPainter, QPen, QColor, QMouseEvent

class Tool(QObject):
    """Classe de base pour les outils interactifs"""
    def __init__(self):
        super().__init__()
        self.is_active = False
        
    def activate(self):
        self.is_active = True
        
    def deactivate(self):
        self.is_active = False
        
    def handle_mouse_press(self, event: QMouseEvent):
        pass
        
    def handle_mouse_move(self, event: QMouseEvent):
        pass
        
    def handle_mouse_release(self, event: QMouseEvent):
        pass
        
    def draw(self, painter: QPainter):
        pass

class AnnotationTool(Tool):
    """Outil pour dessiner des annotations (rectangles, flèches, texte)"""
    
    annotation_created = Signal(dict)
    
    def __init__(self):
        super().__init__()
        self.start_pos = None
        self.current_pos = None
        self.is_drawing = False
        self.current_shape = 'rectangle' # ou 'arrow', 'text'
        self.color = QColor(255, 255, 0) # Jaune
        
    def handle_mouse_press(self, event: QMouseEvent):
        if not self.is_active: return
        if event.button() == Qt.LeftButton:
            self.start_pos = event.position()
            self.current_pos = event.position()
            self.is_drawing = True
            
    def handle_mouse_move(self, event: QMouseEvent):
        if not self.is_active or not self.is_drawing: return
        self.current_pos = event.position()
        
    def handle_mouse_release(self, event: QMouseEvent):
        if not self.is_active or not self.is_drawing: return
        if event.button() == Qt.LeftButton:
            self.is_drawing = False
            self.current_pos = event.position()
            
            # Créer l'annotation
            rect = QRect(self.start_pos.toPoint(), self.current_pos.toPoint()).normalized()
            if rect.width() > 5 or rect.height() > 5:
                annotation = {
                    'type': self.current_shape,
                    'rect': (rect.x(), rect.y(), rect.width(), rect.height()),
                    'color': self.color.name()
                }
                self.annotation_created.emit(annotation)
            
            self.start_pos = None
            self.current_pos = None
            
    def draw(self, painter: QPainter):
        if self.is_active and self.is_drawing and self.start_pos and self.current_pos:
            painter.setPen(QPen(self.color, 2))
            
            rect = QRect(self.start_pos.toPoint(), self.current_pos.toPoint()).normalized()
            painter.drawRect(rect)
