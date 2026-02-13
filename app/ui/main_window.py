"""
Fenêtre principale de l'application SpineAnalyzer Pro
"""

import os
import sys
import psutil
from datetime import datetime
from typing import Optional, Dict, List, Any
import logging

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTabWidget,
    QDockWidget, QStatusBar, QProgressBar, QToolBar, QMenuBar,
    QFileDialog, QMessageBox, QSplitter, QLabel, QPushButton,
    QListWidget, QTextEdit, QApplication, QSizePolicy, QFrame
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
    analysis_progress = Signal(int, str)
    analysis_finished = Signal(dict)
    analysis_error = Signal(str)
    patient_loaded = Signal(dict)
    
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
        self.setWindowTitle("SpineAnalyzer Pro v1.0.0 - Advanced Medical Imaging")
        self.setMinimumSize(1280, 800)
        
        # Icon
        self.setWindowIcon(self.get_icon("app_icon"))
        
        # Central Components
        self.create_menu_bar()
        self.create_toolbars()
        self.create_central_widget()
        self.create_dock_widgets()
        self.create_status_bar()
        
        # Docks take vertical space
        self.setCorner(Qt.TopLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.TopRightCorner, Qt.RightDockWidgetArea)
        self.setCorner(Qt.BottomLeftCorner, Qt.LeftDockWidgetArea)
        self.setCorner(Qt.BottomRightCorner, Qt.RightDockWidgetArea)
        
        # Default geometry
        self.resize(1600, 950)
        self.update_ui_state()
    
    def create_menu_bar(self):
        """Créer la barre de menus"""
        menubar = self.menuBar()
        
        # --- File ---
        file_menu = menubar.addMenu("&Fichier")
        
        self.action_open_dicom = QAction(self.get_icon("folder_open"), "&Ouvrir Dossier DICOM...", self)
        self.action_open_dicom.setShortcut(QKeySequence.Open)
        self.action_open_dicom.triggered.connect(self.open_dicom_folder)
        file_menu.addAction(self.action_open_dicom)
        
        self.action_open_file = QAction(self.get_icon("file_open"), "Ouvrir &Fichier...", self)
        self.action_open_file.setShortcut("Ctrl+Shift+O")
        self.action_open_file.triggered.connect(self.open_dicom_file)
        file_menu.addAction(self.action_open_file)
        
        file_menu.addSeparator()
        
        self.action_export = QAction(self.get_icon("export"), "&Exporter Rapport...", self)
        self.action_export.setShortcut(QKeySequence.Save)
        self.action_export.setEnabled(False)
        self.action_export.triggered.connect(self.export_report)
        file_menu.addAction(self.action_export)
        
        file_menu.addSeparator()
        
        self.action_quit = QAction(self.get_icon("exit"), "&Quitter", self)
        self.action_quit.setShortcut(QKeySequence.Quit)
        self.action_quit.triggered.connect(self.close)
        file_menu.addAction(self.action_quit)
        
        # --- View ---
        view_menu = menubar.addMenu("&Affichage")
        self.action_fullscreen = QAction("&Plein Écran", self)
        self.action_fullscreen.setShortcut("F11")
        self.action_fullscreen.setCheckable(True)
        self.action_fullscreen.triggered.connect(self.toggle_fullscreen)
        view_menu.addAction(self.action_fullscreen)
        
        view_menu.addSeparator()
        
        # Docks visibility
        self.action_show_control_panel = QAction("Panneau de &Contrôle", self)
        self.action_show_control_panel.setCheckable(True)
        self.action_show_control_panel.setChecked(True)
        self.action_show_control_panel.triggered.connect(lambda: self.control_dock.setVisible(self.action_show_control_panel.isChecked()))
        view_menu.addAction(self.action_show_control_panel)
        
        self.action_show_results_panel = QAction("Panneau des &Résultats", self)
        self.action_show_results_panel.setCheckable(True)
        self.action_show_results_panel.setChecked(True)
        self.action_show_results_panel.triggered.connect(lambda: self.results_dock.setVisible(self.action_show_results_panel.isChecked()))
        view_menu.addAction(self.action_show_results_panel)
        
        # --- Tools ---
        analysis_menu = menubar.addMenu("&Analyse")
        
        self.action_run_analysis = QAction(self.get_icon("play"), "&Lancer Analyse Complète", self)
        self.action_run_analysis.setShortcut("F5")
        self.action_run_analysis.setEnabled(False)
        self.action_run_analysis.triggered.connect(self.run_analysis)
        analysis_menu.addAction(self.action_run_analysis)

        self.action_stop_analysis = QAction(self.get_icon("stop"), "&Arrêter", self)
        self.action_stop_analysis.setEnabled(False)
        self.action_stop_analysis.triggered.connect(self.stop_analysis)
        analysis_menu.addAction(self.action_stop_analysis)
        
        # --- Help ---
        help_menu = menubar.addMenu("&Aide")
        self.action_about = QAction("&À propos...", self)
        self.action_about.triggered.connect(self.show_about)
        help_menu.addAction(self.action_about)
    
    def create_toolbars(self):
        """Créer les barres d'outils"""
        self.main_toolbar = QToolBar("Principal", self)
        self.main_toolbar.setIconSize(QSize(28, 28))
        self.main_toolbar.setMovable(False)
        self.addToolBar(Qt.TopToolBarArea, self.main_toolbar)
        
        self.main_toolbar.addAction(self.action_open_dicom)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.action_run_analysis)
        self.main_toolbar.addAction(self.action_stop_analysis)
        self.main_toolbar.addSeparator()
        self.main_toolbar.addAction(self.action_export)
        
        # View Toolbar
        self.view_toolbar = QToolBar("Vues", self)
        self.view_toolbar.setIconSize(QSize(24, 24))
        self.addToolBar(Qt.TopToolBarArea, self.view_toolbar)
        
        # Actions for 2D views would go here
    
    def create_central_widget(self):
        """Créer le widget central"""
        central_widget = QWidget()
        central_widget.setStyleSheet("background-color: #121212;")
        self.setCentralWidget(central_widget)
        
        layout = QHBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Tabs for Viewers
        self.visualization_tabs = QTabWidget()
        self.visualization_tabs.setTabPosition(QTabWidget.North)
        self.visualization_tabs.setDocumentMode(True)
        
        self.dicom_viewer = DICOMViewer()
        self.volume_viewer = VolumeViewer()
        
        self.visualization_tabs.addTab(self.dicom_viewer, "Visualisation 2D")
        self.visualization_tabs.addTab(self.volume_viewer, "Reconstruction 3D")
        
        layout.addWidget(self.visualization_tabs)
    
    def create_dock_widgets(self):
        """Créer les docks"""
        # Control Dock (Left)
        self.control_dock = QDockWidget("Panneau de Contrôle", self)
        self.control_panel = ControlPanel()
        self.control_dock.setWidget(self.control_panel)
        self.control_dock.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.control_dock)
        
        # Results Dock (Right)
        self.results_dock = QDockWidget("Résultats d'Analyse", self)
        self.results_panel = ResultsPanel()
        self.results_dock.setWidget(self.results_panel)
        self.results_dock.setAllowedAreas(Qt.RightDockWidgetArea | Qt.LeftDockWidgetArea)
        self.addDockWidget(Qt.RightDockWidgetArea, self.results_dock)
    
    def create_status_bar(self):
        """Créer la barre de statut"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Patient Info in Status Bar
        self.patient_label = QLabel("Aucun patient")
        self.patient_label.setStyleSheet("font-weight: bold; color: #ccc;")
        self.status_bar.addWidget(self.patient_label)
        
        # Progress
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # System Stats
        self.sys_ram_label = QLabel("RAM: 0%")
        self.sys_cpu_label = QLabel("CPU: 0%")
        self.sys_ram_label.setStyleSheet("color: #888; margin-left: 10px;")
        self.sys_cpu_label.setStyleSheet("color: #888; margin-left: 5px;")
        
        self.status_bar.addPermanentWidget(self.sys_ram_label)
        self.status_bar.addPermanentWidget(self.sys_cpu_label)
        
    def setup_connections(self):
        # Viewers
        self.dicom_viewer.slice_changed.connect(
            lambda i: self.status_bar.showMessage(f"Slice: {i}")
        )
        
        # Control Panel
        self.control_panel.analysis_requested.connect(self.run_analysis)
        self.control_panel.export_requested.connect(self.export_report)
        
        # Analysis Signals
        self.analysis_progress.connect(self.update_progress)
        self.analysis_finished.connect(self.on_analysis_finished)
        self.analysis_error.connect(self.on_analysis_error)
        self.patient_loaded.connect(self.on_patient_loaded)
        
        # Performance Timer
        self.perf_timer = QTimer()
        self.perf_timer.timeout.connect(self.update_system_stats)
        self.perf_timer.start(2000)
        
    def update_system_stats(self):
        try:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            self.sys_cpu_label.setText(f"CPU: {cpu}%")
            self.sys_ram_label.setText(f"RAM: {ram}%")
        except:
            pass
            
    # ... (Rest of the methods: load_settings, load_style, open_dicom_folder, etc. 
    # would be similar but improved. I will implement the critical ones here)
    
    def load_settings(self):
        pass # Placeholder for brevity, similar to original
        
    def load_style(self):
        try:
            from .styles import load_stylesheet
            self.setStyleSheet(load_stylesheet("dark"))
        except Exception:
            pass
            
    def get_icon(self, name):
        return QIcon() # Placeholder
        
    @Slot()
    def open_dicom_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner Dossier DICOM")
        if folder:
            self.status_bar.showMessage("Chargement...")
            try:
                manager = DICOMManager()
                self.current_patient = manager.load_folder(folder)
                
                # Update UI
                self.dicom_viewer.set_patient_data(self.current_patient)
                self.control_panel.set_patient_info(self.current_patient.info)
                self.patient_label.setText(f"Patient: {self.current_patient.info.get('name', 'Inconnu')}")
                self.patient_loaded.emit(self.current_patient.info)
                self.status_bar.showMessage("Prêt", 3000)
                
            except Exception as e:
                QMessageBox.critical(self, "Erreur", str(e))
                self.status_bar.showMessage("Erreur de chargement")

    @Slot()
    def open_dicom_file(self):
        pass

    @Slot()
    def export_report(self):
        if not self.current_patient: return
        dialog = ExportDialog(self)
        if dialog.exec():
            # Generate report logic
            QMessageBox.information(self, "Export", "Rapport généré (Simulation)")

    @Slot()
    def run_analysis(self):
        if not self.current_patient: return
        
        self.is_analysis_running = True
        self.control_panel.set_analysis_state(True)
        self.action_run_analysis.setEnabled(False)
        self.action_stop_analysis.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Start Worker
        self.worker = AnalysisWorker(self.current_patient)
        self.thread = QThread()
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        self.worker.progress.connect(self.analysis_progress.emit)
        self.worker.finished.connect(self.analysis_finished.emit)
        self.worker.error.connect(self.analysis_error.emit)
        
        # Cleanup
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.thread.finished.connect(self.thread.deleteLater)
        
        self.thread.start()

    @Slot()
    def stop_analysis(self):
        if hasattr(self, 'worker'):
            self.worker.stop()

    @Slot(int, str)
    def update_progress(self, val, msg):
        self.progress_bar.setValue(val)
        self.status_bar.showMessage(msg)

    @Slot(dict)
    def on_analysis_finished(self, results):
        self.is_analysis_running = False
        self.control_panel.set_analysis_state(False)
        self.control_panel.set_results_ready(True)
        self.action_run_analysis.setEnabled(True)
        self.action_stop_analysis.setEnabled(False)
        self.progress_bar.setVisible(False)
        self.status_bar.showMessage("Analyse terminée", 5000)
        
        self.results_panel.set_results(results)
        self.current_volume = results.get('volume_3d')
        if self.current_volume:
            self.volume_viewer.set_volume_data(self.current_volume)

    @Slot(str)
    def on_analysis_error(self, err):
        self.is_analysis_running = False
        self.control_panel.set_analysis_state(False)
        self.action_run_analysis.setEnabled(True)
        self.action_stop_analysis.setEnabled(False)
        self.progress_bar.setVisible(False)
        QMessageBox.critical(self, "Erreur Analyse", err)

    @Slot(dict)
    def on_patient_loaded(self, info):
        self.action_run_analysis.setEnabled(True)

    @Slot()
    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
            
    @Slot()
    def show_about(self):
        AboutDialog(self).exec()

    @Slot()
    def set_ui_enabled(self, enabled):
        self.centralWidget().setEnabled(enabled)

    @Slot()
    def set_analysis_ui_state(self, enabled):
        # Logic to disable specific parts during analysis
        pass

    @Slot()
    def log_message(self, msg, level='info'):
        # Log to file or console
        print(f"[{level.upper()}] {msg}")
    
    @Slot()
    def update_ui_state(self):
        pass