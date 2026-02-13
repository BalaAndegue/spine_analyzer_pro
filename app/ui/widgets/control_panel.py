
import logging
from typing import Dict, Any, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QGroupBox, QFormLayout, QFrame
)
from PySide6.QtCore import Qt, Signal, Slot

from ..core.logger import get_logger

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
        
        # Section Informations Patient
        info_group = QGroupBox("Patient")
        info_layout = QFormLayout()
        info_layout.setLabelAlignment(Qt.AlignRight)
        
        self.lbl_name = QLabel("-")
        self.lbl_id = QLabel("-")
        self.lbl_date = QLabel("-")
        self.lbl_modality = QLabel("-")
        
        info_layout.addRow("Nom:", self.lbl_name)
        info_layout.addRow("ID:", self.lbl_id)
        info_layout.addRow("Date:", self.lbl_date)
        info_layout.addRow("Modalité:", self.lbl_modality)
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Section Actions
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout()
        actions_layout.setSpacing(10)
        
        self.btn_analyze = QPushButton("Lancer l'analyse")
        self.btn_analyze.setMinimumHeight(40)
        self.btn_analyze.setStyleSheet("background-color: #007acc; color: white; font-weight: bold;")
        self.btn_analyze.clicked.connect(self.analysis_requested.emit)
        self.btn_analyze.setEnabled(False)  # Désactivé tant qu'aucun patient n'est chargé
        
        self.btn_export = QPushButton("Exporter le rapport")
        self.btn_export.setMinimumHeight(30)
        self.btn_export.clicked.connect(self.export_requested.emit)
        self.btn_export.setEnabled(False)
        
        actions_layout.addWidget(self.btn_analyze)
        actions_layout.addWidget(self.btn_export)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Spacer pour pousser vers le haut
        layout.addStretch()
        
        # Version ou infos système
        sys_info = QLabel("System Ready")
        sys_info.setAlignment(Qt.AlignCenter)
        sys_info.setStyleSheet("color: #666;")
        layout.addWidget(sys_info)

    def set_patient_info(self, info: Dict[str, Any]):
        """Mettre à jour les informations du patient"""
        self.patient_info = info
        
        self.lbl_name.setText(str(info.get('name', 'Inconnu')))
        self.lbl_id.setText(str(info.get('id', 'N/A')))
        self.lbl_date.setText(str(info.get('study_date', 'N/A')))
        self.lbl_modality.setText(str(info.get('modality', 'N/A')))
        
        # Activer le bouton d'analyse si on a un patient
        self.btn_analyze.setEnabled(True)
        self.btn_export.setEnabled(False) # Sera activé après analyse

    def set_analysis_state(self, is_running: bool):
        """Mettre à jour l'état des boutons pendant l'analyse"""
        self.btn_analyze.setEnabled(not is_running)
        self.btn_export.setEnabled(False)
        
    def set_results_ready(self, ready: bool = True):
        """Activer l'export une fois les résultats prêts"""
        self.btn_export.setEnabled(ready)
