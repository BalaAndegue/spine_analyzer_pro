
import sys
import logging
from PySide6.QtWidgets import QApplication

from app.core.config import Config
from app.ui.main_window import MainWindow

logger = logging.getLogger(__name__)

class SpineAnalyzerApp(QApplication):
    """Classe principale de l'application"""
    
    def __init__(self, sys_argv=None):
        if sys_argv is None:
            sys_argv = sys.argv
            
        super().__init__(sys_argv)
        
        self.config = Config()
        self.window = None
        
        self.setApplicationName(self.config.get('app/name'))
        self.setApplicationVersion(self.config.get('app/version'))
        self.setOrganizationName("MedicalAI")
        self.setOrganizationDomain("medicalai.org")
        
        # Initialisation
        self._init_ui()
        
    def _init_ui(self):
        """Initialiser l'interface utilisateur"""
        try:
            # Créer la fenêtre principale
            self.window = MainWindow()
            
            # Appliquer le style
            # (Le style est géré dans MainWindow pour l'instant via config)
            
            self.window.show()
            logger.info("Interface utilisateur initialisée")
            
        except Exception as e:
            logger.critical(f"Erreur d'initialisation UI: {e}", exc_info=True)
            raise e

    def run(self):
        """Lancer l'application"""
        return self.exec()
