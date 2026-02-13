"""
Worker pour l'analyse asynchrone
"""

import time
from typing import Dict, Any
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot, QRunnable

from app.data.dicom_loader import DICOMManager
from app.ai.reconstruction.spine_reconstructor import SpineReconstructor
from app.ai.detection.anomaly_detector import AnomalyDetector
from app.analysis.quantitative import QuantitativeAnalyzer

@dataclass
class AnalysisResult:
    """Résultat de l'analyse"""
    success: bool
    data: Dict[str, Any]
    error: str = None

class AnalysisWorker(QObject):
    """Worker pour l'analyse complète"""
    
    # Signaux
    progress = Signal(int, str)  # pourcentage, message
    finished = Signal(dict)      # résultats
    error = Signal(str)          # message d'erreur
    
    def __init__(self, patient_data: Dict[str, Any]):
        super().__init__()
        self.patient_data = patient_data
        self.is_running = False
        
    @Slot()
    def run(self):
        """Exécuter l'analyse"""
        self.is_running = True
        
        try:
            results = {}
            
            # 1. Reconstruction 3D (20%)
            self.progress.emit(0, "Reconstruction 3D en cours...")
            reconstructor = SpineReconstructor()
            reconstruction_result = reconstructor.reconstruct_from_dicom(
                self.patient_data['dicom_folder']
            )
            results['reconstruction'] = reconstruction_result
            self.progress.emit(20, "Reconstruction 3D terminée")
            
            # 2. Détection d'anomalies (40%)
            self.progress.emit(20, "Détection d'anomalies...")
            detector = AnomalyDetector()
            anomalies = detector.detect_anomalies(
                reconstruction_result['original_volume'],
                reconstruction_result['segmentation_mask']
            )
            results['anomalies'] = anomalies
            self.progress.emit(60, f"{len(anomalies)} anomalies détectées")
            
            # 3. Analyse quantitative (20%)
            self.progress.emit(60, "Analyse quantitative...")
            analyzer = QuantitativeAnalyzer()
            quantitative_results = analyzer.analyze(
                reconstruction_result['mesh'],
                anomalies
            )
            results['quantitative'] = quantitative_results
            self.progress.emit(80, "Analyse quantitative terminée")
            
            # 4. Génération du rapport (20%)
            self.progress.emit(80, "Génération du rapport...")
            results['summary'] = self.generate_summary(results)
            self.progress.emit(100, "Analyse terminée")
            
            # Émettre les résultats
            self.finished.emit(results)
            
        except Exception as e:
            self.error.emit(f"Erreur lors de l'analyse: {str(e)}")
            
        finally:
            self.is_running = False
    
    def generate_summary(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Générer un résumé des résultats"""
        anomalies = results.get('anomalies', [])
        
        summary = {
            'patient_id': self.patient_data.get('id', 'Unknown'),
            'analysis_date': time.strftime("%Y-%m-%d %H:%M:%S"),
            'total_anomalies': len(anomalies),
            'anomaly_types': {},
            'recommendations': []
        }
        
        # Compter les types d'anomalies
        for anomaly in anomalies:
            anomaly_type = anomaly.get('type', 'unknown')
            summary['anomaly_types'][anomaly_type] = summary['anomaly_types'].get(anomaly_type, 0) + 1
        
        # Générer des recommandations
        if summary['total_anomalies'] > 0:
            summary['recommendations'].append(
                "Consultation spécialisée recommandée"
            )
            
            if 'fracture' in summary['anomaly_types']:
                summary['recommendations'].append(
                    "Radiographie complémentaire sous différentes incidences"
                )
            
            if 'tumor' in summary['anomaly_types']:
                summary['recommendations'].append(
                    "IRM avec contraste recommandée pour caractérisation"
                )
        else:
            summary['recommendations'].append(
                "Aucune anomalie majeure détectée. Suivi standard recommandé."
            )
        
        return summary