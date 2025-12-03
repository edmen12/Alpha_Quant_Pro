
content = r"""import sys
sys.setrecursionlimit(10000)
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_dynamic_libs
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# Collect dependencies
datas = [('agents', 'agents'), ('core', 'core'), ('web_ui', 'web_ui'), ('models', 'models'), ('configs', 'configs'), ('RISK_DISCLAIMER.txt', '.'), ('User_Manual.md', '.'), ('EULA.txt', '.'), ('terminal_icon.ico', '.')]
binaries = []
hiddenimports = ['uvicorn', 'fastapi', 'starlette', 'h11', 'click', 'onnxruntime', 'pandas', 'numpy', 'xgboost', 'yfinance', 'scipy', 'sklearn', 'torch', 'gymnasium', 'darkdetect', 'customtkinter', 'tkinter', 'tkinter.font', 'tkinter.ttk', 'plistlib', 'uuid', 'ctypes', 'platform', 'subprocess', 'xml', 'xml.etree.ElementTree', 'xml.parsers.expat', 'colorsys', 'mmap', 'sqlite3', 'multiprocessing', 'cloudscraper', 'bs4', 'cycler', 'kiwisolver', 'pyparsing', 'contourpy', 'fontTools', 'packaging', '_tkinter', 'pyngrok', 'requests', 'pydantic']

# Dynamic path resolution
import site
import os

# Get site-packages directories
site_packages = site.getsitepackages()
# Usually the first one is the main one, but we check
base_site = site_packages[1] if len(site_packages) > 1 else site_packages[0]
base_python = os.path.dirname(sys.executable) # Reliable way to find Python root

print(f"Detected Python Root: {base_python}")
print(f"Detected Site-Packages: {base_site}")

# Helper to find path
def get_path(relative_path, is_site_package=True):
    if is_site_package:
        return os.path.join(base_site, relative_path)
    else:
        return os.path.join(base_python, relative_path)

# Manual customtkinter bundling
datas.append((get_path('customtkinter'), 'customtkinter'))

# Manual MetaTrader5 bundling
datas.append((get_path('MetaTrader5'), 'MetaTrader5'))

# Manual tkinter bundling
# datas.append((get_path('tkinter', False), 'tkinter')) # tkinter is in Lib, not site-packages usually, but let's check
# Actually tkinter is usually in Lib/tkinter, which is not in site-packages.
# Let's be more robust.
lib_path = os.path.join(base_python, 'Lib')
datas.append((os.path.join(lib_path, 'tkinter'), 'tkinter'))

# Manual bundling of _tkinter binary and Tcl/Tk DLLs
dlls_path = os.path.join(base_python, 'DLLs')
binaries.append((os.path.join(dlls_path, '_tkinter.pyd'), '.'))
binaries.append((os.path.join(dlls_path, 'tcl86t.dll'), '.'))
binaries.append((os.path.join(dlls_path, 'tk86t.dll'), '.'))

# Manual bundling of Tcl/Tk data directories
tcl_path = os.path.join(base_python, 'tcl')
datas.append((os.path.join(tcl_path, 'tcl8.6'), 'tcl/tcl8.6'))
datas.append((os.path.join(tcl_path, 'tk8.6'), 'tcl/tk8.6'))

# Manual bundling of Pandas
datas.append((get_path('pandas'), 'pandas'))

# Manual bundling of Matplotlib and PIL
datas.append((get_path('matplotlib'), 'matplotlib'))
datas.append((get_path('PIL'), 'PIL'))

# Manual bundling of ONNX Runtime and XGBoost - REMOVED (Using collect_all)
# datas.append((get_path('onnxruntime'), 'onnxruntime'))
datas.append((get_path('xgboost'), 'xgboost'))

# Helper to safely add module (file or package)
def safe_add_module(name):
    # Try as file
    file_path = get_path(f"{name}.py")
    if os.path.exists(file_path):
        datas.append((file_path, '.'))
        print(f"Bundled module file: {name}.py")
        return

    # Try as package
    dir_path = get_path(name)
    if os.path.exists(dir_path):
        datas.append((dir_path, name))
        print(f"Bundled module package: {name}")
        return
        
    print(f"WARNING: Could not find module {name}")

# Manual bundling of Matplotlib dependencies
# Moved to hiddenimports to avoid path issues
# safe_add_module('cycler')
# safe_add_module('kiwisolver')
# safe_add_module('pyparsing')
# safe_add_module('contourpy')
# safe_add_module('fontTools')
# safe_add_module('packaging')

# Manual bundling of ONNX Runtime dependencies
datas.append((get_path('google/protobuf'), 'google/protobuf'))
datas.append((get_path('flatbuffers'), 'flatbuffers'))
datas.append((get_path('coloredlogs'), 'coloredlogs'))
datas.append((get_path('sympy'), 'sympy'))

# Collect others
tmp_ret = collect_all('stable_baselines3')


datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('shimmy')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
# Removed collect_all('matplotlib') and 'PIL' as we are manually bundling them above

# Removed collect_all('pandas') as we are manually bundling it above
tmp_ret = collect_all('dateutil')

datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]
tmp_ret = collect_all('pytz')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('uvicorn')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('fastapi')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('starlette')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Deep Audit: Force collection of missing dependencies
tmp_ret = collect_all('pyngrok')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('requests')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

tmp_ret = collect_all('pydantic')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# Robust AI Bundling (Fixes Access Violation)
tmp_ret = collect_all('onnxruntime')
datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# tmp_ret = collect_all('xgboost')
# datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# torch and sklearn via hiddenimports (collect_all was too heavy/unstable)
# tmp_ret = collect_all('torch')
# datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]

# tmp_ret = collect_all('sklearn')
# datas += tmp_ret[0]; binaries += tmp_ret[1]; hiddenimports += tmp_ret[2]


block_cipher = None

a = Analysis(
    ['terminal_apple.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['customtkinter', 'setuptools', 'distutils', 'xgboost', 'core', 'MetaTrader5', 'matplotlib', 'PIL', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='AlphaQuantPro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='terminal_icon.ico',
)
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='AlphaQuantPro',
)
"""

with open("AlphaQuantPro.spec", "w", encoding="utf-8") as f:
    f.write(content)
print("Spec file written successfully.")
