"""
Fenêtre principale de l'application SpineAnalyzer Pro
"""

import os
import sys
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QDockWidget, QStatusBar, QProgressBar, QToolBar, QMenuBar,
    QFileDialog, QMessageBox, QSplitter, QLabel, QPushButton,
    QListWidget, QTextEdit, QApplication, QSizePolicy
)
from PySide6.QtCore import (
    Qt, QThread, Signal, Slot, QSize, QTimer, QPoint, QRect
)
from PySide6.QtGui import (
    QAction, QIcon, QKeySequence, QPalette, QColor,
    QFont, QFontDatabase, QPixmap, QImage
)

from .widgets.dicom_viewer import DICOMViewer
from .widgets.volume_viewer import VolumeViewer
from .widgets.results_panel import ResultsPanel
from .widgets.control_panel import ControlPanel
from .widgets.patient_info_widget import PatientInfoWidget
from .widgets.progress_dialog import ProgressDialog
from .dialogs.settings_dialog import SettingsDialog
from .dialogs.export_dialog import ExportDialog
from .dialogs.about_dialog import AboutDialog
from ..data.dicom_loader import DICOMManager
from ..ai.reconstruction.spine_reconstructor import SpineReconstructor
from ..ai.detection.anomaly_detector import AnomalyDetector
from ..workers.analysis_worker import AnalysisWorker
from ..core.config import Config
from ..core.logger import get_logger

logger = get_logger(__name__)


class MainWindow(QMainWindow):
    """Fenêtre principale de l'application"""
    
    # Signaux personnalisés
    analysis_started = Signal()
    analysis_progress = Signal(int, str)  # pourcentage, message
    analysis_finished = Signal(dict)      # résultats
    analysis_error = Signal(str)          # message d'erreur
    patient_loaded = Signal(dict)         # données patient chargées
    volume_rendered = Signal(object)      # volume 3D rendu
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.config = Config()
        self.current_patient = None
        self.current_volume = None
        self.current_mesh = None
        self.detected_anomalies = []
        self.is_analysis_running = False
        
        self.setup_ui()
        self.setup_connections()
        self.load_settings()
        self.load_style()
        
        logger.info("MainWindow initialisée")
    
    def setup_ui(self):
        """Configuration de l'interface utilisateur"""
        self.setWindowTitle("SpineAnalyzer Pro v1.0.0")
        self.setMinimumSize(1200, 700)
        
        # Définir l'icône de l'application
        self.setWindowIcon(self.get_icon("app_icon"))
        
        # Créer les composants principaux
        self.create_menu_bar()
        self.create_toolbars()
        self.create_central_widget()
        self.create_dock_widgets()
        self.create_status_bar()
        
        # Appliquer la taille par défaut
        self.resize(1600, 900)
        
        # Initialiser les états
        self.update_ui_state()
    
    def create_menu_bar(self):
        """Créer la barre de menus"""
        menubar = self.menuBar()
        
        # Menu Fichier
        file_menu = menubar.addMenu("&Fichier")
        
        # Ouvrir DICOM
        self.action_open_dicom = QAction(
            self.get_icon("folder_open"),
            "&Ouvrir DICOM...",
            self
        )
        self.action_open_dicom.setShortcut(QKeySequence.Open)
        self.action_open_dicom.setStatusTip("Ouvrir un dossier DICOM")
        self.action_open_dicom.triggered.connect(self.open_dicom_folder)
        file_menu.addAction(self.action_open_dicom)
        
        # Ouvrir fichier
        self.action_open_file = QAction(
            self.get_icon("file_open"),
            "Ouvrir &fichier...",
            self
        )
        self.action_open_file.setShortcut("Ctrl+Shift+O")
        self.action_open_file.triggered.connect(self.open_dicom_file)
        file_menu.addAction(self.action_open_file)
        
        file_menu.addSeparator()
        
        # Exporter
        self.action_export = QAction(
            self.get_icon("export"),
            "&Exporter rapport...",
            self
        )
        self.action_export.setShortcut(QKeySequence.Save)
        self.action_export.setEnabled(False)
        self.action_export.triggered.connect(self.export_report)
        file_menu.addAction(self.action_export)
        
        file_menu.addSeparator()
        
        # Quitter
        self.action_quit = QAction(
            self.get_icon("exit"),
            "&Quitter",
            self
        )
        self.action_quit.setShortcut(QKeySequence.Quit)
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)
        
        # Menu Édition
        edit_menu = menubar.addMenu("&Édition")
        
        # Paramètres
        self.action_settings = QAction(
            self.get_icon("settings"),
            "&Paramètres...",
            self
        )
        self.action_settings.triggered.connect(self.open_settings)
        edit_menu.addAction(self.action_settings)
        
        edit_menu.addSeparator()
        
        # Annuler/Rétablir
        self.action_undo = QAction(
            self.get_icon("undo"),
            "&Annuler",
            self
        )
        self.action_undo.setShortcut(QKeySequence.Undo)
        self.action_undo.setEnabled(False)
        edit_menu.addAction(self.action_undo)
        
        self.action_redo = QAction(
            self.get_icon("redo"),
            "&Rétablir",
            self
        )
        self.action_redo.setShortcut(QKeySequence.Redo)
        self.action_redo.setEnabled(False)
        edit_menu.addAction(self.action_redo)
        
        # Menu Affichage
        view_menu = menubar.addMenu("&Affichage")
        
        # Plein écran
        self.action_fullscreen = QAction(
            "&Plein écran",
            self
        )
        self.action_fullscreen.setShortcut("F11")
        self.action_fullscreen.setCheckable(True)
        self.action_fullscreen.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.action_fullscreen)
        
        view_menu.addSeparator()
        
        # Afficher/Masquer les docks
        self.action_show_control_panel = QAction(
            "Panneau de &contrôle",
            self
        )
        self.action_show_control_panel.setCheckable(True)
        self.action_show_control_panel.setChecked(True)
        self.action_show_control_panel.triggered.connect(
            lambda: self.control_dock.setVisible(
                self.action_show_control_panel.isChecked()
            )
        )
        view_menu.addAction(self.action_show_control_panel)
        
        self.action_show_results_panel = QAction(
            "Panneau des &résultats",
            self
        )
        self.action_show_results_panel.setCheckable(True)
        self.action_show_results_panel.setChecked(True)
        self.action_show_results_panel.triggered.connect(
            lambda: self.results_dock.setVisible(
                self.action_show_results_panel.isChecked()
            )
        )
        view_menu.addAction(self.action_show_results_panel)
        
        # Menu Analyse
        analysis_menu = menubar.addMenu("&Analyse")
        
        # Lancer l'analyse
        self.action_run_analysis = QAction(
            self.get_icon("play"),
            "&Lancer l'analyse",
            self
        )
        self.action_run_analysis.setShortcut("F5")
        self.action_run_analysis.setEnabled(False)
        self.action_run_analysis.triggered.connect(self.run_analysis)
        analysis_menu.addAction(self.action_run_analysis)
        
        # Arrêter l'analyse
        self.action_stop_analysis = QAction(
            self.get_icon("stop"),
            "&Arrêter l'analyse",
            self
        )
        self.action_stop_analysis.setEnabled(False)
        self.action_stop_analysis.triggered.connect(self.stop_analysis)
        analysis_menu.addAction(self.action_stop_analysis)
        
        analysis_menu.addSeparator()
        
        # Reconstruire 3D
        self.action_reconstruct_3d = QAction(
            self.get_icon("reconstruct"),
            "&Reconstruire en 3D",
            self
        )
        self.action_reconstruct_3d.setEnabled(False)
        self.action_reconstruct_3d.triggered.connect(self.reconstruct_3d)
        analysis_menu.addAction(self.action_reconstruct_3d)
        
        # Menu Outils
        tools_menu = menubar.addMenu("&Outils")
        
        # Annotation
        self.action_annotation = QAction(
            self.get_icon("annotation"),
            "&Outil d'annotation",
            self
        )
        self.action_annotation.setCheckable(True)
        self.action_annotation.setEnabled(False)
        tools_menu.addAction(self.action_annotation)
        
        # Mesure
        self.action_measurement = QAction(
            self.get_icon("measure"),
            "Outil de &mesure",
            self
        )
        self.action_measurement.setCheckable(True)
        self.action_measurement.setEnabled(False)
        tools_menu.addAction(self.action_measurement)
        
        tools_menu.addSeparator()
        
        # Comparer
        self.action_compare = QAction(
            self.get_icon("compare"),
            "&Comparer les études",
            self
        )
        self.action_compare.setEnabled(False)
        tools_menu.addAction(self.action_compare)
        
        # Menu Aide
        help_menu = menubar.addMenu("&Aide")
        
        # Documentation
        self.action_docs = QAction(
            self.get_icon("help"),
            "&Documentation",
            self
        )
        self.action_docs.triggered.connect(self.open_documentation)
        help_menu.addAction(self.action_docs)
        
        # À propos
        self.action_about = QAction(
            "&À propos de SpineAnalyzer Pro...",
            self
        )
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)
    
    def create_toolbars(self):
        """Créer les barres d'outils"""
        # Barre d'outils principale
        self.main_toolbar = QToolBar("Outils principaux", self)
        self.main_toolbar.setIconSize(QSize(24, 24))
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        
        # Boutons principaux
        self.main_toolbar.addAction(self.action_open_dicom)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.action_run_analysis)
        self.main_toolbar.addAction(self.action_stop_analysis)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.action_export)
        
        # Barre d'outils de visualisation
        self.view_toolbar = QToolBar("Visualisation", self)
        self.view_toolbar.setIconSize(QSize(20, 20))
        self.addToolBar(Qt.TopToolBarArea, self.view_toolbar)
        
        # Boutons de vue
        self.action_view_axial = QAction(
            self.get_icon("view_axial"),
            "Vue axiale",
            self
        )
        self.action_view_axial.setCheckable(True)
        self.action_view_axial.setChecked(True)
        
        self.action_view_coronal = QAction(
            self.get_icon("view_coronal"),
            "Vue coronale",
            self
        )
        self.action_view_coronal.setCheckable(True)
        
        self.action_view_sagittal = QAction(
            self.get_icon("view_sagittal"),
            "Vue sagittale",
            self
        )
        self.action_view_sagittal.setCheckable(True)
        
        self.view_toolbar.addAction(self.action_view_axial)
        self.view_toolbar.addAction(self.action_view_coronal)
        self.view_toolbar.addAction(self.action_view_sagittal)
        self.view_toolbar.addSeparator()
        
        # Boutons de rendu 3D
        self.action_toggle_3d = QAction(
            self.get_icon("3d"),
            "Afficher/masquer 3D",
            self
        )
        self.action_toggle_3d.setCheckable(True)
        self.view_toolbar.addAction(self.action_toggle_3d)
    
    def create_central_widget(self):
        """Créer le widget central"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Splitter principal
        self.main_splitter = QSplitter(Qt.Horizontal)
        
        # Zone de visualisation avec onglets
        self.visualization_tabs = QTabWidget()
        self.visualization_tabs.setTabPosition(QTabWidget.North)
        self.visualization_tabs.setDocumentMode(True)
        
        # Créer les visualiseurs
        self.dicom_viewer = DICOMViewer()
        self.volume_viewer = VolumeViewer()
        
        # Ajouter les onglets
        self.visualization_tabs.addTab(self.dicom_viewer, "Vues 2D")
        self.visualization_tabs.addTab(self.volume_viewer, "Vue 3D")
        
        # Panel de contrôle (sera placé dans un dock)
        self.control_panel = ControlPanel()
        
        self.main_splitter.addWidget(self.visualization_tabs)
        self.main_splitter.setStretchFactor(0, 3)  # 75% pour la visualisation
        
        main_layout.addWidget(self.main_splitter)
    
    def create_dock_widgets(self):
        """Créer les widgets dockables"""
        # Dock pour le panneau de contrôle (gauche)
        self.control_dock = QDockWidget("Contrôle", self)
        self.control_dock.setWidget(self.control_panel)
        self.control_dock.setAllowedAreas(
            Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea
        )
        self.control_dock.setFeatures(
            QDockWidget.DockWidgetMovable |
            QDockWidget.DockWidgetFloatable
        )
        self.addDockWidget(Qt.LeftDockWidgetArea, self.control_dock)
        
        # Dock pour les résultats (droite)
        self.results_panel = ResultsPanel()
        self.results_dock = QDockWidget("Résultats", self)
        self.results_dock.setWidget(self.results_panel)
        self.results_dock.setAllowedAreas(
            Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea
        )
        self.addDockWidget(Qt.RightDockWidgetArea, self.results_dock)
        
        # Dock pour les logs (bas)
        self.log_widget = QTextEdit()
        self.log_widget.setReadOnly(True)
        self.log_widget.setMaximumHeight(150)
        
        self.log_dock = QDockWidget("Journal", self)
        self.log_dock.setWidget(self.log_widget)
        self.log_dock.setAllowedAreas(Qt.BottomDockWidgetArea)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.log_dock)
        
        # Tabifier les docks
        self.tabifyDockWidget(self.control_dock, self.results_dock)
        self.control_dock.raise_()
    
    def create_status_bar(self):
        """Créer la barre de statut"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Label pour les informations patient
        self.patient_label = QLabel("Aucun patient chargé")
        self.patient_label.setMinimumWidth(200)
        self.status_bar.addWidget(self.patient_label)
        
        # Label pour les informations de slice
        self.slice_label = QLabel("")
        self.slice_label.setMinimumWidth(150)
        self.status_bar.addWidget(self.slice_label)
        
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Label FPS/Performance
        self.performance_label = QLabel("")
        self.performance_label.setMinimumWidth(100)
        self.status_bar.addPermanentWidget(self.performance_label)
    
    def setup_connections(self):
        """Établir les connexions des signaux"""
        # Connexions des widgets
        self.dicom_viewer.slice_changed.connect(self.on_slice_changed)
        self.control_panel.analysis_requested.connect(self.run_analysis)
        self.control_panel.export_requested.connect(self.export_report)
        
        # Connexions des signaux personnalisés
        self.analysis_progress.connect(self.update_progress)
        self.analysis_finished.connect(self.on_analysis_finished)
        self.analysis_error.connect(self.on_analysis_error)
        self.patient_loaded.connect(self.on_patient_loaded)
        
        # Connexions des boutons de vue
        self.action_view_axial.toggled.connect(
            lambda checked: self.dicom_viewer.set_view_mode('axial') if checked else None
        )
        self.action_view_coronal.toggled.connect(
            lambda checked: self.dicom_viewer.set_view_mode('coronal') if checked else None
        )
        self.action_view_sagittal.toggled.connect(
            lambda checked: self.dicom_viewer.set_view_mode('sagittal') if checked else None
        )
        
        # Connexion du bouton 3D
        self.action_toggle_3d.toggled.connect(
            self.volume_viewer.set_visible
        )
        
        # Timer pour les mises à jour de performance
        self.performance_timer = QTimer()
        self.performance_timer.timeout.connect(self.update_performance)
        self.performance_timer.start(1000)  # Mise à jour chaque seconde
    
    def load_settings(self):
        """Charger les paramètres de l'application"""
        # Charger la configuration
        theme = self.config.get('ui/theme', 'dark')
        font_size = self.config.get('ui/font_size', 10)
        language = self.config.get('ui/language', 'fr')
        
        # Appliquer la police
        font = self.font()
        font.setPointSize(font_size)
        self.setFont(font)
        
        # Restaurer la géométrie de la fenêtre
        geometry = self.config.get('window/geometry')
        if geometry:
            self.restoreGeometry(geometry)
        
        # Restaurer l'état des docks
        dock_state = self.config.get('window/dock_state')
        if dock_state:
            self.restoreState(dock_state)
    
    def load_style(self):
        """Charger le style QSS"""
        theme = self.config.get('ui/theme', 'dark')
        
        try:
            from .styles import load_stylesheet
            stylesheet = load_stylesheet(theme)
            self.setStyleSheet(stylesheet)
        except Exception as e:
            logger.warning(f"Impossible de charger le style: {e}")
    
    def get_icon(self, name: str) -> QIcon:
        """Obtenir une icône par son nom"""
        try:
            from .styles import get_icon as get_icon_func
            return get_icon_func(name)
        except:
            # Fallback vers les icônes système
            return QIcon()
    
    @Slot()
    def open_dicom_folder(self):
        """Ouvrir un dossier DICOM"""
        last_folder = self.config.get('last_folder', '')
        
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner un dossier DICOM",
            last_folder,
            QFileDialog.ShowDirsOnly
        )
        
        if folder:
            try:
                self.log_message(f"Chargement du dossier DICOM: {folder}")
                self.status_bar.showMessage(f"Chargement en cours...")
                
                # Désactiver l'interface pendant le chargement
                self.set_ui_enabled(False)
                
                # Charger les données DICOM
                dicom_manager = DICOMManager()
                self.current_patient = dicom_manager.load_folder(folder)
                
                # Mettre à jour l'interface
                self.dicom_viewer.set_patient_data(self.current_patient)
                self.control_panel.set_patient_info(self.current_patient.info)
                self.patient_label.setText(
                    f"Patient: {self.current_patient.info.get('name', 'Inconnu')}"
                )
                
                # Sauvegarder le dernier dossier
                self.config.set('last_folder', folder)
                
                # Émettre le signal
                self.patient_loaded.emit(self.current_patient.info)
                
                # Mettre à jour l'état de l'UI
                self.update_ui_state()
                
                self.status_bar.showMessage(
                    f"Dossier chargé: {os.path.basename(folder)}",
                    3000
                )
                self.log_message(f"Patient chargé: {self.current_patient.info.get('name', 'Inconnu')}")
                
            except Exception as e:
                logger.error(f"Erreur de chargement DICOM: {e}")
                self.log_message(f"ERREUR: {str(e)}", 'error')
                QMessageBox.critical(
                    self,
                    "Erreur de chargement",
                    f"Impossible de charger le dossier DICOM:\n{str(e)}"
                )
            finally:
                self.set_ui_enabled(True)
    
    @Slot()
    def open_dicom_file(self):
        """Ouvrir un fichier DICOM individuel"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Sélectionner des fichiers DICOM",
            "",
            "Fichiers DICOM (*.dcm);;Tous les fichiers (*)"
        )
        
        if files:
            # Implémenter le chargement de fichiers individuels
            pass
    
    @Slot()
    def run_analysis(self):
        """Lancer l'analyse complète"""
        if not self.current_patient:
            QMessageBox.warning(
                self,
                "Aucune donnée",
                "Veuillez d'abord charger des données DICOM."
            )
            return
        
        if self.is_analysis_running:
            QMessageBox.warning(
                self,
                "Analyse en cours",
                "Une analyse est déjà en cours. Veuillez patienter."
            )
            return
        
        logger.info("Démarrage de l'analyse complète...")
        self.log_message("Démarrage de l'analyse...")
        
        # Afficher la barre de progression
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Désactiver l'interface
        self.set_analysis_ui_state(False)
        self.is_analysis_running = True
        
        # Créer et démarrer le worker d'analyse
        self.analysis_worker = AnalysisWorker(self.current_patient)
        self.analysis_thread = QThread()
        
        self.analysis_worker.moveToThread(self.analysis_thread)
        
        # Connexions des signaux
        self.analysis_thread.started.connect(self.analysis_worker.run)
        self.analysis_worker.progress.connect(self.update_progress)
        self.analysis_worker.finished.connect(self.on_analysis_finished)
        self.analysis_worker.error.connect(self.on_analysis_error)
        self.analysis_worker.finished.connect(self.analysis_thread.quit)
        self.analysis_worker.finished.connect(self.analysis_worker.deleteLater)
        self.analysis_thread.finished.connect(self.analysis_thread.deleteLater)
        self.analysis_thread.finished.connect(
            lambda: setattr(self, 'is_analysis_running', False)
        )
        
        # Démarrer le thread
        self.analysis_thread.start()
        
        self.log_message("Analyse démarrée dans un thread séparé")
    
    @Slot()
    def stop_analysis(self):
        """Arrêter l'analyse en cours"""
        if hasattr(self, 'analysis_worker') and self.analysis_worker:
            self.analysis_worker.stop()
            self.log_message("Analyse interrompue par l'utilisateur")
    
    @Slot()
    def reconstruct_3d(self):
        """Lancer uniquement la reconstruction 3D"""
        if not self.current_patient:
            return
        
        self.log_message("Début de la reconstruction 3D...")
        
        # Créer un dialogue de progression
        progress_dialog = ProgressDialog(
            "Reconstruction 3D",
            "Reconstruction en cours...",
            self
        )
        
        # Lancer la reconstruction dans un thread
        # ... implémentation similaire à run_analysis mais pour reconstruction seulement
    
    @Slot(int, str)
    def update_progress(self, value: int, message: str):
        """Mettre à jour la barre de progression"""
        self.progress_bar.setValue(value)
        self.status_bar.showMessage(message, 2000)
        self.log_message(f"[{value}%] {message}")
    
    @Slot(dict)
    def on_analysis_finished(self, results: dict):
        """Traitement des résultats de l'analyse"""
        logger.info("Analyse terminée avec succès")
        self.log_message("✅ Analyse terminée avec succès")
        
        # Masquer la barre de progression
        self.progress_bar.hide()
        
        # Réactiver l'interface
        self.set_analysis_ui_state(True)
        self.is_analysis_running = False
        
        # Stocker les résultats
        self.detected_anomalies = results.get('anomalies', [])
        self.current_volume = results.get('volume_3d')
        self.current_mesh = results.get('mesh')
        
        # Mettre à jour l'interface
        if self.current_volume:
            self.volume_viewer.set_volume_data(self.current_volume)
        
        if self.current_mesh:
            self.volume_viewer.set_mesh_data(self.current_mesh)
        
        self.results_panel.set_results(results)
        
        # Activer l'export
        self.action_export.setEnabled(True)
        
        # Afficher une notification
        self.status_bar.showMessage("Analyse terminée avec succès", 5000)
        
        # Proposer de générer un rapport
        if self.config.get('ui/auto_report', False):
            QTimer.singleShot(1000, lambda: self.generate_report(results))
    
    @Slot(str)
    def on_analysis_error(self, error_message: str):
        """Gérer les erreurs d'analyse"""
        logger.error(f"Erreur lors de l'analyse: {error_message}")
        self.log_message(f"❌ Erreur: {error_message}", 'error')
        
        # Masquer la barre de progression
        self.progress_bar.hide()
        
        # Réactiver l'interface
        self.set_analysis_ui_state(True)
        self.is_analysis_running = False
        
        # Afficher un message d'erreur
        QMessageBox.critical(
            self,
            "Erreur d'analyse",
            f"Une erreur est survenue lors de l'analyse:\n{error_message}"
        )
    
    @Slot(dict)
    def on_patient_loaded(self, patient_info: dict):
        """Traitement après chargement d'un patient"""
        # Activer les actions appropriées
        self.action_run_analysis.setEnabled(True)
        self.action_reconstruct_3d.setEnabled(True)
        self.action_annotation.setEnabled(True)
        self.action_measurement.setEnabled(True)
    
    @Slot(int)
    def on_slice_changed(self, slice_index: int):
        """Mettre à jour l'affichage de la slice courante"""
        if self.current_patient:
            total_slices = len(self.current_patient.slices)
            self.slice_label.setText(f"Slice: {slice_index+1}/{total_slices}")
    
    @Slot()
    def export_report(self):
        """Exporter un rapport"""
        if not self.detected_anomalies and not self.current_patient:
            QMessageBox.warning(
                self,
                "Aucune donnée",
                "Aucune analyse à exporter. Veuillez d'abord analyser des données."
            )
            return
        
        # Ouvrir le dialogue d'export
        dialog = ExportDialog(self)
        if dialog.exec():
            export_params = dialog.get_export_params()
            
            # Générer le rapport
            self.generate_report(
                {
                    'patient': self.current_patient,
                    'anomalies': self.detected_anomalies,
                    'volume': self.current_volume,
                    'mesh': self.current_mesh
                },
                export_params
            )
    
    def generate_report(self, results: dict, params: Optional[dict] = None):
        """Générer un rapport médical"""
        try:
            from ..reporting.report_generator import ReportGenerator
            
            generator = ReportGenerator()
            
            # Paramètres par défaut
            if params is None:
                params = {
                    'format': 'pdf',
                    'include_images': True,
                    'include_3d': False,
                    'output_dir': self.config.get('export/path', '.')
                }
            
            report_path = generator.generate(
                patient_data=self.current_patient,
                analysis_results=results,
                export_params=params
            )
            
            self.log_message(f"Rapport généré: {report_path}")
            
            # Demander si on veut ouvrir le rapport
            if params.get('open_after_export', True):
                reply = QMessageBox.question(
                    self,
                    "Rapport généré",
                    f"Rapport généré avec succès:\n{os.path.basename(report_path)}\n\n"
                    "Voulez-vous l'ouvrir maintenant?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    # Ouvrir le fichier avec l'application par défaut
                    import subprocess
                    import platform
                    
                    if platform.system() == 'Darwin':  # macOS
                        subprocess.call(['open', report_path])
                    elif platform.system() == 'Windows':  # Windows
                        os.startfile(report_path)
                    else:  # Linux
                        subprocess.call(['xdg-open', report_path])
            
        except Exception as e:
            logger.error(f"Erreur lors de la génération du rapport: {e}")
            self.log_message(f"❌ Erreur de génération de rapport: {str(e)}", 'error')
            QMessageBox.critical(
                self,
                "Erreur",
                f"Impossible de générer le rapport:\n{str(e)}"
            )
    
    @Slot()
    def open_settings(self):
        """Ouvrir la fenêtre des paramètres"""
        dialog = SettingsDialog(self)
        if dialog.exec():
            # Recharger les paramètres et le style
            self.load_settings()
            self.load_style()
            self.log_message("Paramètres mis à jour")
    
    @Slot()
    def show_about(self):
        """Afficher la boîte de dialogue À propos"""
        dialog = AboutDialog(self)
        dialog.exec()
    
    @Slot()
    def open_documentation(self):
        """Ouvrir la documentation"""
        # Implémenter l'ouverture de la documentation
        QMessageBox.information(
            self,
            "Documentation",
            "La documentation est disponible dans le dossier docs/"
        )
    
    @Slot(bool)
    def toggle_fullscreen(self, checked: bool):
        """Basculer en mode plein écran"""
        if checked:
            self.showFullScreen()
        else:
            self.showNormal()
    
    def log_message(self, message: str, level: str = 'info'):
        """Ajouter un message au journal"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Formater selon le niveau
        if level == 'error':
            formatted = f'<span style="color: #ff6b6b;">[{timestamp}] {message}</span>'
        elif level == 'warning':
            formatted = f'<span style="color: #ffd93d;">[{timestamp}] {message}</span>'
        elif level == 'success':
            formatted = f'<span style="color: #6bcf7f;">[{timestamp}] {message}</span>'
        else:
            formatted = f'<span style="color: #a0a0a0;">[{timestamp}] {message}</span>'
        
        self.log_widget.append(formatted)
        
        # Défiler vers le bas
        scrollbar = self.log_widget.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
    
    def update_ui_state(self):
        """Mettre à jour l'état de l'interface"""
        has_patient = self.current_patient is not None
        has_results = len(self.detected_anomalies) > 0
        
        # Activer/désactiver les actions
        self.action_run_analysis.setEnabled(has_patient)
        self.action_reconstruct_3d.setEnabled(has_patient)
        self.action_export.setEnabled(has_results)
        self.action_annotation.setEnabled(has_patient)
        self.action_measurement.setEnabled(has_patient)
        
        # Mettre à jour le panneau de contrôle
        self.control_panel.set_enabled(has_patient)
    
    def set_ui_enabled(self, enabled: bool):
        """Activer/désactiver l'interface"""
        self.action_open_dicom.setEnabled(enabled)
        self.action_open_file.setEnabled(enabled)
        self.action_settings.setEnabled(enabled)
        self.control_panel.setEnabled(enabled)
    
    def set_analysis_ui_state(self, enabled: bool):
        """Mettre à jour l'état de l'UI pendant l'analyse"""
        self.action_run_analysis.setEnabled(enabled)
        self.action_stop_analysis.setEnabled(not enabled)
        self.action_export.setEnabled(enabled and len(self.detected_anomalies) > 0)
        self.control_panel.set_enabled(enabled)
    
    def update_performance(self):
        """Mettre à jour les informations de performance"""
        # Calculer le FPS approximatif
        fps = "60 FPS"  # À implémenter avec des mesures réelles
        memory = f"{self.get_memory_usage():.1f} MB"
        self.performance_label.setText(f"{fps} | {memory}")
    
    def get_memory_usage(self) -> float:
        """Obtenir l'utilisation mémoire en MB"""
        import psutil
        process = psutil.Process()
        return process.memory_info().rss / 1024 / 1024
    
    def closeEvent(self, event):
        """Gérer la fermeture de l'application"""
        # Sauvegarder la configuration
        self.config.set('window/geometry', self.saveGeometry())
        self.config.set('window/dock_state', self.saveState())
        self.config.save()
        
        # Vérifier si une analyse est en cours
        if self.is_analysis_running:
            reply = QMessageBox.question(
                self,
                "Analyse en cours",
                "Une analyse est en cours. Voulez-vous vraiment quitter ?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                event.ignore()
                return
        
        # Arrêter les threads
        if hasattr(self, 'analysis_thread') and self.analysis_thread.isRunning():
            self.analysis_thread.quit()
            self.analysis_thread.wait(2000)  # Attendre 2 secondes
        
        logger.info("Fermeture de l'application")
        event.accept()