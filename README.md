# Alpha Quant Trading Terminal

**完全自包含的专业级自动交易终端** - 支持 MetaTrader 5 实盘/模拟交易。

**✨ 特色：整个文件夹可以随意移动到任何位置，无需修改配置！**

## 🚀 快速启动

### 方式一：直接运行源码 (推荐开发者)
```bash
cd trading_terminal
python terminal_apple.py
```

### 方式二：运行安装包 (推荐用户)
下载并安装 `AlphaQuantPro_Setup.exe`，直接运行桌面快捷方式。

## 📁 文件结构

```
trading_terminal/           # 📦 完全独立的交易终端
├── agents/                 # 🤖 Agent Bundle 存储目录
│   ├── agent_bundle_xxx/   # 👈 您的策略包放在这里
│   ├── ...
│
├── core/                   # 🏗️ 核心架构模块
│   ├── web_server.py      # 🌐 Web 监控后端
│   └── ...
│
├── engine_core.py         # ⚙️ 交易引擎核心
├── terminal_apple.py      # 🍎 主程序（iOS 风格 GUI）
├── terminal_lite.py       # 🚀 Lite 版（VPS 专用 - 开发中）
└── README.md              # 📖 本文件
```

## ✨ 主要功能

### 1. 🍎 iOS 风格界面
- 采用 CustomTkinter 构建的现代化 UI
- 玻璃拟态 (Glassmorphism) 设计
- 丝滑的动画效果

### 2. 🌐 远程 Web 监控 (v1.4.0 新增)
- **手机随时查看**: 在手机浏览器访问 `http://<VPS_IP>:8000`
- **远程控制**: 远程启动/停止交易引擎
- **全功能配置**: 远程修改所有参数 (品种、风控、Telegram 等)
- **安全**: 强制密码验证 + Token 认证

### 3. 📊 实时 K 线图表
- 专业蜡烛图显示
- 自动更新（3秒间隔）

### 4. 💰 账户监控
- 实时余额/净值
- 浮动盈亏（颜色编码）

### 5. 📱 Telegram 通知
- 新信号推送
- 交易执行提醒

### 4. 🤖 Agent Bundle 系统
- 动态加载各种策略
- 自动管理依赖
- 向后兼容旧格式
- **[📚 查看详细开发指南 (AGENT_BUNDLE_GUIDE.md)](AGENT_BUNDLE_GUIDE.md)**

### 5. 📋 交易历史
- 完整交易记录
- 时间/价格/盈亏

## 🔧 配置步骤

### 1. 准备 MT5
1. 安装 MetaTrader 5
2. 登录账户
3. 启用算法交易：
   - 工具 → 选项 → 专家顾问
   - ✅ 允许算法交易

### 2. 配置 Telegram（可选）
1. 创建 Bot：
   - 搜索 @BotFather
   - 发送 `/newbot`
   - 获取 Bot Token

2. 获取 Chat ID：
   - 向 Bot 发消息
   - 搜索 @userinfobot
   - 获取 Chat ID

3. 在终端中配置：
   - 切换到"⚙️ Advanced"标签
   - 填写 Token 和 Chat ID
   - 点击"测试连接"

### 3. 选择 Agent
1. 在下拉菜单选择策略（如 `agent_bundle_alpha_35`）
2. 设置品种（默认 XAUUSD）
3. 设置手数（建议 0.01）
4. 点击 "▶ START TRADING"

## 📦 依赖项

```
customtkinter
MetaTrader5
matplotlib
pandas
numpy
requests  # For Telegram
```

## Agent Bundle 位置

Agent bundles 应放在：
```
../New_model/agent_bundle_xxx/
```

## ⚠️ 重要提示

1. **首次使用请用模拟账户测试**
2. **最小手数从 0.01 开始**
3. **确保网络稳定（用于 Telegram 和 yfinance）**
4. **定期检查日志标签页**

## 🆘 故障排查

### 问题：MT5 连接失败
- ✅ 确认 MT5 已打开
- ✅ 确认已登录账户
- ✅ 重启 MT5

### 问题：Agent 加载失败
- ✅ 检查 bundle 路径是否正确
- ✅ 查看日志标签页错误信息
- ✅ 确认 requirements.txt 中的依赖已安装

### 问题：Telegram 无法发送
- ✅ 检查 Token 和 Chat ID 是否正确
- ✅ 向 Bot 发送过消息激活
- ✅ 检查网络连接

## 📞 技术支持

遇到问题请查看：
- 系统日志（📝 System Logs 标签页）
- Agent Bundle README
- MT5 专家日志

---

## 📦 安装说明 (v1.4.0)

由于 GitHub 文件大小限制，安装包被分为两部分。请按照以下步骤安装：

1.  **下载所有 3 个文件** (从 Releases 页面)：
    - `AlphaQuantPro_Setup.part1`
    - `AlphaQuantPro_Setup.part2`
    - `MERGE_INSTALLER.bat`
2.  **将它们放在同一个文件夹中**。
3.  **双击运行** `MERGE_INSTALLER.bat`。
    - 脚本会自动合并生成 `AlphaQuantPro_Setup.exe`。
4.  **运行** 生成的 `AlphaQuantPro_Setup.exe` 进行安装。

## ⚠️ 关于 Agent Bundles

出于商业机密保护，本仓库**不包含**核心策略模型 (`agents/` 和 `models/` 目录)。
请联系管理员获取授权的策略包，并将其放入安装目录下的 `agents/` 文件夹中。

---

**版本**: 1.4.0
**最后更新**: 2025-11-30
