"""
Widget de visualisation d'images DICOM 2D
"""

import numpy as np
from typing import Optional, Dict, List, Tuple
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QSlider,
    QPushButton, QComboBox, QSpinBox, QCheckBox, QGroupBox,
    QGridLayout, QSplitter, QScrollArea
)
from PySide6.QtCore import Qt, Signal, Slot, QSize, QRect
from PySide6.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QFont,
    QMouseEvent, QWheelEvent, QKeyEvent
)

from ..data.dicom_loader import PatientData, SliceData
from ..core.logger import get_logger

logger = get_logger(__name__)


class DICOMViewer(QWidget):
    """Widget pour visualiser les images DICOM en 2D"""
    
    # Signaux
    slice_changed = Signal(int)  # Index de la slice courante
    view_mode_changed = Signal(str)  # 'axial', 'coronal', 'sagittal'
    mouse_position_changed = Signal(float, float, float)  # x, y, value
    annotation_added = Signal(dict)  # Annotation ajoutée
    measurement_added = Signal(dict)  # Mesure ajoutée
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.patient_data = None
        self.current_slice_index = 0
        self.view_mode = 'axial'  # 'axial', 'coronal', 'sagittal'
        self.window_level = 40
        self.window_width = 400
        self.zoom_factor = 1.0
        self.pan_offset = (0, 0)
        self.is_panning = False
        self.last_mouse_pos = None
        self.annotations = []
        self.measurements = []
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurer l'interface du widget"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Splitter pour les contrôles et l'image
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de contrôle gauche
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Groupe navigation
        nav_group = QGroupBox("Navigation")
        nav_layout = QVBoxLayout()
        
        # Mode de vue
        self.view_mode_combo = QComboBox()
        self.view_mode_combo.addItems(["Axiale", "Coronale", "Sagittale"])
        self.view_mode_combo.currentIndexChanged.connect(
            lambda i: self.set_view_mode(['axial', 'coronal', 'sagittal'][i])
        )
        nav_layout.addWidget(QLabel("Vue:"))
        nav_layout.addWidget(self.view_mode_combo)
        
        # Slider de slice
        self.slice_slider = QSlider(Qt.Horizontal)
        self.slice_slider.setMinimum(0)
        self.slice_slider.setMaximum(0)
        self.slice_slider.valueChanged.connect(self.set_slice_index)
        nav_layout.addWidget(QLabel("Slice:"))
        nav_layout.addWidget(self.slice_slider)
        
        # SpinBox pour slice précise
        self.slice_spinbox = QSpinBox()
        self.slice_spinbox.setMinimum(0)
        self.slice_spinbox.setMaximum(0)
        self.slice_spinbox.valueChanged.connect(self.set_slice_index)
        nav_layout.addWidget(self.slice_spinbox)
        
        # Boutons de navigation
        nav_buttons_layout = QGridLayout()
        
        self.btn_first = QPushButton("◀◀")
        self.btn_prev = QPushButton("◀")
        self.btn_next = QPushButton("▶")
        self.btn_last = QPushButton("▶▶")
        self.btn_play = QPushButton("▶▶")  # Pour animation
        
        self.btn_first.clicked.connect(self.first_slice)
        self.btn_prev.clicked.connect(self.previous_slice)
        self.btn_next.clicked.connect(self.next_slice)
        self.btn_last.clicked.connect(self.last_slice)
        self.btn_play.clicked.connect(self.toggle_play)
        
        nav_buttons_layout.addWidget(self.btn_first, 0, 0)
        nav_buttons_layout.addWidget(self.btn_prev, 0, 1)
        nav_buttons_layout.addWidget(self.btn_next, 0, 2)
        nav_buttons_layout.addWidget(self.btn_last, 0, 3)
        nav_buttons_layout.addWidget(self.btn_play, 1, 0, 1, 4)
        
        nav_layout.addLayout(nav_buttons_layout)
        nav_group.setLayout(nav_layout)
        control_layout.addWidget(nav_group)
        
        # Groupe fenêtrage
        ww_wl_group = QGroupBox("Fenêtrage (WW/WL)")
        ww_wl_layout = QVBoxLayout()
        
        # Slider niveau de fenêtre
        self.wl_slider = QSlider(Qt.Horizontal)
        self.wl_slider.setRange(-1000, 1000)
        self.wl_slider.setValue(self.window_level)
        self.wl_slider.valueChanged.connect(self.set_window_level)
        ww_wl_layout.addWidget(QLabel("Niveau (WL):"))
        ww_wl_layout.addWidget(self.wl_slider)
        
        # Slider largeur de fenêtre
        self.ww_slider = QSlider(Qt.Horizontal)
        self.ww_slider.setRange(1, 2000)
        self.ww_slider.setValue(self.window_width)
        self.ww_slider.valueChanged.connect(self.set_window_width)
        ww_wl_layout.addWidget(QLabel("Largeur (WW):"))
        ww_wl_layout.addWidget(self.ww_slider)
        
        # Boutons préréglages
        presets_layout = QHBoxLayout()
        
        presets = {
            "Os": (1500, 300),
            "Poumon": (1500, -600),
            "Abdomen": (400, 40),
            "Cerveau": (80, 40)
        }
        
        for name, (ww, wl) in presets.items():
            btn = QPushButton(name)
            btn.clicked.connect(
                lambda checked, ww=ww, wl=wl: self.set_window_preset(ww, wl)
            )
            presets_layout.addWidget(btn)
        
        ww_wl_layout.addLayout(presets_layout)
        ww_wl_group.setLayout(ww_wl_layout)
        control_layout.addWidget(ww_wl_group)
        
        # Groupe zoom/pan
        zoom_group = QGroupBox("Zoom & Déplacement")
        zoom_layout = QVBoxLayout()
        
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.zoom_slider.valueChanged.connect(
            lambda v: self.set_zoom_factor(v / 100.0)
        )
        zoom_layout.addWidget(QLabel("Zoom:"))
        zoom_layout.addWidget(self.zoom_slider)
        
        # Boutons zoom
        zoom_buttons_layout = QHBoxLayout()
        
        self.btn_zoom_in = QPushButton("+")
        self.btn_zoom_out = QPushButton("-")
        self.btn_zoom_fit = QPushButton("Ajuster")
        self.btn_zoom_reset = QPushButton("Réinitialiser")
        
        self.btn_zoom_in.clicked.connect(self.zoom_in)
        self.btn_zoom_out.clicked.connect(self.zoom_out)
        self.btn_zoom_fit.clicked.connect(self.zoom_fit)
        self.btn_zoom_reset.clicked.connect(self.zoom_reset)
        
        zoom_buttons_layout.addWidget(self.btn_zoom_in)
        zoom_buttons_layout.addWidget(self.btn_zoom_out)
        zoom_buttons_layout.addWidget(self.btn_zoom_fit)
        zoom_buttons_layout.addWidget(self.btn_zoom_reset)
        
        zoom_layout.addLayout(zoom_buttons_layout)
        zoom_group.setLayout(zoom_layout)
        control_layout.addWidget(zoom_group)
        
        # Étirer pour pousser vers le bas
        control_layout.addStretch()
        
        # Zone d'affichage d'image (à droite)
        self.image_display = QLabel()
        self.image_display.setAlignment(Qt.AlignCenter)
        self.image_display.setMinimumSize(400, 400)
        self.image_display.setStyleSheet(
            "background-color: black; border: 1px solid #555;"
        )
        
        # Ajouter au splitter
        splitter.addWidget(control_panel)
        splitter.addWidget(self.image_display)
        splitter.setSizes([250, 750])
        
        main_layout.addWidget(splitter)
        
        # Zone d'infos en bas
        self.info_label = QLabel()
        self.info_label.setStyleSheet(
            "padding: 5px; background-color: #2a2a2a; color: #aaa;"
        )
        main_layout.addWidget(self.info_label, 0, Qt.AlignBottom)
    
    def setup_connections(self):
        """Établir les connexions"""
        # Connexions déjà faites dans setup_ui
        pass
    
    def set_patient_data(self, patient_data: PatientData):
        """Définir les données du patient à afficher"""
        self.patient_data = patient_data
        
        if patient_data and patient_data.slices:
            # Mettre à jour les contrôles de navigation
            num_slices = len(patient_data.slices)
            self.slice_slider.setMaximum(num_slices - 1)
            self.slice_spinbox.setMaximum(num_slices - 1)
            
            # Réinitialiser la vue
            self.current_slice_index = 0
            self.zoom_factor = 1.0
            self.pan_offset = (0, 0)
            
            # Afficher la première slice
            self.update_display()
            
            # Mettre à jour les informations
            self.update_info_label()
    
    def set_slice_index(self, index: int):
        """Définir l'index de la slice courante"""
        if not self.patient_data or not self.patient_data.slices:
            return
        
        # Limiter l'index
        index = max(0, min(index, len(self.patient_data.slices) - 1))
        
        if index != self.current_slice_index:
            self.current_slice_index = index
            
            # Synchroniser les contrôles
            self.slice_slider.blockSignals(True)
            self.slice_spinbox.blockSignals(True)
            
            self.slice_slider.setValue(index)
            self.slice_spinbox.setValue(index)
            
            self.slice_slider.blockSignals(False)
            self.slice_spinbox.blockSignals(False)
            
            # Mettre à jour l'affichage
            self.update_display()
            self.update_info_label()
            
            # Émettre le signal
            self.slice_changed.emit(index)
    
    def set_view_mode(self, mode: str):
        """Définir le mode de vue"""
        if mode not in ['axial', 'coronal', 'sagittal']:
            return
        
        if mode != self.view_mode:
            self.view_mode = mode
            
            # Mettre à jour la combo box
            index = ['axial', 'coronal', 'sagittal'].index(mode)
            self.view_mode_combo.setCurrentIndex(index)
            
            # Réinitialiser la vue
            self.current_slice_index = 0
            self.zoom_factor = 1.0
            self.pan_offset = (0, 0)
            
            # Mettre à jour l'affichage
            self.update_display()
            
            # Émettre le signal
            self.view_mode_changed.emit(mode)
    
    def set_window_level(self, level: int):
        """Définir le niveau de fenêtre"""
        self.window_level = level
        self.update_display()
    
    def set_window_width(self, width: int):
        """Définir la largeur de fenêtre"""
        self.window_width = width
        self.update_display()
    
    def set_window_preset(self, width: int, level: int):
        """Définir un préréglage de fenêtre"""
        self.window_width = width
        self.window_level = level
        
        # Mettre à jour les sliders
        self.ww_slider.setValue(width)
        self.wl_slider.setValue(level)
        
        self.update_display()
    
    def set_zoom_factor(self, factor: float):
        """Définir le facteur de zoom"""
        self.zoom_factor = max(0.1, min(5.0, factor))
        self.zoom_slider.setValue(int(self.zoom_factor * 100))
        self.update_display()
    
    def update_display(self):
        """Mettre à jour l'affichage de l'image"""
        if not self.patient_data or not self.patient_data.slices:
            self.image_display.clear()
            return
        
        # Obtenir la slice courante
        slice_data = self.get_current_slice()
        if not slice_data or slice_data.pixel_array is None:
            return
        
        # Convertir les pixels DICOM en QImage
        image = self.dicom_to_qimage(
            slice_data.pixel_array,
            self.window_width,
            self.window_level
        )
        
        # Appliquer le zoom et le pan
        if self.zoom_factor != 1.0:
            new_size = QSize(
                int(image.width() * self.zoom_factor),
                int(image.height() * self.zoom_factor)
            )
            image = image.scaled(
                new_size,
                Qt.KeepAspectRatio,
                Qt.SmoothTransformation
            )
        
        # Convertir en QPixmap pour l'affichage
        pixmap = QPixmap.fromImage(image)
        
        # Appliquer le pan
        if self.pan_offset != (0, 0):
            # Créer un pixmap plus grand et positionner l'image décalée
            pass
        
        # Afficher
        self.image_display.setPixmap(pixmap)
    
    def dicom_to_qimage(self, pixel_array: np.ndarray, 
                        window_width: int, 
                        window_level: int) -> QImage:
        """
        Convertir un array DICOM en QImage avec fenêtrage
        """
        # Appliquer le fenêtrage
        min_val = window_level - window_width // 2
        max_val = window_level + window_width // 2
        
        # Normaliser entre 0-255
        normalized = np.clip(pixel_array, min_val, max_val)
        normalized = ((normalized - min_val) / 
                     (max_val - min_val) * 255).astype(np.uint8)
        
        # Créer l'image
        height, width = normalized.shape
        bytes_per_line = width
        
        # Convertir en QImage (format grayscale)
        image = QImage(
            normalized.data,
            width,
            height,
            bytes_per_line,
            QImage.Format_Grayscale8
        )
        
        # Copier les données car l'array peut être libéré
        return image.copy()
    
    def get_current_slice(self) -> Optional[SliceData]:
        """Obtenir la slice courante selon le mode de vue"""
        if not self.patient_data:
            return None
        
        # Pour l'instant, on utilise juste les slices axiales
        # À compléter pour les reconstructions coronales/sagittales
        if self.current_slice_index < len(self.patient_data.slices):
            return self.patient_data.slices[self.current_slice_index]
        
        return None
    
    def update_info_label(self):
        """Mettre à jour le label d'informations"""
        if not self.patient_data:
            self.info_label.setText("Aucune donnée chargée")
            return
        
        slice_data = self.get_current_slice()
        if slice_data:
            info = f"""
            Slice: {self.current_slice_index + 1}/{len(self.patient_data.slices)} | 
            Position: {slice_data.position} | 
            WW/WL: {self.window_width}/{self.window_level} | 
            Zoom: {self.zoom_factor:.2f}x
            """
            self.info_label.setText(info.strip().replace('\n', ''))
    
    # Méthodes de navigation
    def first_slice(self):
        """Aller à la première slice"""
        self.set_slice_index(0)
    
    def last_slice(self):
        """Aller à la dernière slice"""
        if self.patient_data:
            self.set_slice_index(len(self.patient_data.slices) - 1)
    
    def previous_slice(self):
        """Aller à la slice précédente"""
        self.set_slice_index(self.current_slice_index - 1)
    
    def next_slice(self):
        """Aller à la slice suivante"""
        self.set_slice_index(self.current_slice_index + 1)
    
    def toggle_play(self):
        """Basculer l'animation automatique"""
        # À implémenter
        pass
    
    # Méthodes de zoom
    def zoom_in(self):
        """Zoom avant"""
        self.set_zoom_factor(self.zoom_factor * 1.2)
    
    def zoom_out(self):
        """Zoom arrière"""
        self.set_zoom_factor(self.zoom_factor / 1.2)
    
    def zoom_fit(self):
        """Ajuster l'image à la fenêtre"""
        # À implémenter
        self.zoom_factor = 1.0
        self.pan_offset = (0, 0)
        self.update_display()
    
    def zoom_reset(self):
        """Réinitialiser le zoom"""
        self.zoom_factor = 1.0
        self.zoom_slider.setValue(100)
        self.update_display()
    
    # Événements souris
    def mousePressEvent(self, event: QMouseEvent):
        """Gérer l'appui de la souris"""
        if event.button() == Qt.LeftButton:
            self.is_panning = True
            self.last_mouse_pos = event.position()
        elif event.button() == Qt.RightButton:
            # Menu contextuel pour annotations
            pass
    
    def mouseMoveEvent(self, event: QMouseEvent):
        """Gérer le mouvement de la souris"""
        if self.is_panning and self.last_mouse_pos:
            delta = event.position() - self.last_mouse_pos
            self.pan_offset = (
                self.pan_offset[0] + delta.x(),
                self.pan_offset[1] + delta.y()
            )
            self.last_mouse_pos = event.position()
            self.update_display()
        
        # Émettre la position de la souris
        if self.patient_data and self.image_display.pixmap():
            pos = event.pos()
            # Convertir les coordonnées de l'écran aux coordonnées de l'image
            # et émettre le signal mouse_position_changed
    
    def mouseReleaseEvent(self, event: QMouseEvent):
        """Gérer le relâchement de la souris"""
        if event.button() == Qt.LeftButton:
            self.is_panning = False
            self.last_mouse_pos = None
    
    def wheelEvent(self, event: QWheelEvent):
        """Gérer la molette de la souris"""
        # Changer de slice avec la molette
        delta = event.angleDelta().y()
        if delta > 0:
            self.previous_slice()
        else:
            self.next_slice()
    
    def keyPressEvent(self, event: QKeyEvent):
        """Gérer les touches du clavier"""
        key = event.key()
        
        if key == Qt.Key_Left:
            self.previous_slice()
        elif key == Qt.Key_Right:
            self.next_slice()
        elif key == Qt.Key_Plus or key == Qt.Key_Equal:
            self.zoom_in()
        elif key == Qt.Key_Minus:
            self.zoom_out()
        elif key == Qt.Key_0:
            self.zoom_reset()
        elif key == Qt.Key_Space:
            self.toggle_play()
        else:
            super().keyPressEvent(event)