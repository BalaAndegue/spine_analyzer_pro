
import logging
from typing import Dict, Any, List, Optional
import numpy as np

logger = logging.getLogger(__name__)


class QuantitativeAnalyzer:
    """Analyseur quantitatif — métriques rachidiennes réelles."""

    def analyze(
        self,
        mesh: Any,
        anomalies: List[Dict[str, Any]],
        vertebrae: Optional[List[Dict[str, Any]]] = None,
        volume: Optional[np.ndarray] = None,
        bone_mask: Optional[np.ndarray] = None,
        spacing: tuple = (1.0, 1.0, 1.0),
    ) -> Dict[str, Any]:
        dz, dy, dx = spacing
        voxel_vol_mm3 = dz * dy * dx
        metrics: Dict[str, Any] = {}

        # Volume osseux
        if bone_mask is not None and bone_mask.any():
            n_bone = int(bone_mask.sum())
            metrics["bone_volume_cm3"]  = round(n_bone * voxel_vol_mm3 / 1000, 2)
            metrics["bone_voxel_count"] = n_bone
        elif mesh is not None:
            try:
                metrics["mesh_volume_cm3"] = round(abs(mesh.volume) / 1000, 2)
            except Exception:
                pass

        # Densité HU
        if volume is not None and bone_mask is not None and bone_mask.any():
            hu_vals = volume[bone_mask]
            metrics["hu_mean"]   = round(float(hu_vals.mean()), 1)
            metrics["hu_std"]    = round(float(hu_vals.std()),  1)
            metrics["hu_min"]    = round(float(hu_vals.min()),  1)
            metrics["hu_max"]    = round(float(hu_vals.max()),  1)
            metrics["bone_density_index"] = round(
                float(np.clip((hu_vals.mean() - 200) / 1400, 0, 1)), 3
            )

        # Métriques vertèbres
        if vertebrae:
            h_list   = [v["height_mm"]         for v in vertebrae]
            comp_list = [v["compression_ratio"]  for v in vertebrae]

            metrics["vertebrae_count"]         = len(vertebrae)
            metrics["mean_vertebra_height_mm"] = round(float(np.mean(h_list)), 1)
            metrics["min_vertebra_height_mm"]  = round(float(np.min(h_list)),  1)
            metrics["mean_compression_ratio"]  = round(float(np.mean(comp_list)), 3)
            metrics["min_compression_ratio"]   = round(float(np.min(comp_list)), 3)

            statuses = [v.get("ml_status", v.get("status", "normal")) for v in vertebrae]
            for s in ["normal", "ostéopénique", "suspect", "comprimée"]:
                key = s.replace("é","e").replace("è","e")
                metrics[f"count_{key}"] = statuses.count(s)

            metrics["estimated_cobb_angle_deg"] = round(self._estimate_cobb(vertebrae), 1)

            worst = int(np.argmin(comp_list))
            metrics["most_compressed_vertebra"] = vertebrae[worst].get("label", "?")
            metrics["most_compressed_ratio"]    = round(comp_list[worst], 3)

        if anomalies:
            metrics["total_anomalies"] = len(anomalies)

        logger.info(f"Analyse quantitative : {len(metrics)} métriques calculées")
        return metrics

    def _estimate_cobb(self, vertebrae: List[Dict[str, Any]]) -> float:
        if len(vertebrae) < 3:
            return 0.0
        try:
            centroids = np.array([v["centroid_px"] for v in vertebrae])
            z = centroids[:, 0]
            x = centroids[:, 2]
            if z.ptp() < 1:
                return 0.0
            coeffs = np.polyfit(z, x, 1)
            res = x - np.polyval(coeffs, z)
            return float(np.degrees(np.arctan2(res.ptp(), z.ptp())))
        except Exception:
            return 0.0
