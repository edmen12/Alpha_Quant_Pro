@echo off
echo ========================================================
echo   AlphaQuantPro Release Build Script
echo ========================================================
echo.

echo [1/5] Cleaning previous build artifacts...
rmdir /s /q build dist
REM del *.spec

echo.
echo [2/5] Using Existing Spec File...
REM python write_spec.py
if %errorlevel% neq 0 goto :error

echo.
echo [3/5] Running PyInstaller (This may take a while)...
python -m PyInstaller AlphaQuantPro.spec --clean --noconfirm
if %errorlevel% neq 0 goto :error

echo.
echo [4/5] Patching Tkinter Dependencies...
REM python copy_tkinter_deps.py
REM if %errorlevel% neq 0 goto :error

echo.
echo [5/5] Compiling Installer with Inno Setup...
"C:\Program Files (x86)\Inno Setup 6\ISCC.exe" AlphaQuantPro_PyInstaller.iss
if %errorlevel% neq 0 goto :error

echo.
echo ========================================================
echo   BUILD SUCCESSFUL!
echo   Installer: Installer\AlphaQuantPro_Setup.exe
echo ========================================================
pause
exit /b 0

:error
echo.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
echo   BUILD FAILED! Check messages above.
echo !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
pause
exit /b 1
