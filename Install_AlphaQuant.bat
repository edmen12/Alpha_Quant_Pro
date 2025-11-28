@echo off
echo ========================================
echo  Alpha Quant Pro - 安装程序
echo ========================================
echo.

set INSTALL_DIR=%ProgramFiles%\AlphaQuantPro
set APPDATA_DIR=%APPDATA%\AlphaQuantPro

echo 正在安装到: %INSTALL_DIR%
echo.

REM 创建安装目录
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
if not exist "%APPDATA_DIR%" mkdir "%APPDATA_DIR%"

echo 正在复制文件...
xcopy /E /I /Y "AlphaQuantPro_Portable" "%INSTALL_DIR%"

echo.
echo 正在创建桌面快捷方式...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\Desktop\Alpha Quant Pro.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\Start_AlphaQuant.bat'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

echo.
echo ========================================
echo  安装完成！
echo ========================================
echo.
echo 程序已安装到: %INSTALL_DIR%
echo 桌面快捷方式已创建
echo.
pause
