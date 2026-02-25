"""
VertebraClassifier — Classification légère de l'état de chaque vertèbre.
Utilise RandomForestClassifier (scikit-learn) sur des features simples.
Aucun GPU requis. Entraîné sur des exemples synthétiques intégrés.
"""

import numpy as np
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

# Features : [hu_mean, hu_std, height_mm, compression_ratio, bone_fraction]
# Labels   : 0=normal, 1=ostéopénique, 2=suspect, 3=comprimée

_TRAINING_DATA = np.array([
    # hu_mean  hu_std  h_mm  comp  bone%
    [600, 80,  30, 1.00, 5.0],   # normal
    [650, 70,  28, 0.98, 6.0],   # normal
    [550, 90,  32, 1.02, 4.5],   # normal
    [700, 60,  27, 0.95, 7.0],   # normal
    [580, 85,  31, 1.05, 5.5],   # normal
    [200, 60,  30, 0.99, 2.0],   # ostéopénique
    [180, 50,  29, 1.00, 1.5],   # ostéopénique
    [220, 70,  28, 0.98, 2.5],   # ostéopénique
    [150, 45,  31, 1.02, 1.2],   # ostéopénique
    [600, 80,  18, 0.55, 5.0],   # comprimée
    [620, 75,  15, 0.45, 5.5],   # comprimée
    [580, 90,  20, 0.60, 4.5],   # comprimée
    [500, 110, 25, 1.30, 4.0],   # suspect
    [480, 120, 26, 1.35, 3.5],   # suspect
    [520, 100, 24, 1.28, 4.2],   # suspect
    [400, 95,  29, 0.72, 3.0],   # suspect
], dtype=np.float32)

_TRAINING_LABELS = np.array([0,0,0,0,0, 1,1,1,1, 3,3,3, 2,2,2,2])

CLASS_NAMES = {0: "normal", 1: "ostéopénique", 2: "suspect", 3: "comprimée"}
CLASS_COLORS = {
    "normal":       "#4CAF50",
    "ostéopénique": "#FF9800",
    "suspect":      "#F44336",
    "comprimée":    "#9C27B0",
}


class VertebraClassifier:
    """
    Classifie l'état de chaque vertèbre à partir de ses métriques.
    Entraîné au démarrage sur une base synthétique (quelques secondes).
    """

    def __init__(self):
        self._model = None
        self._is_trained = False
        self._train()

    def _train(self):
        try:
            from sklearn.ensemble import RandomForestClassifier
            from sklearn.preprocessing import StandardScaler
            from sklearn.pipeline import Pipeline

            self._model = Pipeline([
                ("scaler", StandardScaler()),
                ("clf", RandomForestClassifier(
                    n_estimators=100,
                    max_depth=5,
                    random_state=42,
                    class_weight="balanced",
                )),
            ])
            self._model.fit(_TRAINING_DATA, _TRAINING_LABELS)
            self._is_trained = True
            logger.info("VertebraClassifier entraîné (RandomForest, 16 exemples)")
        except ImportError:
            logger.warning("scikit-learn non disponible — classification par règles")
        except Exception as e:
            logger.error(f"Erreur entraînement classificateur : {e}")

    def classify(self, vertebrae: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Enrichit chaque dict vertèbre avec 'ml_status', 'confidence', 'color'.

        Args:
            vertebrae : liste retournée par VertebraDetector.detect()
        Returns:
            La même liste enrichie (in-place + retour)
        """
        if not vertebrae:
            return vertebrae

        for v in vertebrae:
            features = np.array([[
                v.get("hu_mean", 400),
                v.get("hu_std", 80),
                v.get("height_mm", 25),
                v.get("compression_ratio", 1.0),
                v.get("bone_fraction", 5.0),
            ]], dtype=np.float32)

            if self._is_trained and self._model is not None:
                pred  = int(self._model.predict(features)[0])
                proba = self._model.predict_proba(features)[0]
                conf  = float(proba[pred])
                ml_status = CLASS_NAMES.get(pred, "unknown")
            else:
                # Fallback par règles
                ml_status = v.get("status", "normal")
                conf = 0.7

            v["ml_status"]  = ml_status
            v["confidence"] = round(conf, 2)
            v["color"]      = CLASS_COLORS.get(ml_status, "#AAAAAA")

        return vertebrae

    @property
    def is_trained(self) -> bool:
        return self._is_trained
