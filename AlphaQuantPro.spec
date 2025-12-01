import sys
sys.setrecursionlimit(10000)
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = '1'
os.environ['SDL_VIDEODRIVER'] = 'dummy'

from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_dynamic_libs
from PyInstaller.building.build_main import Analysis, PYZ, EXE, COLLECT

# Collect dependencies
datas = [('core', 'core'), ('web_ui', 'web_ui')]
binaries = []
hiddenimports = ['onnxruntime', 'pandas', 'numpy', 'xgboost', 'yfinance', 'scipy', 'sklearn', 'torch', 'gymnasium', 'darkdetect', 'customtkinter', 'tkinter', 'tkinter.font', 'tkinter.ttk', 'plistlib', 'uuid', 'ctypes', 'platform', 'subprocess', 'xml', 'xml.etree.ElementTree', 'xml.parsers.expat', 'colorsys', 'mmap', 'sqlite3', 'multiprocessing', 'uvicorn', 'fastapi', 'uvicorn.logging', 'uvicorn.loops', 'uvicorn.loops.auto', 'uvicorn.protocols', 'uvicorn.protocols.http', 'uvicorn.protocols.http.auto', 'uvicorn.lifespan', 'uvicorn.lifespan.on', 'email.mime.multipart', 'email.mime.text', 'email.mime.base']

# Manual customtkinter bundling
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\customtkinter', 'customtkinter'))

# Manual MetaTrader5 bundling
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\MetaTrader5', 'MetaTrader5'))

# Manual tkinter bundling
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\tkinter', 'tkinter'))

# Manual bundling of _tkinter binary and Tcl/Tk DLLs
binaries.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\DLLs\_tkinter.pyd', '.'))
binaries.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\DLLs\tcl86t.dll', '.'))
binaries.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\DLLs\tk86t.dll', '.'))

# Manual bundling of Tcl/Tk data directories (Required for initialization)

datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tcl8.6', 'tcl/tcl8.6'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\tcl\tk8.6', 'tcl/tk8.6'))

# Manual bundling of Pandas (Nuclear Option for dependencies)
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\pandas', 'pandas'))

# Manual bundling of Matplotlib and PIL (Nuclear Option v3)
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\matplotlib', 'matplotlib'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\PIL', 'PIL'))

# Manual bundling of ONNX Runtime and XGBoost (Nuclear Option v4)
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\onnxruntime', 'onnxruntime'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\xgboost', 'xgboost'))

# Manual bundling of Matplotlib dependencies (Nuclear Option v5 - Fix 'cycler' error)
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\cycler', 'cycler'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\kiwisolver', 'kiwisolver'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\pyparsing', 'pyparsing'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\contourpy', 'contourpy'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\fontTools', 'fontTools'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\packaging', 'packaging'))


# Manual bundling of ONNX Runtime dependencies (Nuclear Option v6 - Deep Audit)
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\google\protobuf', 'google/protobuf'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\flatbuffers', 'flatbuffers'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\coloredlogs', 'coloredlogs'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\sympy', 'sympy'))

# Manual bundling of FastAPI and Uvicorn (Nuclear Option v7 - Web Server)
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\uvicorn', 'uvicorn'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\fastapi', 'fastapi'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\starlette', 'starlette'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\pydantic', 'pydantic'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\anyio', 'anyio'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\sniffio', 'sniffio'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\h11', 'h11'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\click', 'click'))
datas.append((r'C:\Users\User\AppData\Local\Programs\Python\Python311\Lib\site-packages\typing_extensions.py', '.'))

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

# XGBoost binaries - Removed as we are manually bundling the whole package
# binaries += collect_dynamic_libs('xgboost')


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
    excludes=['customtkinter', 'setuptools', 'pkg_resources', 'distutils', 'xgboost', 'onnxruntime', 'core', 'MetaTrader5', 'matplotlib', 'PIL', 'pandas', 'tkinter'],
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
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='Alpha_Quant_Pro_logo.ico',
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
