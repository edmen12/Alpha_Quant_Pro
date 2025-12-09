"""
Feature Engineering Module
Provides shared feature computation logic and base TradingAgent for agent bundles.
"""
import numpy as np
import pandas as pd
import logging
from core.base_model import BaseModel
from core.io_schema import ModelInput, ModelOutput

logger = logging.getLogger(__name__)

class TradingAgent(BaseModel):
    """
    Base Trading Agent class that implements the standard interface.
    This class is often extended or used directly by agent bundles.
    """
    
    def __init__(self, bundle_dir: str):
        self.bundle_dir = bundle_dir
        self.name = "GenericTradingAgent"
        
    def predict(self, model_input: ModelInput) -> ModelOutput:
        """
        Default prediction logic (placeholder).
        Real agents should override this or implement their own logic.
        """
        return ModelOutput(
            signal="HOLD",
            confidence=0.0,
            tag="default_hold"
        )
        
    def get_info(self) -> dict:
        return {
            "name": self.name,
            "type": "base_feature_engineering_agent",
            "version": "1.0.0"
        }

def compute_features(df: pd.DataFrame) -> np.ndarray:
    """
    Compute standard technical indicators/features.
    This is a shared utility often used by agents.
    """
    if df is None or df.empty:
        return np.array([])
        
    # Basic feature set (example)
    # 1. Returns
    df = df.copy()
    df['returns'] = df['close'].pct_change().fillna(0)
    
    # 2. Volatility
    df['volatility'] = df['returns'].rolling(20).std().fillna(0)
    
    # Return last row as features
    return df.iloc[-1][['returns', 'volatility']].values

class FeatureEngineerV2:
    """
    Feature Engineer V2 Class
    Provides backward compatibility for agents expecting this class.
    """
    def __init__(self):
        pass
        
    def compute_features(self, df: pd.DataFrame) -> np.ndarray:
        """
        Wrapper for the standalone compute_features function.
        """
        return compute_features(df)

    def process(self, df: pd.DataFrame):
        """
        Process DataFrame and return (df_processed, feature_cols)
        """
        if df is None or df.empty:
            return df, []
            
        df = df.copy()
        
        # Ensure standard columns
        if 'close' not in df.columns:
            return df, []
            
        # --- Feature Calculation ---
        close = df['close']
        high = df['high']
        low = df['low']
        volume = df['volume'] if 'volume' in df.columns else pd.Series(0, index=df.index)
        
        # 1. Log Returns
        df['log_ret'] = np.log(close / close.shift(1)).fillna(0)
        
        # 2. ATR Normalized
        tr1 = high - low
        tr2 = (high - close.shift(1)).abs()
        tr3 = (low - close.shift(1)).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(14).mean()
        df['atr_norm'] = (atr / close).fillna(0)
        
        # 3. MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        df['macd'] = ema12 - ema26
        df['macd_signal'] = df['macd'].ewm(span=9, adjust=False).mean()
        df['macd_hist'] = df['macd'] - df['macd_signal']
        
        # 4. Trends (Simple MA Crossover proxies)
        ma50 = close.rolling(50).mean()
        ma200 = close.rolling(200).mean()
        df['trend_short'] = (close / ma50 - 1).fillna(0)
        df['trend_long'] = (close / ma200 - 1).fillna(0)
        
        # 5. RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi'] = df['rsi'].fillna(50) / 100.0 # Normalize 0-1
        
        # 6. Bollinger Width
        bb_mid = close.rolling(20).mean()
        bb_std = close.rolling(20).std()
        df['bb_width'] = ((bb_mid + 2*bb_std) - (bb_mid - 2*bb_std)) / bb_mid
        df['bb_width'] = df['bb_width'].fillna(0)
        
        # 7. Time Features
        if 'datetime' in df.columns:
            dt = pd.to_datetime(df['datetime'])
            df['hour_sin'] = np.sin(2 * np.pi * dt.dt.hour / 24)
            df['hour_cos'] = np.cos(2 * np.pi * dt.dt.hour / 24)
            df['day_sin'] = np.sin(2 * np.pi * dt.dt.dayofweek / 7)
            df['day_cos'] = np.cos(2 * np.pi * dt.dt.dayofweek / 7)
        else:
            # Fallback if no datetime
            df['hour_sin'] = 0
            df['hour_cos'] = 0
            df['day_sin'] = 0
            df['day_cos'] = 0
            
        # 8. Volume Change
        df['vol_change'] = volume.pct_change().fillna(0)
        
        # Define feature columns in correct order
        feature_cols = [
            "log_ret", "atr_norm", "macd", "macd_signal", "macd_hist",
            "trend_long", "trend_short", "rsi", "bb_width",
            "hour_sin", "hour_cos", "day_sin", "day_cos", "vol_change"
        ]
        
        # Fill any remaining NaNs
        df[feature_cols] = df[feature_cols].fillna(0.0)
        
        return df, feature_cols

