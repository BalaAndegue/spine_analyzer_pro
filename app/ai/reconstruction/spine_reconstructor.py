"""
SpineReconstructor — Orchestration du pipeline de reconstruction 3D.
Utilise VolumeBuilder, BoneSegmenter et MeshGenerator (Marching Cubes).
Aucun GPU requis.
"""

import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple

logger = logging.getLogger(__name__)


class SpineReconstructor:
    """
    Orchestrateur du pipeline de reconstruction 3D du rachis.

    Pipeline :
        DICOM folder
            → DICOMManager (chargement volume)
            → VolumeBuilder (normalisation + seuillage HU)
            → BoneSegmenter (masque os)
            → MeshGenerator (Marching Cubes → pv.PolyData)
    """

    def __init__(
        self,
        hu_low: int = 200,
        hu_high: int = 1600,
        step_size: int = 2,
        decimate_ratio: float = 0.3,
        smooth_iterations: int = 20,
    ):
        """
        Args:
            hu_low/hu_high    : fenêtre HU pour la segmentation os
            step_size         : sous-échantillonnage Marching Cubes (1=fin, 2=rapide)
            decimate_ratio    : fraction de faces supprimées lors de la décimation
            smooth_iterations : lissage du maillage final
        """
        self.hu_low = hu_low
        self.hu_high = hu_high
        self.step_size = step_size
        self.decimate_ratio = decimate_ratio
        self.smooth_iterations = smooth_iterations
        self.is_initialized = True

        # Instanciation lazy des modules
        self._volume_builder = None
        self._segmenter = None
        self._mesh_generator = None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reconstruct_from_dicom(
        self,
        dicom_folder: str,
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Reconstruit un volume 3D et un maillage os depuis un dossier DICOM.

        Args:
            dicom_folder     : chemin vers le dossier DICOM
            progress_callback: callable(pct: int, msg: str) — progression optionnelle

        Returns:
            dict avec les clés :
                'original_volume'    : numpy array brut (Z, Y, X)
                'normalized_volume'  : numpy array float32 [0, 1]
                'segmentation_mask'  : numpy array bool (os)
                'mesh'               : pv.PolyData ou None
                'spacing'            : tuple (dz, dy, dx) en mm
                'stats'              : dict de statistiques
        """
        def _progress(pct, msg):
            logger.info(f"[{pct}%] {msg}")
            if progress_callback:
                progress_callback(pct, msg)

        _progress(0, "Chargement des fichiers DICOM...")

        # 1. Chargement DICOM
        from app.data.dicom_loader import DICOMManager
        manager = DICOMManager()
        patient_data = manager.load_folder(dicom_folder)
        volume = manager.get_volume_array()
        spacing = getattr(patient_data, 'spacing', (1.0, 1.0, 1.0))

        logger.info(f"Volume chargé : {volume.shape}, spacing={spacing}")
        _progress(20, "Volume DICOM chargé")

        # 2. Construction du volume (normalisation + lissage)
        _progress(25, "Normalisation et préparation du volume...")
        builder = self._get_volume_builder()
        volume_f, bone_mask_builder = builder.prepare(
            volume, spacing=spacing, smooth=True
        )
        _progress(40, "Volume préparé")

        # 3. Segmentation os (seuillage HU)
        _progress(45, "Segmentation osseuse...")
        segmenter = self._get_segmenter()
        bone_mask = segmenter.segment_with_cleanup(volume)
        bone_fraction = segmenter.get_volume_fraction(bone_mask)
        _progress(60, f"Segmentation : {bone_fraction:.1f}% de voxels os")

        # 4. Génération du maillage (Marching Cubes)
        _progress(65, "Génération du maillage 3D (Marching Cubes)...")
        mesh = self._generate_mesh(bone_mask, spacing)
        _progress(90, "Maillage généré")

        # 5. Statistiques
        stats = self._compute_stats(volume, bone_mask, mesh)
        _progress(100, "Reconstruction terminée")

        return {
            'original_volume': volume,
            'normalized_volume': volume_f,
            'segmentation_mask': bone_mask,
            'mesh': mesh,
            'spacing': spacing,
            'stats': stats,
        }

    def reconstruct_from_volume(
        self,
        volume: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        progress_callback=None,
    ) -> Dict[str, Any]:
        """
        Reconstruit depuis un numpy array déjà chargé (sans recharger DICOM).
        Utile pour les tests ou si le volume est déjà en mémoire.
        """
        def _progress(pct, msg):
            logger.info(f"[{pct}%] {msg}")
            if progress_callback:
                progress_callback(pct, msg)

        _progress(0, "Préparation du volume...")
        builder = self._get_volume_builder()
        volume_f, _ = builder.prepare(volume, spacing=spacing, smooth=True)
        _progress(30, "Volume préparé")

        _progress(35, "Segmentation osseuse...")
        segmenter = self._get_segmenter()
        bone_mask = segmenter.segment_with_cleanup(volume)
        _progress(60, "Segmentation terminée")

        _progress(65, "Marching Cubes...")
        mesh = self._generate_mesh(bone_mask, spacing)
        _progress(95, "Maillage prêt")

        stats = self._compute_stats(volume, bone_mask, mesh)
        _progress(100, "Terminé")

        return {
            'original_volume': volume,
            'normalized_volume': volume_f,
            'segmentation_mask': bone_mask,
            'mesh': mesh,
            'spacing': spacing,
            'stats': stats,
        }

    # ------------------------------------------------------------------
    # Privé
    # ------------------------------------------------------------------

    def _get_volume_builder(self):
        if self._volume_builder is None:
            from app.ai.reconstruction.volume_builder import VolumeBuilder
            self._volume_builder = VolumeBuilder(
                hu_low=self.hu_low,
                hu_high=self.hu_high,
            )
        return self._volume_builder

    def _get_segmenter(self):
        if self._segmenter is None:
            from app.ai.reconstruction.segmentation import BoneSegmenter
            self._segmenter = BoneSegmenter(preset='spine')
            self._segmenter.hu_low = self.hu_low
            self._segmenter.hu_high = self.hu_high
        return self._segmenter

    def _get_mesh_generator(self):
        if self._mesh_generator is None:
            from app.ai.reconstruction.mesh_generator import MeshGenerator
            self._mesh_generator = MeshGenerator(
                level=0.5,
                step_size=self.step_size,
                decimate_ratio=self.decimate_ratio,
                smooth_iterations=self.smooth_iterations,
            )
        return self._mesh_generator

    def _generate_mesh(self, bone_mask: np.ndarray, spacing: tuple):
        """Génère le maillage PyVista depuis le masque os."""
        generator = self._get_mesh_generator()
        try:
            mesh = generator.generate_from_mask(bone_mask, spacing=spacing)
            return mesh
        except Exception as e:
            logger.error(f"Erreur lors de la génération du maillage : {e}")
            return None

    def _compute_stats(self, volume, bone_mask, mesh) -> Dict[str, Any]:
        """Calcule des statistiques de base sur le volume et le maillage."""
        stats = {
            'volume_shape': volume.shape,
            'bone_voxels': int(bone_mask.sum()),
            'total_voxels': int(bone_mask.size),
            'bone_fraction_pct': float(bone_mask.sum() / bone_mask.size * 100),
            'hu_min': float(volume.min()),
            'hu_max': float(volume.max()),
            'hu_mean': float(volume.mean()),
        }

        if mesh is not None:
            stats['mesh_vertices'] = mesh.n_points
            stats['mesh_faces'] = mesh.n_cells
        else:
            stats['mesh_vertices'] = 0
            stats['mesh_faces'] = 0
            stats['mesh_error'] = 'Maillage non généré'

        return stats