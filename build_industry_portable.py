# Build Script - Industry Grade (Refined Portable)
# Uses embedded Python runtime + compiled .pyc files + Industry Structure

import os
import shutil
import sys
import compileall
from pathlib import Path

print("=" * 70)
print(" Alpha Quant Pro - Build (Industry Grade - Portable)")
print(" Method: Embedded Runtime + Compiled Source + Structured Layout")
print("=" * 70)
print()

BUILD_DIR = Path("build_industry")
RUNTIME_DIR = BUILD_DIR / "runtime"
SERVICE_DIR = BUILD_DIR / "service"
UI_DIR = BUILD_DIR / "ui"

# Step 1: Clean
if BUILD_DIR.exists():
    print("Cleaning build directory...")
    shutil.rmtree(BUILD_DIR)
BUILD_DIR.mkdir()

print("✅ Clean complete\n")

# Step 2: Create Directory Structure
print("Step 1/4: Creating Directory Structure...")
RUNTIME_DIR.mkdir()
SERVICE_DIR.mkdir()
(UI_DIR / "assets").mkdir(parents=True)
(BUILD_DIR / "updater").mkdir()

# Step 3: Copy Python Runtime & Dependencies
print("Step 2/4: Copying Runtime & Dependencies...")
# We use the current environment's site-packages
# In a real scenario, we would download python-embed.zip
# Here we copy the portable bundle libs we created earlier if they exist, 
# or copy from current env (risky due to size/hardlinks).
# Let's use the 'AlphaQuantPro_Portable' created earlier if available, as it has deps installed.

PORTABLE_SRC = Path("AlphaQuantPro_Portable")
if not PORTABLE_SRC.exists():
    print("❌ AlphaQuantPro_Portable not found. Please run create_portable.py first.")
    # Fallback: Run create_portable.py logic here? 
    # It's better to assume the user has the portable bundle or we recreate it.
    # Let's recreate the portable bundle logic quickly here.
    print("   Re-creating base portable bundle...")
    subprocess.run([sys.executable, "create_portable.py"], check=True)

# Copy Libs from Portable
print("   Copying libraries...")
shutil.copytree(PORTABLE_SRC / "lib", RUNTIME_DIR / "lib")
# Copy Python DLLs/Executables (simulated by copying from system or portable)
# For this environment, we might just rely on the user having python installed?
# No, "Portable" means we need the python dlls.
# The 'create_portable.py' script created a 'python' dir but didn't fully populate it with embeddable python.
# It just copied source files and installed deps to 'lib'.
# To make it truly portable/industry, we need the python executable and dll.
# Let's copy the current python executable and dlls.
current_python = Path(sys.executable)
shutil.copy(current_python, BUILD_DIR / "AlphaQuantPro_Runner.exe") # Rename python to App
# Copy python3.dll, python311.dll etc.
for file in current_python.parent.glob("python*.dll"):
    shutil.copy(file, BUILD_DIR)

print("✅ Runtime setup complete")

# Step 4: Copy & Compile Source Code
print("Step 3/4: Copying & Compiling Source Code...")

# Copy Source to Service
for file in Path(".").glob("*.py"):
    if "build" not in file.name and "create_" not in file.name:
        shutil.copy(file, SERVICE_DIR)

# Copy Directories
if Path("agents").exists():
    shutil.copytree("agents", SERVICE_DIR / "agents")
if Path("core").exists():
    shutil.copytree("core", SERVICE_DIR / "core")

# Copy Assets
if Path("Alpha_Quant_Pro_logo.png").exists():
    shutil.copy("Alpha_Quant_Pro_logo.png", UI_DIR / "assets" / "logo.png")

# Compile to .pyc
print("   Compiling to .pyc...")
compileall.compile_dir(SERVICE_DIR, force=True, quiet=1)

# Remove .py files (Obfuscation)
print("   Removing .py source files...")
for py_file in SERVICE_DIR.rglob("*.py"):
    py_file.unlink()

print("✅ Source compiled and secured")

# Step 5: Create Launcher
print("Step 4/4: Creating Launcher...")
# We need a launcher that sets PYTHONPATH to runtime/lib and runs service/terminal_apple.pyc
# We can use a VBS launcher or a simple batch for now.
# Industry standard would be a C++ exe.
# Let's stick to the VBS launcher but adapted for this structure.

launcher_vbs = """
Set WshShell = CreateObject("WScript.Shell")
' Set Environment Variables
Set WshEnv = WshShell.Environment("PROCESS")
WshEnv("PYTHONPATH") = "runtime/lib;service"
' Run the compiled main script using the embedded python
WshShell.Run "AlphaQuantPro_Runner.exe service/terminal_apple.pyc", 0, False
Set WshShell = Nothing
"""
with open(BUILD_DIR / "AlphaQuantPro.vbs", "w") as f:
    f.write(launcher_vbs)

print("✅ Build Complete!")
print(f"   Output: {BUILD_DIR.absolute()}")
size = sum(f.stat().st_size for f in BUILD_DIR.rglob('*') if f.is_file())
print(f"   Total Size: {size / (1024*1024):.2f} MB")
print("=" * 70)
