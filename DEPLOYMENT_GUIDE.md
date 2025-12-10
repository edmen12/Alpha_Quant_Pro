# 🚀 Alpha Quant Pro V2.0.0 部署与安全指南

## 1. 开发者工作站 (您) 🧑‍💻
在发布软件之前，您必须**编译**并**打包**应用程序，以确保许可逻辑的安全。

### 步骤 A：构建二进制核心 (Cython)
即使将 `core/license_manager.py` 编译为 `.pyd` 二进制文件，从而隐藏 `SECRET_KEY` (密钥)。
```powershell
python build_core.py build_ext --inplace
```
*结果: 生成 `core/license_manager.cp3XX-win_amd64.pyd`。*

### 步骤 B：打包应用程序 (PyInstaller)
将所有内容打包成一个独立的可执行文件。
> **注意**: PyInstaller V6+ 已移除 `--key` 加密功能。我们依赖 **Cython** (步骤 A) 作为核心安全保护。
```powershell
pyinstaller --clean AlphaQuantPro.spec
```
*结果: 生成 `dist/AlphaQuantPro/AlphaQuantPro.exe`。*

### 步骤 C：创建安装程序 (Inno Setup)
将发布文件封装成专业的安装包。
```powershell
& "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" AlphaQuantPro_PyInstaller.iss
```
*结果: `Installer/AlphaQuantPro_Setup.exe` (将此文件发送给用户)。*

---

## 2. 销售与激活流程 🤝

### 第一阶段：自动分发 (Auto-Distribution)
1.  将 `AlphaQuantPro_Setup.exe` 发送给客户。
2.  客户安装并运行软件。
3.  **自动上报**: 软件启动时会自动将 **机器码 (HWID)** 发送到您的 Telegram Bot。
4.  您会在 Telegram 收到类似消息：
    > 🔥 *NEW ACTIVATION REQUEST*
    > 💻 *HWID*: `26E9F03CAF...`
    > Generate Key: `/keygen ...`
5.  客户端界面显示 "Request Sent! Admin Notified"。

### 第二阶段：生成密钥 (管理员 Admin)
1.  在您的机器上，打开项目文件夹的终端。
2.  使用客户的机器码运行注册机：
    ```powershell
    python keygen.py 26E9F03CAF0F2D3F
    ```
3.  **获取密钥**: 脚本输出一个唯一的激活码 (例如：`409B-0F4B-AE29-281C`)。
4.  将此激活码发回给客户。

### 第三阶段：激活 (用户 User)
1.  客户在弹窗中输入激活码。
2.  应用程序验证 `HMAC(HWID, SECRET) == Key`。
3.  **成功**: 应用程序启动，许可信息保存到 `license.key`。
4.  **安全机制**: 如果他们将软件复制给朋友的电脑，机器码会改变，原激活码将失效。🚫

---

## 安全架构 🛡️
*   **第一层 (离线锁)**: 机器码 (HWID) + HMAC-SHA256 签名。
*   **第二层 (逻辑隐藏)**: `license_manager.py` 被编译为 C 代码 (`.pyd`)。`SECRET_KEY` 不会以明文形式显示。
*   **第三层 (依赖打包)**: PyInstaller 将所有依赖打包在一起，增加逆向工程的复杂性。
