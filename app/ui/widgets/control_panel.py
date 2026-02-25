
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QPushButton, QLabel, QStyle
)
from PySide6.QtCore import Qt, Signal, Slot

from ...core.logger import get_logger
from .custom_widgets import ModernCard, InfoRow, StatusLed

logger = get_logger(__name__)

class ControlPanel(QWidget):
    """Panneau de contrôle principal"""
    
    # Signaux
    analysis_requested = Signal()
    export_requested = Signal()
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.patient_info = {}
        self.setup_ui()
        
    def setup_ui(self):
        """Configurer l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)
        
        # --- Section Patient ---
        self.patient_card = ModernCard("Patient Actuel")
        
        self.row_name = InfoRow("Nom")
        self.row_id = InfoRow("ID")
        self.row_modality = InfoRow("Modalité")
        
        self.patient_card.add_widget(self.row_name)
        self.patient_card.add_widget(self.row_id)
        self.patient_card.add_widget(self.row_modality)
        
        layout.addWidget(self.patient_card)
        
        # --- Section Analyse ---
        self.analysis_card = ModernCard("Actions Analyse")
        
        # Status
        status_layout = QVBoxLayout()
        self.status_led = StatusLed(color="#00e676") # Green
        self.status_label = QLabel("Prêt")
        self.status_label.setStyleSheet("color: #888;")
        
        # Analysis Button
        self.btn_analyze = QPushButton("Lancer l'analyse complète")
        self.btn_analyze.setMinimumHeight(45)
        self.btn_analyze.setCursor(Qt.PointingHandCursor)
        self.btn_analyze.setStyleSheet("""
            QPushButton {
                background-color: #1976d2; 
                font-weight: bold; 
                font-size: 11pt;
                border: none;
            }
            QPushButton:hover { background-color: #2196f3; }
            QPushButton:pressed { background-color: #0d47a1; }
            QPushButton:disabled { background-color: #333; color: #666; }
        """)
        self.btn_analyze.clicked.connect(self.analysis_requested.emit)
        self.btn_analyze.setEnabled(False) 
        
        self.analysis_card.add_widget(self.btn_analyze)
        
        # Info about analysis
        hint = QLabel("Détection automatique des vertèbres et anomalies.")
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #666; font-size: 9pt; font-style: italic;")
        self.analysis_card.add_widget(hint)
        
        layout.addWidget(self.analysis_card)
        
        # --- Section Export ---
        self.export_card = ModernCard("Rapports")
        
        self.btn_export = QPushButton("Générer & Exporter Dossier")
        self.btn_export.setMinimumHeight(40)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DialogSaveButton))
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.btn_export.setEnabled(False)
        
        self.export_card.add_widget(self.btn_export)
        layout.addWidget(self.export_card)
        
        layout.addStretch()
        
        # System Footer
        sys_info = QLabel("SpineAnalyzer Pro v1.0")
        sys_info.setAlignment(Qt.AlignCenter)
        sys_info.setStyleSheet("color: #444; font-size: 8pt; margin-bottom: 5px;")
        layout.addWidget(sys_info)

    def set_patient_info(self, info: Dict[str, Any]):
        """Mettre à jour les informations du patient"""
        self.patient_info = info
        
        self.row_name.set_value(info.get('name', 'Inconnu'))
        self.row_id.set_value(info.get('id', 'N/A'))
        self.row_modality.set_value(info.get('modality', 'N/A'))
        
        self.btn_analyze.setEnabled(True)
        self.status_label.setText("Prêt pour analyse")
        self.status_led.set_status(True, "#2196f3") # Blue for ready

    def set_analysis_state(self, is_running: bool):
        """Mettre à jour l'état des boutons pendant l'analyse"""
        self.btn_analyze.setEnabled(not is_running)
        self.btn_export.setEnabled(False)
        
        if is_running:
            self.btn_analyze.setText("Analyse en cours...")
            self.status_led.set_status(True, "#ff9800") # Orange
        else:
            self.btn_analyze.setText("Lancer l'analyse complète")
        
    def set_results_ready(self, ready: bool = True):
        """Activer l'export une fois les résultats prêts"""
        self.btn_export.setEnabled(ready)
        if ready:
            self.status_led.set_status(True, "#00e676") # Green
            self.btn_analyze.setText("Relancer l'analyse")
