
from PySide6.QtWidgets import QWidget, QHBoxLayout, QSlider, QSpinBox, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal

class SliceNavigator(QWidget):
    """Widget de navigation dans les slices"""
    
    slice_changed = Signal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_slices = 0
        self.current_slice = 0
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.label = QLabel("Slice:")
        layout.addWidget(self.label)
        
        self.slider = QSlider(Qt.Horizontal)
        self.slider.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.slider)
        
        self.spinbox = QSpinBox()
        self.spinbox.valueChanged.connect(self._on_value_changed)
        layout.addWidget(self.spinbox)
        
        self.total_label = QLabel("/ 0")
        layout.addWidget(self.total_label)
        
    def set_total_slices(self, total: int):
        self.total_slices = total
        self.slider.setMaximum(max(0, total - 1))
        self.spinbox.setMaximum(max(0, total - 1))
        self.total_label.setText(f"/ {total}")
        
    def set_current_slice(self, index: int):
        self.current_slice = max(0, min(index, self.total_slices - 1))
        self.slider.setValue(self.current_slice)
        self.spinbox.setValue(self.current_slice)
        
    def _on_value_changed(self, value: int):
        if value != self.current_slice:
            self.current_slice = value
            self.slider.blockSignals(True)
            self.spinbox.blockSignals(True)
            self.slider.setValue(value)
            self.spinbox.setValue(value)
            self.slider.blockSignals(False)
            self.spinbox.blockSignals(False)
            self.slice_changed.emit(value)
