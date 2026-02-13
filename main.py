#!/usr/bin/env python3
"""
SpineAnalyzer Pro - Application d'analyse rachidienne IA
"""

import sys
import os
import logging

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.application import SpineAnalyzerApp
from app.core.logger import setup_logging

def main():
    """Fonction principale de l'application"""
    # Configuration du logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        logger.info("Démarrage de SpineAnalyzer Pro")
        
        # Initialiser l'application Qt
        from PySide6.QtWidgets import QApplication
        
        # Créer l'application Qt
        app = QApplication(sys.argv)
        app.setApplicationName("SpineAnalyzer Pro")
        app.setOrganizationName("MedicalAI")
        app.setOrganizationDomain("medicalai.org")
        
        # Charger les styles
        from app.ui.styles import load_stylesheet
        stylesheet = load_stylesheet("dark")
        app.setStyleSheet(stylesheet)
        
        # Créer et afficher la fenêtre principale
        window = SpineAnalyzerApp()
        window.show()
        
        logger.info("Application lancée avec succès")
        
        # Exécuter la boucle d'événements
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Erreur lors du démarrage: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()