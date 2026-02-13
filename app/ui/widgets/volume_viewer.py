"""
Widget de visualisation 3D avec PyVista/VTK
"""

import numpy as np
from typing import Optional, Dict, Any
import pyvista as pv
from pyvistaqt import QtInteractor
import logging

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QSlider, QLabel, QComboBox, QCheckBox, QGroupBox,
    QSplitter, QSpinBox
)
from PySide6.QtCore import Qt, Signal, Slot, QTimer
from PySide6.QtGui import QColor

from ..core.logger import get_logger

logger = get_logger(__name__)


class VolumeViewer(QWidget):
    """Widget pour visualiser les volumes 3D"""
    
    # Signaux
    volume_loaded = Signal()
    mesh_loaded = Signal()
    rendering_changed = Signal(str)  # Mode de rendu
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.volume_data = None
        self.mesh_data = None
        self.plotter = None
        self.is_volume_visible = True
        self.is_mesh_visible = True
        self.rendering_mode = 'surface'  # 'surface', 'wireframe', 'points'
        self.opacity = 0.8
        
        self.setup_ui()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurer l'interface du widget"""
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Splitter pour les contrôles et la vue 3D
        splitter = QSplitter(Qt.Horizontal)
        
        # Panneau de contrôle gauche
        control_panel = QWidget()
        control_layout = QVBoxLayout(control_panel)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        # Groupe d'affichage
        display_group = QGroupBox("Affichage")
        display_layout = QVBoxLayout()
        
        # Visibilité du volume
        self.volume_checkbox = QCheckBox("Afficher le volume")
        self.volume_checkbox.setChecked(self.is_volume_visible)
        self.volume_checkbox.toggled.connect(self.toggle_volume_visibility)
        display_layout.addWidget(self.volume_checkbox)
        
        # Visibilité du mesh
        self.mesh_checkbox = QCheckBox("Afficher le mesh")
        self.mesh_checkbox.setChecked(self.is_mesh_visible)
        self.mesh_checkbox.toggled.connect(self.toggle_mesh_visibility)
        display_layout.addWidget(self.mesh_checkbox)
        
        # Mode de rendu
        display_layout.addWidget(QLabel("Mode de rendu:"))
        self.rendering_combo = QComboBox()
        self.rendering_combo.addItems(["Surface", "Fil de fer", "Points"])
        self.rendering_combo.currentIndexChanged.connect(
            lambda i: self.set_rendering_mode(['surface', 'wireframe', 'points'][i])
        )
        display_layout.addWidget(self.rendering_combo)
        
        # Opacité
        display_layout.addWidget(QLabel("Opacité:"))
        self.opacity_slider = QSlider(Qt.Horizontal)
        self.opacity_slider.setRange(10, 100)
        self.opacity_slider.setValue(int(self.opacity * 100))
        self.opacity_slider.valueChanged.connect(
            lambda v: self.set_opacity(v / 100.0)
        )
        display_layout.addWidget(self.opacity_slider)
        
        display_group.setLayout(display_layout)
        control_layout.addWidget(display_group)
        
        # Groupe de couleurs
        color_group = QGroupBox("Couleurs")
        color_layout = QVBoxLayout()
        
        # Couleur du volume
        color_layout.addWidget(QLabel("Couleur volume:"))
        self.volume_color_combo = QComboBox()
        self.volume_color_combo.addItems(["Gris", "Bone", "Hot", "Jet", "Viridis"])
        self.volume_color_combo.currentIndexChanged.connect(self.update_colors)
        color_layout.addWidget(self.volume_color_combo)
        
        # Couleur du mesh
        color_layout.addWidget(QLabel("Couleur mesh:"))
        self.mesh_color_combo = QComboBox()
        self.mesh_color_combo.addItems(["Rouge", "Vert", "Bleu", "Jaune", "Blanc"])
        self.mesh_color_combo.currentIndexChanged.connect(self.update_colors)
        color_layout.addWidget(self.mesh_color_combo)
        
        color_group.setLayout(color_layout)
        control_layout.addWidget(color_group)
        
        # Groupe de rotation/zoom
        transform_group = QGroupBox("Transformation")
        transform_layout = QVBoxLayout()
        
        # Rotation
        transform_layout.addWidget(QLabel("Rotation X:"))
        self.rotation_x_slider = QSlider(Qt.Horizontal)
        self.rotation_x_slider.setRange(0, 360)
        self.rotation_x_slider.valueChanged.connect(
            lambda v: self.rotate_camera('x', v)
        )
        transform_layout.addWidget(self.rotation_x_slider)
        
        transform_layout.addWidget(QLabel("Rotation Y:"))
        self.rotation_y_slider = QSlider(Qt.Horizontal)
        self.rotation_y_slider.setRange(0, 360)
        self.rotation_y_slider.valueChanged.connect(
            lambda v: self.rotate_camera('y', v)
        )
        transform_layout.addWidget(self.rotation_y_slider)
        
        # Zoom
        transform_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Horizontal)
        self.zoom_slider.setRange(10, 500)
        self.zoom_slider.setValue(100)
        self.zoom_slider.valueChanged.connect(
            lambda v: self.set_camera_zoom(v / 100.0)
        )
        transform_layout.addWidget(self.zoom_slider)
        
        # Boutons de vue prédéfinis
        views_layout = QHBoxLayout()
        
        views = {
            "Face": (0, 0),
            "Dos": (180, 0),
            "Gauche": (90, 0),
            "Droite": (270, 0),
            "Haut": (0, 90),
            "Bas": (0, -90)
        }
        
        for name, (x, y) in views.items():
            btn = QPushButton(name)
            btn.clicked.connect(
                lambda checked, x=x, y=y: self.set_view(x, y)
            )
            views_layout.addWidget(btn)
        
        transform_layout.addLayout(views_layout)
        
        # Boutons de réinitialisation
        reset_btn = QPushButton("Réinitialiser la vue")
        reset_btn.clicked.connect(self.reset_view)
        transform_layout.addWidget(reset_btn)
        
        transform_group.setLayout(transform_layout)
        control_layout.addWidget(transform_group)
        
        # Boutons d'export
        export_group = QGroupBox("Export")
        export_layout = QVBoxLayout()
        
        self.btn_screenshot = QPushButton("Capture d'écran")
        self.btn_screenshot.clicked.connect(self.take_screenshot)
        export_layout.addWidget(self.btn_screenshot)
        
        self.btn_export_stl = QPushButton("Exporter STL")
        self.btn_export_stl.clicked.connect(self.export_stl)
        export_layout.addWidget(self.btn_export_stl)
        
        export_group.setLayout(export_layout)
        control_layout.addWidget(export_group)
        
        # Étirer pour pousser vers le bas
        control_layout.addStretch()
        
        # Vue 3D (à droite)
        self.plotter_widget = QtInteractor(self)
        
        # Configurer le plotter
        self.plotter = self.plotter_widget
        self.plotter.set_background("black")
        self.plotter.enable_anti_aliasing()
        
        # Ajouter au splitter
        splitter.addWidget(control_panel)
        splitter.addWidget(self.plotter_widget)
        splitter.setSizes([300, 700])
        
        main_layout.addWidget(splitter)
    
    def setup_connections(self):
        """Établir les connexions"""
        pass
    
    def set_volume_data(self, volume_data: np.ndarray):
        """Définir les données volumétriques à afficher"""
        self.volume_data = volume_data
        
        if volume_data is not None:
            try:
                # Créer un PyVista UniformGrid
                grid = pv.UniformGrid()
                grid.dimensions = volume_data.shape
                grid.spacing = (1, 1, 1)  # À ajuster selon les métadonnées DICOM
                grid.point_data["values"] = volume_data.flatten(order="F")
                
                # Ajouter au plotter
                self.plotter.add_volume(
                    grid,
                    cmap="bone",
                    opacity=self.opacity,
                    show_scalar_bar=True
                )
                
                # Ajuster la caméra
                self.plotter.reset_camera()
                
                # Mettre à jour l'interface
                self.volume_checkbox.setEnabled(True)
                
                # Émettre le signal
                self.volume_loaded.emit()
                
                logger.info("Volume 3D chargé avec succès")
                
            except Exception as e:
                logger.error(f"Erreur lors du chargement du volume: {e}")
    
    def set_mesh_data(self, mesh_data):
        """Définir les données de mesh à afficher"""
        self.mesh_data = mesh_data
        
        if mesh_data is not None:
            try:
                # Ajouter le mesh au plotter
                actor = self.plotter.add_mesh(
                    mesh_data,
                    color="red",
                    opacity=0.7,
                    show_edges=True
                )
                
                # Mettre à jour l'interface
                self.mesh_checkbox.setEnabled(True)
                
                # Émettre le signal
                self.mesh_loaded.emit()
                
                logger.info("Mesh 3D chargé avec succès")
                
            except Exception as e:
                logger.error(f"Erreur lors du chargement du mesh: {e}")
    
    def set_visible(self, visible: bool):
        """Définir la visibilité du widget"""
        self.plotter_widget.setVisible(visible)
    
    @Slot(bool)
    def toggle_volume_visibility(self, visible: bool):
        """Basculer la visibilité du volume"""
        self.is_volume_visible = visible
        
        if hasattr(self.plotter, 'volume_actor'):
            self.plotter.volume_actor.SetVisibility(visible)
            self.plotter.render()
    
    @Slot(bool)
    def toggle_mesh_visibility(self, visible: bool):
        """Basculer la visibilité du mesh"""
        self.is_mesh_visible = visible
        
        if hasattr(self.plotter, 'mesh_actor'):
            self.plotter.mesh_actor.SetVisibility(visible)
            self.plotter.render()
    
    @Slot(str)
    def set_rendering_mode(self, mode: str):
        """Définir le mode de rendu"""
        self.rendering_mode = mode
        
        if mode == 'wireframe':
            representation = 1  # Wireframe
        elif mode == 'points':
            representation = 0  # Points
        else:
            representation = 2  # Surface
        
        # Appliquer au volume
        if hasattr(self.plotter, 'volume_actor'):
            self.plotter.volume_actor.GetProperty().SetRepresentation(representation)
        
        # Appliquer au mesh
        if hasattr(self.plotter, 'mesh_actor'):
            self.plotter.mesh_actor.GetProperty().SetRepresentation(representation)
        
        self.plotter.render()
        self.rendering_changed.emit(mode)
    
    @Slot(float)
    def set_opacity(self, opacity: float):
        """Définir l'opacité"""
        self.opacity = max(0.0, min(1.0, opacity))
        
        # Appliquer au volume
        if hasattr(self.plotter, 'volume_actor'):
            self.plotter.volume_actor.GetProperty().SetOpacity(self.opacity)
        
        # Appliquer au mesh
        if hasattr(self.plotter, 'mesh_actor'):
            self.plotter.mesh_actor.GetProperty().SetOpacity(self.opacity)
        
        self.plotter.render()
    
    def update_colors(self):
        """Mettre à jour les couleurs"""
        # Obtenir les couleurs sélectionnées
        volume_color = self.volume_color_combo.currentText().lower()
        mesh_color = self.mesh_color_combo.currentText().lower()
        
        # Mapper les noms de couleurs aux valeurs VTK
        color_map = {
            'gris': (0.5, 0.5, 0.5),
            'bone': (0.76, 0.76, 0.76),
            'hot': (1.0, 0.0, 0.0),
            'jet': (0.0, 0.0, 1.0),
            'viridis': (0.27, 0.0, 0.33),
            'rouge': (1.0, 0.0, 0.0),
            'vert': (0.0, 1.0, 0.0),
            'bleu': (0.0, 0.0, 1.0),
            'jaune': (1.0, 1.0, 0.0),
            'blanc': (1.0, 1.0, 1.0)
        }
        
        # Appliquer les couleurs
        if hasattr(self.plotter, 'volume_actor') and volume_color in color_map:
            self.plotter.volume_actor.GetProperty().SetColor(color_map[volume_color])
        
        if hasattr(self.plotter, 'mesh_actor') and mesh_color in color_map:
            self.plotter.mesh_actor.GetProperty().SetColor(color_map[mesh_color])
        
        self.plotter.render()
    
    def rotate_camera(self, axis: str, angle: float):
        """Faire tourner la caméra"""
        if axis == 'x':
            self.plotter.camera.elevation = angle
        elif axis == 'y':
            self.plotter.camera.azimuth = angle
        
        self.plotter.render()
    
    def set_camera_zoom(self, factor: float):
        """Définir le zoom de la caméra"""
        self.plotter.camera.zoom(factor)
        self.plotter.render()
    
    def set_view(self, azimuth: float, elevation: float):
        """Définir une vue prédéfinie"""
        self.plotter.view_isometric()
        self.plotter.camera.azimuth = azimuth
        self.plotter.camera.elevation = elevation
        
        # Mettre à jour les sliders
        self.rotation_x_slider.setValue(int(elevation))
        self.rotation_y_slider.setValue(int(azimuth))
        
        self.plotter.render()
    
    def reset_view(self):
        """Réinitialiser la vue"""
        self.plotter.reset_camera()
        
        # Réinitialiser les sliders
        self.rotation_x_slider.setValue(0)
        self.rotation_y_slider.setValue(0)
        self.zoom_slider.setValue(100)
        
        self.plotter.render()
    
    def take_screenshot(self):
        """Prendre une capture d'écran"""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Enregistrer la capture d'écran",
                "",
                "Images PNG (*.png);;Images JPEG (*.jpg *.jpeg)"
            )
            
            if filename:
                self.plotter.screenshot(filename)
                logger.info(f"Capture d'écran sauvegardée: {filename}")
                
        except Exception as e:
            logger.error(f"Erreur lors de la capture d'écran: {e}")
    
    def export_stl(self):
        """Exporter le mesh au format STL"""
        try:
            from PySide6.QtWidgets import QFileDialog
            
            if self.mesh_data is None:
                logger.warning("Aucun mesh à exporter")
                return
            
            filename, _ = QFileDialog.getSaveFileName(
                self,
                "Exporter le mesh STL",
                "",
                "Fichiers STL (*.stl)"
            )
            
            if filename:
                self.mesh_data.save(filename)
                logger.info(f"Mesh exporté: {filename}")
                
        except Exception as e:
            logger.error(f"Erreur lors de l'export STL: {e}")
    
    def clear(self):
        """Effacer toutes les données affichées"""
        self.plotter.clear()
        self.volume_data = None
        self.mesh_data = None
        
        # Désactiver les contrôles
        self.volume_checkbox.setEnabled(False)
        self.mesh_checkbox.setEnabled(False)
        
        self.plotter.render()