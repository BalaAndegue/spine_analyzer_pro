"""
AnalysisWorker — Pipeline d'analyse complet asynchrone.
Intègre : reconstruction 3D, détection vertèbres, classification IA, métriques réelles.
"""

import time
import traceback
from typing import Dict, Any

from PySide6.QtCore import QObject, Signal, Slot

from app.data.dicom_loader import DICOMManager
from app.ai.reconstruction.spine_reconstructor import SpineReconstructor
from app.ai.detection.anomaly_detector import AnomalyDetector
from app.ai.detection.vertebra_detector import VertebraDetector
from app.ai.detection.vertebra_classifier import VertebraClassifier
from app.analysis.quantitative import QuantitativeAnalyzer


class AnalysisWorker(QObject):
    """Worker pour l'analyse complète asynchrone (QThread)."""

    progress = Signal(int, str)   # pourcentage, message
    finished = Signal(dict)       # résultats complets
    error    = Signal(str)        # message d'erreur

    def __init__(self, patient_data: Dict[str, Any]):
        super().__init__()
        self.patient_data = patient_data   # dict avec 'id', 'dicom_folder', 'info'
        self.is_running   = False

    @Slot()
    def run(self):
        self.is_running = True
        try:
            results = {}
            dicom_folder = self.patient_data.get("dicom_folder", "")

            # ── 1. Reconstruction 3D ──────────────────────────────────── 0→35%
            self.progress.emit(0, "Chargement DICOM et reconstruction 3D...")
            reconstructor = SpineReconstructor(step_size=1)   # step=1 → plus de détails
            recon = reconstructor.reconstruct_from_dicom(
                dicom_folder,
                progress_callback=lambda p, m: self.progress.emit(int(p * 0.35), m),
            )
            results["reconstruction"] = recon
            self.progress.emit(35, "Reconstruction 3D terminée")

            mesh       = recon.get("mesh")
            volume     = recon.get("original_volume")
            bone_mask  = recon.get("segmentation_mask")
            spacing    = recon.get("spacing", (1.0, 1.0, 1.0))

            # ── 2. Détection des vertèbres ─────────────────────────────── 35→60%
            self.progress.emit(35, "Détection et localisation des vertèbres...")
            vertebrae = []
            if bone_mask is not None and volume is not None:
                detector  = VertebraDetector()
                vertebrae = detector.detect(bone_mask, volume, spacing=spacing)

                # Classification IA
                self.progress.emit(50, "Classification IA des vertèbres...")
                clf = VertebraClassifier()
                vertebrae = clf.classify(vertebrae)

            results["vertebrae"] = vertebrae
            self.progress.emit(60, f"{len(vertebrae)} vertèbres détectées et classifiées")

            # ── 3. Détection d'anomalies ────────────────────────────────── 60→75%
            self.progress.emit(60, "Détection d'anomalies...")
            anomalies = []
            if volume is not None and bone_mask is not None:
                detector_anom = AnomalyDetector()
                try:
                    anomalies = detector_anom.detect_anomalies(volume, bone_mask)
                except Exception:
                    anomalies = []
            results["anomalies"] = anomalies
            self.progress.emit(75, f"{len(anomalies)} anomalies détectées")

            # ── 4. Analyse quantitative ─────────────────────────────────── 75→90%
            self.progress.emit(75, "Calcul des métriques rachidiennes...")
            analyzer = QuantitativeAnalyzer()
            quantitative = analyzer.analyze(
                mesh       = mesh,
                anomalies  = anomalies,
                vertebrae  = vertebrae,
                volume     = volume,
                bone_mask  = bone_mask,
                spacing    = spacing,
            )
            results["quantitative"] = quantitative
            # Passer mesh et infos vertèbres pour l'affichage 3D
            results["mesh"]      = mesh
            results["vertebrae"] = vertebrae
            self.progress.emit(90, "Métriques calculées")

            # ── 5. Rapport ─────────────────────────────────────────────── 90→100%
            self.progress.emit(90, "Génération du rapport...")
            results["summary"] = self._generate_summary(results)
            self.progress.emit(100, "Analyse complète terminée ✅")

            self.finished.emit(results)

        except Exception as e:
            tb = traceback.format_exc()
            self.error.emit(f"Erreur analyse : {e}\n{tb}")
        finally:
            self.is_running = False

    def stop(self):
        self.is_running = False

    def _generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        anomalies  = results.get("anomalies", [])
        vertebrae  = results.get("vertebrae", [])
        quant      = results.get("quantitative", {})
        spacing    = results.get("reconstruction", {}).get("spacing", (1.0, 1.0, 1.0))

        recs = []

        # Recommandations basées sur les vertèbres classifiées
        comprimees = [v for v in vertebrae if v.get("ml_status") == "comprimée"]
        suspects   = [v for v in vertebrae if v.get("ml_status") == "suspect"]
        osteos     = [v for v in vertebrae if v.get("ml_status") == "ostéopénique"]

        if comprimees:
            labels = ", ".join(v["label"] for v in comprimees)
            recs.append(f"⚠️ Fracture-tassement suspectée : {labels} — IRM recommandée")
        if suspects:
            labels = ", ".join(v["label"] for v in suspects)
            recs.append(f"⚠️ Vertèbres suspectes : {labels} — surveillance rapprochée")
        if osteos:
            recs.append("💊 Densité HU basse — Bilan ostéoporose (ostéodensitométrie) conseillé")

        cobb = quant.get("estimated_cobb_angle_deg", 0)
        if cobb > 10:
            recs.append(f"📐 Déformation axiale estimée {cobb:.1f}° — consulter un chirurgien rachidien")
        elif cobb > 5:
            recs.append(f"📐 Légère déformation axiale ({cobb:.1f}°) — suivi semestriel")

        if not recs:
            recs.append("✅ Aucune anomalie significative détectée — suivi standard recommandé")

        return {
            "patient_id":       self.patient_data.get("id", "Unknown"),
            "analysis_date":    time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_anomalies":  len(anomalies),
            "vertebrae_count":  len(vertebrae),
            "recommendations":  recs,
            "spacing_mm":       spacing,
        }