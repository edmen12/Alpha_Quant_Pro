import os
import sys
import json
import pandas as pd
import numpy as np
import xgboost as xgb
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Optional

# Import V5 Feature Engineering
try:
    from .feature_engineering import FeatureEngineerV2
except ImportError:
    from feature_engineering import FeatureEngineerV2

@dataclass
class ModelInput:
    timestamp: datetime
    symbol: str
    timeframe: str
    price: float
    history_candles: List[Dict] | pd.DataFrame
    candle: Dict
    position: int          # 0=Flat, 1=Long, -1=Short
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
    signal: str            # "BUY" / "SELL" / "HOLD"
    size: float            # Lots
    sl: Optional[float]
    tp: Optional[float]
    confidence: float
    tag: str
    extra: Dict

class TradingAgent:
    def __init__(self, bundle_dir: str):
        """
        Alpha Prime V5 Agent (Hybrid + Trailing Stop)
        """
        self.bundle_dir = bundle_dir
        self.booster = None
        
        # Load Configs
        try:
            with open(os.path.join(bundle_dir, "agent_config.json"), 'r') as f:
                self.config = json.load(f)
            with open(os.path.join(bundle_dir, "risk_manager.json"), 'r') as f:
                self.risk_config = json.load(f)
        except Exception as e:
            print(f"Config Load Error: {e}")
            self.config = {}
            self.risk_config = {}

        # Load XGBoost Model
        model_filename = self.config.get("components", {}).get("model", "model_v5_hybrid.json")
        model_path = os.path.join(bundle_dir, model_filename)
        print(f"Loading Agent Model V5 from: {model_path}")
        
        try:
            self.booster = xgb.Booster()
            self.booster.load_model(model_path)
            print("✅ XGBoost V5 Loaded Successfully")
        except Exception as e:
            print(f"❌ Model Load Failed: {e}")
            
        # Initialize Logic Components
        self.fe = FeatureEngineerV2()
        self.sl_state = {}     # {symbol: current_sl_price}
        self.peak_price = {}   # {symbol: highest_price_seen_in_trade}
        self.trough_price = {} # {symbol: lowest_price_seen_in_trade}

    def predict_from_input(self, model_input: ModelInput) -> ModelOutput:
        """
        Main V5 Execution Logic
        """
        sym = model_input.symbol
        price = model_input.price
        
        # 0. Safety Guards
        # Hard Stop Failsafe (if SL missing on server side)
        # 50 points distance approx
        if model_input.position != 0:
            if model_input.position == 1:
                dist = price - model_input.entry_price
                if dist < -50.0:  # Hard SL hit
                    return self._close(sym, "HARD_SL_HIT")
            else:
                dist = model_input.entry_price - price
                if dist < -50.0:
                    return self._close(sym, "HARD_SL_HIT")

        # 1. Feature Engineering
        # print(f"[AGENT DEBUG] history_candles type: {type(model_input.history_candles)}")
        if hasattr(model_input.history_candles, 'shape'):
             pass
             # print(f"[AGENT DEBUG] history_candles shape: {model_input.history_candles.shape}")
             # print(f"[AGENT DEBUG] history_candles columns: {list(model_input.history_candles.columns)}")
        if isinstance(model_input.history_candles, list):
            df = pd.DataFrame(model_input.history_candles)
        else:
            df = model_input.history_candles.copy()
            
        df_processed, feature_cols = self.fe.process(df)
        
        if df_processed.empty:
             return self._hold("WAIT_DATA", 0, 0, 0)
             
        # Extract Logic Variables
        latest_row = df_processed.iloc[-1]
        
        # Features for Model
        try:
            # Create DMatrix for single row
            feat_vector = df_processed.iloc[[-1]][feature_cols]
            dtest = xgb.DMatrix(feat_vector)
            probs = self.booster.predict(dtest)
            
            # Extract Probabilities
            # multi:softprob returns [p0, p1, p2]
            if len(probs.shape) == 1:
                p_hold, p_buy, p_sell = probs
            else:
                p_hold, p_buy, p_sell = probs[0]
                
        except Exception as e:
            print(f"Prediction Error: {e}")
            return self._hold(f"PREDICT_ERR_{str(e)[:10]}", 0, 0, 0)
            
        # Logic Variables
        h1_trend = latest_row.get('h1_trend', 0)
        atr_pct = latest_row.get('atr_14_pct', 0.2)
        atr_val = (atr_pct / 100.0) * price # Convert % to Price Distance
        
        # print(f"[AGENT DEBUG] {sym} | P_HOLD={p_hold:.2f} P_BUY={p_buy:.2f} P_SELL={p_sell:.2f} | H1_TREND={h1_trend} | ATR={atr_pct:.2f}%")
        
        # Parameters (Phase 14/15 Optimized)
        threshold = 0.50
        sl_mult = 2.0    # Initial SL
        activ_mult = 1.0 # Activation Trail
        trail_mult = 1.5 # Trail Dist
        
        # State Cleanups
        if model_input.position == 0:
            if sym in self.sl_state: del self.sl_state[sym]
            if sym in self.peak_price: del self.peak_price[sym]
            if sym in self.trough_price: del self.trough_price[sym]
            
        # -----------------------------------------------------------
        # LOGIC CORE: Hybrid Ensemble (Model + Filters)
        # -----------------------------------------------------------
        
        # A. Trailing Stop Management (Priority 1)
        sl_price = None
        
        if model_input.position != 0:
            # Default to existing state or init
            if sym not in self.sl_state:
                # Recover State based on entry
                if model_input.position == 1:
                    self.sl_state[sym] = model_input.entry_price - (sl_mult * atr_val)
                    self.peak_price[sym] = price
                else:
                    self.sl_state[sym] = model_input.entry_price + (sl_mult * atr_val)
                    self.trough_price[sym] = price
            
            current_sl = self.sl_state[sym]
            
            # Trailing Update Logic
            if model_input.position == 1:
                # Update Peak
                if price > self.peak_price.get(sym, 0):
                    self.peak_price[sym] = price
                
                peak = self.peak_price[sym]
                profit_dist = peak - model_input.entry_price
                
                # Check Activation
                if profit_dist > (activ_mult * atr_val):
                    # Qualified to Trail
                    new_sl = peak - (trail_mult * atr_val)
                    if new_sl > current_sl:
                        current_sl = new_sl # Move SL up
                        self.sl_state[sym] = current_sl
                        
            elif model_input.position == -1:
                # Update Trough
                if price < self.trough_price.get(sym, 999999):
                    self.trough_price[sym] = price
                    
                trough = self.trough_price[sym]
                profit_dist = model_input.entry_price - trough
                
                if profit_dist > (activ_mult * atr_val):
                    new_sl = trough + (trail_mult * atr_val)
                    if new_sl < current_sl:
                        current_sl = new_sl # Move SL down
                        self.sl_state[sym] = current_sl
            
            # Set SL for Output
            sl_price = current_sl
            
            # --- Active Exit via Signal? ---
            # V5 Logic: Trend Following rarely uses Counter-Signal Exit unless H1 reverses?
            # Model Logic: If we are Long, and H1 flips to -1, AND p_sell > threshold -> REVERSE.
            # Let's keep it simple: Only Trailing Stop Exit or explicit Reversal Signal.
            
            # Reversal Check
            if model_input.position == 1:
                if p_sell > threshold and h1_trend == -1:
                     return self._signal("SELL", self._calc_size(model_input), None, "REVERSAL_SHORT", extra={"p":float(p_sell)})
            elif model_input.position == -1:
                if p_buy > threshold and h1_trend == 1:
                    return self._signal("BUY", self._calc_size(model_input), None, "REVERSAL_LONG", extra={"p":float(p_buy)})
            
            # Otherwise HOLD (Let Trailing Stop work)
            return self._signal("HOLD", 0.0, sl_price, "TRAILING", extra={"sl": sl_price})

        # B. Entry Logic (Priority 2)
        if model_input.position == 0:
            
            # Long Setup
            if p_buy > threshold:
                # H1 Trend Filter (The Shield)
                if h1_trend == 1:
                    # Execute BUY
                    size = self._calc_size(model_input)
                    sl_dist = sl_mult * atr_val
                    init_sl = price - sl_dist
                    self.sl_state[sym] = init_sl
                    self.peak_price[sym] = price
                    
                    return self._signal("BUY", size, init_sl, "V5_TREND_LONG", extra={"p":float(p_buy)})
                
            # Short Setup
            if p_sell > threshold:
                # H1 Trend Filter
                if h1_trend == -1:
                    # Execute SELL
                    size = self._calc_size(model_input)
                    sl_dist = sl_mult * atr_val
                    init_sl = price + sl_dist
                    self.sl_state[sym] = init_sl
                    self.trough_price[sym] = price
                    
                    return self._signal("SELL", size, init_sl, "V5_TREND_SHORT", extra={"p":float(p_sell)})
        # Default Hold
        return self._hold("WAIT_SIGNAL", p_hold, p_buy, p_sell)


    # --- Helpers ---
    
    def _calc_size(self, input_data: ModelInput) -> float:
        """
        Calculate Lot Size based on Risk Manager (0.1 per 10k)
        """
        equity = input_data.equity
        # Rule: 0.1 Lot per $10,000
        # Multiplier = 0.1 / 10000 = 0.00001
        
        base_lots = equity * 0.00001
        
        # Clamp
        base_lots = max(0.01, round(base_lots, 2))
        base_lots = min(5.0, base_lots)
        
        return base_lots

    def _hold(self, reason, p_hold=0.0, p_buy=0.0, p_sell=0.0):
        return ModelOutput("HOLD", 0.0, None, None, 0.0, reason, {
            "p_up": float(p_buy),
            "p_down": float(p_sell),
            "p_hold": float(p_hold)
        })
        
    def _close(self, sym, reason):
        # To close, we send opposite signal? Or just flat?
        # Agent interface usually implies Target State.
        # But 'signal' field is "BUY"/"SELL"/"HOLD". 
        # Usually Engine handles exits. 
        # If we return "SELL" when Long -> Close Long (and OPEN Short if size > 0).
        # We want to Close Only. 
        # We can return size=0.0 with signal? No.
        # Let's assume Engine closes if we signal opposite with logic.
        # Actually simplest is to send "flat" command if supported?
        # Looking at original code:
        # if target_state=0 -> SEND "SELL" (if Long). tag="CLOSE_LONG".
        return ModelOutput("CLOSE", 0.0, None, None, 1.0, reason, {})

    def _signal(self, sig, size, sl, tag, extra=None):
        return ModelOutput(sig, size, sl, None, 1.0, tag, extra if extra else {})
