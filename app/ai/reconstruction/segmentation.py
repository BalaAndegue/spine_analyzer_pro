"""
BoneSegmenter — Segmentation des structures osseuses par seuillage HU.
Approche algorithmique pure, sans modèle IA.
"""

import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class BoneSegmenter:
    """
    Segmente l'os dans un volume DICOM par seuillage Hounsfield.

    Plages HU de référence :
      Graisse      : -190 à -30
      Tissu mou    : -30  à 200
      Os spongieux : 200  à 700
      Os cortical  : 700  à 1900
      Métal/prothèse: > 1900
    """

    # Presets de segmentation
    PRESETS = {
        'bone_cortical': (700, 1900),
        'bone_all': (200, 1900),
        'bone_soft': (200, 700),
        'spine': (200, 1600),      # Adapté pour la colonne (évite les prothèses)
    }

    def __init__(self, preset: str = 'spine'):
        assert preset in self.PRESETS, f"Preset inconnu: {preset}. Valides: {list(self.PRESETS.keys())}"
        self.hu_low, self.hu_high = self.PRESETS[preset]
        self.preset = preset

    def segment(self, volume: np.ndarray) -> np.ndarray:
        """
        Retourne un masque binaire (bool) de l'os.

        Détecte automatiquement si le volume est en HU réels ou normalisé [0,1].
        """
        vmin, vmax = float(volume.min()), float(volume.max())
        logger.info(f"BoneSegmenter [{self.preset}] — HU range [{self.hu_low}, {self.hu_high}]")

        if vmax > 10:
            # Volume en HU réels
            mask = (volume >= self.hu_low) & (volume <= self.hu_high)
        else:
            # Volume normalisé [0,1] — on suppose une calibration standard CT
            norm_low = (self.hu_low + 1024) / 4024
            norm_high = min((self.hu_high + 1024) / 4024, 1.0)
            mask = (volume >= norm_low) & (volume <= norm_high)

        mask = mask.astype(bool)
        ratio = mask.sum() / mask.size * 100
        logger.info(f"Segmentation terminée: {mask.sum():,} voxels os ({ratio:.1f}%)")
        return mask

    def segment_with_cleanup(
        self,
        volume: np.ndarray,
        min_size: int = 1000,
    ) -> np.ndarray:
        """
        Segmentation + suppression des petites composantes isolées.
        Plus propre mais plus lent.
        """
        mask = self.segment(volume)

        try:
            from scipy.ndimage import label, binary_fill_holes

            # Remplir les trous
            mask = binary_fill_holes(mask)

            # Garder uniquement les grandes composantes
            labeled, num = label(mask)
            if num > 1:
                sizes = [(labeled == i).sum() for i in range(1, num + 1)]
                mask = labeled == (np.argmax(sizes) + 1)
                logger.info(f"Cleanup: {num} composantes → 1 conservée ({max(sizes):,} voxels)")

        except ImportError:
            logger.warning("scipy non disponible — cleanup ignoré")

        return mask.astype(bool)

    def get_volume_fraction(self, mask: np.ndarray) -> float:
        """Retourne le pourcentage de voxels os."""
        return float(mask.sum()) / mask.size * 100
