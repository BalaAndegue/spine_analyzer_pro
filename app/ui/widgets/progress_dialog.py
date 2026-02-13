
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar
from PySide6.QtCore import Qt

class ProgressDialog(QDialog):
    """Dialogue de progression simple"""
    
    def __init__(self, title: str, message: str, parent=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setFixedSize(400, 150)
        self.setWindowModality(Qt.WindowModal)
        self.setWindowFlags(Qt.Dialog | Qt.CustomizeWindowHint | Qt.WindowTitleHint)
        
        # Style
        self.setStyleSheet("""
            QDialog { background-color: #1e1e1e; border: 1px solid #333; }
            QLabel { color: #e0e0e0; font-size: 10pt; }
            QProgressBar { border: 1px solid #333; height: 20px; text-align: center; color: white; }
            QProgressBar::chunk { background-color: #2196f3; }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        self.label = QLabel(message)
        self.label.setWordWrap(True)
        layout.addWidget(self.label)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0) # Indéterminé par défaut
        layout.addWidget(self.progress)
        
    def set_message(self, message: str):
        self.label.setText(message)
        
    def set_value(self, value: int):
        if value < 0:
            self.progress.setRange(0, 0)
        else:
            self.progress.setRange(0, 100)
            self.progress.setValue(value)
