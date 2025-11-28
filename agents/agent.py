from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional, Sequence

import numpy as np

try:
    import onnxruntime as ort
except ImportError:  # pragma: no cover - runtime requirement
    ort = None


@dataclass
class ModelOutput:
    signal: str
    size: float
    sl: Optional[float]
    tp: Optional[float]
    confidence: float
    tag: str
    extra: Dict[str, Any]


@dataclass
class ModelInput:
    """
    统一 Agent 输入结构，和 CHU_LIAN / ER_NIAN bundle 保持一致。
    """

    # 时间与价格
    timestamp: datetime
    price: float  # 当前交易价格（mid / close）
    features: np.ndarray  # FeatureBuilder 输出（1D 向量，对应 feature_schema 顺序）

    # 市场环境
    symbol: str
    timeframe: str  # "M1" / "M5" / "M15" / "H1" 等
    regime: Optional[str]

    # 持仓状态
    position: int  # -1 / 0 / 1
    bars_held: int
    open_trades: int
    entry_price: Optional[float]

    # 风控状态
    daily_pnl: float
    daily_drawdown: float
    equity: float
    balance: float

    # 最新 K 线数据
    candle: Dict[str, float]

    # 引擎自带的额外信息（例如 spread、volatility 等）
    meta: Dict[str, Any]


class TradingAgent:
    """
    经典 AI_MODEL_V7 分类模型的 bundle 适配层（ONNX 版本）。

    - 引擎侧只需要构造 ModelInput（features 已按 feature_schema 顺序填好）
    - 内部加载 model.onnx（sklearn → ONNX 导出的 3 类概率输出）
    - 输出统一的 ModelOutput（HOLD / BUY / SELL + SL/TP 价格级别）
    """

    def __init__(self, bundle_dir: Optional[str] = None) -> None:
        if bundle_dir is None:
            bundle_dir = Path(__file__).resolve().parent
        self.bundle_dir = Path(bundle_dir)

        if ort is None:
            raise ImportError(
                "onnxruntime is required to run TradingAgent. "
                "Please `pip install onnxruntime` in your environment."
            )

        cfg_path = self.bundle_dir / "agent_config.json"
        schema_path = self.bundle_dir / "feature_schema.json"
        risk_path = self.bundle_dir / "risk_manager.json"
        model_path = self.bundle_dir / "model.onnx"

        if not model_path.exists():
            raise FileNotFoundError(f"ONNX model not found at {model_path}")

        self.config = json.loads(cfg_path.read_text(encoding="utf-8"))
        self.schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.risk_cfg = json.loads(risk_path.read_text(encoding="utf-8"))

        output_cfg = self.config.get("output", {})
        self.conf_threshold = float(output_cfg.get("confidence_threshold", 0.5))
        timeframe_str = str(self.config.get("timeframe", "M15")).upper()
        tf_map = {"M1": 1, "M5": 5, "M15": 15, "M30": 30, "H1": 60, "H4": 240}
        self.timeframe_minutes = tf_map.get(timeframe_str, 1)
        horizon_minutes = float(self.risk_cfg.get("position_horizon_minutes", 0.0))
        self.max_holding_bars = (
            int(np.ceil(horizon_minutes / self.timeframe_minutes))
            if horizon_minutes > 0 and self.timeframe_minutes > 0
            else 0
        )

        feature_names: Sequence[str] = self.schema.get("features", [])
        self.feature_names = list(feature_names)
        self.feature_dim = len(self.feature_names)

        providers = ["CPUExecutionProvider"]
        self.session = ort.InferenceSession(str(model_path), providers=providers)
        self._input_name = self.session.get_inputs()[0].name

    # --- 内部工具 ---

    def _apply_risk(
        self,
        signal: str,
        size: float,
        sl: Optional[float],
        tp: Optional[float],
        *,
        open_trades: int,
        daily_drawdown: float,
        bars_held: int,
        price: float,
        equity: float,
    ) -> tuple[str, float, Optional[float], Optional[float]]:
        max_open = int(self.risk_cfg.get("max_open_trades", 3))
        max_dd = float(self.risk_cfg.get("max_daily_drawdown", 0.05))
        hard_sl_pct = float(self.risk_cfg.get("hard_stop_loss_pct", 0.0))
        tp_fallback_pct = float(self.risk_cfg.get("take_profit_pct", 0.0))
        risk_pct = float(self.risk_cfg.get("per_trade_risk_pct", 0.0))

        if open_trades >= max_open or daily_drawdown <= -abs(max_dd):
            return "HOLD", 0.0, None, None

        if self.max_holding_bars > 0 and bars_held >= self.max_holding_bars:
            return "HOLD", 0.0, None, None

        if sl is None and hard_sl_pct > 0.0:
            sl = (
                price * (1.0 - hard_sl_pct)
                if signal == "BUY"
                else price * (1.0 + hard_sl_pct)
            )
        if tp is None and tp_fallback_pct > 0.0:
            tp = (
                price * (1.0 + tp_fallback_pct)
                if signal == "BUY"
                else price * (1.0 - tp_fallback_pct)
            )

        if risk_pct > 0.0 and equity > 0.0 and price > 0.0 and sl is not None:
            if signal == "BUY":
                risk_per_unit = price - sl
            elif signal == "SELL":
                risk_per_unit = sl - price
            else:
                risk_per_unit = 0.0
            if risk_per_unit > 0.0:
                max_size = (equity * risk_pct) / risk_per_unit
                if max_size < size:
                    size = max_size
        return signal, size, sl, tp

    def _run_onnx(self, features: np.ndarray) -> np.ndarray:
        if features.ndim == 1:
            features = features[None, :]

        if features.shape[1] != self.feature_dim:
            raise ValueError(
                f"Expected feature_dim={self.feature_dim}, got {features.shape[1]}"
            )

        x = features.astype(np.float32)
        outputs = self.session.run(None, {self._input_name: x})

        # skl2onnx 默认导出: [output_label: ndarray, output_probability: list[dict]]
        probs_arr = None
        if len(outputs) >= 2 and isinstance(outputs[1], list):
            maps = outputs[1]
            if maps and isinstance(maps[0], dict):
                m = maps[0]
                keys = set(m.keys())
                if keys <= {-1, 0, 1}:
                    # ONNX 导出的概率映射键是 {-1, 0, 1}（典型的 SELL/HOLD/BUY 标签），
                    # 这里需要重排成 config 假定的顺序 [HOLD, BUY, SELL]。
                    reorder = {-1: 2, 0: 0, 1: 1}
                    probs_arr = np.zeros((1, 3), dtype=np.float32)
                    for k, v in m.items():
                        idx = reorder.get(int(k))
                        if idx is not None:
                            probs_arr[0, idx] = float(v)
                else:
                    probs_arr = np.array(
                        [float(m.get(i, 0.0)) for i in range(3)],
                        dtype=np.float32,
                    )[None, :]

        if probs_arr is None:
            probs_arr = np.asarray(outputs[0], dtype=np.float32)

        if probs_arr.ndim == 1:
            probs_arr = probs_arr[None, :]

        if probs_arr.ndim != 2 or probs_arr.shape[1] < 3:
            raise ValueError(
                f"AI_MODEL_V7 expected to output (batch, 3) probabilities, got {probs_arr.shape}"
            )
        return probs_arr

    # --- 核心预测接口（features + price） ---

    def predict(
        self,
        features: np.ndarray,
        price: float,
        *,
        position: int = 0,
        bars_held: int = 0,
        open_trades: int = 0,
        daily_drawdown: float = 0.0,
        equity: float = 0.0,
        regime: Optional[str] = None,
    ) -> ModelOutput:
        """
        统一输出接口，与 CHU_LIAN 的 TradingAgent.predict 保持风格一致。
        """
        features = np.asarray(features, dtype=np.float32).ravel()
        if features.shape[0] != self.feature_dim:
            raise ValueError(
                f"Expected feature_dim={self.feature_dim}, got {features.shape[0]}"
            )

        probs = self._run_onnx(features)
        probs_row = probs[0]
        action_idx = int(np.argmax(probs_row))
        confidence = float(probs_row[action_idx])

        # 0=HOLD, 1=BUY, 2=SELL
        if action_idx == 1:
            raw_signal = "BUY"
        elif action_idx == 2:
            raw_signal = "SELL"
        else:
            raw_signal = "HOLD"

        if confidence < self.conf_threshold:
            raw_signal = "HOLD"
            action_idx = 0

        actions_cfg = self.config.get("output", {}).get("actions", {})
        action_cfg = actions_cfg.get(str(action_idx), {})

        size = float(action_cfg.get("size", 0.0))
        sl_pct = float(action_cfg.get("sl_pct", 0.0))
        tp_pct = float(action_cfg.get("tp_pct", 0.0))

        if raw_signal == "BUY":
            sl = price * (1.0 - sl_pct) if sl_pct > 0.0 else None
            tp = price * (1.0 + tp_pct) if tp_pct > 0.0 else None
        elif raw_signal == "SELL":
            sl = price * (1.0 + sl_pct) if sl_pct > 0.0 else None
            tp = price * (1.0 - tp_pct) if tp_pct > 0.0 else None
        else:
            sl = None
            tp = None

        signal, size, sl, tp = self._apply_risk(
            raw_signal,
            size,
            sl,
            tp,
            open_trades=open_trades,
            daily_drawdown=daily_drawdown,
            bars_held=bars_held,
            price=price,
            equity=equity,
        )

        tag = f"AI_MODEL_V7_cls_action_{action_idx}"
        extra: Dict[str, Any] = {
            "probs": probs_row.tolist(),
            "action_idx": action_idx,
            "position": position,
            "bars_held": bars_held,
            "open_trades": open_trades,
            "daily_drawdown": daily_drawdown,
            "regime": regime,
            "feature_dim": self.feature_dim,
            "feature_names": self.feature_names,
        }

        return ModelOutput(
            signal=signal,
            size=size,
            sl=sl,
            tp=tp,
            confidence=confidence,
            tag=tag,
            extra=extra,
        )

    # --- 推荐入口：ModelInput ---, 与 CHU_LIAN 一致 ---

    def predict_from_input(self, mi: ModelInput) -> ModelOutput:
        """
        推荐统一入口：接受 ModelInput，基于 feature_schema 自动分配特征：
        - 若 mi.features 是向量（统一输入），长度>=feature_dim 时取前 feature_dim，长度不足时零填充；
        - 若 mi.features 是 dict / 映射，则按 feature_schema.json 中的特征名依次取值，缺失补 0。
        - 若 features 完全为空/None，则退化为全 0 向量（保证统一 I/O，不中断引擎）。
        """
        features_arr: Optional[np.ndarray] = None
        try:
            if mi.features is not None:  # type: ignore[truthy-function]
                # 1) 先尝试当作纯向量使用（统一输入可能比 17 维多，允许截断/零填充）
                arr = np.asarray(mi.features, dtype=np.float32).ravel()
                if arr.shape[0] > 0:
                    if arr.shape[0] >= self.feature_dim:
                        features_arr = arr[: self.feature_dim]
                    else:
                        padded = np.zeros(self.feature_dim, dtype=np.float32)
                        padded[: arr.shape[0]] = arr
                        features_arr = padded
                else:
                    # 2) 若向量为空，再尝试当作 name->value 映射，按 schema 补全/重排
                    feats_dict: Dict[str, Any] = {}
                    if isinstance(mi.features, dict):
                        feats_dict = mi.features  # type: ignore[assignment]
                    else:
                        try:
                            feats_dict = dict(mi.features)  # type: ignore[arg-type]
                        except Exception:
                            feats_dict = {}
                    if feats_dict:
                        ordered = [
                            float(feats_dict.get(name, 0.0))
                            for name in self.feature_names
                        ]
                        features_arr = np.asarray(ordered, dtype=np.float32)
        except Exception:
            features_arr = None

        if features_arr is None:
            # 兼容 README 中“features 可为空/占位”的统一格式：
            # 在完全缺失时退化为全 0 特征，保证 Agent 仍然可用（但信号质量依赖上游特征是否合理提供）。
            features_arr = np.zeros(self.feature_dim, dtype=np.float32)
            print(
                "[agent_warn] features missing -> filled zeros; check upstream data pipeline",
                flush=True,
            )

        if np.count_nonzero(features_arr) == 0:
            print(
                f"[agent_warn] features all zero (dim={self.feature_dim}); mean={float(np.mean(features_arr))}",
                flush=True,
            )

        return self.predict(
            features=features_arr,
            price=float(mi.price),
            position=mi.position,
            bars_held=mi.bars_held,
            open_trades=mi.open_trades,
            daily_drawdown=mi.daily_drawdown,
            equity=mi.equity,
            regime=mi.regime,
        )


__all__ = ["TradingAgent", "ModelOutput", "ModelInput"]
