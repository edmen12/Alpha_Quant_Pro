# Build Script - Industry Grade (PyInstaller + Manual Restructure)
# Since Nuitka failed, we use PyInstaller onedir (proven to work) + restructure

import subprocess
import sys
import shutil
from pathlib import Path

print("=" * 70)
print(" Alpha Quant Pro - Build (Industry Grade)")
print(" Method: PyInstaller onedir + Manual Restructuring")
print("=" * 70)
print()

# Step 1: Clean previous builds
if Path("build").exists():
    print("Cleaning build...")
    shutil.rmtree("build")
if Path("dist").exists():
    print("Cleaning dist...")
    shutil.rmtree("dist")

print("✅ Clean complete\n")

# Step 2: PyInstaller build (ONEDIR)
print("Step 1/3: Running PyInstaller...")
print("─" * 70)

cmd = [
    sys.executable, "-m", "PyInstaller",
    "--onedir",           # Industry standard
    "--windowed",         # No console
    "--name=AlphaQuantPro",
   
    # Data
    "--add-data=agents;agents",
    "--add-data=core;core",
    "--add-data=Alpha_Quant_Pro_logo.png;.",
    
    # Hidden imports
    "--hidden-import=packaging.version",
    "--hidden-import=packaging.specifiers",
    
    # Entry
    "terminal_apple.py"
]

try:
    subprocess.run(cmd, check=True)
    print("\n✅ PyInstaller build complete\n")
except subprocess.CalledProcessError:
    print("\n❌ PyInstaller failed\n")
    sys.exit(1)

# Step 2: Restructure to industry standards
print("Step 2/3: Restructuring to industry standards...")
print("─" * 70)

BUILD_DIR = Path("build_industry")
if BUILD_DIR.exists():
    shutil.rmtree(BUILD_DIR)

# Create directory structure
(BUILD_DIR / "runtime").mkdir(parents=True)
(BUILD_DIR / "service").mkdir(parents=True)
(BUILD_DIR / "ui" / "assets").mkdir(parents=True)
(BUILD_DIR / "updater").mkdir(parents=True)

# Move PyInstaller output
dist_dir = Path("dist/AlphaQuantPro")
if dist_dir.exists():
    # Main exe to root
    shutil.copy(dist_dir / "AlphaQuantPro.exe", BUILD_DIR / "AlphaQuantPro.exe")
    
    # Runtime dependencies
    for item in dist_dir.iterdir():
        if item.name == "AlphaQuantPro.exe":
            continue
        if item.is_dir():
            shutil.copytree(item, BUILD_DIR / "runtime" / item.name)
        else:
            shutil.copy(item, BUILD_DIR / "runtime" / item.name)
    
    print("✅ Restructure complete\n")
else:
    print("❌ Dist directory not found\n")
    sys.exit(1)

# Step 3: Summary
print("Step 3/3: Build Summary")
print("─" * 70)
print()
print(f"✅ Build complete! Output:")
print(f"   {BUILD_DIR.absolute()}/")
print()
print("Structure:")
print("  AlphaQuantPro.exe       ← Main executable")
print("  runtime/                ← Python + dependencies")
print("  service/                ← (Future: compiled modules)")
print("  ui/assets/              ← UI resources")
print("  updater/                ← (Future: updater.exe)")
print()

# Size
size = sum(f.stat().st_size for f in BUILD_DIR.rglob('*') if f.is_file())
print(f"Total size: {size / (1024*1024):.2f} MB")
print("=" * 70)
