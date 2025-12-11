# Alpha Quant Pro 2.0 (Trading Terminal)

![Version](https://img.shields.io/badge/version-2.1.1-blue.svg) ![Platform](https://img.shields.io/badge/platform-Windows_10%2F11-blue.svg) ![Tech](https://img.shields.io/badge/tech-Python_%7C_Next.js_%7C_MT5-green.svg)

**Alpha Quant Pro** 是一个专业级、自包含的量化交易终端，专为 MetaTrader 5 (MT5) 设计。它结合了现代化的桌面 UI、强大的 AI 代理架构和远程 Web 监控能力，为您提供全方位的自动交易解决方案。

---

## ✨ 核心特性 (Key Features)

### 🖥️ 桌面终端 (Desktop Terminal)
*   **iOS 风格现代化 UI**: 基于 CustomTkinter 的玻璃拟态设计，操作丝滑流畅。
*   **实时图表**: 内置高性能 K 线图表，支持缩放、拖拽和实时价格更新。
*   **Agent 管理**: 一键加载/切换不同的 AI 策略包 (Agent Bundles)，无需重启。
*   **风险风控**: 内置 "Risk Guard" 守护进程，强制执行止损和最大回撤限制。

### 🌐 Web 仪表盘 (Web Dashboard)
*   **远程监控**: 通过手机或浏览器随时随地查看账户状态 (`/dashboard`)。
*   **移动端适配**: 完美适配 iOS/Android 移动端操作。
*   **无需公网 IP**: 集成 **Ngrok** 隧道，一键开启远程访问，无需配置路由器。
*   **安全认证**: 强制 Token 验证 + SHA-256 密码哈希，保障账户安全。
*   **全功能控制**: 支持远程启动/停止引擎、修改参数、查看历史订单。

### 🤖 智能架构 (Smart Architecture)
*   **插件化策略**: 策略被打包为独立的 `Agent Bundle`，包含独立的 Python 环境和依赖，互不冲突。
*   **热更新**: 支持在运行时动态重新加载策略模型。
*   **Telegram 集成**: 实时推送交易信号、成交通知和账户日报。

---

## � 安装与启动 (Installation)

### 方式一：安装包 (推荐)
1. 下载最新发布的 `AlphaQuantPro_Setup.exe`。
2. 运行安装程序，按照提示完成安装。
3. 桌面会出现快捷方式，双击即可运行。

### 方式二：绿色版 (Portable)
1. 解压 `AlphaQuantPro_Portable.zip` (或 `dist_v2/AlphaQuantPro` 目录)。
2. 直接运行文件夹内的 `AlphaQuantPro.exe`。
3. **可移植性**: 整个文件夹可以移动到任何位置（如 U 盘），配置和数据随身携带。

---

## 📖 使用指南 (User Guide)

### 1. 初始配置
1.  **准备 MT5**: 确保本机已安装 MetaTrader 5 并登录账户。
2.  **启用 Algo**: 在 MT5 中点击 "Algo Trading" (允许算法交易)，并在选项中勾选 "Allow DLL imports"。
3.  **启动终端**: 运行 Alpha Quant Pro。

### 2. 加载策略
1.  在左侧 "Agent Selection" 下拉菜单中选择一个策略包（如 `agent_bundle_alpha_v2`）。
2.  设置交易品种 (Symbol，默认 `XAUUSD`)。
3.  点击 **"▶ START TRADING"** 按钮。

### 3. 配置远程访问 (可选)
1.  进入 **"Settings"** 页面。
2.  设置 **"Web Password"** (远程访问密码)。
3.  开启 **"Remote Dashboard"** 开关。
4.  (推荐) 开启 **"Ngrok Tunnel"** 并输入您的 Ngrok Auth Token。
5.  在 **"Logs"** 页面查看生成的公网访问链接。

### 4. Telegram 通知 (可选)
1.  在 Settings 页面填入您的 `Bot Token` 和 `Chat ID`。
2.  点击 "Test" 测试发送一条消息。
3.  保存配置，即可接收实时交易推送。

---

## � 目录结构

```
AlphaQuantPro/
├── AlphaQuantPro.exe      # 主程序
├── Guardian.exe           # 守护进程 (防崩溃/风控)
├── web_ui/                # Web Dashboard 前端资源
├── agents/                # 策略包存放目录 (放入新的 bundle 即可识别)
│   ├── agent_bundle_v1/
│   └── ...
├── workspace/             # 数据存储 (数据库、日志、配置)
│   ├── terminal_config.json
│   ├── AlphaQuant.log
│   └── ...
└── _internal/             # Python 运行时环境 (依赖库)
```

---

## 🔐 安全说明

*   **本地运行**: 所有交易逻辑仅在您本地电脑运行，私钥和 API Key 不会上载云端。
*   **Web 安全**: 远程访问仅通过加密隧道传输，且所有敏感操作均需密码验证。
*   **开源透明**: 核心架构代码在 GitHub 可见，无后门。

---

## ⚠️ 免责声明 (Disclaimer)

本软件仅供教育和研究使用。
*   **高风险**: 外汇和差价合约交易存在高风险，可能导致资金损失。
*   **无建议**: 本软件不构成任何投资建议。
*   **责任**: 用户需自行承担使用本软件产生的所有风险和结果。

---

Copyright © 2025 Alpha Quant Pro. All Rights Reserved.
