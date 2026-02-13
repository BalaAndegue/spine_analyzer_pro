
import sys
import os

files = [
    "app/ui/widgets/custom_widgets.py",
    "app/ui/widgets/patient_info_widget.py",
    "app/ui/widgets/control_panel.py",
    "app/ui/widgets/results_panel.py",
    "app/ui/main_window.py"
]

print("Checking syntax...")
for f in files:
    path = os.path.abspath(f)
    try:
        with open(path, 'r') as file:
            source = file.read()
        compile(source, path, 'exec')
        print(f"OK: {f}")
    except Exception as e:
        print(f"ERROR in {f}: {e}")
