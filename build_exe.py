
import PyInstaller.__main__
import os
import shutil

# Define paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(BASE_DIR, "dist")
BUILD_DIR = os.path.join(BASE_DIR, "build")

# Clean previous builds
if os.path.exists(DIST_DIR):
    shutil.rmtree(DIST_DIR)
if os.path.exists(BUILD_DIR):
    shutil.rmtree(BUILD_DIR)

print("🚀 Starting Build Process (onedir mode)...")

PyInstaller.__main__.run([
    'terminal_apple.py',
    '--name=AlphaQuantPro',
    '--onedir',
    '--windowed',
    '--add-data=agents;agents',
    '--add-data=core;core',
    '--add-data=Alpha_Quant_Pro_logo.png;.',
    '--hidden-import=customtkinter',
    '--hidden-import=pandas',
    '--hidden-import=matplotlib',
    '--hidden-import=MetaTrader5',
    '--hidden-import=PIL',
    '--hidden-import=PIL._tkinter_finder',
    '--noconfirm'
])

print("✅ Build Complete! Check the 'dist/AlphaQuantPro' folder.")
