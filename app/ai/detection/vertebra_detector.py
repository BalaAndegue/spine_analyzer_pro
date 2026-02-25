"""
VertebraDetector — Détection et localisation des vertèbres dans le volume 3D.
Approche algorithmique pure : analyse de la courbe d'épaisseur osseuse sur l'axe Z.
Aucun modèle IA / GPU requis.
"""

import numpy as np
import logging
from typing import List, Dict, Any, Tuple, Optional
from scipy.ndimage import gaussian_filter1d
from scipy.signal import find_peaks

logger = logging.getLogger(__name__)


# Labels vertébraux du bas vers le haut (orientation CT standard)
VERTEBRA_LABELS = {
    "thoracique": ["T1", "T2", "T3", "T4", "T5", "T6",
                   "T7", "T8", "T9", "T10", "T11", "T12"],
    "lombaire":   ["L1", "L2", "L3", "L4", "L5"],
    "sacre":      ["S1"],
}
ALL_LABELS = ["S1", "L5", "L4", "L3", "L2", "L1",
              "T12", "T11", "T10", "T9", "T8", "T7",
              "T6", "T5", "T4", "T3", "T2", "T1"]


class VertebraDetector:
    """
    Détecte et localise chaque vertèbre dans un volume CT.

    Algorithme :
    1. Calculer le profil osseux Z : nb de voxels os par coupe
    2. Lisser le profil avec un filtre gaussien
    3. Détecter les minima locaux → positions des disques intervertébraux
    4. Segmenter chaque région entre deux minima → une vertèbre
    5. Calculer les métriques par vertèbre (centroïde, hauteur, HU, compression)
    """

    def __init__(
        self,
        min_vertebra_slices: int = 3,
        gaussian_sigma: float = 2.0,
        min_peak_prominence: float = 0.1,
    ):
        self.min_vertebra_slices = min_vertebra_slices
        self.sigma = gaussian_sigma
        self.prominence = min_peak_prominence

    def detect(
        self,
        bone_mask: np.ndarray,
        volume: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ) -> List[Dict[str, Any]]:
        """
        Détecter toutes les vertèbres dans le volume.

        Args:
            bone_mask : numpy bool (Z, Y, X) — masque os
            volume    : numpy float32 (Z, Y, X) — valeurs HU
            spacing   : (dz, dy, dx) en mm

        Returns:
            Liste de dicts, un par vertèbre détectée :
            {
              'label': 'L3',
              'z_start': int, 'z_end': int,
              'z_range_mm': float,
              'centroid_px': (z, y, x),
              'height_mm': float,
              'hu_mean': float,
              'hu_std': float,
              'bone_fraction': float,
              'compression_ratio': float,   # ant vs post height
              'status': str,               # 'normal' / 'suspect' / 'comprimée'
            }
        """
        dz, dy, dx = spacing
        nz = bone_mask.shape[0]

        # 1. Profil osseux sur Z
        profile = bone_mask.sum(axis=(1, 2)).astype(float)
        if profile.max() < 10:
            logger.warning("Profil osseux vide — aucune vertèbre détectée")
            return []

        # Normaliser
        norm_profile = profile / profile.max()

        # 2. Lisser
        smooth = gaussian_filter1d(norm_profile, sigma=self.sigma)

        # 3. Détecter les minima locaux (= disques)
        # On inverse pour find_peaks (cherche minima)
        inverted = smooth.max() - smooth
        min_distance = max(3, int(5 / dz))  # au moins 5 mm entre vertèbres
        peaks, props = find_peaks(
            inverted,
            prominence=self.prominence,
            distance=min_distance,
        )

        # Ajouter les bornes
        boundaries = sorted([0] + list(peaks) + [nz - 1])

        # 4. Construire les vertèbres
        vertebrae_raw = []
        for i in range(len(boundaries) - 1):
            z0, z1 = boundaries[i], boundaries[i + 1]
            if (z1 - z0) < self.min_vertebra_slices:
                continue
            vertebrae_raw.append((z0, z1))

        if not vertebrae_raw:
            logger.warning("Aucune vertèbre segmentée (profil uniforme)")
            return []

        # 5. Attribuer les labels (du bas vers le haut = ordre ascendant Z en CT)
        n = len(vertebrae_raw)
        labels = self._assign_labels(n)

        # 6. Calculer les métriques
        vertebrae = []
        for idx, ((z0, z1), label) in enumerate(zip(vertebrae_raw, labels)):
            v = self._compute_metrics(
                z0, z1, label, bone_mask, volume, spacing
            )
            vertebrae.append(v)
            logger.debug(f"  {label}: z=[{z0},{z1}], H={v['height_mm']:.1f}mm, "
                         f"HU={v['hu_mean']:.0f}, status={v['status']}")

        logger.info(f"Détection terminée : {len(vertebrae)} vertèbres")
        return vertebrae

    # ──────────────────────────────────────────────────────────────
    # Privé
    # ──────────────────────────────────────────────────────────────

    def _assign_labels(self, n: int) -> List[str]:
        """Attribuer les labels vertébraux selon le nombre détecté."""
        # On prend les n derniers labels du bas vers le haut
        labels_pool = ALL_LABELS[::-1]   # T1→T12→L1→L5→S1
        if n <= len(labels_pool):
            # Centrer sur les lombaires si n ≤ 5
            if n <= 6:
                start = ALL_LABELS.index("L5") if "L5" in ALL_LABELS else 0
                pool = ALL_LABELS[start:]
                return pool[:n] if len(pool) >= n else ALL_LABELS[:n]
            return ALL_LABELS[:n]
        return [f"V{i+1}" for i in range(n)]

    def _compute_metrics(
        self,
        z0: int, z1: int,
        label: str,
        bone_mask: np.ndarray,
        volume: np.ndarray,
        spacing: Tuple[float, float, float],
    ) -> Dict[str, Any]:
        dz, dy, dx = spacing
        nz, ny, nx = bone_mask.shape

        region_mask = bone_mask[z0:z1]
        region_vol  = volume[z0:z1]

        hu_vals = region_vol[region_mask]
        hu_mean = float(hu_vals.mean()) if len(hu_vals) > 0 else 0.0
        hu_std  = float(hu_vals.std())  if len(hu_vals) > 0 else 0.0
        bone_fraction = float(region_mask.mean())

        height_mm = (z1 - z0) * dz

        # Centroïde
        if region_mask.any():
            coords = np.array(np.where(region_mask))
            c_local = coords.mean(axis=1)
            centroid = (c_local[0] + z0, c_local[1], c_local[2])
        else:
            centroid = ((z0 + z1) / 2, ny / 2, nx / 2)

        # Ratio compression : hauteur anterieure vs posterieure
        ny_half = ny // 2
        ant  = region_mask[:, :ny_half, :].sum(axis=0)  # moitié antérieure
        post = region_mask[:, ny_half:, :].sum(axis=0)  # moitié postérieure
        h_ant  = float(ant.sum())  / max((z1-z0)*nx, 1)
        h_post = float(post.sum()) / max((z1-z0)*nx, 1)
        comp_ratio = h_ant / max(h_post, 0.001)

        # Classification simple
        status = self._classify(hu_mean, comp_ratio, height_mm)

        return {
            "label":            label,
            "z_start":          int(z0),
            "z_end":            int(z1),
            "height_mm":        round(height_mm, 1),
            "centroid_px":      tuple(float(c) for c in centroid),
            "hu_mean":          round(hu_mean, 1),
            "hu_std":           round(hu_std, 1),
            "bone_fraction":    round(bone_fraction * 100, 2),
            "compression_ratio": round(comp_ratio, 3),
            "status":           status,
        }

    def _classify(self, hu_mean: float, comp_ratio: float, height_mm: float) -> str:
        """Classification simple basée sur des seuils cliniques."""
        if comp_ratio < 0.7:
            return "comprimée"
        if hu_mean < 150:
            return "ostéopénique"
        if abs(comp_ratio - 1.0) > 0.25:
            return "suspect"
        return "normal"
