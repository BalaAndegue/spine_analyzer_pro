
import os
from pathlib import Path
from PySide6.QtWidgets import QApplication, QStyle
from PySide6.QtGui import QIcon

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


def get_icon(name: str) -> QIcon:
    """
    Récupérer une icône.
    Utilise les icônes standard de QStyle si disponibles.
    """
    style = QApplication.style()
    SP = QStyle.StandardPixmap
    
    # Mapping des noms d'icônes vers les icônes standard Qt
    mapping = {
        # File operations
        "folder_open": SP.SP_DirOpenIcon,
        "file_open": SP.SP_FileIcon,
        "save": SP.SP_DialogSaveButton,
        "export": SP.SP_DialogSaveButton,
        "exit": SP.SP_DialogCloseButton,
        
        # Navigation / Actions
        "play": SP.SP_MediaPlay,
        "stop": SP.SP_MediaStop,
        "pause": SP.SP_MediaPause,
        "settings": SP.SP_FileDialogDetailedView,
        "help": SP.SP_DialogHelpButton,
        "about": SP.SP_MessageBoxInformation,
        
        # Views
        "view_axial": SP.SP_FileDialogListView,
        "view_coronal": SP.SP_FileDialogDetailedView,
        "view_sagittal": SP.SP_FileDialogInfoView,
        
        # Tools
        "annotation": SP.SP_FileIcon,
        "measure": SP.SP_FileDialogDetailedView,
        "compare": SP.SP_BrowserReload,
        
        # Editor
        "undo": SP.SP_ArrowBack,
        "redo": SP.SP_ArrowForward,
        
        # App
        "app_icon": SP.SP_DesktopIcon,
        "3d": SP.SP_ComputerIcon
    }
    
    if name in mapping:
        return style.standardIcon(mapping[name])
        
    return QIcon()