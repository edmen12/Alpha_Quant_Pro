import pandas as pd
import numpy as np
# import onnxruntime as ort # Not needed for this dummy test
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
        if df is None or len(df) < self.lookback:
            return ModelOutput("HOLD", 0.0, tag="Not enough data")

        # (示例) 计算简单的特征
        # close_prices = df['close'].values[-self.lookback:]
        # input_tensor = close_prices.reshape(1, -1).astype(np.float32)

        # 2. 模型推理 (Mock)
        # inputs = {self.session.get_inputs()[0].name: input_tensor}
        # outputs = self.session.run(None, inputs)
        prob = 0.8 # Mock high probability

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
