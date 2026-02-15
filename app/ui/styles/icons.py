"""
Gestionnaire centralisé d'icônes pour SpineAnalyzer Pro
Utilise QtAwesome pour des icônes vectorielles modernes
"""

from PySide6.QtGui import QIcon, QPixmap, QPainter, QColor
from PySide6.QtCore import Qt, QSize
from PySide6.QtWidgets import QStyle, QApplication
from typing import Optional, Dict
import qtawesome as qta


class IconManager:
    """Gestionnaire centralisé d'icônes pour l'application"""
    
    # Mapping des noms d'icônes vers les icônes FontAwesome
    _ICON_MAP: Dict[str, str] = {
        # Fichiers et dossiers
        'open': 'fa5s.folder-open',
        'open-file': 'fa5s.file-medical',
        'save': 'fa5s.save',
        'export': 'fa5s.file-export',
        'import': 'fa5s.file-import',
        'folder': 'fa5s.folder',
        
        # Actions
        'play': 'fa5s.play',
        'pause': 'fa5s.pause',
        'stop': 'fa5s.stop',
        'refresh': 'fa5s.sync-alt',
        'settings': 'fa5s.cog',
        'preferences': 'fa5s.sliders-h',
        
        # Navigation
        'first': 'fa5s.step-backward',
        'previous': 'fa5s.chevron-left',
        'next': 'fa5s.chevron-right',
        'last': 'fa5s.step-forward',
        'up': 'fa5s.chevron-up',
        'down': 'fa5s.chevron-down',
        
        # Zoom et visualisation
        'zoom-in': 'fa5s.search-plus',
        'zoom-out': 'fa5s.search-minus',
        'zoom-fit': 'fa5s.compress',
        'zoom-reset': 'fa5s.expand',
        'fullscreen': 'fa5s.expand-arrows-alt',
        
        # Outils médicaux
        'analyze': 'fa5s.microscope',
        'brain': 'fa5s.brain',
        'bone': 'fa5s.bone',
        'heart': 'fa5s.heartbeat',
        'xray': 'fa5s.x-ray',
        
        # Interface
        'info': 'fa5s.info-circle',
        'warning': 'fa5s.exclamation-triangle',
        'error': 'fa5s.times-circle',
        'success': 'fa5s.check-circle',
        'help': 'fa5s.question-circle',
        'about': 'fa5s.info',
        
        # Édition
        'edit': 'fa5s.edit',
        'delete': 'fa5s.trash',
        'add': 'fa5s.plus',
        'remove': 'fa5s.minus',
        'clear': 'fa5s.times',
        
        # Divers
        'close': 'fa5s.times',
        'exit': 'fa5s.sign-out-alt',
        'user': 'fa5s.user',
        'calendar': 'fa5s.calendar',
        'clock': 'fa5s.clock',
        'chart': 'fa5s.chart-line',
        'report': 'fa5s.file-alt',
        'print': 'fa5s.print',
        
        # 3D et annotation
        'cube': 'fa5s.cube',
        'ruler': 'fa5s.ruler',
        'pen': 'fa5s.pen',
        'marker': 'fa5s.map-marker-alt',
    }
    
    _cache: Dict[str, QIcon] = {}
    
    @classmethod
    def get(cls, name: str, color: Optional[str] = None, size: int = 16) -> QIcon:
        """
        Récupère une icône par nom
        
        Args:
            name: Nom de l'icône (voir _ICON_MAP)
            color: Couleur de l'icône (hex ou nom CSS), None pour couleur par défaut
            size: Taille de l'icône en pixels
            
        Returns:
            QIcon de l'icône demandée
        """
        cache_key = f"{name}_{color}_{size}"
        
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # Récupérer le nom FontAwesome
        fa_name = cls._ICON_MAP.get(name, 'fa5s.question')
        
        try:
            # Options pour l'icône
            options = {}
            if color:
                options['color'] = color
            
            # Créer l'icône avec qtawesome
            icon = qta.icon(fa_name, **options)
            
            # Mettre en cache
            cls._cache[cache_key] = icon
            return icon
            
        except Exception as e:
            # Fallback sur une icône système en cas d'erreur
            print(f"Erreur lors de la création de l'icône '{name}': {e}")
            return cls._get_system_icon('SP_MessageBoxQuestion')
    
    @classmethod
    def _get_system_icon(cls, sp_icon: str) -> QIcon:
        """Récupère une icône système Qt"""
        app = QApplication.instance()
        if app and hasattr(QStyle, sp_icon):
            style = app.style()
            return style.standardIcon(getattr(QStyle, sp_icon))
        return QIcon()
    
    @classmethod
    def get_themed(cls, name: str, theme: str = 'dark', size: int = 16) -> QIcon:
        """
        Récupère une icône avec la couleur adaptée au thème
        
        Args:
            name: Nom de l'icône
            theme: 'dark' ou 'light'
            size: Taille de l'icône
            
        Returns:
            QIcon avec la couleur adaptée au thème
        """
        color = '#e0e0e0' if theme == 'dark' else '#212121'
        return cls.get(name, color=color, size=size)
    
    @classmethod
    def create_colored_icon(cls, name: str, color: str, size: int = 16) -> QIcon:
        """
        Crée une icône colorée
        
        Args:
            name: Nom de l'icône
            color: Couleur de l'icône (hex)
            size: Taille de l'icône
            
        Returns:
            QIcon colorée
        """
        return cls.get(name, color=color, size=size)
    
    @classmethod
    def clear_cache(cls):
        """Vide le cache d'icônes"""
        cls._cache.clear()


# Fonction helper pour un accès rapide
def get_icon(name: str, **kwargs) -> QIcon:
    """
    Fonction helper pour récupérer rapidement une icône
    
    Args:
        name: Nom de l'icône
        **kwargs: Arguments optionnels (color, size, etc.)
        
    Returns:
        QIcon
    """
    return IconManager.get(name, **kwargs)
