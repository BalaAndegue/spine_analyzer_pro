
from PySide6.QtWidgets import QWidget, QFormLayout, QLabel, QGroupBox, QVBoxLayout
from PySide6.QtCore import Qt

class PatientInfoWidget(QWidget):
    """Widget affichant les informations du patient"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        group = QGroupBox("Informations Patient")
        form = QFormLayout()
        form.setLabelAlignment(Qt.AlignRight)
        
        self.lbl_name = QLabel("-")
        self.lbl_id = QLabel("-")
        self.lbl_sex = QLabel("-")
        self.lbl_birth = QLabel("-")
        self.lbl_date = QLabel("-")
        self.lbl_inst = QLabel("-")
        
        # Style pour les valeurs
        val_style = "font-weight: bold; color: #007acc;"
        self.lbl_name.setStyleSheet(val_style)
        self.lbl_id.setStyleSheet(val_style)
        
        form.addRow("Nom:", self.lbl_name)
        form.addRow("ID:", self.lbl_id)
        form.addRow("Sexe:", self.lbl_sex)
        form.addRow("Date Naissance:", self.lbl_birth)
        form.addRow("Date Examen:", self.lbl_date)
        form.addRow("Institution:", self.lbl_inst)
        
        group.setLayout(form)
        layout.addWidget(group)
        
    def set_data(self, info: dict):
        """Mettre à jour les données"""
        self.lbl_name.setText(str(info.get('name', 'Inconnu')))
        self.lbl_id.setText(str(info.get('id', 'N/A')))
        self.lbl_sex.setText(str(info.get('sex', 'N/A')))
        self.lbl_birth.setText(str(info.get('birth_date', 'N/A')))
        self.lbl_date.setText(str(info.get('study_date', 'N/A')))
        self.lbl_inst.setText(str(info.get('institution', 'N/A')))
