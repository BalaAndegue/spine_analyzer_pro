
import os
from pathlib import Path
from typing import Any, Dict
import yaml
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

class Config:
    """Gestionnaire de configuration de l'application"""
    
    _instance = None
    _config = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance
    
    def _load_config(self):
        """Charger la configuration depuis les fichiers et l'environnement"""
        # Configuration par défaut
        self._config = {
            'app': {
                'name': 'SpineAnalyzer Pro',
                'version': '1.0.0',
                'debug': os.getenv('DEBUG', 'False').lower() == 'true',
                'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            },
            'paths': {
                'base_dir': str(Path(__file__).parent.parent.parent),
                'data_dir': os.getenv('DATA_DIR', str(Path(__file__).parent.parent.parent / 'data')),
                'models_dir': os.getenv('MODELS_DIR', str(Path(__file__).parent.parent.parent / 'models')),
                'logs_dir': os.getenv('LOGS_DIR', str(Path(__file__).parent.parent.parent / 'logs')),
                'temp_dir': os.getenv('TEMP_DIR', str(Path(__file__).parent.parent.parent / 'temp')),
            },
            'ui': {
                'theme': 'dark',
                'font_size': 10,
                'language': 'fr',
                'auto_report': False,
                'window': {
                    'geometry': None,
                    'dock_state': None
                }
            },
            'ai': {
                'reconstruction': {
                    'model_path': 'reconstruction/model.pth',
                    'device': 'cuda' if os.getenv('USE_GPU', 'True').lower() == 'true' else 'cpu'
                },
                'detection': {
                    'model_path': 'detection/yolov8n.pt',
                    'confidence_threshold': 0.5
                }
            },
            'dicom': {
                'auto_anonymize': True,
                'series_description_filter': ['spine', 'rachis', 'vertebra']
            }
        }
        
        # Charger fichier de config utilisateur si existant
        config_path = Path(self._config['paths']['base_dir']) / 'config.yaml'
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(self._config, user_config)
            except Exception as e:
                print(f"Erreur lors du chargement de la configuration: {e}")

    def _merge_config(self, base: Dict, update: Dict):
        """Fusionner récursivement les dictionnaires de configuration"""
        for k, v in update.items():
            if k in base and isinstance(base[k], dict) and isinstance(v, dict):
                self._merge_config(base[k], v)
            else:
                base[k] = v

    def get(self, key: str, default: Any = None) -> Any:
        """Récupérer une valeur de configuration (ex: 'ui/theme')"""
        keys = key.split('/')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Définir une valeur de configuration"""
        keys = key.split('/')
        target = self._config
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        
        # Sauvegarder (optionnel, à implémenter si besoin de persistance immédiate)

    @property
    def paths(self) -> Dict[str, str]:
        return self._config['paths']
