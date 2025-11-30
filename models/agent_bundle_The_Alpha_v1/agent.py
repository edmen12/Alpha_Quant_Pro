import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import logging
import numpy as np
import pandas as pd
import xgboost as xgb
import yfinance as yf
from stable_baselines3 import PPO


# --- 数据结构定义（与 README 契合） ---
@dataclass
class ModelInput:
    timestamp: datetime
    symbol: str
    timeframe: str
    price: float
    history_candles: List[Dict] | pd.DataFrame
    candle: Dict
    position: int
    bars_held: int
    open_trades: int
    entry_price: float
    daily_pnl: float
    daily_drawdown: float
    equity: float
    balance: float
    meta: Dict


@dataclass
class ModelOutput:
    signal: str  # "BUY" / "SELL" / "HOLD"
    size: float  # 0.0 ~ 1.0
    sl: Optional[float]
    tp: Optional[float]
    confidence: float  # 0.0 ~ 1.0
    tag: str
    extra: Dict


class TradingAgent:
    """
    三道防线：
    1) Dead Zone (XGB 信号死区) -> 防止 Always-In
    2) Regime Filter (EMA200 熊市禁多，可配置)
    3) RL 决策 (PPO)，特征屏蔽：仅末两维保留信号
    """

    def __init__(self, bundle_dir: str, dead_zone: Optional[float] = None):
        base = Path(bundle_dir).resolve()
        self.bundle_dir = Path(__file__).resolve().parent if not base.exists() else base
        self.base_dir = str(self.bundle_dir)
        self.risk_cfg = self._load_risk_cfg()
        # 优先使用传入 dead_zone，否则回落到配置文件
        cfg_dead_zone = self.risk_cfg.get("signal_filters", {}).get(
            "dead_zone_threshold", 0.60
        )
        self.dead_zone = cfg_dead_zone if dead_zone is None else dead_zone
        trend_cfg = self.risk_cfg.get("trend_filters", {})
        self.use_trend_filter = bool(trend_cfg.get("enabled", True))
        self.ema_period = int(trend_cfg.get("period", 200))
        self.regime_rules = trend_cfg.get("regime_rules", {})
        self.feature_schema = self._load_feature_schema()
        self.feature_stats = self._load_feature_stats()
        self.feature_dim = int(self.feature_schema.get("feature_dim", 39))
        self.history_window = int(self.feature_schema.get("history_window_size", 300))
        
        # Volatility Settings
        self.vol_cfg = self.risk_cfg.get("volatility_settings", {})
        self.use_atr = self.vol_cfg.get("use_atr_sl", False)
        self.atr_period = int(self.vol_cfg.get("atr_period", 14))
        self.sl_mult = float(self.vol_cfg.get("sl_multiplier", 1.5))
        self.tp_mult = float(self.vol_cfg.get("tp_multiplier", 3.0))
        
        self._yf_cache: Dict[str, pd.Series] = {}

        # 模型加载
        self.ppo = PPO.load(self.bundle_dir / "models" / "ppo_best_xauusd.zip")
        self.xgb_up = xgb.Booster()
        self.xgb_up.load_model(str(self.bundle_dir / "models" / "xgb_up.json"))
        self.xgb_down = xgb.Booster()
        self.xgb_down.load_model(str(self.bundle_dir / "models" / "xgb_down.json"))

        print(f"[Agent] Loaded PPO + XGB from {self.bundle_dir}")
        print(
            f"[Agent] Risk Controls -> DeadZone={self.dead_zone}, "
            f"TrendFilter={'ON' if self.use_trend_filter else 'OFF'}(EMA{self.ema_period})"
        )

    # ---------------------- 公共接口 ----------------------
    def predict_from_input(self, model_input: ModelInput) -> ModelOutput:
        df_hist = self._to_dataframe(model_input.history_candles)
        if df_hist.empty:
            return ModelOutput("HOLD", 0.0, None, None, 0.0, "NoData", {})
        if len(df_hist) < max(self.history_window, self.ema_period):
            return ModelOutput(
                "HOLD", 0.0, None, None, 0.0, "Cold_Start_Data_Not_Ready", {}
            )

        # 1) 计算基本行情量化
        ema_val = self._ema(df_hist["close"], self.ema_period)
        current_price = float(model_input.price)

        # 2) 生成特征并做 XGB 推理
        feat_row = self._compute_features(df_hist)
        
        # XGBoost 仅接受 36 个特征，需移除多余的 3 个 (wti_close_ret, gld_close, gld_close_ret)
        xgb_cols = [c for c in feat_row.columns if c not in ['wti_close_ret', 'gld_close', 'gld_close_ret']]
        feat_row_xgb = feat_row[xgb_cols]
        
        
        dmat = xgb.DMatrix(feat_row_xgb)
        p_up = float(self.xgb_up.predict(dmat)[0])
        p_down = float(self.xgb_down.predict(dmat)[0])
        
        # logging.info(f"[Agent] Raw Preds -> Up: {p_up:.4f}, Down: {p_down:.4f}")

        # 3) Dead Zone：信号弱则强制空仓
        if p_up < self.dead_zone and p_down < self.dead_zone:
            return ModelOutput(
                "HOLD",
                0.0,
                None,
                None,
                max(p_up, p_down), # Show real confidence instead of fixed 0.4
                f"DeadZone(thr={self.dead_zone:.2f})",
                {"p_up": p_up, "p_down": p_down, "ema": ema_val},
            )

        # 4) Regime Filter：熊市禁多（可扩展禁空）
        allow_long = True
        allow_short = True
        regime_msg = "Neutral"
        if self.use_trend_filter and ema_val is not None:
            if current_price < ema_val:
                if self.regime_rules.get("bear_market") == "block_long":
                    allow_long = False
                    regime_msg = "Bear_NoLong"
            else:
                regime_msg = "Bull"

        # 5) 构造 RL 观测（特征屏蔽：仅末两维保留信号）
        masked_len = max(self.feature_dim - 2, 0)
        obs = np.zeros(self.feature_dim, dtype=np.float32)
        if masked_len > 0:
            obs[:masked_len] = 0.0
        obs[-2] = p_up
        obs[-1] = p_down
        assert len(obs) == self.feature_dim, "Obs dim mismatch"

        action, _ = self.ppo.predict(obs, deterministic=True)

        # 6) 最终裁决
        final_signal = "HOLD"
        tag = "RL_Hold"
        sl_price = None
        tp_price = None
        
        # Calculate Dynamic Risk Parameters
        sl_dist = 5.0   # Default 500 pips
        tp_dist = 10.0  # Default 1000 pips
        
        if self.use_atr and len(df_hist) > self.atr_period + 1:
            try:
                high = df_hist['high']
                low = df_hist['low']
                close = df_hist['close']
                prev_close = close.shift(1)
                tr1 = high - low
                tr2 = (high - prev_close).abs()
                tr3 = (low - prev_close).abs()
                tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
                atr_val = tr.rolling(window=self.atr_period).mean().iloc[-1]
                
                if atr_val > 0:
                    sl_dist = atr_val * self.sl_mult
                    tp_dist = atr_val * self.tp_mult
            except Exception as e:
                print(f"[Agent] ATR calc failed: {e}")

        if action == 1:
            if allow_long:
                final_signal = "BUY"
                tag = f"RL_Buy({p_up:.2f})"
                sl_price = current_price - sl_dist
                tp_price = current_price + tp_dist
            else:
                tag = "Regime_Block_Long"
        elif action == 2:
            if allow_short:
                final_signal = "SELL"
                tag = f"RL_Sell({p_down:.2f})"
                sl_price = current_price + sl_dist
                tp_price = current_price - tp_dist
            else:
                tag = "Regime_Block_Short"

        confidence = max(p_up, p_down)
        return ModelOutput(
            final_signal,
            1.0 if final_signal != "HOLD" else 0.0,
            sl_price,
            tp_price,
            confidence,
            tag,
            {
                "p_up": p_up,
                "p_down": p_down,
                "ema": ema_val,
                "allow_long": allow_long,
                "allow_short": allow_short,
                "raw_action": int(action),
                "regime": regime_msg,
            },
        )

    # ---------------------- 内部工具 ----------------------
    def _load_risk_cfg(self) -> Dict:
        risk_path = self.bundle_dir / "risk_manager.json"
        if risk_path.exists():
            try:
                cfg = json.loads(risk_path.read_text(encoding="utf-8"))
            except Exception as exc:  # noqa: BLE001
                print(
                    f"[Warning] Failed to load risk_manager.json, fallback to defaults. Error: {exc}"
                )
                cfg = {}
        else:
            print("[Warning] risk_manager.json not found, fallback to defaults.")
            cfg = {}

        # 递归安全取值，填充缺省
        signal_cfg = cfg.get("signal_filters", {})
        if "dead_zone_threshold" not in signal_cfg:
            print("[Warning] signal_filters.dead_zone_threshold missing, use 0.60")
            signal_cfg["dead_zone_threshold"] = 0.60
        trend_cfg = cfg.get("trend_filters", {})
        if "enabled" not in trend_cfg:
            print("[Warning] trend_filters.enabled missing, use True")
            trend_cfg["enabled"] = True
        if "period" not in trend_cfg:
            print("[Warning] trend_filters.period missing, use 200")
            trend_cfg["period"] = 200
        if "regime_rules" not in trend_cfg:
            trend_cfg["regime_rules"] = {}

        cfg["signal_filters"] = signal_cfg
        cfg["trend_filters"] = trend_cfg
        return cfg

    def _load_feature_schema(self) -> Dict:
        schema_path = self.bundle_dir / "feature_schema.json"
        if schema_path.exists():
            return json.loads(schema_path.read_text())
        return {"feature_dim": 39}

    def _load_feature_stats(self) -> Optional[Dict[str, Dict[str, float]]]:
        stats_path = self.bundle_dir / "feature_stats.json"
        if stats_path.exists():
            try:
                return json.loads(stats_path.read_text())
            except Exception as exc:  # noqa: BLE001
                print(f"[Warning] Failed to load feature_stats.json: {exc}")
        return None

    def _to_dataframe(self, history) -> pd.DataFrame:
        if isinstance(history, pd.DataFrame):
            return history.copy()
        return pd.DataFrame(history)

    def _ema(self, series: pd.Series, window: int) -> Optional[float]:
        if len(series) < window:
            return None
        return float(series.ewm(span=window, adjust=False).mean().iloc[-1])

    def _compute_features(self, df_hist: pd.DataFrame) -> pd.DataFrame:
        """
        占位：此处应复刻训练时的特征工程。
        当前实现：若缺列则自动在本地计算核心 TA/时间特征，并对齐 schema 顺序。
        若宏观列缺失则填 0，并打印一次警告。
        """
        if df_hist.empty:
            raise ValueError("history_candles is empty")
        expected_cols = self.feature_schema.get("feature_names") or []
        if not expected_cols:
            raise ValueError("feature_schema missing 'feature_names'")

        df_feat = self._ensure_features(df_hist.copy(), expected_cols)

        # 应用训练时统计量进行标准化（存在则使用）
        if self.feature_stats:
            for col, stat in self.feature_stats.items():
                if col in df_feat.columns:
                    df_feat[col] = (df_feat[col] - stat.get("mean", 0.0)) / (
                        stat.get("std", 1.0) + 1e-8
                    )

        last_row = df_feat.loc[:, expected_cols].iloc[[-1]].astype(np.float32)
        return last_row

    def _fetch_yf_series(
        self, ticker: str, start: pd.Timestamp, end: pd.Timestamp
    ) -> Optional[pd.Series]:
        """下载 yfinance 收盘价并缓存 (带重试，每天最多更新一次)。"""
        # Check if cache exists and is fresh (same day or later)
        if ticker in self._yf_cache:
            cached_series = self._yf_cache[ticker]
            if not cached_series.empty:
                last_cached_date = cached_series.index[-1].date()
                if last_cached_date >= end.date():
                    logging.info(f"[Agent] Using cached data for {ticker} (cached until {last_cached_date})")
                    return cached_series
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                data = yf.download(
                    ticker,
                    start=start.date(),
                    end=end.date() + pd.Timedelta(days=1),
                    progress=False,
                    auto_adjust=False,
                )
                if data.empty or "Close" not in data:
                    if attempt < max_retries - 1:
                        logging.warning(f"[Agent] yfinance returned empty for {ticker}, retrying ({attempt+1}/{max_retries})")
                        continue
                    else:
                        logging.error(f"[Agent] yfinance FAILED after {max_retries} retries for {ticker}")
                        return None
                
                # Extract Close column - handle MultiIndex case
                if isinstance(data.columns, pd.MultiIndex):
                    # Multi-ticker download, get specific ticker
                    series = data["Close"][ticker].copy()
                else:
                    # Single ticker download
                    series = data["Close"].copy()
                
                # Critical validation: index MUST be DatetimeIndex
                if not isinstance(series.index, pd.DatetimeIndex):
                    logging.error(f"[Agent] CRITICAL: {ticker} series has wrong index type: {type(series.index)}")
                    logging.error(f"[Agent] Index sample: {series.index[:3].tolist() if len(series.index) > 0 else 'empty'}")
                    return None
                
                # Ensure datetime index
                series.index = pd.to_datetime(series.index)
                self._yf_cache[ticker] = series
                return series
            except Exception as exc:
                if attempt < max_retries - 1:
                    logging.warning(f"[Agent] yfinance error for {ticker}: {exc}, retrying ({attempt+1}/{max_retries})")
                else:
                    logging.error(f"[Agent] yfinance FAILED after {max_retries} retries for {ticker}: {exc}")
                    return None
        return None

    def _ensure_features(
        self, df: pd.DataFrame, expected_cols: List[str]
    ) -> pd.DataFrame:
        """生成/补齐必需特征；宏观列缺失时填 0 并告警一次。"""
        if "datetime" not in df.columns:
            raise ValueError("history_candles must include 'datetime'")
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)

        # 基础价量
        for c in ["open", "high", "low", "close", "volume"]:
            if c not in df.columns:
                raise ValueError(f"history_candles missing base column '{c}'")

        # 收益/对数收益
        df["log_ret"] = np.log(df["close"] / df["close"].shift()).replace(
            [np.inf, -np.inf], np.nan
        )
        for c in ["open", "high", "low", "close"]:
            df[f"{c}_ret"] = np.log(df[c] / df[c].shift()).replace(
                [np.inf, -np.inf], np.nan
            )

        # 时间特征
        df["hour"] = df["datetime"].dt.hour
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
        df["session_state"] = pd.cut(
            df["hour"], bins=[-1, 7, 15, 23], labels=[0, 1, 2]
        ).astype(int)

        # zscore 96
        roll_mean = df["close"].rolling(96).mean()
        roll_std = df["close"].rolling(96).std() + 1e-8
        df["zscore_close"] = (df["close"] - roll_mean) / roll_std
        lr = df["log_ret"]
        lr_mean = lr.rolling(96).mean()
        lr_std = lr.rolling(96).std() + 1e-8
        df["zscore_log_ret"] = (lr - lr_mean) / lr_std

        # MACD
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        df["macd"] = ema12 - ema26
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # RSI 14
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        roll_up = gain.rolling(14).mean()
        roll_down = loss.rolling(14).mean()
        rs = roll_up / (roll_down + 1e-8)
        df["rsi"] = 100 - (100 / (1 + rs))

        # CCI 20
        tp = (df["high"] + df["low"] + df["close"]) / 3
        sma_tp = tp.rolling(20).mean()
        mad_tp = (tp - sma_tp).abs().rolling(20).mean()
        df["cci"] = (tp - sma_tp) / (0.015 * (mad_tp + 1e-8))

        # ATR 14
        high_low = df["high"] - df["low"]
        high_close = (df["high"] - df["close"].shift()).abs()
        low_close = (df["low"] - df["close"].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        df["atr"] = tr.rolling(14).mean()

        # ADX 14
        up_move = df["high"].diff()
        down_move = -df["low"].diff()
        plus_dm = (
            (up_move.where((up_move > down_move) & (up_move > 0), 0.0))
            .ewm(alpha=1 / 14, adjust=False)
            .mean()
        )
        minus_dm = (
            (down_move.where((down_move > up_move) & (down_move > 0), 0.0))
            .ewm(alpha=1 / 14, adjust=False)
            .mean()
        )
        atr_ewm = tr.ewm(alpha=1 / 14, adjust=False).mean()
        plus_di = 100 * (plus_dm / (atr_ewm + 1e-8))
        minus_di = 100 * (minus_dm / (atr_ewm + 1e-8))
        dx = (abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)) * 100
        df["adx"] = dx.ewm(alpha=1 / 14, adjust=False).mean()

        # 波动率
        df["vol_96"] = df["log_ret"].rolling(96).std()
        df["vol_288"] = df["log_ret"].rolling(288).std()
        df["volatility_ratio"] = df["volume"] / (df["volume"].rolling(96).mean() + 1e-8)

        # 宏观/外盘：缺失则尝试 yfinance 填充，仍缺则填 0 并告警
        macro_cols = [
            "dxy_close",
            "dxy_close_ret",
            "dxy_ret",
            "us10y_price",
            "us10y_price_ret",
            "us10y_price_ret_pct",
            "wti_close",
            "wti_close_ret",
            "gld_close",
            "gld_close_ret",
            "corr_close_dxy",
            "corr_close_us10y",
            "corr_dxy_60",
            "corr_close_us10y_60",
        ]
        missing_macro = [c for c in macro_cols if c not in df.columns]
        if missing_macro:
            start_dt = df["datetime"].min()
            end_dt = df["datetime"].max()
            
            # CRITICAL: Extend range to 120 days to ensure 60+ trading days after weekends/holidays
            min_start = end_dt - pd.Timedelta(days=120)
            if start_dt > min_start:
                start_dt = min_start

            
            ticker_map = {
                "dxy_close": "DX-Y.NYB",
                "us10y_price": "^TNX",
                "wti_close": "CL=F",
                "gld_close": "GLD",
            }
            for col, ticker in ticker_map.items():
                if col in df.columns:
                    continue
                series = self._fetch_yf_series(ticker, start_dt, end_dt)
                if series is not None:
                    # CRITICAL FIX: Remove timezone if present
                    try:
                        if hasattr(series.index, 'tz') and series.index.tz is not None:
                            series.index = series.index.tz_localize(None)
                    except Exception as e:
                        logging.warning(f"[Agent] Timezone conversion warning for {ticker}: {e}")
                    
                    # Resample to daily and forward+backward fill
                    ser = (
                        series.resample("D")
                        .last()
                        .reindex(
                            pd.date_range(
                                start=start_dt.floor("D"),
                                end=end_dt.floor("D"),
                                freq="D",
                            )
                        )
                        .fillna(method='ffill')  # Forward fill
                        .fillna(method='bfill')  # Backward fill for leading NaNs
                    )
                    
                    # Debug: Check if ffill worked
                    nan_count = int(ser.isnull().sum())
                    total_count_ser = int(len(ser))
                    if nan_count == total_count_ser:
                        logging.error(f"[Agent] CRITICAL: {ticker} data is ALL NaN after reindex+ffill!")
                        logging.error(f"[Agent] series dates: {series.index.tolist()}")
                        logging.error(f"[Agent] target range: {start_dt.floor('D')} to {end_dt.floor('D')}")
                    
                    # Map to df - use merge for robustness
                    ser_df = pd.DataFrame({'date': ser.index, 'value': ser.values})
                    df['_merge_key'] = df['datetime'].dt.floor('D')
                    df_merged = df.merge(ser_df, left_on='_merge_key', right_on='date', how='left')
                    df[col] = df_merged['value'].values  # Use .values to avoid index alignment issues
                    df.drop(columns=['_merge_key'], inplace=True)
                    
                    # Debug: Check mapping result
                    mapped_count = df[col].notna().sum()
                    total_count = len(df)
                    if mapped_count == 0:
                        logging.error(f"[Agent] CRITICAL: {col} mapping FAILED! 0/{total_count} rows mapped")
                    elif mapped_count < total_count:
                        logging.warning(f"[Agent] {col} partial mapping: {mapped_count}/{total_count} rows OK")



        # Macro returns/correlations calculation - MUST be done at DAILY level BEFORE mapping
        # Calculate returns on daily series first
        macro_features = {}
        
        if "dxy_close" in df.columns and df["dxy_close"].notna().any():
            # Get the daily series (extract unique daily values)
            daily_df = df[['datetime', 'dxy_close']].copy()
            daily_df['date'] = daily_df['datetime'].dt.floor('D')
            daily_dxy = daily_df.groupby('date')['dxy_close'].first().sort_index()
            
            # Calculate returns at daily level
            daily_dxy_ret = np.log(daily_dxy / daily_dxy.shift()).replace([np.inf, -np.inf], np.nan).fillna(0)
            
            # Map back to M15
            ret_dict = daily_dxy_ret.to_dict()
            df["dxy_close_ret"] = df["datetime"].dt.floor("D").map(ret_dict)
            df["dxy_ret"] = df["dxy_close_ret"]  # Alias
        
        if "us10y_price" in df.columns and df["us10y_price"].notna().any():
            daily_df = df[['datetime', 'us10y_price']].copy()
            daily_df['date'] = daily_df['datetime'].dt.floor('D')
            daily_us10y = daily_df.groupby('date')['us10y_price'].first().sort_index()
            
            daily_us10y_ret = np.log(daily_us10y / daily_us10y.shift()).replace([np.inf, -np.inf], np.nan).fillna(0)
            daily_us10y_ret_pct = daily_us10y.pct_change().replace([np.inf, -np.inf], np.nan).fillna(0)
            
            df["us10y_price_ret"] = df["datetime"].dt.floor("D").map(daily_us10y_ret.to_dict())
            df["us10y_price_ret_pct"] = df["datetime"].dt.floor("D").map(daily_us10y_ret_pct.to_dict())
        
        if "wti_close" in df.columns and df["wti_close"].notna().any():
            daily_df = df[['datetime', 'wti_close']].copy()
            daily_df['date'] = daily_df['datetime'].dt.floor('D')
            daily_wti = daily_df.groupby('date')['wti_close'].first().sort_index()
            
            daily_wti_ret = np.log(daily_wti / daily_wti.shift()).replace([np.inf, -np.inf], np.nan).fillna(0)
            df["wti_close_ret"] = df["datetime"].dt.floor("D").map(daily_wti_ret.to_dict())
        
        if "gld_close" in df.columns and df["gld_close"].notna().any():
            daily_df = df[['datetime', 'gld_close']].copy()
            daily_df['date'] = daily_df['datetime'].dt.floor('D')
            daily_gld = daily_df.groupby('date')['gld_close'].first().sort_index()
            
            daily_gld_ret = np.log(daily_gld / daily_gld.shift()).replace([np.inf, -np.inf], np.nan).fillna(0)
            df["gld_close_ret"] = df["datetime"].dt.floor("D").map(daily_gld_ret.to_dict())
        
        # Correlations - download Gold daily history separately for correlation calculation
        if {"close", "dxy_close"}.issubset(df.columns):
            # Get extended date range
            start_dt = df["datetime"].min()
            end_dt = df["datetime"].max()
            min_start = end_dt - pd.Timedelta(days=120)
            if start_dt > min_start:
                start_dt = min_start
            
            # Download Gold daily data (use GC=F futures or XAUUSD)
            gold_series = self._fetch_yf_series("GC=F", start_dt, end_dt)
            
            if gold_series is not None and len(gold_series) >= 60:
                # Resample to daily
                gold_daily = gold_series.resample("D").last().fillna(method='ffill').fillna(method='bfill')
                
                # Get DXY daily directly from source to ensure full history
                dxy_series = self._fetch_yf_series("DX-Y.NYB", start_dt, end_dt)
                if dxy_series is not None:
                    dxy_daily = dxy_series.resample("D").last().fillna(method='ffill').fillna(method='bfill')
                    
                    # Align indices
                    common_dates = gold_daily.index.intersection(dxy_daily.index)
                    logging.info(f"[Agent] Correlation calc (DXY): Gold={len(gold_daily)} days, DXY={len(dxy_daily)} days, Common={len(common_dates)} days")
                    if len(common_dates) >= 60:
                        gold_aligned = gold_daily.loc[common_dates]
                        dxy_aligned = dxy_daily.loc[common_dates]
                    
                    # Calculate 60-day correlation
                    daily_corr = gold_aligned.rolling(60).corr(dxy_aligned).fillna(0)
                    
                    # Map to M15
                    df["corr_dxy_60"] = df["datetime"].dt.floor("D").map(daily_corr.to_dict()).fillna(method='ffill')
                    df["corr_close_dxy"] = df["corr_dxy_60"]

                else:
                    logging.warning(f"[Agent] Insufficient common dates for correlation: {len(common_dates)}/60")
                    df["corr_dxy_60"] = -0.05  # Use training mean
                    df["corr_close_dxy"] = -0.05
            else:
                logging.warning(f"[Agent] Gold data insufficient for correlation, using mean")
                df["corr_dxy_60"] = -0.05
                df["corr_close_dxy"] = -0.05
        
        if {"close", "us10y_price"}.issubset(df.columns):
            start_dt = df["datetime"].min()
            end_dt = df["datetime"].max()
            min_start = end_dt - pd.Timedelta(days=120)
            if start_dt > min_start:
                start_dt = min_start
            
            gold_series = self._fetch_yf_series("GC=F", start_dt, end_dt)
            
            if gold_series is not None and len(gold_series) >= 60:
                gold_daily = gold_series.resample("D").last().fillna(method='ffill').fillna(method='bfill')
                
                # Get US10Y daily directly from source
                us10y_series = self._fetch_yf_series("^TNX", start_dt, end_dt)
                if us10y_series is not None:
                    us10y_daily = us10y_series.resample("D").last().fillna(method='ffill').fillna(method='bfill')
                    
                    common_dates = gold_daily.index.intersection(us10y_daily.index)
                    logging.info(f"[Agent] Correlation calc (US10Y): Gold={len(gold_daily)} days, US10Y={len(us10y_daily)} days, Common={len(common_dates)} days")
                    if len(common_dates) >= 60:
                        gold_aligned = gold_daily.loc[common_dates]
                        us10y_aligned = us10y_daily.loc[common_dates]
                    
                    daily_corr = gold_aligned.rolling(60).corr(us10y_aligned).fillna(0)
                    
                    df["corr_close_us10y_60"] = df["datetime"].dt.floor("D").map(daily_corr.to_dict()).fillna(method='ffill')
                    df["corr_close_us10y"] = df["corr_close_us10y_60"]

                else:
                    df["corr_close_us10y_60"] = -0.02
                    df["corr_close_us10y"] = -0.02
            else:
                df["corr_close_us10y_60"] = -0.02
                df["corr_close_us10y"] = -0.02
        
        # Validation: Check for suspicious 0 values in macro features
        validation_cols = ['dxy_close_ret', 'us10y_price_ret', 'wti_close_ret', 'corr_dxy_60', 'corr_close_us10y_60']
        for col in validation_cols:
            if col in df.columns:
                unique_vals = df.groupby(df['datetime'].dt.floor('D'))[col].first().tail(3)
                if (unique_vals == 0).all():
                    logging.warning(f"[Agent] WARNING: {col} has all zeros in last 3 days - possible data issue")

        # Final check for missing macro columns AND NaNs
        # STRICT MODE: All features must be valid
        still_missing = [c for c in macro_cols if c not in df.columns]
        if still_missing:
            logging.error(f"[Agent] CRITICAL: Missing macro cols {still_missing}")
            logging.error(f"[Agent] This will cause model prediction errors. Check yfinance connectivity.")
            for c in still_missing:
                df[c] = 0.0  # Fallback, but log error
        
        # Check for NaNs in macro columns and fill with Mean (Neutral)
        nan_cols = []
        for c in macro_cols:
            if c in df.columns and df[c].isnull().any():
                nan_cols.append(c)
                fill_val = 0.0
                if self.feature_stats and c in self.feature_stats:
                    fill_val = self.feature_stats[c].get("mean", 0.0)
                logging.warning(f"[Agent] Feature {c} has NaNs. Filling with Mean={fill_val:.4f}")
                df[c] = df[c].fillna(fill_val)
        
        if nan_cols:
            logging.warning(f"[Agent] {len(nan_cols)} features had NaNs: {nan_cols}")
            logging.warning(f"[Agent] Recommendation: Check yfinance data quality or internet connection.")

        df = df.drop(columns=["hour"], errors="ignore")
        return df


def load_agent(bundle_dir: str) -> TradingAgent:
    return TradingAgent(bundle_dir=bundle_dir)
