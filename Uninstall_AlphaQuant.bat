@echo off
echo ========================================
echo  Alpha Quant Pro - 卸载程序
echo ========================================
echo.

set INSTALL_DIR=%ProgramFiles%\AlphaQuantPro
set APPDATA_DIR=%APPDATA%\AlphaQuantPro

echo 正在删除程序文件...
if exist "%INSTALL_DIR%" (
    rmdir /S /Q "%INSTALL_DIR%"
    echo 已删除: %INSTALL_DIR%
)

echo 正在删除用户数据...
if exist "%APPDATA_DIR%\logs" (
    rmdir /S /Q "%APPDATA_DIR%\logs"
)

echo 正在删除桌面快捷方式...
if exist "%USERPROFILE%\Desktop\Alpha Quant Pro.lnk" (
    del "%USERPROFILE%\Desktop\Alpha Quant Pro.lnk"
)

echo.
echo ========================================
echo  卸载完成！
echo ========================================
pause
