"""
Reconstruction 3D de la colonne vertébrale à partir d'images DICOM
"""

import torch
import numpy as np
from typing import Optional, Tuple, Dict, Any
import SimpleITK as sitk
import monai
from monai.networks.nets import UNet
from monai.transforms import Compose, LoadImage, EnsureChannelFirst, ScaleIntensity

class SpineReconstructor:
    """Reconstructeur 3D de la colonne vertébrale"""
    
    def __init__(self, device: str = "cuda" if torch.cuda.is_available() else "cpu"):
        self.device = torch.device(device)
        self.model = self._load_model()
        self.transforms = self._get_transforms()
        
    def _load_model(self) -> UNet:
        """Charger le modèle de segmentation"""
        # Configuration du modèle UNet 3D
        model = UNet(
            spatial_dims=3,
            in_channels=1,
            out_channels=1,
            channels=(16, 32, 64, 128, 256),
            strides=(2, 2, 2, 2),
            num_res_units=2,
        )
        
        # Charger les poids pré-entraînés
        model_path = "models/segmentation/vertebrae_unet.pth"
        if os.path.exists(model_path):
            model.load_state_dict(torch.load(model_path, map_location=self.device))
        else:
            print(f"Avertissement: Modèle non trouvé à {model_path}")
            print("Utilisation d'un modèle non entraîné")
        
        model.to(self.device)
        model.eval()
        
        return model
    
    def reconstruct_from_dicom(self, dicom_folder: str) -> Dict[str, Any]:
        """
        Reconstruire un modèle 3D à partir d'un dossier DICOM
        
        Args:
            dicom_folder: Chemin vers le dossier DICOM
            
        Returns:
            Dict contenant le volume 3D, le mesh et les métadonnées
        """
        print(f"Reconstruction depuis: {dicom_folder}")
        
        # 1. Charger les images DICOM
        reader = sitk.ImageSeriesReader()
        dicom_names = reader.GetGDCMSeriesFileNames(dicom_folder)
        reader.SetFileNames(dicom_names)
        
        try:
            image = reader.Execute()
        except Exception as e:
            raise ValueError(f"Erreur de chargement DICOM: {e}")
        
        # 2. Convertir en numpy array
        volume = sitk.GetArrayFromImage(image)  # Shape: (depth, height, width)
        spacing = image.GetSpacing()
        origin = image.GetOrigin()
        
        print(f"Volume chargé: {volume.shape}, spacing: {spacing}")
        
        # 3. Prétraiter le volume
        volume_processed = self.preprocess_volume(volume)
        
        # 4. Segmenter la colonne vertébrale
        with torch.no_grad():
            # Préparer les données pour le modèle
            input_tensor = torch.from_numpy(volume_processed).float().unsqueeze(0).unsqueeze(0)
            input_tensor = input_tensor.to(self.device)
            
            # Inference
            output = self.model(input_tensor)
            segmentation = torch.sigmoid(output).squeeze().cpu().numpy()
            
            # Seuillage
            binary_mask = (segmentation > 0.5).astype(np.uint8)
        
        # 5. Générer le mesh 3D
        mesh = self.generate_mesh(binary_mask, spacing)
        
        # 6. Calculer les métriques
        metrics = self.compute_metrics(binary_mask, volume)
        
        return {
            'original_volume': volume,
            'segmentation_mask': binary_mask,
            'mesh': mesh,
            'spacing': spacing,
            'origin': origin,
            'metrics': metrics
        }
    
    def preprocess_volume(self, volume: np.ndarray) -> np.ndarray:
        """Prétraiter le volume pour la segmentation"""
        # Normalisation
        volume = volume.astype(np.float32)
        volume = (volume - volume.min()) / (volume.max() - volume.min() + 1e-8)
        
        # Redimensionnement si nécessaire
        target_shape = (128, 256, 256)  # Taille optimale pour le modèle
        if volume.shape != target_shape:
            # Utiliser SimpleITK pour le redimensionnement
            sitk_volume = sitk.GetImageFromArray(volume)
            resampler = sitk.ResampleImageFilter()
            resampler.SetSize(target_shape[::-1])  # SimpleITK utilise (width, height, depth)
            resampler.SetInterpolator(sitk.sitkLinear)
            volume_resized = sitk.GetArrayFromImage(resampler.Execute(sitk_volume))
            volume = volume_resized
        
        return volume
    
    def generate_mesh(self, binary_mask: np.ndarray, spacing: Tuple[float, float, float]):
        """Générer un mesh 3D à partir d'un masque binaire"""
        try:
            import pyvista as pv
            from skimage import measure
            
            # Utiliser marching cubes
            verts, faces, normals, values = measure.marching_cubes(
                binary_mask,
                level=0.5,
                spacing=spacing,
                step_size=1,
                allow_degenerate=False
            )
            
            # Créer un mesh PyVista
            faces = np.hstack([np.full((faces.shape[0], 1), 3), faces])
            mesh = pv.PolyData(verts, faces)
            
            # Lisser le mesh
            mesh = mesh.smooth(n_iter=50)
            
            return mesh
            
        except ImportError:
            print("Avertissement: PyVista non installé, retour du mesh sous forme de tuples")
            return {
                'vertices': verts.tolist(),
                'faces': faces.tolist(),
                'normals': normals.tolist()
            }
    
    def compute_metrics(self, mask: np.ndarray, volume: np.ndarray) -> Dict[str, float]:
        """Calculer les métriques du volume segmenté"""
        # Compter les voxels de la colonne
        voxel_count = np.sum(mask)
        
        # Volume physique (en mm³)
        voxel_volume = np.prod(self.spacing) if hasattr(self, 'spacing') else 1.0
        physical_volume = voxel_count * voxel_volume
        
        # Intensité moyenne de la colonne
        mean_intensity = np.mean(volume[mask > 0]) if voxel_count > 0 else 0
        
        return {
            'voxel_count': int(voxel_count),
            'physical_volume_mm3': float(physical_volume),
            'mean_intensity': float(mean_intensity),
            'mask_density': float(voxel_count / mask.size)
        }