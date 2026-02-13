
from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout
from PySide6.QtCore import Qt
from .custom_widgets import ModernCard, InfoRow

class PatientInfoWidget(QWidget):
    """Widget affichant les informations du patient"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Create Modern Card
        self.card = ModernCard("Dossier Patient")
        
        # Profile Header (Icon + Name)
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Placeholder Icon (could be replaced with real image later)
        icon_label = QLabel("👤")
        icon_label.setStyleSheet("""
            font-size: 32px;
            background-color: #333;
            border-radius: 24px;
            padding: 8px;
            min-width: 48px;
            min-height: 48px;
            qproperty-alignment: AlignCenter;
        """)
        header_layout.addWidget(icon_label)
        
        # Name and ID
        name_layout = QVBoxLayout()
        name_layout.setSpacing(2)
        
        self.lbl_name = QLabel("-")
        self.lbl_name.setStyleSheet("font-size: 14pt; font-weight: bold; color: #ffffff;")
        
        self.lbl_id = QLabel("ID: -")
        self.lbl_id.setStyleSheet("font-size: 9pt; color: #2196f3; font-weight: bold;")
        
        name_layout.addWidget(self.lbl_name)
        name_layout.addWidget(self.lbl_id)
        header_layout.addLayout(name_layout)
        header_layout.addStretch()
        
        self.card.add_layout(header_layout)
        
        # Divider
        line = QLabel()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #333333; margin: 4px 0;")
        self.card.add_widget(line)
        
        # Details
        self.row_sex = InfoRow("Sexe")
        self.row_birth = InfoRow("Date Naissance")
        self.row_date = InfoRow("Date Examen")
        self.row_inst = InfoRow("Institution")
        
        self.card.add_widget(self.row_sex)
        self.card.add_widget(self.row_birth)
        self.card.add_widget(self.row_date)
        self.card.add_widget(self.row_inst)
        
        layout.addWidget(self.card)
        
    def set_data(self, info: dict):
        """Mettre à jour les données"""
        name = str(info.get('name', 'Inconnu'))
        pid = str(info.get('id', 'N/A'))
        
        self.lbl_name.setText(name)
        self.lbl_id.setText(f"ID: {pid}")
        
        self.row_sex.set_value(info.get('sex', 'N/A'))
        self.row_birth.set_value(info.get('birth_date', 'N/A'))
        self.row_date.set_value(info.get('study_date', 'N/A'))
        self.row_inst.set_value(info.get('institution', 'N/A'))
