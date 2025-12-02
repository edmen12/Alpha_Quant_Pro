# 🚀 Alpha Quant Pro Deployment Guide

## Dual-Track Release Strategy
We maintain two types of installers to balance "Out-of-the-Box" experience for new users and "Fast Updates" for existing users.

### 1. Full Installer (The "House")
*   **Filename**: `AlphaQuantPro_Setup.exe` (~600MB)
*   **Contents**: Full Python Runtime, Dependencies (Torch, Pandas, etc.), Application Code.
*   **Target Audience**: New users, or major version upgrades (e.g., Python version bump, new dependencies).
*   **Build Command**:
    ```powershell
    # 1. Build Dist
    pyinstaller AlphaQuantPro.spec
    # 2. Pack Installer
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" AlphaQuantPro_PyInstaller.iss
    ```

### 2. Patch Installer (The "Furniture")
*   **Filename**: `AlphaQuantPro_Patch_Setup.exe` (~5-10MB)
*   **Contents**: Only `AlphaQuantPro.exe` (and optionally `agents/`).
*   **Target Audience**: Existing users needing Bug Fixes, UI Tweaks, or Strategy Updates.
*   **Build Command**:
    ```powershell
    # 1. Build Dist (If code changed)
    pyinstaller AlphaQuantPro.spec
    # 2. Pack Patch
    & "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" AlphaQuantPro_Patch.iss
    ```

## Release Workflow

### Scenario A: Bug Fix / Logic Update
1.  Modify code (e.g., `engine_core.py`).
2.  Run `pyinstaller AlphaQuantPro.spec`.
3.  Run `ISCC AlphaQuantPro_Patch.iss`.
4.  Distribute `AlphaQuantPro_Patch_Setup.exe`.

### Scenario B: New Dependency / Major Upgrade
1.  `pip install new-lib`.
2.  Update `AlphaQuantPro.spec` (hidden imports).
3.  Run `pyinstaller AlphaQuantPro.spec`.
4.  Run `ISCC AlphaQuantPro_PyInstaller.iss`.
5.  Distribute `AlphaQuantPro_Setup.exe`.

## User Communication Template
> **🚀 Alpha Quant Pro v1.3.x Released**
>
> *   **New Users**: Download `AlphaQuantPro_Setup.exe` (Full Installer).
> *   **Existing Users**: Download `AlphaQuantPro_Patch_Setup.exe` (Fast Update).
