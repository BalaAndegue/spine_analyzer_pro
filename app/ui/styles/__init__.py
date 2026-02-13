"""
Styles et thèmes pour l'interface SpineAnalyzer Pro
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any

from PySide6.QtGui import QIcon, QPixmap, QColor
from PySide6.QtCore import QFile, QTextStream


def load_stylesheet(theme: str = "dark") -> str:
    """
    Charger une feuille de style QSS
    
    Args:
        theme: Nom du thème ('dark', 'light', 'medical')
    
    Returns:
        Chaîne QSS
    """
    theme_file = f"{theme}_theme.qss"
    styles_dir = Path(__file__).parent
    
    # Essayer de charger depuis le fichier
    qss_file = styles_dir / theme_file
    if qss_file.exists():
        try:
            with open(qss_file, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Erreur de chargement du style {theme}: {e}")
    
    # Fallback vers des styles intégrés
    if theme == "dark":
        return get_dark_stylesheet()
    elif theme == "light":
        return get_light_stylesheet()
    elif theme == "medical":
        return get_medical_stylesheet()
    else:
        return get_dark_stylesheet()


def get_icon(name: str) -> QIcon:
    """
    Obtenir une icône par son nom
    
    Args:
        name: Nom de l'icône
    
    Returns:
        QIcon
    """
    # Chemin vers les ressources
    icons_dir = Path(__file__).parent.parent.parent / "resources" / "icons"
    
    # Essayer différents formats
    extensions = ['.svg', '.png', '.ico']
    
    for ext in extensions:
        icon_path = icons_dir / f"{name}{ext}"
        if icon_path.exists():
            return QIcon(str(icon_path))
    
    # Fallback vers les icônes système
    return QIcon.fromTheme(name)


def get_dark_stylesheet() -> str:
    """Feuille de style sombre par défaut"""
    return """
    /* SpineAnalyzer Pro - Dark Theme */
    
    QMainWindow {
        background-color: #1a1a1a;
    }
    
    QWidget {
        color: #e0e0e0;
        background-color: #2a2a2a;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
    }
    
    QMenuBar {
        background-color: #1e1e1e;
        border-bottom: 1px solid #333;
    }
    
    QMenuBar::item {
        background-color: transparent;
        padding: 5px 10px;
    }
    
    QMenuBar::item:selected {
        background-color: #3a3a3a;
    }
    
    QMenu {
        background-color: #2a2a2a;
        border: 1px solid #444;
    }
    
    QMenu::item {
        padding: 5px 20px 5px 20px;
    }
    
    QMenu::item:selected {
        background-color: #3a3a3a;
    }
    
    QToolBar {
        background-color: #252525;
        border: none;
        spacing: 5px;
        padding: 3px;
    }
    
    QToolButton {
        background-color: transparent;
        border: 1px solid transparent;
        border-radius: 3px;
        padding: 5px;
    }
    
    QToolButton:hover {
        background-color: #3a3a3a;
        border: 1px solid #555;
    }
    
    QToolButton:pressed {
        background-color: #4a4a4a;
    }
    
    QToolButton:checked {
        background-color: #4a4a4a;
        border: 1px solid #666;
    }
    
    QDockWidget {
        titlebar-close-icon: url(close_light.png);
        titlebar-normal-icon: url(float_light.png);
        background-color: #2a2a2a;
    }
    
    QDockWidget::title {
        background-color: #1e1e1e;
        padding: 5px;
        border: none;
    }
    
    QGroupBox {
        font-weight: bold;
        border: 1px solid #444;
        border-radius: 5px;
        margin-top: 10px;
        padding-top: 10px;
    }
    
    QGroupBox::title {
        subcontrol-origin: margin;
        left: 10px;
        padding: 0 5px 0 5px;
    }
    
    QPushButton {
        background-color: #3a3a3a;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 5px 15px;
        min-height: 25px;
    }
    
    QPushButton:hover {
        background-color: #4a4a4a;
        border: 1px solid #666;
    }
    
    QPushButton:pressed {
        background-color: #5a5a5a;
    }
    
    QPushButton:disabled {
        background-color: #2a2a2a;
        color: #666;
        border: 1px solid #444;
    }
    
    QPushButton#btnAnalyze {
        background-color: #4CAF50;
        color: white;
        font-weight: bold;
    }
    
    QPushButton#btnAnalyze:hover {
        background-color: #45a049;
    }
    
    QPushButton#btnAnalyze:pressed {
        background-color: #3d8b40;
    }
    
    QLabel {
        color: #e0e0e0;
    }
    
    QLineEdit, QTextEdit, QPlainTextEdit {
        background-color: #1e1e1e;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 5px;
        selection-background-color: #4a4a4a;
    }
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
        border: 1px solid #6a6a6a;
    }
    
    QComboBox {
        background-color: #1e1e1e;
        border: 1px solid #555;
        border-radius: 3px;
        padding: 5px;
        min-height: 25px;
    }
    
    QComboBox:hover {
        border: 1px solid #666;
    }
    
    QComboBox:focus {
        border: 1px solid #6a6a6a;
    }
    
    QComboBox::drop-down {
        border: none;
    }
    
    QComboBox::down-arrow {
        image: url(down_arrow_light.png);
        width: 12px;
        height: 12px;
    }
    
    QComboBox QAbstractItemView {
        background-color: #2a2a2a;
        border: 1px solid #555;
        selection-background-color: #3a3a3a;
    }
    
    QCheckBox {
        spacing: 8px;
    }
    
    QCheckBox::indicator {
        width: 16px;
        height: 16px;
    }
    
    QCheckBox::indicator:unchecked {
        border: 1px solid #555;
        background-color: #1e1e1e;
    }
    
    QCheckBox::indicator:checked {
        border: 1px solid #555;
        background-color: #4a4a4a;
        image: url(checkbox_checked.png);
    }
    
    QRadioButton {
        spacing: 8px;
    }
    
    QRadioButton::indicator {
        width: 16px;
        height: 16px;
    }
    
    QRadioButton::indicator:unchecked {
        border: 1px solid #555;
        border-radius: 8px;
        background-color: #1e1e1e;
    }
    
    QRadioButton::indicator:checked {
        border: 1px solid #555;
        border-radius: 8px;
        background-color: #4a4a4a;
    }
    
    QSlider::groove:horizontal {
        background-color: #1e1e1e;
        height: 6px;
        border-radius: 3px;
    }
    
    QSlider::handle:horizontal {
        background-color: #6a6a6a;
        width: 16px;
        height: 16px;
        border-radius: 8px;
        margin: -5px 0;
    }
    
    QSlider::handle:horizontal:hover {
        background-color: #8a8a8a;
    }
    
    QSlider::add-page:horizontal {
        background-color: #444;
    }
    
    QSlider::sub-page:horizontal {
        background-color: #6a6a6a;
    }
    
    QProgressBar {
        background-color: #1e1e1e;
        border: 1px solid #555;
        border-radius: 3px;
        text-align: center;
    }
    
    QProgressBar::chunk {
        background-color: #4CAF50;
        border-radius: 2px;
    }
    
    QTabWidget::pane {
        background-color: #2a2a2a;
        border: 1px solid #444;
    }
    
    QTabBar::tab {
        background-color: #3a3a3a;
        color: #e0e0e0;
        padding: 8px 15px;
        margin-right: 2px;
        border: 1px solid #444;
        border-bottom: none;
        border-top-left-radius: 3px;
        border-top-right-radius: 3px;
    }
    
    QTabBar::tab:selected {
        background-color: #2a2a2a;
        border-bottom: 1px solid #2a2a2a;
    }
    
    QTabBar::tab:hover {
        background-color: #4a4a4a;
    }
    
    QScrollBar:vertical {
        background-color: #1e1e1e;
        width: 12px;
    }
    
    QScrollBar::handle:vertical {
        background-color: #4a4a4a;
        border-radius: 6px;
        min-height: 20px;
    }
    
    QScrollBar::handle:vertical:hover {
        background-color: #5a5a5a;
    }
    
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
        background: none;
    }
    
    QScrollBar:horizontal {
        background-color: #1e1e1e;
        height: 12px;
    }
    
    QScrollBar::handle:horizontal {
        background-color: #4a4a4a;
        border-radius: 6px;
        min-width: 20px;
    }
    
    QScrollBar::handle:horizontal:hover {
        background-color: #5a5a5a;
    }
    
    QTreeView, QListView, QTableView {
        background-color: #1e1e1e;
        border: 1px solid #555;
        selection-background-color: #3a3a3a;
        alternate-background-color: #252525;
    }
    
    QHeaderView::section {
        background-color: #252525;
        color: #e0e0e0;
        padding: 5px;
        border: 1px solid #444;
    }
    
    QStatusBar {
        background-color: #1e1e1e;
        color: #a0a0a0;
        border-top: 1px solid #333;
    }
    
    /* Styles spécifiques à l'application médicale */
    MedicalLabel {
        font-weight: bold;
        color: #4CAF50;
    }
    
    WarningLabel {
        color: #FFA500;
        font-weight: bold;
    }
    
    ErrorLabel {
        color: #FF6B6B;
        font-weight: bold;
    }
    
    SuccessLabel {
        color: #4CAF50;
        font-weight: bold;
    }
    """


def get_light_stylesheet() -> str:
    """Feuille de style claire"""
    return """
    /* SpineAnalyzer Pro - Light Theme */
    
    QMainWindow {
        background-color: #f0f0f0;
    }
    
    QWidget {
        color: #333333;
        background-color: #ffffff;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
    }
    
    /* ... styles similaires mais avec couleurs claires ... */
    """


def get_medical_stylesheet() -> str:
    """Feuille de style médical (bleu professionnel)"""
    return """
    /* SpineAnalyzer Pro - Medical Theme */
    
    QMainWindow {
        background-color: #1a2639;
    }
    
    QWidget {
        color: #e8f4f8;
        background-color: #2c3e50;
        font-family: 'Segoe UI', Arial, sans-serif;
        font-size: 10pt;
    }
    
    QMenuBar {
        background-color: #1a252f;
        border-bottom: 1px solid #34495e;
    }
    
    /* ... styles avec palette médicale bleue ... */
    """