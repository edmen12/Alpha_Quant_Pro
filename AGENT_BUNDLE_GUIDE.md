# Agent Bundle 开发指南

本指南详细说明了如何为 Alpha Quant Trading Terminal 创建、配置和部署自定义交易策略代理 (Agent Bundle)。

## 1. 什么是 Agent Bundle?

Agent Bundle 是一个独立的文件夹，包含了一个交易策略所需的所有资源：
- **模型文件**: `.onnx`, `.pth`, `.pkl` 等。
- **代码逻辑**: `agent.py` (必须包含)。
- **配置文件**: `config.json` (定义元数据和参数)。
- **依赖项**: `requirements.txt` (可选)。

这种设计使得策略可以像插件一样即插即用，且互不干扰。

## 2. 目录结构

一个标准的 Agent Bundle 结构如下：

```text
agent_bundle_MyStrategy/
├── agent.py              # 核心逻辑 (必须)
├── config.json           # 配置文件 (必须)
├── model.onnx            # 模型文件 (推荐 ONNX)
├── scaler.pkl            # 数据预处理对象 (可选)
├── requirements.txt      # 额外依赖 (可选)
└── README.md             # 策略说明 (可选)
```

## 3. 配置文件 (config.json)

`config.json` 定义了 Agent 的基本信息和默认参数。

```json
{
    "name": "My Custom Strategy",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "A trend-following strategy using LSTM.",
    "type": "model",  // "model" 或 "rule_based"
    "framework": "onnx", // "onnx", "pytorch", "sklearn"
    "input_schema": "v7", // 推荐使用 v7 标准输入
    "default_symbol": "XAUUSD",
    "default_timeframe": "M15",
    "parameters": {
        "lookback": 60,
        "threshold": 0.7
    }
}
```

## 4. 核心代码 (agent.py)

`agent.py` 必须包含一个名为 `Agent` 的类，并实现 `predict` 方法。

### 4.1 输入输出数据结构

系统使用标准化的数据类进行通信 (定义在 `core.io_schema`)：

**输入 (ModelInput):**
```python
@dataclass
class ModelInput:
    timestamp: datetime
    symbol: str
    timeframe: str
    price: float
    history_candles: pd.DataFrame  # 包含 Open, High, Low, Close, Volume
    candle: dict                   # 当前 K 线数据
    position: int                  # 当前持仓: 1 (多), -1 (空), 0 (无)
    bars_held: int                 # 持仓 K 线数
    open_trades: int               # 持仓单数
    entry_price: float             # 开仓价格
    daily_pnl: float               # 当日盈亏
    daily_drawdown: float          # 当日回撤
    equity: float                  # 账户净值
    balance: float                 # 账户余额
    meta: dict = None              # 额外元数据
```

**输出 (ModelOutput):**
```python
@dataclass
class ModelOutput:
    signal: str          # "BUY", "SELL", "HOLD", "CLOSE_BUY", "CLOSE_SELL"
    confidence: float    # 置信度 (0.0 - 1.0)
    sl: float = 0.0      # 建议止损价 (可选)
    tp: float = 0.0      # 建议止盈价 (可选)
    tag: str = ""        # 信号标签 (用于日志)
    extra: dict = None   # 额外调试信息
```

### 4.2 代码模板

```python
import pandas as pd
import numpy as np
import onnxruntime as ort
from core.io_schema import ModelInput, ModelOutput

class TradingAgent:
    def __init__(self, bundle_path, config=None):
        """
        初始化 Agent
        :param bundle_path: Bundle 文件夹的绝对路径
        :param config: config.json 的内容 (可选, 也可以在内部加载)
        """
        self.path = bundle_path
        # 如果 config 未传入，可以在这里加载
        import json
        import os
        if config is None:
             try:
                 with open(os.path.join(bundle_path, 'config.json'), 'r') as f:
                     self.config = json.load(f)
             except:
                 self.config = {"parameters": {"lookback": 60, "threshold": 0.7}}
        else:
            self.config = config
            
        self.lookback = self.config.get("parameters", {}).get("lookback", 60)
        
        # 加载模型 (示例: 如果有模型文件)
        # model_path = f"{bundle_path}/model.onnx"
        # self.session = ort.InferenceSession(model_path)

    def predict(self, data: ModelInput) -> ModelOutput:
        """
        生成交易信号
        """
        # 1. 数据预处理
        df = data.history_candles
        if len(df) < self.lookback:
            return ModelOutput("HOLD", 0.0, tag="Not enough data")

        # (示例) 计算简单的特征
        close_prices = df['close'].values[-self.lookback:]
        input_tensor = close_prices.reshape(1, -1).astype(np.float32)

        # 2. 模型推理
        inputs = {self.session.get_inputs()[0].name: input_tensor}
        outputs = self.session.run(None, inputs)
        prob = outputs[0][0][0] # 假设输出是上涨概率

        # 3. 生成信号
        signal = "HOLD"
        confidence = float(prob)
        
        threshold = self.config["parameters"]["threshold"]

        if prob > threshold:
            signal = "BUY"
        elif prob < (1 - threshold):
            signal = "SELL"

        return ModelOutput(
            signal=signal,
            confidence=confidence,
            tag=f"Model Pred: {prob:.2f}"
        )
```

## 5. 支持的模型框架

虽然您可以运行任何 Python 代码，但为了性能和兼容性，推荐使用以下框架：

1.  **ONNX (推荐)**:
    -   **优点**: 跨平台，推理速度快，无需安装庞大的 PyTorch/TensorFlow 库。
    -   **适用**: 神经网络，传统机器学习模型。

2.  **Scikit-learn**:
    -   **优点**: 简单易用，适合传统 ML (随机森林, SVM)。
    -   **注意**: 需要保存为 `.pkl` 或 `.joblib`。

3.  **PyTorch**:
    -   **优点**: 灵活性高，支持最新架构。
    -   **注意**: 依赖包体积大，推理速度可能不如 ONNX。

## 6. 如何导入和使用

1.  **创建文件夹**: 在 `trading_terminal/agents/` 目录下创建一个新文件夹，例如 `agent_bundle_MyNewStrategy`。
2.  **添加文件**: 将您的 `agent.py`, `config.json` 和模型文件放入该文件夹。
3.  **重启终端**: 关闭并重新打开 `AlphaQuantPro.exe`。
4.  **选择策略**: 在 "Settings" (设置) 标签页的 "Agent Bundle" 下拉菜单中，您应该能看到 `MyNewStrategy`。
5.  **运行**: 选择策略，点击 "Save"，然后点击 "START TRADING"。

## 7. 调试与日志

-   Agent 的 `print()` 输出会被重定向到系统日志。
-   在终端的 "Logs" 标签页可以查看 Agent 的加载状态和报错信息。
-   如果 Agent 加载失败，请检查 `config.json` 格式是否正确，以及 `agent.py` 是否有语法错误。
