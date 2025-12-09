import pandas as pd
import numpy as np
from datetime import datetime

class FeatureEngineerV2:
    """
    Alpha Prime V5 Feature Engineering (Phase 13 Hybrid).
    Matches 'generate_v5.py' logic exactly.
    Verified against Data Leakage Audit (Phase 15).
    """
    
    def __init__(self):
        # The exact feature output order expected by XGBoost model
        self.feature_cols = [
            'atr_14_pct', 'adx_14',          # Regime
            'price_pos_bb', 'bb_width_pct',  # Strategy
            'dist_sma200_pct', 'rsi_14',     # Strategy
            'log_ret_1', 'log_ret_5',        # Kinetic
            'hour_sin', 'hour_cos',          # Time
            'is_asia', 'is_ny',              # Time
            'h1_trend'                       # Context
        ]
        
    def process(self, df):
        # Expecting df with: datetime, open, high, low, close, volume (optional)
        df = df.copy()
        
        # 1. Standardize columns
        df.columns = [c.lower() for c in df.columns]
        rename_map = {}
        if 'time' in df.columns: rename_map['time'] = 'datetime'
        if 'tick_volume' in df.columns: rename_map['tick_volume'] = 'volume'
        if 'vol' in df.columns: rename_map['vol'] = 'volume'
        if rename_map: df.rename(columns=rename_map, inplace=True)
        
        # 2. Ensure Datetime
        if 'datetime' in df.columns:
            df['datetime'] = pd.to_datetime(df['datetime'])
            df = df.sort_values('datetime').reset_index(drop=True)
            
        # 3. Validation Check (Need sufficient bars)
        if len(df) < 200:
            # Not enough data for SMA 200
            # Return empty or partial?
            # Better to return empty to signal "Not Ready"
            return pd.DataFrame(), []
            
        close = df['close']
        high = df['high']
        low = df['low']
        
        # --- A. Volatility & Regime ---
        # ATR 14
        tr1 = high - low
        tr2 = abs(high - close.shift(1))
        tr3 = abs(low - close.shift(1))
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr_14 = tr.ewm(alpha=1/14, adjust=False).mean()
        df['atr_14_pct'] = (atr_14 / close) * 100
        
        # ADX 14
        up = high.diff()
        down = -low.diff()
        plus_dm = np.where((up > down) & (up > 0), up, 0.0)
        minus_dm = np.where((down > up) & (down > 0), down, 0.0)
        
        plus_dm_ewm = pd.Series(plus_dm).ewm(alpha=1/14, adjust=False).mean()
        minus_dm_ewm = pd.Series(minus_dm).ewm(alpha=1/14, adjust=False).mean()
        
        # Safety for division by zero
        tr_ewm = tr.ewm(alpha=1/14, adjust=False).mean()
        plus_di = 100 * (plus_dm_ewm / tr_ewm)
        minus_di = 100 * (minus_dm_ewm / tr_ewm)
        
        sum_di = plus_di + minus_di
        sum_di = sum_di.replace(0, 1e-9) # Avoid div zero
        
        dx = 100 * abs(plus_di - minus_di) / sum_di
        df['adx_14'] = dx.ewm(alpha=1/14, adjust=False).mean()
        
        # --- B. Strategy Logic ---
        # Bollinger Bands (20, 2.0)
        sma_20 = close.rolling(20).mean()
        std_20 = close.rolling(20).std()
        bb_upper = sma_20 + (2.0 * std_20)
        bb_lower = sma_20 - (2.0 * std_20)
        
        bb_range = bb_upper - bb_lower
        bb_range = bb_range.replace(0, 1e-9)
        
        df['price_pos_bb'] = (close - bb_lower) / bb_range
        df['bb_width_pct'] = (bb_range / sma_20) * 100
        
        # SMA 200 Dist
        sma_200 = close.rolling(200).mean()
        df['dist_sma200_pct'] = ((close - sma_200) / sma_200) * 100
        
        # RSI 14
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).fillna(0)
        loss = (-delta.where(delta < 0, 0)).fillna(0)
        
        avg_gain = gain.ewm(alpha=1/14, adjust=False).mean()
        avg_loss = loss.ewm(alpha=1/14, adjust=False).mean()
        
        rs = avg_gain / avg_loss.replace(0, 1e-9)
        df['rsi_14'] = 100 - (100 / (1 + rs))
        
        # Kinetic
        df['log_ret_1'] = np.log(close / close.shift(1))
        df['log_ret_5'] = np.log(close / close.shift(5))
        
        # --- C. Time Features ---
        df['hour'] = df['datetime'].dt.hour
        df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
        df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)
        df['is_asia'] = np.where(df['hour'].between(0, 8), 1, 0)
        df['is_ny'] = np.where(df['hour'].between(12, 20), 1, 0)
        
        # --- D. MTF Alignment (H1 Trend) ---
        # Robust Resampling using pandas 'resample' with ffill
        # df is M15. H1 is standard hours.
        # We need "Closed H1 Bar" status to avoid lookahead?
        # In generate_v5, we used standard resample.
        # Here we do the same for consistency with Model Training.
        
        try:
            df_h1 = df.set_index('datetime').resample('1h')['close'].last().to_frame()
            df_h1['h1_ema_50'] = df_h1['close'].ewm(span=50, adjust=False).mean()
            df_h1['h1_trend'] = np.where(df_h1['close'] > df_h1['h1_ema_50'], 1, -1)
            
            # Shift H1 data by 1 to prevent look-ahead bias
            # The '10:00' H1 bar contains data up to 11:00.
            # We must not see it at 10:15. We should see the '09:00' bar.
            df_h1 = df_h1.shift(1)
            
            # Map back to M15 (Forward Fill)
            # using merge_asof or reindex
            # Reindex with ffill propagates the last known H1 value to current M15 bars.
            # This is correct.
            h1_trend_mapped = df_h1['h1_trend'].reindex(df.set_index('datetime').index, method='ffill').values
            df['h1_trend'] = h1_trend_mapped
            
            # Debug Print (Last H1 row)
            # last_h1 = df_h1.iloc[-1]
            # print(f"[FE DEBUG] H1 Close: {last_h1['close']:.2f} | EMA50: {last_h1['h1_ema_50']:.2f} | Trend: {last_h1['h1_trend']}")
            
        except Exception as e:
            # Fallback (e.g. at start of history)
            # print(f"[FE DEBUG] H1 Trend Error: {e}")
            df['h1_trend'] = 0
            
        if 'h1_trend' in df.columns:
             latest = df.iloc[-1]
             # We can't access h1_ema_50 easily here as it is in df_h1 local var
             # But we can print from df_h1 before mapping
             pass
             
        # Fill NaNs generated by rolling/reindex
        # Usually dropna is safer for Inference to avoid Garbage In
        df_clean = df.dropna().reset_index(drop=True)
        
        return df_clean, self.feature_cols
