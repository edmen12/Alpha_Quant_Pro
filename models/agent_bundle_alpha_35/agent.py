import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
import xgboost as xgb
import yfinance as yf

# --- 数据结构定义 ---
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
    Alpha 35: Pure XGBoost Agent
    Replicates the logic of Sharpe 7.31 backtest.
    - Threshold: 0.6
    - Horizon: 12 bars
    - Stop Loss: 0.2%
    """

    def __init__(self, bundle_dir: str):
        base = Path(bundle_dir).resolve()
        self.bundle_dir = Path(__file__).resolve().parent if not base.exists() else base
        self.feature_schema = self._load_feature_schema()
        self.feature_stats = self._load_feature_stats()
        self.feature_dim = int(self.feature_schema.get("feature_dim", 39))
        self.history_window = int(self.feature_schema.get("history_window_size", 300))
        self._yf_cache: Dict[str, pd.Series] = {}

        # Load XGBoost Models
        model_up_path = (self.bundle_dir / "xgb_up.json").resolve()
        model_down_path = (self.bundle_dir / "xgb_down.json").resolve()
        
        print(f"[Alpha 35] Bundle Dir: {self.bundle_dir}")
        print(f"[Alpha 35] Loading UP model from: {model_up_path}")
        if not model_up_path.exists():
            print(f"ERROR: UP Model file does not exist at {model_up_path}")
        
        self.xgb_up = xgb.Booster()
        self.xgb_up.load_model(str(model_up_path))
        self.xgb_down = xgb.Booster()
        self.xgb_down.load_model(str(model_down_path))

        # Strategy Params
        self.threshold = 0.5  # Lowered from 0.6 for more frequent signals
        self.horizon = 12
        self.sl_pct = 0.002

        print(f"[Alpha 35] Loaded XGBoost Models. Threshold={self.threshold}, Horizon={self.horizon}")

    def predict_from_input(self, model_input: ModelInput) -> ModelOutput:
        df_hist = self._to_dataframe(model_input.history_candles)
        if df_hist.empty or len(df_hist) < self.history_window:
            return ModelOutput("HOLD", 0.0, None, None, 0.0, "NoData", {})

        # 1. Compute Features
        feat_row = self._compute_features(df_hist)
        dmat = xgb.DMatrix(feat_row)
        p_up = float(self.xgb_up.predict(dmat)[0])
        p_down = float(self.xgb_down.predict(dmat)[0])

        current_price = float(model_input.price)
        position = model_input.position
        bars_held = model_input.bars_held

        # 2. Exit Logic (Time Exit)
        if position != 0:
            if bars_held >= self.horizon:
                # Time Exit triggered
                signal = "SELL" if position > 0 else "BUY"
                return ModelOutput(signal, 1.0, None, None, 1.0, "TimeExit", {"bars": bars_held})
            else:
                return ModelOutput("HOLD", 0.0, None, None, 0.0, "Holding", {"bars": bars_held})

        # 3. Entry Logic
        signal = "HOLD"
        sl = None
        confidence = max(p_up, p_down)
        tag = "Wait"

        if p_up > self.threshold:
            signal = "BUY"
            sl = current_price * (1 - self.sl_pct)
            tag = f"XGB_Buy({p_up:.2f})"
        elif p_down > self.threshold:
            signal = "SELL"
            sl = current_price * (1 + self.sl_pct)
            tag = f"XGB_Sell({p_down:.2f})"

        return ModelOutput(
            signal,
            1.0 if signal != "HOLD" else 0.0,
            sl,
            None, # No TP
            confidence,
            tag,
            {"p_up": p_up, "p_down": p_down}
        )

    # --- Helpers (Restored from v1 with WTI Support) ---
    def _load_feature_schema(self) -> Dict:
        schema_path = self.bundle_dir / "feature_schema.json"
        if schema_path.exists():
            return json.loads(schema_path.read_text())
        return {"feature_dim": 39}

    def _load_feature_stats(self) -> Optional[Dict[str, Dict[str, float]]]:
        stats_path = self.bundle_dir / "feature_stats.json"
        if stats_path.exists():
            return json.loads(stats_path.read_text())
        return None

    def _to_dataframe(self, history) -> pd.DataFrame:
        if isinstance(history, pd.DataFrame):
            return history.copy()
        return pd.DataFrame(history)

    def _compute_features(self, df_hist: pd.DataFrame) -> pd.DataFrame:
        if df_hist.empty:
            raise ValueError("history_candles is empty")
        expected_cols = self.feature_schema.get("feature_names") or []
        
        df_feat = self._ensure_features(df_hist.copy(), expected_cols)

        # Apply Standardization
        # CRITICAL: Skip standardization for absolute price/volume features
        # These features are outside training range due to price regime change
        # Only standardize relative features (returns, ratios, z-scores, etc.)
        SKIP_STANDARDIZE = {
            'open', 'high', 'low', 'close',  # Absolute prices
            'volume',  # Absolute volume
            'dxy_close', 'us10y_price', 'wti_close', 'gld_close',  # Macro absolute prices
            'zscore_close', 'zscore_log_ret',  # Already z-scored
            'rsi', 'cci', 'adx',  # Already normalized
            'hour_sin', 'hour_cos', 'session_state',  # Cyclic
            'volatility_ratio',  # Ratio
            'datetime'  # Non-numeric
        }
        
        # Apply Rolling Window Standardization for non-skipped features
        # This matches the training logic (generate_rl_dataset.py)
        WINDOW = 200
        for col in df_feat.columns:
            if col not in SKIP_STANDARDIZE and pd.api.types.is_numeric_dtype(df_feat[col]):
                # Rolling Z-Score
                roll_mean = df_feat[col].rolling(window=WINDOW, min_periods=50).mean()
                roll_std = df_feat[col].rolling(window=WINDOW, min_periods=50).std() + 1e-8
                df_feat[col] = (df_feat[col] - roll_mean) / roll_std
                # Fill NaNs (start of series) with 0.0
                df_feat[col] = df_feat[col].fillna(0.0)
        
        # Ensure all expected columns exist (fill 0 if missing after all attempts)
        for col in expected_cols:
            if col not in df_feat.columns:
                df_feat[col] = 0.0
        
        # Sanitize (Remove Inf/NaN)
        df_feat = df_feat.replace([np.inf, -np.inf], np.nan).fillna(0.0)
                
        last_row = df_feat.loc[:, expected_cols].iloc[[-1]].astype(np.float32)
        return last_row

    def _fetch_yf_series(self, ticker: str, start: pd.Timestamp, end: pd.Timestamp) -> Optional[pd.Series]:
        # Disable cache for live trading to ensure fresh data
        # if ticker in self._yf_cache: return self._yf_cache[ticker]
        
        try:
            # Download with buffer
            data = yf.download(ticker, start=start.date() - pd.Timedelta(days=5), end=end.date() + pd.Timedelta(days=1), progress=False, auto_adjust=False)
            if data.empty or "Close" not in data: return None
            series = data["Close"].copy()
            if isinstance(series, pd.DataFrame): series = series.iloc[:, 0] # Handle multi-index if any
            series.index = pd.to_datetime(series.index)
            # self._yf_cache[ticker] = series # Don't cache
            return series
        except: return None

    def _ensure_features(self, df: pd.DataFrame, expected_cols: List[str]) -> pd.DataFrame:
        if "datetime" not in df.columns: df["datetime"] = pd.to_datetime(df.index)
        df["datetime"] = pd.to_datetime(df["datetime"])
        df = df.sort_values("datetime").reset_index(drop=True)
        
        # FIX: Normalize volume to match training data scale
        # Training data has volume mean=0.64, std=0.50
        # But MT5 tick_volume is in thousands (e.g., 8775)
        # Divide by 10000 to bring it to the right scale
        if "volume" in df.columns:
            df["volume"] = df["volume"] / 10000.0
        
        # Basic Features
        df["log_ret"] = np.log(df["close"] / df["close"].shift()).replace([np.inf, -np.inf], np.nan)
        for c in ["open", "high", "low", "close"]:
            df[f"{c}_ret"] = np.log(df[c] / df[c].shift()).replace([np.inf, -np.inf], np.nan)
            
        # Time
        df["hour"] = df["datetime"].dt.hour
        df["hour_sin"] = np.sin(2 * np.pi * df["hour"] / 24.0)
        df["hour_cos"] = np.cos(2 * np.pi * df["hour"] / 24.0)
        df["session_state"] = pd.cut(df["hour"], bins=[-1, 7, 15, 23], labels=[0, 1, 2]).astype(int)

        # ZScore 96
        roll_mean = df["close"].rolling(96).mean()
        roll_std = df["close"].rolling(96).std() + 1e-8
        df["zscore_close"] = (df["close"] - roll_mean) / roll_std
        lr = df["log_ret"]
        df["zscore_log_ret"] = (lr - lr.rolling(96).mean()) / (lr.rolling(96).std() + 1e-8)

        # MACD (Convert to relative values)
        ema12 = df["close"].ewm(span=12, adjust=False).mean()
        ema26 = df["close"].ewm(span=26, adjust=False).mean()
        macd_abs = ema12 - ema26
        # De-absolutize: MACD as percentage of price
        df["macd"] = macd_abs / (df["close"] + 1e-8)
        df["macd_signal"] = df["macd"].ewm(span=9, adjust=False).mean()
        df["macd_hist"] = df["macd"] - df["macd_signal"]

        # RSI 14
        delta = df["close"].diff()
        gain = delta.clip(lower=0)
        loss = -delta.clip(upper=0)
        rs = gain.rolling(14).mean() / (loss.rolling(14).mean() + 1e-8)
        df["rsi"] = 100 - (100 / (1 + rs))

        # CCI 20
        tp = (df["high"] + df["low"] + df["close"]) / 3
        df["cci"] = (tp - tp.rolling(20).mean()) / (0.015 * (tp.rolling(20).apply(lambda x: np.mean(np.abs(x - np.mean(x)))) + 1e-8))

        # ATR 14 (Convert to relative: ATR as percentage of price)
        tr = pd.concat([df["high"]-df["low"], (df["high"]-df["close"].shift()).abs(), (df["low"]-df["close"].shift()).abs()], axis=1).max(axis=1)
        atr_abs = tr.rolling(14).mean()
        # De-absolutize: ATR as percentage of price
        df["atr"] = atr_abs / (df["close"] + 1e-8)

        # ADX 14
        up_move = df["high"].diff()
        down_move = -df["low"].diff()
        plus_dm = (up_move.where((up_move > down_move) & (up_move > 0), 0.0)).ewm(alpha=1/14).mean()
        minus_dm = (down_move.where((down_move > up_move) & (down_move > 0), 0.0)).ewm(alpha=1/14).mean()
        atr_ewm = tr.ewm(alpha=1/14).mean()
        dx = (abs(plus_dm - minus_dm) / (plus_dm + minus_dm + 1e-8)) * 100
        df["adx"] = dx.ewm(alpha=1/14).mean()

        # Volatility (already relative)
        df["vol_96"] = df["log_ret"].rolling(96).std()
        df["vol_288"] = df["log_ret"].rolling(288).std()
        df["volatility_ratio"] = df["volume"] / (df["volume"].rolling(96).mean() + 1e-8)

        # Macro/External (Fetch from YFinance if missing)
        macro_cols = ["dxy_close", "us10y_price", "wti_close", "gld_close"]
        ticker_map = {
            "dxy_close": "DX-Y.NYB",
            "us10y_price": "^TNX",
            "wti_close": "CL=F",
            "gld_close": "GLD"
        }
        
        missing = [c for c in macro_cols if c not in df.columns]
        if missing:
            start_dt = df["datetime"].min()
            end_dt = df["datetime"].max()
            
            # CRITICAL: Extend range to at least 120 days for 60-day rolling correlations
            min_start = end_dt - pd.Timedelta(days=120)
            if start_dt > min_start:
                start_dt = min_start

            for col in missing:
                ticker = ticker_map.get(col)
                if ticker:
                    series = self._fetch_yf_series(ticker, start_dt, end_dt)
                    if series is not None:
                        # Resample to Daily and forward fill to match M15 timestamps
                        ser_daily = series.resample('D').last().ffill()
                        # Map daily values to M15 dataframe based on date
                        df[col] = df["datetime"].dt.floor('D').map(ser_daily).ffill()
        
        # Macro Returns & Correlations
        if "dxy_close" in df.columns:
            df["dxy_close_ret"] = np.log(df["dxy_close"] / df["dxy_close"].shift()).replace([np.inf, -np.inf], 0)
            df["dxy_ret"] = df["dxy_close_ret"]
            
        if "us10y_price" in df.columns:
            df["us10y_price_ret"] = np.log(df["us10y_price"] / df["us10y_price"].shift()).replace([np.inf, -np.inf], 0)
            df["us10y_price_ret_pct"] = df["us10y_price"].pct_change().replace([np.inf, -np.inf], 0)

        if "wti_close" in df.columns:
             df["wti_close_ret"] = np.log(df["wti_close"] / df["wti_close"].shift()).replace([np.inf, -np.inf], 0)

        if "gld_close" in df.columns:
             df["gld_close_ret"] = np.log(df["gld_close"] / df["gld_close"].shift()).replace([np.inf, -np.inf], 0)

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
                    if len(common_dates) >= 60:
                        gold_aligned = gold_daily.loc[common_dates]
                        dxy_aligned = dxy_daily.loc[common_dates]
                        
                        # Calculate 60-day correlation
                        daily_corr = gold_aligned.rolling(60).corr(dxy_aligned).fillna(0)
                        
                        # Map to M15
                        df["corr_dxy_60"] = df["datetime"].dt.floor("D").map(daily_corr.to_dict()).fillna(method='ffill')
                        df["corr_close_dxy"] = df["corr_dxy_60"]

                    else:
                        df["corr_dxy_60"] = -0.05  # Use training mean
                        df["corr_close_dxy"] = -0.05
                else:
                     df["corr_dxy_60"] = -0.05
                     df["corr_close_dxy"] = -0.05
            else:
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
            else:
                df["corr_close_us10y_60"] = -0.02
                df["corr_close_us10y"] = -0.02

        # Fill remaining missing with 0
        for c in expected_cols:
            if c not in df.columns: df[c] = 0.0
            
        return df

def load_agent(bundle_dir: str) -> TradingAgent:
    return TradingAgent(bundle_dir=bundle_dir)
