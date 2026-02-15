"""
Module de configuration du logging pour SpineAnalyzer Pro
"""

import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional


def setup_logging(log_level: str = "INFO", log_file: Optional[str] = None) -> None:
    """
    Configure le système de logging pour l'application
    
    Args:
        log_level: Niveau de logging (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Chemin du fichier de log (optionnel)
    """
    # Créer le dossier de logs si nécessaire
    if log_file is None:
        log_dir = Path(__file__).parent.parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)
        log_file = log_dir / f"spine_analyzer_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configuration du format de log
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # Configuration du niveau de log
    level = getattr(logging, log_level.upper(), logging.INFO)
    
    # Configuration des handlers
    handlers = [
        # Handler pour la console
        logging.StreamHandler(sys.stdout),
        # Handler pour le fichier
        logging.FileHandler(log_file, encoding='utf-8')
    ]
    
    # Configuration de base du logging
    logging.basicConfig(
        level=level,
        format=log_format,
        datefmt=date_format,
        handlers=handlers
    )
    
    # Logger pour l'application
    logger = logging.getLogger("SpineAnalyzer")
    logger.info(f"Logging configuré - Niveau: {log_level}, Fichier: {log_file}")


def get_logger(name: str) -> logging.Logger:
    """
    Récupère un logger pour un module spécifique
    
    Args:
        name: Nom du module (typiquement __name__)
        
    Returns:
        Logger configuré pour le module
    """
    return logging.getLogger(name)


def set_log_level(level: str) -> None:
    """
    Change le niveau de logging global
    
    Args:
        level: Nouveau niveau (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    log_level = getattr(logging, level.upper(), logging.INFO)
    logging.getLogger().setLevel(log_level)
    logging.info(f"Niveau de logging changé à: {level}")
