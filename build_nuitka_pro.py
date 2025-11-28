# Nuitka Build Script - Industry Grade (onedir mode)
# Compiles terminal_apple.py into AlphaQuantPro.exe with full dependency tree

import subprocess
import sys
import os
import shutil
from pathlib import Path

print("=" * 70)
print(" Alpha Quant Pro - Nuitka Compilation (Industry Grade)")
print("=" * 70)
print()
print("Mode: ONEDIR (not onefile)")
print("Expected time: 60-90 minutes")
print("Expected output: build/AlphaQuantPro.dist/")
print()
print("=" * 70)
print()

# Clean previous builds
if os.path.exists("build"):
    print("Cleaning previous build...")
    shutil.rmtree("build")
    print("✅ Clean complete")
    print()

# Nuitka command for ONEDIR mode
cmd = [
    sys.executable, "-m", "nuitka",
    
    # === CORE OPTIONS ===
    "--standalone",           # Include all dependencies
    "--onedir",              # NOT onefile (industry standard)
    "--windows-disable-console",  # No CMD window
    
    # === OUTPUT ===
    "--output-dir=build",
    "--output-filename=AlphaQuantPro.exe",
    
    # === ICON ===
    # "--windows-icon-from-ico=Alpha_Quant_Pro_logo.ico",  # Skipped for now
    
    # === DATA FILES ===
    "--include-data-dir=agents=agents",
    "--include-data-dir=core=core",
    "--include-data-file=Alpha_Quant_Pro_logo.png=ui/assets/logo.png",
    
    # === PLUGINS ===
    "--enable-plugin=tk-inter",
    
    # === IMPORTS ===
    "--follow-imports",
    "--nofollow-import-to=*.tests",
    
    # === OPTIMIZATION ===
    "--lto=yes",              # Link-time optimization
    
    # === ENTRY POINT ===
    "terminal_apple.py"
]

print("Command:")
print(" ".join(cmd[:10]))
print("  ... (truncated)")
print()
print("Starting compilation...")
print("─" * 70)
print()

# Run compilation
try:
    result = subprocess.run(cmd, check=True)
    print()
    print("=" * 70)
    print("✅ Compilation successful!")
    print()
    print("Output location:")
    print(f"   build/AlphaQuantPro.dist/")
    print(f"   build/AlphaQuantPro.dist/AlphaQuantPro.exe")
    print()
    
    # Check output size
    dist_dir = Path("build/AlphaQuantPro.dist")
    if dist_dir.exists():
        size = sum(f.stat().st_size for f in dist_dir.rglob('*') if f.is_file())
        print(f"Total size: {size / (1024*1024*1024):.2f} GB")
    
    print("=" * 70)
    
except subprocess.CalledProcessError as e:
    print()
    print("=" * 70)
    print(f"❌ Compilation failed!")
    print()
    print("Common issues:")
    print("  1. Missing C++ compiler (install Visual Studio Build Tools)")
    print("  2. PyTorch module resolution issues")
    print("  3. Out of memory")
    print()
    print("Check error above for details.")
    print("=" * 70)
    sys.exit(1)
