"""
ReconstructionWorker — Worker Qt asynchrone pour la reconstruction 3D.
S'exécute dans un QThread séparé pour ne pas bloquer l'interface.
"""

import logging
from typing import Dict, Any, Optional

from PySide6.QtCore import QObject, Signal, Slot

logger = logging.getLogger(__name__)


class ReconstructionWorker(QObject):
    """
    Worker Qt pour la reconstruction 3D asynchrone.

    Signaux :
        progress(int, str)  — pourcentage + message
        finished(dict)      — résultats du pipeline
        error(str)          — message d'erreur
    """

    progress = Signal(int, str)
    finished = Signal(dict)
    error = Signal(str)

    def __init__(
        self,
        dicom_folder: Optional[str] = None,
        volume=None,
        spacing=(1.0, 1.0, 1.0),
        hu_low: int = 200,
        hu_high: int = 1600,
        step_size: int = 2,
        decimate_ratio: float = 0.3,
    ):
        """
        Args:
            dicom_folder : chemin DICOM (prioritaire si fourni)
            volume       : numpy array 3D si déjà en mémoire
            spacing      : (dz, dy, dx) en mm
            hu_low/high  : fenêtre HU pour segmentation os
            step_size    : sous-échantillonnage Marching Cubes
            decimate_ratio: décimation du maillage
        """
        super().__init__()
        self.dicom_folder = dicom_folder
        self.volume = volume
        self.spacing = spacing
        self.hu_low = hu_low
        self.hu_high = hu_high
        self.step_size = step_size
        self.decimate_ratio = decimate_ratio
        self._stop_requested = False

    @Slot()
    def run(self):
        """Exécuter la reconstruction dans le thread courant."""
        try:
            from app.ai.reconstruction.spine_reconstructor import SpineReconstructor

            reconstructor = SpineReconstructor(
                hu_low=self.hu_low,
                hu_high=self.hu_high,
                step_size=self.step_size,
                decimate_ratio=self.decimate_ratio,
            )

            def _progress_cb(pct, msg):
                if not self._stop_requested:
                    self.progress.emit(pct, msg)

            if self.dicom_folder:
                results = reconstructor.reconstruct_from_dicom(
                    self.dicom_folder,
                    progress_callback=_progress_cb,
                )
            elif self.volume is not None:
                results = reconstructor.reconstruct_from_volume(
                    self.volume,
                    spacing=self.spacing,
                    progress_callback=_progress_cb,
                )
            else:
                self.error.emit("Aucune source de données fournie (DICOM ou volume)")
                return

            if not self._stop_requested:
                self.finished.emit(results)

        except Exception as e:
            logger.error(f"ReconstructionWorker erreur: {e}", exc_info=True)
            self.error.emit(f"Erreur reconstruction 3D : {str(e)}")

    def stop(self):
        """Demander l'arrêt propre."""
        self._stop_requested = True
        logger.info("Arrêt du ReconstructionWorker demandé")
