#!/bin/bash
# Script de lancement - SpineAnalyzer Pro
# Résout le conflit entre les plugins Qt5 d'Anaconda et PySide6 (Qt6)

cd "$(dirname "$0")"

export QT_QPA_PLATFORM_PLUGIN_PATH=/home/bala/anaconda3/lib/python3.12/site-packages/PySide6/Qt/plugins/platforms

echo "🚀 Lancement de SpineAnalyzer Pro..."
python3 main.py "$@"
