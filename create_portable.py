
import os
import shutil
import subprocess
import sys

print("🚀 Creating Portable Application Bundle...")

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BUNDLE_DIR = os.path.join(BASE_DIR, "AlphaQuantPro_Portable")

# Clean previous bundle
if os.path.exists(BUNDLE_DIR):
    shutil.rmtree(BUNDLE_DIR)

os.makedirs(BUNDLE_DIR)

print("1. Creating Python embedded distribution...")
# Download Python embeddable package (you'll need to do this manually)
# For now, we'll use the current Python installation

# Copy Python runtime
python_dir = os.path.join(BUNDLE_DIR, "python")
os.makedirs(python_dir)

print("2. Copying application files...")
# Copy source files
for item in ["agents", "core", "*.py", "*.png", "*.json", "*.db", "*.vbs"]:
    if "*" in item:
        import glob
        for file in glob.glob(item):
            if os.path.isfile(file):
                shutil.copy(file, BUNDLE_DIR)
    elif os.path.exists(item):
        if os.path.isdir(item):
            shutil.copytree(item, os.path.join(BUNDLE_DIR, item))
        else:
            shutil.copy(item, BUNDLE_DIR)

print("3. Installing dependencies to bundle...")
# Install all dependencies to the bundle directory
subprocess.run([
    sys.executable, "-m", "pip", "install",
    "-r", "requirements.txt",
   "-t", os.path.join(BUNDLE_DIR, "lib"),
    "--no-warn-script-location"
])

print("4. Creating launcher script...")
launcher = """@echo off
SET PYTHONPATH=%~dp0lib;%PYTHONPATH%
python terminal_apple.py
pause
"""
with open(os.path.join(BUNDLE_DIR, "Start_AlphaQuant.bat"), "w") as f:
    f.write(launcher)

print(f"✅ Portable bundle created at: {BUNDLE_DIR}")
print(f"   Size: ~{sum(os.path.getsize(os.path.join(dp, f)) for dp, dn, filenames in os.walk(BUNDLE_DIR) for f in filenames) / (1024*1024*1024):.2f} GB")
