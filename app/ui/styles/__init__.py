
import os
from pathlib import Path

def load_stylesheet(theme_name: str = "dark") -> str:
    """Charger la feuille de style QSS"""
    base_dir = Path(__file__).parent
    
    if theme_name == "dark":
        file_path = base_dir / "dark_theme.qss"
    else:
        file_path = base_dir / "light_theme.qss"
        
    if file_path.exists():
        with open(file_path, "r") as f:
            return f.read()
    return ""

def get_icon(name: str):
    """Placeholder pour le chargement d'icônes"""
    from PySide6.QtGui import QIcon
    # Ici, on devrait charger l'icône depuis un fichier
    # Pour l'instant on retourne une icône vide
    return QIcon()