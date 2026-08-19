import os
import shutil
import sys

try:
    import PyInstaller.__main__
except ImportError:
    print("PyInstaller is not installed. Run: pip install pyinstaller", file=sys.stderr)
    sys.exit(1)

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(SCRIPT_DIR, "dist")
BUILD_DIR = os.path.join(SCRIPT_DIR, "build")

# Clean up previous build artifacts
if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)

print("Building standalone EXE...")
PyInstaller.__main__.run([
    "main.py",
    "--onefile",
    "--name", "nvr_script",
    "--clean",
    "--noconfirm",
])

print(f"\nDone. EXE is at: {os.path.join(DIST_DIR, 'nvr_script.exe')}")
print("Place this EXE in a folder with a config.json file (it will create a default one on first run if missing).")
