
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
    
    # Mapping des noms d'icônes vers les icônes standard Qt
    mapping = {
        # File operations
        "folder_open": QStyle.SP_DirOpenIcon,
        "file_open": QStyle.SP_FileIcon,
        "save": QStyle.SP_DialogSaveButton,
        "export": QStyle.SP_DialogSaveButton,
        "exit": QStyle.SP_DialogCloseButton,
        
        # Navigation / Actions
        "play": QStyle.SP_MediaPlay,
        "stop": QStyle.SP_MediaStop,
        "pause": QStyle.SP_MediaPause,
        "settings": QStyle.SP_FileDialogDetailedView,
        "help": QStyle.SP_DialogHelpButton,
        "about": QStyle.SP_MessageBoxInformation,
        
        # Views
        "view_axial": QStyle.SP_FileDialogListView,
        "view_coronal": QStyle.SP_FileDialogDetailedView,
        "view_sagittal": QStyle.SP_FileDialogInfoView,
        
        # Tools
        "annotation": QStyle.SP_FileIcon,
        "measure": QStyle.SP_FileDialogDetailedView,
        "compare": QStyle.SP_BrowserReload,
        
        # Editor
        "undo": QStyle.SP_ArrowBack,
        "redo": QStyle.SP_ArrowForward,
        
        # App
        "app_icon": QStyle.SP_DesktopIcon,
        "3d": QStyle.SP_ComputerIcon
    }
    
    if name in mapping:
        return style.standardIcon(mapping[name])
        
    return QIcon()