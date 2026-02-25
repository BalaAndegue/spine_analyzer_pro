"""
Tests unitaires pour les modules de reconstruction 3D.
Teste VolumeBuilder, BoneSegmenter et MeshGenerator sur des volumes synthétiques.
"""

import sys
import os
import unittest
import numpy as np

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def create_sphere_volume(shape=(64, 64, 64), radius=20, center=None, bg_hu=-1024, bone_hu=800):
    """Crée un volume synthétique avec une sphère osseuse."""
    if center is None:
        center = tuple(s // 2 for s in shape)
    volume = np.full(shape, bg_hu, dtype=np.float32)
    z, y, x = np.ogrid[:shape[0], :shape[1], :shape[2]]
    dist = np.sqrt((z - center[0])**2 + (y - center[1])**2 + (x - center[2])**2)
    volume[dist <= radius] = bone_hu
    return volume


def create_normalized_sphere(shape=(64, 64, 64), radius=20):
    """Crée un volume normalisé [0,1] avec une sphère."""
    volume = np.zeros(shape, dtype=np.float32)
    center = tuple(s // 2 for s in shape)
    z, y, x = np.ogrid[:shape[0], :shape[1], :shape[2]]
    dist = np.sqrt((z - center[0])**2 + (y - center[1])**2 + (x - center[2])**2)
    volume[dist <= radius] = 1.0
    return volume


# ============================================================
class TestVolumeBuilder(unittest.TestCase):

    def setUp(self):
        from app.ai.reconstruction.volume_builder import VolumeBuilder
        self.builder = VolumeBuilder()

    def test_normalize_output_range(self):
        """La normalisation doit produire des valeurs dans [0, 1]."""
        volume = create_sphere_volume()
        normalized = self.builder.normalize(volume)
        self.assertAlmostEqual(float(normalized.min()), 0.0, places=5)
        self.assertAlmostEqual(float(normalized.max()), 1.0, places=5)
        self.assertEqual(normalized.dtype, np.float32)

    def test_normalize_constant_volume(self):
        """Un volume constant doit retourner un volume de zéros."""
        volume = np.ones((32, 32, 32), dtype=np.float32) * 500
        normalized = self.builder.normalize(volume)
        self.assertTrue(np.all(normalized == 0.0))

    def test_compute_bone_mask_hu_values(self):
        """Le masque doit isoler uniquement les voxels os en HU réels."""
        volume = create_sphere_volume(
            shape=(50, 50, 50), radius=15,
            bg_hu=-500, bone_hu=900
        )
        mask = self.builder.compute_bone_mask(volume)
        self.assertEqual(mask.dtype, bool)
        # Les voxels os doivent être dans le masque
        bone_voxels = mask.sum()
        self.assertGreater(bone_voxels, 0)
        # Les voxels fond ne doivent pas être dans le masque
        bg_mask = volume == -500
        self.assertTrue(np.all(~mask[bg_mask]))

    def test_prepare_returns_correct_types(self):
        """prepare() doit retourner (float32 array, bool array)."""
        volume = create_sphere_volume()
        vol_f, bone_mask = self.builder.prepare(volume, smooth=False)
        self.assertEqual(vol_f.dtype, np.float32)
        self.assertEqual(bone_mask.dtype, bool)
        self.assertEqual(vol_f.shape, volume.shape)
        self.assertEqual(bone_mask.shape, volume.shape)

    def test_gaussian_smooth_reduces_noise(self):
        """Le lissage gaussien ne doit pas agrandir significativement le volume."""
        volume = create_normalized_sphere()
        smoothed = self.builder.apply_gaussian_smooth(volume, sigma=1.0)
        self.assertEqual(smoothed.shape, volume.shape)
        # La somme ne devrait pas exploser
        self.assertLess(float(smoothed.max()), 1.5)


# ============================================================
class TestBoneSegmenter(unittest.TestCase):

    def setUp(self):
        from app.ai.reconstruction.segmentation import BoneSegmenter
        self.segmenter = BoneSegmenter(preset='spine')

    def test_segment_detects_bone(self):
        """La segmentation doit trouver les voxels os."""
        volume = create_sphere_volume(bg_hu=-500, bone_hu=900)
        mask = self.segmenter.segment(volume)
        self.assertGreater(mask.sum(), 0)

    def test_segment_excludes_soft_tissue(self):
        """Les tissus mous (-500 HU) ne doivent pas être dans le masque."""
        volume = np.full((30, 30, 30), -500, dtype=np.float32)
        mask = self.segmenter.segment(volume)
        self.assertEqual(mask.sum(), 0)

    def test_get_volume_fraction(self):
        """Le pourcentage doit être dans [0, 100]."""
        volume = create_sphere_volume()
        mask = self.segmenter.segment(volume)
        pct = self.segmenter.get_volume_fraction(mask)
        self.assertGreaterEqual(pct, 0.0)
        self.assertLessEqual(pct, 100.0)

    def test_all_presets_work(self):
        """Tous les presets doivent s'instancier sans erreur."""
        from app.ai.reconstruction.segmentation import BoneSegmenter
        for preset in BoneSegmenter.PRESETS:
            seg = BoneSegmenter(preset=preset)
            volume = create_sphere_volume()
            mask = seg.segment(volume)
            self.assertIsNotNone(mask)


# ============================================================
class TestMeshGenerator(unittest.TestCase):

    def setUp(self):
        from app.ai.reconstruction.mesh_generator import MeshGenerator
        self.generator = MeshGenerator(
            level=0.5,
            step_size=2,
            decimate_ratio=0.3,
            smooth_iterations=5,
        )

    def test_generate_from_mask_returns_polydata(self):
        """La génération depuis un masque sphérique doit retourner un PolyData."""
        import pyvista as pv
        try:
            from skimage.measure import marching_cubes
        except ImportError:
            self.skipTest("scikit-image non disponible")

        mask = create_normalized_sphere(shape=(50, 50, 50), radius=18) > 0.5
        mesh = self.generator.generate_from_mask(mask)

        self.assertIsNotNone(mesh, "Le maillage ne devrait pas être None pour une sphère")
        self.assertIsInstance(mesh, pv.PolyData)
        self.assertGreater(mesh.n_points, 0)
        self.assertGreater(mesh.n_cells, 0)

    def test_generate_empty_volume_returns_none(self):
        """Un volume vide (tout à 0) doit retourner None."""
        volume = np.zeros((30, 30, 30), dtype=np.float32)
        mesh = self.generator.generate(volume, level=0.5)
        self.assertIsNone(mesh)

    def test_full_volume_returns_none(self):
        """Un volume plein (tout à 1) doit retourner None (pas de surface isolée)."""
        volume = np.ones((30, 30, 30), dtype=np.float32)
        mesh = self.generator.generate(volume, level=0.5)
        self.assertIsNone(mesh)

    def test_spacing_applied(self):
        """Le maillage avec un grand spacing doit avoir des coordonnées plus grandes."""
        try:
            from skimage.measure import marching_cubes
        except ImportError:
            self.skipTest("scikit-image non disponible")

        mask = create_normalized_sphere(shape=(40, 40, 40), radius=15) > 0.5
        mesh1 = self.generator.generate_from_mask(mask, spacing=(1.0, 1.0, 1.0))
        mesh2 = self.generator.generate_from_mask(mask, spacing=(2.0, 2.0, 2.0))

        if mesh1 is not None and mesh2 is not None:
            # Avec spacing*2, les coordonnées doivent être environ 2x plus grandes
            self.assertGreater(mesh2.bounds[1], mesh1.bounds[1] * 1.5)


# ============================================================
class TestSpineReconstructor(unittest.TestCase):

    def test_reconstruct_from_volume(self):
        """Test d'intégration complet sur un volume synthétique."""
        try:
            from skimage.measure import marching_cubes
        except ImportError:
            self.skipTest("scikit-image non disponible")

        from app.ai.reconstruction.spine_reconstructor import SpineReconstructor

        # Volume synthétique avec une sphère simulant une vertèbre
        volume = create_sphere_volume(
            shape=(60, 60, 60), radius=22,
            bg_hu=-400, bone_hu=700
        )

        reconstructor = SpineReconstructor(hu_low=200, hu_high=1600, step_size=2)
        results = reconstructor.reconstruct_from_volume(volume, spacing=(1.0, 1.0, 1.0))

        self.assertIn('original_volume', results)
        self.assertIn('normalized_volume', results)
        self.assertIn('segmentation_mask', results)
        self.assertIn('mesh', results)
        self.assertIn('stats', results)

        self.assertIsNotNone(results['mesh'], "Un maillage doit être généré")
        self.assertGreater(results['stats']['bone_voxels'], 0)
        self.assertGreater(results['stats']['mesh_vertices'], 0)


if __name__ == '__main__':
    unittest.main(verbosity=2)
