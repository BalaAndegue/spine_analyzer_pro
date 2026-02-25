"""
MeshGenerator — Génération de maillage 3D par Marching Cubes.
Utilise scikit-image et PyVista. Aucun GPU requis.
"""

import numpy as np
import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class MeshGenerator:
    """
    Génère un maillage 3D (pv.PolyData) depuis un volume numpy binaire ou scalaire.

    Utilise l'algorithme Marching Cubes (Lorensen 1987) via scikit-image.
    Post-processing : décimation, calcul des normales.
    """

    def __init__(
        self,
        level: float = 0.5,
        step_size: int = 2,
        decimate_ratio: float = 0.3,
        smooth_iterations: int = 20,
    ):
        """
        Args:
            level           : isovaleur (0–1 si volume normalisé, 0.5 = frontière os)
            step_size       : pas de sous-échantillonnage (1=tous les voxels, 2=1/8)
            decimate_ratio  : fraction de triangles à supprimer (0=rien, 0.9=beaucoup)
            smooth_iterations: iterations de lissage Laplacien sur le mesh
        """
        self.level = level
        self.step_size = step_size
        self.decimate_ratio = decimate_ratio
        self.smooth_iterations = smooth_iterations

    def generate(
        self,
        volume: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
        level: Optional[float] = None,
    ):
        """
        Génère un maillage 3D PyVista depuis un volume numpy.

        Args:
            volume  : numpy array 3D, float32 normalisé [0,1] ou masque bool
            spacing : taille d'un voxel en mm (dz, dy, dx)
            level   : isovaleur (remplace le défaut si fourni)

        Returns:
            pv.PolyData : maillage prêt pour VolumeViewer, ou None si erreur
        """
        import pyvista as pv

        try:
            from skimage.measure import marching_cubes
        except ImportError:
            logger.error("scikit-image non installé — pip install scikit-image")
            return None

        iso = level if level is not None else self.level
        vol = volume.astype(np.float32)

        logger.info(f"Marching Cubes — shape={vol.shape}, level={iso}, step={self.step_size}")

        try:
            verts, faces, normals, values = marching_cubes(
                vol,
                level=iso,
                spacing=spacing,          # mm par voxel
                step_size=self.step_size,
                allow_degenerate=False,
                gradient_direction='ascent',  # os = valeurs hautes
            )
        except ValueError as e:
            logger.error(f"Marching Cubes échec : {e}")
            return None

        n_verts = len(verts)
        n_faces = len(faces)
        logger.info(f"Mesh brut : {n_verts:,} sommets, {n_faces:,} triangles")

        if n_verts < 10:
            logger.warning("Mesh insuffisant — vérifier le seuillage HU")
            return None

        # Construire le PolyData PyVista
        mesh = self._build_polydata(verts, faces, normals)

        # Post-processing
        mesh = self._postprocess(mesh)

        logger.info(f"Mesh final : {mesh.n_points:,} sommets, {mesh.n_cells:,} triangles")
        return mesh

    def generate_from_mask(
        self,
        mask: np.ndarray,
        spacing: Tuple[float, float, float] = (1.0, 1.0, 1.0),
    ):
        """
        Génère un maillage depuis un masque binaire (bool numpy).
        Préférable pour un contrôle précis de la segmentation.
        """
        return self.generate(mask.astype(np.float32), spacing=spacing, level=0.5)

    # ------------------------------------------------------------------
    # Privé
    # ------------------------------------------------------------------

    def _build_polydata(self, verts, faces, normals):
        """Construit un pv.PolyData depuis les résultats Marching Cubes."""
        import pyvista as pv

        # PyVista attend des faces au format [n_pts, v0, v1, v2, ...]
        n_faces = len(faces)
        face_arr = np.hstack([
            np.full((n_faces, 1), 3, dtype=np.int64),
            faces.astype(np.int64)
        ])

        mesh = pv.PolyData(verts, face_arr)

        # Normales
        if normals is not None and len(normals) == len(verts):
            mesh.point_data['Normals'] = normals

        return mesh

    def _postprocess(self, mesh):
        """Décimation + lissage Laplacien."""
        try:
            # Décimation (réduit le nombre de polygones)
            if self.decimate_ratio > 0 and mesh.n_cells > 5000:
                mesh = mesh.decimate(self.decimate_ratio)
                logger.debug(f"Après décimation: {mesh.n_cells:,} triangles")

            # Calcul des normales de surface
            mesh = mesh.compute_normals(
                cell_normals=True,
                point_normals=True,
                consistent_normals=True,
                auto_orient_normals=True,
                non_manifold_traversal=False,
            )

            # Lissage
            if self.smooth_iterations > 0:
                mesh = mesh.smooth(n_iter=self.smooth_iterations, relaxation_factor=0.1)

        except Exception as e:
            logger.warning(f"Post-processing partiel : {e}")

        return mesh
