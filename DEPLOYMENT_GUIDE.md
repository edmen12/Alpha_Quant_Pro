# Windows VPS 部署指南

本指南将指导您如何在 Windows VPS 上部署 Alpha Quant Trading Terminal，实现 24/7 全天候自动交易和远程监控。

## 1. 为什么选择 Windows VPS?

由于 MetaTrader 5 的 Python API (`MetaTrader5` 库) **仅支持 Windows 操作系统**，因此必须使用 Windows Server。
- **Linux (Wine)**: 极不稳定，官方不支持 Python API，**强烈不推荐**。
- **Windows Server**: 原生支持，稳定可靠。

## 2. 推荐配置

- **CPU**: 2 vCPU (最低 1 vCPU，但建议 2 以保证 GUI 流畅)
- **RAM**: 4GB (最低 2GB)
- **OS**: Windows Server 2019 或 2022 (Datacenter Edition)
- **供应商**: AWS (EC2 Windows), 阿里云 (ECS Windows), Vultr, Contabo 等。

## 3. 部署步骤

### 第一步：连接 VPS
1.  使用 Windows 自带的 **远程桌面连接 (Remote Desktop Connection)**。
2.  输入 VPS 的公网 IP 地址。
3.  输入用户名 (通常是 `Administrator`) 和密码。

### 第二步：环境准备
在 VPS 上安装以下软件：
1.  **MetaTrader 5**: 下载并安装您的经纪商提供的 MT5 终端。
    -   登录您的交易账户。
    -   **重要**: 在 `工具` -> `选项` -> `专家顾问` 中，勾选 **"允许算法交易"**。
2.  **Python 3.10+**: 从 [Python 官网](https://www.python.org/downloads/windows/) 下载。
    -   **重要**: 安装时务必勾选 **"Add Python to PATH"**。
3.  **Git (可选)**: 用于拉取代码。

### 第三步：安装终端
1.  将 `trading_terminal` 文件夹复制到 VPS (可以直接从本地电脑复制粘贴到远程桌面)。
2.  打开 PowerShell 或 CMD，进入文件夹：
    ```powershell
    cd C:\Users\Administrator\Desktop\trading_terminal
    ```
3.  安装依赖：
    ```powershell
    pip install -r requirements.txt
    pip install fastapi uvicorn # 安装 Web 监控组件
    ```

### 第四步：运行与监控
1.  双击运行 `AlphaQuantPro.exe` (或 `python terminal_apple.py`)。
2.  **设置安全密码 (重要)**:
    -   进入 "Settings" 页面。
    -   在 "REMOTE ACCESS SECURITY" 下的 "Web Dashboard Password" 输入框中设置您的访问密码。
    -   点击 "START TRADING" 保存并启动。
3.  **远程监控**:
    -   在 VPS 浏览器中访问 `http://localhost:8000` 确认面板正常。
    -   **手机访问**:
        -   需要在 VPS 防火墙 (和云服务商的安全组) 中放行 **TCP 8000** 端口。
        -   在手机浏览器输入: `http://<VPS_公网_IP>:8000`。
        -   **输入密码**: 首次访问需要输入您在第 2 步设置的密码。

## 4. 24/7 自动运行配置 (防掉线)

为了防止远程桌面断开后程序停止，或服务器重启后未自动运行：

### 设置自动登录 (Auto Logon)
1.  下载微软官方工具 [Autologon](https://learn.microsoft.com/en-us/sysinternals/downloads/autologon)。
2.  运行并输入密码，启用自动登录。

### 设置启动项
1.  创建一个快捷方式指向 `AlphaQuantPro.exe`。
2.  按 `Win + R`，输入 `shell:startup`。
3.  将快捷方式复制到该文件夹中。

这样，即使服务器重启，它也会自动登录并启动交易终端。

## 5. 常见问题

**Q: 关闭远程桌面后 MT5 停止运行？**
A: 不要点击 "注销" (Sign out)，直接点击远程桌面顶部的 "X" 关闭窗口。程序会继续在后台运行。

**Q: 手机无法访问 Web 面板？**
A: 请检查：
1.  VPS 的 Windows 防火墙是否允许了 Python/端口 8000。
2.  云服务商 (AWS/阿里云) 的安全组 (Security Group) 是否参加入站规则允许 TCP 8000。
