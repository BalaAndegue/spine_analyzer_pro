
import logging
from typing import Dict, Any, List

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLabel, QGroupBox, QHeaderView, QTabWidget, QTextEdit
)
from PySide6.QtCore import Qt

from ..core.logger import get_logger

logger = get_logger(__name__)

class ResultsPanel(QWidget):
    """Panneau d'affichage des résultats d'analyse"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configurer l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Onglets pour différents types de résultats
        self.tabs = QTabWidget()
        
        # Onglet Anomalies
        self.anomalies_tree = QTreeWidget()
        self.anomalies_tree.setHeaderLabels(["Type", "Slice", "Confiance", "Détails"])
        self.anomalies_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tabs.addTab(self.anomalies_tree, "Anomalies")
        
        # Onglet Métriques
        self.metrics_widget = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics_widget)
        self.metrics_label = QLabel("Aucune métrique disponible")
        self.metrics_label.setAlignment(Qt.AlignTop)
        self.metrics_layout.addWidget(self.metrics_label)
        self.tabs.addTab(self.metrics_widget, "Métriques")
        
        # Onglet Résumé/Recommandations
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.tabs.addTab(self.summary_text, "Résumé")
        
        layout.addWidget(self.tabs)
        
    def set_results(self, results: Dict[str, Any]):
        """Afficher les résultats"""
        self.clear()
        
        # 1. Anomalies
        anomalies = results.get('anomalies', [])
        for anomaly in anomalies:
            item = QTreeWidgetItem(self.anomalies_tree)
            item.setText(0, str(anomaly.get('type', 'Unknown')))
            item.setText(1, str(anomaly.get('slice_index', '-')))
            conf = anomaly.get('confidence', 0.0)
            item.setText(2, f"{conf:.2f}")
            item.setText(3, str(anomaly.get('description', '')))
            
            # Color code based on confidence or severity (optional)
            
        # 2. Métriques
        quantitative = results.get('quantitative', {})
        metrics_text = "<h3>Métriques Rachidiennes</h3>"
        metrics_text += "<ul>"
        for k, v in quantitative.items():
            nice_key = k.replace('_', ' ').title()
            if isinstance(v, float):
                metrics_text += f"<li><b>{nice_key}:</b> {v:.2f}</li>"
            else:
                metrics_text += f"<li><b>{nice_key}:</b> {v}</li>"
        metrics_text += "</ul>"
        self.metrics_label.setText(metrics_text)
        
        # 3. Résumé
        summary = results.get('summary', {})
        recs = summary.get('recommendations', [])
        
        summary_html = "<h2>Rapport Sommaire</h2>"
        summary_html += f"<p><b>Date:</b> {summary.get('analysis_date', '-')}</p>"
        summary_html += f"<p><b>Total Anomalies:</b> {summary.get('total_anomalies', 0)}</p>"
        
        if recs:
            summary_html += "<h3>Recommandations:</h3><ul>"
            for rec in recs:
                summary_html += f"<li>{rec}</li>"
            summary_html += "</ul>"
            
        self.summary_text.setHtml(summary_html)
        
        # Focus sur l'onglet anomalies s'il y en a
        if anomalies:
            self.tabs.setCurrentIndex(0)

    def clear(self):
        """Effacer les résultats"""
        self.anomalies_tree.clear()
        self.metrics_label.setText("Aucune métrique disponible")
        self.summary_text.clear()
