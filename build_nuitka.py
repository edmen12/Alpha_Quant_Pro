# Nuitka Build Script for Alpha Quant Pro
# Compiles terminal_apple.py into a standalone .exe

import subprocess
import sys
import os

print("=" * 60)
print(" Alpha Quant Pro - Nuitka Compilation")
print("=" * 60)
print()
print("⚠️  WARNING:")
print("   - Compilation time: 30-60 minutes")
print("   - CPU usage: 100% (multi-core)")
print("   - Final EXE size: ~2-3 GB")
print()
print("Starting compilation...")
print()

# Nuitka command
cmd = [
    sys.executable, "-m", "nuitka",
    
    # Basic options
    "--standalone",
    "--onefile",
   "--windows-disable-console",
    
    # Output
    "--output-dir=build_nuitka",
    "--output-filename=AlphaQuantPro.exe",
    
    # Icon
    # "--windows-icon-from-ico=Alpha_Quant_Pro_logo.ico",
    
    # Include data files
    "--include-data-dir=agents=agents",
    "--include-data-dir=core=core",
    "--include-data-file=Alpha_Quant_Pro_logo.png=Alpha_Quant_Pro_logo.png",
    
    # Plugins
    "--enable-plugin=tk-inter",
    
    # Follow imports
    "--follow-imports",
    
    # Optimization
    "--lto=yes",
    
    # Entry point
    "terminal_apple.py"
]

print("Command:")
print(" ".join(cmd))
print()

# Run compilation
try:
    result = subprocess.run(cmd, check=True)
    print()
    print("=" * 60)
    print("✅ Compilation successful!")
    print(f"   Output: build_nuitka\\AlphaQuantPro.exe")
    print("=" * 60)
except subprocess.CalledProcessError as e:
    print()
    print("=" * 60)
    print(f"❌ Compilation failed: {e}")
    print("=" * 60)
    sys.exit(1)
