
from typing import Dict, Any

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QGroupBox, QCheckBox, QComboBox, 
    QLineEdit, QFileDialog, QFormLayout
)
from PySide6.QtCore import Qt

class ExportDialog(QDialog):
    """Dialogue pour l'exportation des résultats"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("Exporter le rapport")
        self.setFixedWidth(450)
        
        layout = QVBoxLayout(self)
        
        # Format d'export
        format_group = QGroupBox("Format")
        format_layout = QVBoxLayout()
        
        self.fmt_pdf = QCheckBox("Rapport PDF")
        self.fmt_pdf.setChecked(True)
        
        self.fmt_dicom = QCheckBox("DICOM Structured Report (SR)")
        self.fmt_dicom.setChecked(False)
        self.fmt_dicom.setToolTip("Non disponible dans cette version")
        self.fmt_dicom.setEnabled(False)
        
        self.fmt_images = QCheckBox("Images annotées (JPG/PNG)")
        self.fmt_images.setChecked(True)
        
        format_layout.addWidget(self.fmt_pdf)
        format_layout.addWidget(self.fmt_dicom)
        format_layout.addWidget(self.fmt_images)
        format_group.setLayout(format_layout)
        layout.addWidget(format_group)
        
        # Contenu
        content_group = QGroupBox("Contenu à inclure")
        content_layout = QVBoxLayout()
        
        self.inc_patient = QCheckBox("Informations patient")
        self.inc_patient.setChecked(True)
        self.inc_patient.setEnabled(False) # Obligatoire
        
        self.inc_measurements = QCheckBox("Mesures et métriques")
        self.inc_measurements.setChecked(True)
        
        self.inc_anomalies = QCheckBox("Liste des anomalies détectées")
        self.inc_anomalies.setChecked(True)
        
        self.inc_3d = QCheckBox("Captures de la reconstruction 3D")
        self.inc_3d.setChecked(True)
        
        content_layout.addWidget(self.inc_patient)
        content_layout.addWidget(self.inc_measurements)
        content_layout.addWidget(self.inc_anomalies)
        content_layout.addWidget(self.inc_3d)
        content_group.setLayout(content_layout)
        layout.addWidget(content_group)
        
        # Destination
        dest_group = QGroupBox("Destination")
        dest_layout = QHBoxLayout()
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Sélectionner un dossier...")
        
        browse_btn = QPushButton("Parcourir...")
        browse_btn.clicked.connect(self.browse_folder)
        
        dest_layout.addWidget(self.path_edit)
        dest_layout.addWidget(browse_btn)
        dest_group.setLayout(dest_layout)
        layout.addWidget(dest_group)
        
        # Boutons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.btn_cancel = QPushButton("Annuler")
        self.btn_cancel.clicked.connect(self.reject)
        
        self.btn_export = QPushButton("Exporter")
        self.btn_export.setDefault(True)
        self.btn_export.setStyleSheet("background-color: #007acc; color: white; font-weight: bold;")
        self.btn_export.clicked.connect(self.accept)
        
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_export)
        layout.addLayout(btn_layout)
        
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choisir le dossier de destination")
        if folder:
            self.path_edit.setText(folder)
            
    def get_export_params(self) -> Dict[str, Any]:
        """Récupérer les paramètres choisis"""
        return {
            'formats': {
                'pdf': self.fmt_pdf.isChecked(),
                'dicom_sr': self.fmt_dicom.isChecked(),
                'images': self.fmt_images.isChecked()
            },
            'content': {
                'measurements': self.inc_measurements.isChecked(),
                'anomalies': self.inc_anomalies.isChecked(),
                '3d_views': self.inc_3d.isChecked()
            },
            'destination': self.path_edit.text()
        }
