"""
Boîte de dialogue des paramètres
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget,
    QWidget, QLabel, QComboBox, QSpinBox, QDoubleSpinBox,
    QCheckBox, QLineEdit, QPushButton, QGroupBox,
    QFormLayout, QFileDialog, QMessageBox, QListWidget
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QIntValidator, QDoubleValidator

from ...core.config import Config
from ...core.logger import get_logger

logger = get_logger(__name__)


class SettingsDialog(QDialog):
    """Dialogue des paramètres de l'application"""
    
    settings_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.settings = {}
        
        self.setup_ui()
        self.load_settings()
        self.setup_connections()
    
    def setup_ui(self):
        """Configurer l'interface"""
        self.setWindowTitle("Paramètres - SpineAnalyzer Pro")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout(self)
        
        # Onglets
        self.tab_widget = QTabWidget()
        
        # Onglet Interface
        self.ui_tab = self.create_ui_tab()
        self.tab_widget.addTab(self.ui_tab, "Interface")
        
        # Onglet IA/Modèles
        self.ai_tab = self.create_ai_tab()
        self.tab_widget.addTab(self.ai_tab, "IA & Modèles")
        
        # Onglet Performance
        self.perf_tab = self.create_performance_tab()
        self.tab_widget.addTab(self.perf_tab, "Performance")
        
        # Onglet Export
        self.export_tab = self.create_export_tab()
        self.tab_widget.addTab(self.export_tab, "Export")
        
        layout.addWidget(self.tab_widget)
        
        # Boutons
        button_layout = QHBoxLayout()
        
        self.btn_apply = QPushButton("Appliquer")
        self.btn_ok = QPushButton("OK")
        self.btn_cancel = QPushButton("Annuler")
        self.btn_reset = QPushButton("Réinitialiser")
        
        button_layout.addWidget(self.btn_reset)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_apply)
        button_layout.addWidget(self.btn_ok)
        button_layout.addWidget(self.btn_cancel)
        
        layout.addLayout(button_layout)
    
    def create_ui_tab(self) -> QWidget:
        """Créer l'onglet Interface"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Thème
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["Sombre", "Clair", "Médical"])
        layout.addRow("Thème:", self.theme_combo)
        
        # Langue
        self.language_combo = QComboBox()
        self.language_combo.addItems(["Français", "English", "Español"])
        layout.addRow("Langue:", self.language_combo)
        
        # Taille de police
        self.font_size_spin = QSpinBox()
        self.font_size_spin.setRange(8, 20)
        layout.addRow("Taille police:", self.font_size_spin)
        
        # Dernier dossier
        self.last_folder_edit = QLineEdit()
        self.btn_browse_folder = QPushButton("Parcourir...")
        
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(self.last_folder_edit)
        folder_layout.addWidget(self.btn_browse_folder)
        
        layout.addRow("Dernier dossier:", folder_layout)
        
        # Options d'interface
        self.check_auto_load = QCheckBox("Charger automatiquement le dernier dossier")
        self.check_auto_report = QCheckBox("Générer automatiquement un rapport après analyse")
        self.check_save_window_state = QCheckBox("Sauvegarder l'état des fenêtres")
        
        layout.addRow(self.check_auto_load)
        layout.addRow(self.check_auto_report)
        layout.addRow(self.check_save_window_state)
        
        return widget
    
    def create_ai_tab(self) -> QWidget:
        """Créer l'onglet IA & Modèles"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Device
        self.device_combo = QComboBox()
        self.device_combo.addItems(["Auto", "CPU", "GPU"])
        layout.addRow("Périphérique:", self.device_combo)
        
        # Batch size
        self.batch_size_spin = QSpinBox()
        self.batch_size_spin.setRange(1, 16)
        layout.addRow("Taille de batch:", self.batch_size_spin)
        
        # Seuil de confiance
        self.confidence_spin = QDoubleSpinBox()
        self.confidence_spin.setRange(0.1, 1.0)
        self.confidence_spin.setSingleStep(0.05)
        layout.addRow("Seuil confiance:", self.confidence_spin)
        
        # Modèles
        layout.addRow(QLabel("<b>Modèles pré-entraînés:</b>"))
        
        self.model_list = QListWidget()
        self.model_list.addItems([
            "Ségmentation vertébrale",
            "Détection fractures",
            "Classification tumeurs",
            "Reconstruction 3D"
        ])
        self.model_list.setMaximumHeight(100)
        layout.addRow(self.model_list)
        
        # Chemin modèles
        self.model_path_edit = QLineEdit()
        self.btn_browse_models = QPushButton("Parcourir...")
        
        model_path_layout = QHBoxLayout()
        model_path_layout.addWidget(self.model_path_edit)
        model_path_layout.addWidget(self.btn_browse_models)
        
        layout.addRow("Dossier modèles:", model_path_layout)
        
        return widget
    
    def create_performance_tab(self) -> QWidget:
        """Créer l'onglet Performance"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Threads
        self.threads_spin = QSpinBox()
        self.threads_spin.setRange(1, 16)
        layout.addRow("Threads:", self.threads_spin)
        
        # Cache
        self.cache_size_spin = QSpinBox()
        self.cache_size_spin.setRange(100, 10000)
        self.cache_size_spin.setSuffix(" MB")
        layout.addRow("Cache max:", self.cache_size_spin)
        
        # Compression
        self.compression_combo = QComboBox()
        self.compression_combo.addItems(["Aucune", "Légère", "Moyenne", "Forte"])
        layout.addRow("Compression:", self.compression_combo)
        
        # Logging
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR"])
        layout.addRow("Niveau log:", self.log_level_combo)
        
        return widget
    
    def create_export_tab(self) -> QWidget:
        """Créer l'onglet Export"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # Format par défaut
        self.format_combo = QComboBox()
        self.format_combo.addItems(["PDF", "HTML", "DICOM SR", "DOCX"])
        layout.addRow("Format:", self.format_combo)
        
        # Dossier d'export
        self.export_path_edit = QLineEdit()
        self.btn_browse_export = QPushButton("Parcourir...")
        
        export_layout = QHBoxLayout()
        export_layout.addWidget(self.export_path_edit)
        export_layout.addWidget(self.btn_browse_export)
        
        layout.addRow("Dossier export:", export_layout)
        
        # Options d'export
        self.check_include_images = QCheckBox("Inclure les images")
        self.check_include_3d = QCheckBox("Inclure les vues 3D")
        self.check_open_after_export = QCheckBox("Ouvrir après export")
        self.check_annotations = QCheckBox("Inclure les annotations")
        
        layout.addRow(self.check_include_images)
        layout.addRow(self.check_include_3d)
        layout.addRow(self.check_open_after_export)
        layout.addRow(self.check_annotations)
        
        return widget
    
    def setup_connections(self):
        """Établir les connexions"""
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_ok.clicked.connect(self.accept_and_apply)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        
        self.btn_browse_folder.clicked.connect(self.browse_folder)
        self.btn_browse_models.clicked.connect(self.browse_models)
        self.btn_browse_export.clicked.connect(self.browse_export)
    
    def load_settings(self):
        """Charger les paramètres actuels"""
        # Interface
        theme_map = {'dark': 0, 'light': 1, 'medical': 2}
        theme = self.config.get('ui/theme', 'dark')
        self.theme_combo.setCurrentIndex(theme_map.get(theme, 0))
        
        language = self.config.get('ui/language', 'fr')
        lang_map = {'fr': 0, 'en': 1, 'es': 2}
        self.language_combo.setCurrentIndex(lang_map.get(language, 0))
        
        self.font_size_spin.setValue(self.config.get('ui/font_size', 10))
        self.last_folder_edit.setText(self.config.get('last_folder', ''))
        self.check_auto_load.setChecked(self.config.get('ui/auto_load', True))
        self.check_auto_report.setChecked(self.config.get('ui/auto_report', False))
        self.check_save_window_state.setChecked(self.config.get('ui/save_window_state', True))
        
        # IA
        device = self.config.get('ai/device', 'auto')
        device_map = {'auto': 0, 'cpu': 1, 'gpu': 2}
        self.device_combo.setCurrentIndex(device_map.get(device, 0))
        
        self.batch_size_spin.setValue(self.config.get('ai/batch_size', 4))
        self.confidence_spin.setValue(self.config.get('ai/confidence_threshold', 0.5))
        self.model_path_edit.setText(self.config.get('ai/model_path', './models'))
        
        # Performance
        self.threads_spin.setValue(self.config.get('performance/threads', 4))
        self.cache_size_spin.setValue(self.config.get('performance/cache_size_mb', 1024))
        
        compression = self.config.get('performance/compression', 'none')
        comp_map = {'none': 0, 'light': 1, 'medium': 2, 'strong': 3}
        self.compression_combo.setCurrentIndex(comp_map.get(compression, 0))
        
        log_level = self.config.get('logging/level', 'INFO')
        level_map = {'DEBUG': 0, 'INFO': 1, 'WARNING': 2, 'ERROR': 3}
        self.log_level_combo.setCurrentIndex(level_map.get(log_level, 1))
        
        # Export
        export_format = self.config.get('export/format', 'pdf')
        format_map = {'pdf': 0, 'html': 1, 'dicom_sr': 2, 'docx': 3}
        self.format_combo.setCurrentIndex(format_map.get(export_format, 0))
        
        self.export_path_edit.setText(self.config.get('export/path', './exports'))
        self.check_include_images.setChecked(self.config.get('export/include_images', True))
        self.check_include_3d.setChecked(self.config.get('export/include_3d', False))
        self.check_open_after_export.setChecked(self.config.get('export/open_after_export', True))
        self.check_annotations.setChecked(self.config.get('export/include_annotations', True))
    
    def get_current_settings(self) -> dict:
        """Obtenir les paramètres actuels de l'interface"""
        return {
            'ui/theme': ['dark', 'light', 'medical'][self.theme_combo.currentIndex()],
            'ui/language': ['fr', 'en', 'es'][self.language_combo.currentIndex()],
            'ui/font_size': self.font_size_spin.value(),
            'last_folder': self.last_folder_edit.text(),
            'ui/auto_load': self.check_auto_load.isChecked(),
            'ui/auto_report': self.check_auto_report.isChecked(),
            'ui/save_window_state': self.check_save_window_state.isChecked(),
            
            'ai/device': ['auto', 'cpu', 'gpu'][self.device_combo.currentIndex()],
            'ai/batch_size': self.batch_size_spin.value(),
            'ai/confidence_threshold': self.confidence_spin.value(),
            'ai/model_path': self.model_path_edit.text(),
            
            'performance/threads': self.threads_spin.value(),
            'performance/cache_size_mb': self.cache_size_spin.value(),
            'performance/compression': ['none', 'light', 'medium', 'strong'][self.compression_combo.currentIndex()],
            'logging/level': ['DEBUG', 'INFO', 'WARNING', 'ERROR'][self.log_level_combo.currentIndex()],
            
            'export/format': ['pdf', 'html', 'dicom_sr', 'docx'][self.format_combo.currentIndex()],
            'export/path': self.export_path_edit.text(),
            'export/include_images': self.check_include_images.isChecked(),
            'export/include_3d': self.check_include_3d.isChecked(),
            'export/open_after_export': self.check_open_after_export.isChecked(),
            'export/include_annotations': self.check_annotations.isChecked()
        }
    
    @Slot()
    def apply_settings(self):
        """Appliquer les paramètres"""
        settings = self.get_current_settings()
        
        # Sauvegarder dans la configuration
        for key, value in settings.items():
            self.config.set(key, value)
        
        self.config.save()
        
        # Émettre le signal
        self.settings_changed.emit(settings)
        
        QMessageBox.information(
            self,
            "Paramètres",
            "Paramètres appliqués avec succès."
        )
    
    @Slot()
    def accept_and_apply(self):
        """Appliquer et fermer"""
        self.apply_settings()
        self.accept()
    
    @Slot()
    def reset_to_defaults(self):
        """Réinitialiser aux valeurs par défaut"""
        reply = QMessageBox.question(
            self,
            "Réinitialiser",
            "Voulez-vous vraiment réinitialiser tous les paramètres aux valeurs par défaut?",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.config.reset_to_defaults()
            self.load_settings()
    
    @Slot()
    def browse_folder(self):
        """Parcourir pour un dossier"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner un dossier",
            self.last_folder_edit.text()
        )
        
        if folder:
            self.last_folder_edit.setText(folder)
    
    @Slot()
    def browse_models(self):
        """Parcourir pour un dossier de modèles"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier des modèles",
            self.model_path_edit.text()
        )
        
        if folder:
            self.model_path_edit.setText(folder)
    
    @Slot()
    def browse_export(self):
        """Parcourir pour un dossier d'export"""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier d'export",
            self.export_path_edit.text()
        )
        
        if folder:
            self.export_path_edit.setText(folder)