# Alpha Quant Trading Terminal

**完全自包含的专业级自动交易终端** - 支持 MetaTrader 5 实盘/模拟交易。

**✨ 特色：整个文件夹可以随意移动到任何位置，无需修改配置！**

## 🚀 快速启动

```bash
cd trading_terminal
python terminal_pro.py
```

## 📁 文件结构

```
trading_terminal/           # 📦 完全独立的交易终端
├── agents/                 # 🤖 Agent Bundle 存储目录
│   ├── agent_bundle_alpha_35/
│   ├── agent_bundle_The_Alpha_v1/
│   ├── agent_bundle_AI_MODEL_V7_1/
│   └── ...
│
├── core/                   # 🏗️ 核心架构模块
│   ├── __init__.py
│   ├── io_schema.py       # 标准化 IO 格式
│   ├── base_model.py      # 模型基类
│   ├── agent_adapter.py   # Agent 适配器
│   └── dependency_manager.py # 依赖管理
│
├── engine_core.py         # ⚙️ 交易引擎核心
├── terminal_pro.py        # 🖥️ 主程序（GUI）
├── telegram_notifier.py   # 📱 Telegram 通知模块
└── README.md              # 📖 本文件
```

**💡 提示：** 
- 所有 Agent Bundles 都在 `agents/` 目录
- 不依赖外部路径
- 整个文件夹可以直接复制到其他电脑使用

## ✨ 主要功能

### 1. 📊 实时 K 线图表
- 专业蜡烛图显示
- 自动更新（3秒间隔）
- 显示最近 50 根 K 线

### 2. 💰 账户监控
- 实时余额/净值
- 浮动盈亏（颜色编码）
- 信号置信度

### 3. 📱 Telegram 通知
- 新信号推送
- 交易执行提醒
- 盈亏更新

### 4. 🤖 Agent Bundle 系统
- 动态加载各种策略
- 自动管理依赖
- 向后兼容旧格式

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

**版本**: 1.0.0  
**最后更新**: 2025-11-26
