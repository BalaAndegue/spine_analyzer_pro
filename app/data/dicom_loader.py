
import os
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import pydicom
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PatientData:
    """Structure de données pour un patient"""
    id: str
    info: Dict[str, Any]
    slices: List[pydicom.dataset.FileDataset]
    volume: Optional[np.ndarray] = None
    dicom_folder: str = ""

class DICOMManager:
    """Gestionnaire de chargement et manipulation DICOM"""
    
    def __init__(self):
        self.current_patient: Optional[PatientData] = None

    def load_folder(self, folder_path: str) -> PatientData:
        """Charger un dossier contenant des fichiers DICOM"""
        dicom_files = []
        patient_info = {}
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Dossier introuvable: {folder_path}")

        # Parcourir le dossier
        for root, _, files in os.walk(folder_path):
            for file in files:
                filepath = os.path.join(root, file)
                try:
                    # Tenter de lire le fichier comme DICOM
                    ds = pydicom.dcmread(filepath, stop_before_pixels=True)
                    
                    # Vérifier si c'est une image
                    if "PixelData" in ds:
                        # Re-lire avec les pixels si nécessaire, ou stocker le chemin pour lecture lazy
                        # Pour l'instant on lit tout le dataset
                        full_ds = pydicom.dcmread(filepath)
                        dicom_files.append(full_ds)
                        
                        # Extraire les infos patient du premier fichier valide
                        if not patient_info:
                            patient_info = self._extract_patient_info(full_ds)
                            
                except (pydicom.errors.InvalidDicomError, IsADirectoryError):
                    continue
                except Exception as e:
                    logger.warning(f"Erreur de lecture {filepath}: {e}")

        if not dicom_files:
            raise ValueError("Aucun fichier DICOM valide trouvé dans ce dossier")

        # Trier par InstanceNumber ou ImagePositionPatient
        dicom_files.sort(key=lambda x: int(x.InstanceNumber) if 'InstanceNumber' in x else x.filename)

        # Créer l'objet PatientData
        patient_id = patient_info.get('id', 'Unknown')
        
        self.current_patient = PatientData(
            id=patient_id,
            info=patient_info,
            slices=dicom_files,
            dicom_folder=folder_path
        )
        
        logger.info(f"Chargé {len(dicom_files)} fichiers DICOM pour le patient {patient_id}")
        return self.current_patient

    def _extract_patient_info(self, ds: pydicom.dataset.FileDataset) -> Dict[str, Any]:
        """Extraire les métadonnées pertinentes"""
        def get_val(tag, default="N/A"):
            return str(getattr(ds, tag, default))

        return {
            'id': get_val('PatientID'),
            'name': get_val('PatientName'),
            'birth_date': get_val('PatientBirthDate'),
            'sex': get_val('PatientSex'),
            'study_date': get_val('StudyDate'),
            'modality': get_val('Modality'),
            'manufacturer': get_val('Manufacturer'),
            'institution': get_val('InstitutionName')
        }

    def get_volume_array(self) -> np.ndarray:
        """Convertir les slices en volume numpy 3D"""
        if not self.current_patient or not self.current_patient.slices:
            return np.array([])
            
        slices = self.current_patient.slices
        
        # Supposer que toutes les slices ont la même taille et type
        shape = (len(slices), slices[0].Rows, slices[0].Columns)
        volume = np.zeros(shape, dtype=np.float32)
        
        for i, s in enumerate(slices):
            volume[i] = s.pixel_array.astype(np.float32)
            
            # Appliquer RescaleSlope et RescaleIntercept si présents (Unités Hounsfield)
            slope = getattr(s, 'RescaleSlope', 1)
            intercept = getattr(s, 'RescaleIntercept', 0)
            volume[i] = volume[i] * slope + intercept
            
        self.current_patient.volume = volume
        return volume
