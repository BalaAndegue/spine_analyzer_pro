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
        
        # SpineAnalyzerApp hérite déjà de QApplication, pas besoin d'en créer une séparée
        app = SpineAnalyzerApp(sys.argv)
        
        logger.info("Application lancée avec succès")
        
        # Exécuter la boucle d'événements
        sys.exit(app.exec())
        
    except Exception as e:
        logger.critical(f"Erreur lors du démarrage: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()