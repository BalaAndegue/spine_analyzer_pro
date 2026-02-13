
import logging
from typing import Dict, Any, List, Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem, 
    QLabel, QHeaderView, QTabWidget, QTextEdit, QScrollArea
)
from PySide6.QtCore import Qt

from ..core.logger import get_logger
from .custom_widgets import ModernCard, InfoRow

logger = get_logger(__name__)

class ResultsPanel(QWidget):
    """Panneau d'affichage des résultats d'analyse"""
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Configurer l'interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 0)
        
        # Onglets pour différents types de résultats
        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        
        # --- Onglet Anomalies ---
        self.anomalies_widget = QWidget()
        anom_layout = QVBoxLayout(self.anomalies_widget)
        anom_layout.setContentsMargins(5, 5, 5, 5)
        
        self.anomalies_tree = QTreeWidget()
        self.anomalies_tree.setHeaderLabels(["Type", "Slice", "Conf", "Détails"])
        self.anomalies_tree.header().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.anomalies_tree.header().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.anomalies_tree.header().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.anomalies_tree.setAlternatingRowColors(True)
        anom_layout.addWidget(self.anomalies_tree)
        
        self.tabs.addTab(self.anomalies_widget, "Anomalies")
        
        # --- Onglet Métriques ---
        self.metrics_scroll = QScrollArea()
        self.metrics_scroll.setWidgetResizable(True)
        self.metrics_widget = QWidget()
        self.metrics_layout = QVBoxLayout(self.metrics_widget)
        self.metrics_layout.setSpacing(2)
        self.metrics_layout.setAlignment(Qt.AlignTop)
        
        self.metrics_scroll.setWidget(self.metrics_widget)
        self.tabs.addTab(self.metrics_scroll, "Métriques")
        
        # --- Onglet Résumé ---
        self.summary_text = QTextEdit()
        self.summary_text.setReadOnly(True)
        self.summary_text.setStyleSheet("border: none; padding: 10px;")
        self.tabs.addTab(self.summary_text, "Rapport")
        
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
            
            # Highlight severe anomalies ?
            if conf > 0.8:
                item.setForeground(0, Qt.red)
            
        # 2. Métriques
        quantitative = results.get('quantitative', {})
        if quantitative:
            card = ModernCard("Métriques Rachidiennes")
            for k, v in quantitative.items():
                nice_key = k.replace('_', ' ').title()
                val_str = f"{v:.2f}" if isinstance(v, float) else str(v)
                row = InfoRow(nice_key, val_str)
                card.add_widget(row)
            self.metrics_layout.addWidget(card)
        else:
            self.metrics_layout.addWidget(QLabel("Aucune métrique disponible"))
        
        # 3. Résumé
        self.update_summary(results.get('summary', {}))
        
        # Focus sur l'onglet anomalies s'il y en a
        if anomalies:
            self.tabs.setCurrentIndex(0)
            
    def update_summary(self, summary: dict):
        recs = summary.get('recommendations', [])
        
        css = """
        <style>
            h2 { color: #2196f3; }
            h3 { color: #e0e0e0; margin-top: 10px; }
            p { margin-bottom: 5px; }
            li { margin-bottom: 3px; }
        </style>
        """
        
        html = f"{css}<h2>Rapport Sommaire</h2>"
        html += f"<p><b>Date:</b> {summary.get('analysis_date', '-')}</p>"
        html += f"<p><b>Total Anomalies:</b> {summary.get('total_anomalies', 0)}</p>"
        
        if recs:
            html += "<h3>Recommandations:</h3><ul>"
            for rec in recs:
                html += f"<li>{rec}</li>"
            html += "</ul>"
            
        self.summary_text.setHtml(html)

    def clear(self):
        """Effacer les résultats"""
        self.anomalies_tree.clear()
        # Clear metrics layout
        while self.metrics_layout.count():
            child = self.metrics_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        self.summary_text.clear()
