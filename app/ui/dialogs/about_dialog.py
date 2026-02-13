
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton, 
    QHBoxLayout, QWidget, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPixmap

from ...core.config import Config

class AboutDialog(QDialog):
    """Boîte de dialogue À propos"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = Config()
        self.setup_ui()
        
    def setup_ui(self):
        self.setWindowTitle("À propos de SpineAnalyzer Pro")
        self.setFixedSize(500, 400)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Titre et Logo
        header_layout = QHBoxLayout()
        
        # Logo (placeholder ou load if exists)
        # logo_label = QLabel()
        # logo_label.setPixmap(QPixmap("resources/icons/app_icon.png").scaled(64, 64, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        # header_layout.addWidget(logo_label)
        
        title_layout = QVBoxLayout()
        title = QLabel("SpineAnalyzer Pro")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #007acc;")
        verson = QLabel(f"Version {self.config.get('app/version', '1.0.0')}")
        verson.setStyleSheet("font-size: 14px; color: #888;")
        
        title_layout.addWidget(title)
        title_layout.addWidget(verson)
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # Ligne de séparation
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        layout.addWidget(line)
        
        # Description
        desc_text = """
        <p><b>SpineAnalyzer Pro</b> est une application médicale d'analyse rachidienne assistée par intelligence artificielle.</p>
        <p>Cette application permet :</p>
        <ul>
            <li>La visualisation d'images DICOM</li>
            <li>La reconstruction 3D du rachis</li>
            <li>La détection automatique d'anomalies (fractures, hernies, etc.)</li>
            <li>L'analyse quantitative et biométrique</li>
        </ul>
        <p><i>Développé par l'équipe MedicalAI.</i></p>
        """
        desc = QLabel(desc_text)
        desc.setWordWrap(True)
        desc.setTextFormat(Qt.RichText)
        layout.addWidget(desc)
        
        layout.addStretch()
        
        # Copyright / Licence
        footer_layout = QVBoxLayout()
        footer_layout.setSpacing(2)
        license = QLabel("Licence: MIT")
        license.setStyleSheet("color: #666; font-size: 11px;")
        copyright = QLabel("© 2024 MedicalAI Team. Tous droits réservés.")
        copyright.setStyleSheet("color: #666; font-size: 11px;")
        
        footer_layout.addWidget(license, 0, Qt.AlignCenter)
        footer_layout.addWidget(copyright, 0, Qt.AlignCenter)
        layout.addLayout(footer_layout)
        
        # Bouton Fermer
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        close_btn = QPushButton("Fermer")
        close_btn.setFixedWidth(100)
        close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(close_btn)
        btn_layout.addStretch()
        
        layout.addLayout(btn_layout)
