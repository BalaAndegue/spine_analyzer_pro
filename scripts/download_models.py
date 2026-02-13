
import os
import requests
from pathlib import Path
import logging

# Configuration du logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# URLs des modèles
MODELS = {
    'yolov8n.pt': 'https://github.com/ultralytics/assets/releases/download/v0.0.0/yolov8n.pt',
    # Ajouter d'autres modèles si nécessaire
}

def download_file(url: str, dest_path: Path):
    """Télécharger un fichier avec barre de progression"""
    if dest_path.exists():
        logger.info(f"Le fichier existe déjà: {dest_path}")
        return

    logger.info(f"Téléchargement de {url} vers {dest_path}...")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        with open(dest_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        
        logger.info(f"Téléchargement terminé: {dest_path}")
    except Exception as e:
        logger.error(f"Erreur lors du téléchargement de {url}: {e}")
        if dest_path.exists():
            dest_path.unlink()

def main():
    """Script principal"""
    base_dir = Path(__file__).parent.parent
    models_dir = base_dir / 'models' / 'detection'
    
    # Créer les dossiers si nécessaire
    models_dir.mkdir(parents=True, exist_ok=True)
    
    for name, url in MODELS.items():
        dest_path = models_dir / name
        download_file(url, dest_path)

if __name__ == "__main__":
    main()
