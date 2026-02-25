"""
VolumeBuilder — Préparation du volume 3D DICOM pour la reconstruction.
Normalisation, fenêtrage HU, et filtrage gaussien.
"""

import numpy as np
import logging
from typing import Tuple, Optional

logger = logging.getLogger(__name__)


class VolumeBuilder:
    """
    Prépare un volume numpy 3D (issu de DICOM) pour la reconstruction Marching Cubes.

    Étapes :
    1. Normalisation min-max → float32 [0, 1]
    2. Fenêtrage Hounsfield Unit (HU) pour isoler l'os
    3. Lissage gaussien optionnel pour réduire le bruit
    """

    # Fenêtre HU par défaut pour l'os cortical
    HU_BONE_LOW: int = 200     # seuil bas (os spongieux inclus)
    HU_BONE_HIGH: int = 1900   # seuil haut (os cortical dense)

    def __init__(
        self,
        hu_low: int = HU_BONE_LOW,
        hu_high: int = HU_BONE_HIGH,
        gaussian_sigma: float = 1.0,
    ):
        self.hu_low = hu_low
        self.hu_high = hu_high
        self.gaussian_sigma = gaussian_sigma

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def prepare(
        self,
        volume: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        smooth: bool = True,
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Pipeline complet : retourne (volume_normalisé, masque_os).

        Args:
            volume   : numpy array 3D brut (valeurs HU ou entiers)
            spacing  : (dz, dy, dx) en mm — sert à calibrer l'isosurface
            smooth   : appliquer le lissage gaussien avant le Marching Cubes

        Returns:
            volume_float32  : volume normalisé [0, 1]
            bone_mask       : masque binaire (bool) de l'os
        """
        logger.info(f"Volume shape={volume.shape}, dtype={volume.dtype}, "
                    f"range=[{volume.min()}, {volume.max()}]")

        # 1. Cast + normalisation
        volume_f = self.normalize(volume)

        # 2. Masque os (avant normalisation, sur les HU réels si disponibles)
        bone_mask = self.compute_bone_mask(volume)

        # 3. Lissage
        if smooth:
            volume_f = self.apply_gaussian_smooth(volume_f, sigma=self.gaussian_sigma)

        logger.info(f"Préparation terminée — bone voxels: {bone_mask.sum():,} / {bone_mask.size:,}")
        return volume_f, bone_mask

    def normalize(self, volume: np.ndarray) -> np.ndarray:
        """Normalise le volume en float32 dans [0, 1]."""
        v = volume.astype(np.float32)
        vmin, vmax = float(v.min()), float(v.max())
        if vmax - vmin < 1e-6:
            return np.zeros_like(v)
        return (v - vmin) / (vmax - vmin)

    def apply_hu_window(
        self,
        volume: np.ndarray,
        low: Optional[int] = None,
        high: Optional[int] = None,
    ) -> np.ndarray:
        """
        Applique une fenêtre de Hounsfield (clip + normalise).
        Utile si le volume contient des valeurs HU calibrées.
        """
        low = low if low is not None else self.hu_low
        high = high if high is not None else self.hu_high
        clipped = np.clip(volume.astype(np.float32), low, high)
        return (clipped - low) / (high - low)

    def compute_bone_mask(self, volume: np.ndarray) -> np.ndarray:
        """
        Segmentation os par seuillage HU.
        Fonctionne que le volume soit en HU réels ou déjà normalisé [0,1].
        """
        vmin, vmax = float(volume.min()), float(volume.max())

        if vmax > 10:
            # Valeurs HU réelles (typiquement -1024 à 3000)
            mask = (volume >= self.hu_low) & (volume <= self.hu_high)
        else:
            # Volume déjà normalisé → estimation proportionnelle
            norm_low = (self.hu_low + 1024) / 4024
            norm_high = min((self.hu_high + 1024) / 4024, 1.0)
            mask = (volume >= norm_low) & (volume <= norm_high)

        return mask.astype(bool)

    def apply_gaussian_smooth(self, volume: np.ndarray, sigma: float = 1.0) -> np.ndarray:
        """Applique un filtre gaussien pour réduire le bruit."""
        try:
            from scipy.ndimage import gaussian_filter
            return gaussian_filter(volume.astype(np.float32), sigma=sigma)
        except ImportError:
            logger.warning("scipy non disponible — lissage ignoré")
            return volume.astype(np.float32)
