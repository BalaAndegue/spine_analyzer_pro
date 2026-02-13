#!/usr/bin/env python3
'''
Script d'installation de SpineAnalyzer Pro


import subprocess
import sys
import os

def run_command(cmd: str):
    """Exécuter une commande shell"""
    print(f"Exécution: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Erreur: {result.stderr}")
    return result.returncode

def main():
    print("=" * 60)
    print("Installation de SpineAnalyzer Pro")
    print("=" * 60)
    
    # 1. Créer un environnement virtuel (optionnel)
    create_venv = input("Créer un environnement virtuel ? (o/n): ").lower()
    if create_venv == 'o':
        venv_name = input("Nom de l'environnement [venv]: ") or "venv"
        run_command(f"python -m venv {venv_name}")
        
        if sys.platform == "win32":
            activate_cmd = f"{venv_name}\\Scripts\\activate"
        else:
            activate_cmd = f"source {venv_name}/bin/activate"
        
        print(f"Activez l'environnement avec: {activate_cmd}")
    
    # 2. Installer les dépendances
    print("\nInstallation des dépendances...")
    run_command("pip install --upgrade pip")
    
    # Installer à partir de requirements.txt
    if os.path.exists("requirements.txt"):
        run_command("pip install -r requirements.txt")
    else:
        # Installer les packages essentiels
        essential_packages = [
            "PySide6",
            "pydicom",
            "numpy",
            "opencv-python",
            "torch",
            "torchvision",
            "monai",
            "pyvista",
            "matplotlib",
            "pandas"
        ]
        run_command(f"pip install {' '.join(essential_packages)}")
    
    # 3. Télécharger les modèles pré-entraînés
    print("\nTéléchargement des modèles pré-entraînés...")
    models_dir = "models"
    os.makedirs(models_dir, exist_ok=True)
    
    # Télécharger TotalSegmentator
    print("Installation de TotalSegmentator...")
    run_command("pip install TotalSegmentator")
    
    # 4. Créer la structure des dossiers
    print("\nCréation de la structure des dossiers...")
    folders = [
        "data/patients",
        "data/cache",
        "data/exports",
        "logs",
        "resources/icons",
        "resources/fonts"
    ]
    
    for folder in folders:
        os.makedirs(folder, exist_ok=True)
        print(f"Créé: {folder}")
    
    # 5. Tester l'installation
    print("\nTest de l'installation...")
    test_cmd = f"{sys.executable} -c \"import PySide6; print('PySide6 OK')\""
    run_command(test_cmd)
    
    print("\n" + "=" * 60)
    print("Installation terminée avec succès !")
    print("Pour démarrer l'application:")
    print("  python main.py")
    print("=" * 60)

if __name__ == "__main__":
    main() '''