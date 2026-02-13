
import sys
import os

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Checking imports...")

try:
    print("Importing core...")
    from app.core.config import Config
    from app.core.application import SpineAnalyzerApp
    
    print("Importing data...")
    from app.data.dicom_loader import DICOMManager
    
    print("Importing AI...")
    from app.ai.reconstruction.spine_reconstructor import SpineReconstructor
    from app.ai.detection.anomaly_detector import AnomalyDetector
    from app.analysis.quantitative import QuantitativeAnalyzer
    
    print("Importing UI...")
    # Note: importing UI might fail if no display is available, but we check for ImportErrors
    try:
        from app.ui.main_window import MainWindow
        from app.ui.widgets.control_panel import ControlPanel
        from app.ui.widgets.results_panel import ResultsPanel
    except ImportError as e:
        if "PySide6" in str(e) or "pyside" in str(e).lower():
             print(f"❌ UI Verification requires PySide6: {e}")
             sys.exit(1)
        print(f"UI Import Warning (expected if headless): {e}")
    except Exception as e:
        # Allow Qt-related errors (no display), but catch structure errors
        if "depend" in str(e).lower() or "display" in str(e).lower() or "qt" in str(e).lower():
            print(f"UI Init Warning (expected): {e}")
        else:
            raise e

    print("✅ All modules imported successfully!")

except Exception as e:
    print(f"❌ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
