
import logging
import os
from typing import List, Dict, Any
import numpy as np
from pathlib import Path

# Import optionnel de YOLO
try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """Détecteur d'anomalies rachidiennes basé sur YOLOv8"""
    
    def __init__(self, model_path: str = None):
        if model_path is None:
            # Chemin par défaut relatif
            base_dir = Path(__file__).parent.parent.parent.parent
            model_path = os.path.join(base_dir, "models", "detection", "yolov8n.pt")
            
        self.model_path = model_path
        self.model = None
        self._load_model()

    def _load_model(self):
        """Charger le modèle YOLO"""
        if not HAS_YOLO:
            logger.warning("Ultralytics/YOLO non installé. Le détecteur fonctionnera en mode simulation.")
            return

        if os.path.exists(self.model_path):
            try:
                self.model = YOLO(self.model_path)
                logger.info(f"Modèle chargé depuis {self.model_path}")
            except Exception as e:
                logger.error(f"Impossible de charger le modèle: {e}")
        else:
            logger.warning(f"Modèle introuvable à {self.model_path}. Le téléchargement sera nécessaire.")

    def detect_anomalies(self, volume: np.ndarray, mask: np.ndarray = None) -> List[Dict[str, Any]]:
        """
        Détecter des anomalies dans le volume 3D (slice par slice).
        
        Args:
            volume: Array numpy 3D (Z, Y, X)
            mask: Masque de segmentation optionnel
            
        Returns:
            Liste de dictionnaires décrivant les anomalies
        """
        anomalies = []
        
        if not HAS_YOLO or self.model is None:
            # Mode Simulation si pas de modèle
            logger.info("Détection simulée (pas de modèle chargé)")
            if volume.shape[0] > 10:
                # Créer une fausse anomalie pour la démo
                anomalies.append({
                    'slice_index': volume.shape[0] // 2,
                    'type': 'Fracture (Simulated)',
                    'confidence': 0.95,
                    'bbox': [100, 100, 200, 200],
                    'description': "Simulation: Fracture détectée"
                })
            return anomalies

        # Pour optimiser, on ne traite qu'une slice sur 5 ou 10
        step = max(1, len(volume) // 20) 
        
        for i in range(0, len(volume), step):
            slice_img = volume[i]
            
            # Normaliser pour YOLO (0-255 uint8)
            img_normalized = ((slice_img - slice_img.min()) / (slice_img.max() - slice_img.min() + 1e-8) * 255).astype(np.uint8)
            
            # Convertir en RGB (3 canaux) pour YOLO
            img_rgb = np.stack((img_normalized,)*3, axis=-1)
            
            # Inférence
            results = self.model(img_rgb, verbose=False)
            
            # Convertir les résultats
            for r in results:
                for box in r.boxes:
                    coords = box.xyxy[0].tolist() # x1, y1, x2, y2
                    conf = float(box.conf[0])
                    cls = int(box.cls[0])
                    label = self.model.names[cls]
                    
                    if conf > 0.4: # Seuil de confiance arbitraire
                        anomalies.append({
                            'slice_index': i,
                            'type': label,
                            'confidence': conf,
                            'bbox': coords,
                            'description': f"Possible {label} detected on slice {i}"
                        })

        
        logger.info(f"Détection terminée. {len(anomalies)} anomalies trouvées.")
        return anomalies
