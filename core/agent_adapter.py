"""
Agent Bundle Adapter - Dynamically loads and wraps agent bundles
"""
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional
import numpy as np
import pandas as pd

from core.base_model import BaseModel
from core.io_schema import ModelInput, ModelOutput
from core.dependency_manager import check_and_install_dependencies

logger = logging.getLogger(__name__)


class AgentBundleAdapter(BaseModel):
    """
    Adapter that wraps an agent bundle and exposes the BaseModel interface
    """
    
    def __init__(self, bundle_path: str):
        """
        Initialize adapter for a specific agent bundle
        
        Args:
            bundle_path: Path to agent bundle directory
        """
        self.bundle_path = Path(bundle_path)
        self.bundle_name = self.bundle_path.name
        self._agent = None
        self._agent_module = None
        
        logger.info(f"Initializing AgentBundleAdapter for '{self.bundle_name}'")
        
        # Check and install dependencies
        check_and_install_dependencies(self.bundle_path)
        
        # Load the agent
        self._load_agent()
    
    def _load_agent(self):
        """Dynamically load agent.py from bundle"""
        agent_file = self.bundle_path / "agent.py"
        
        if not agent_file.exists():
            raise FileNotFoundError(f"agent.py not found in {self.bundle_path}")
        
        # Create unique module name - use hash to avoid conflicts with bundle name
        import hashlib
        hash_suffix = hashlib.md5(str(self.bundle_path.absolute()).encode()).hexdigest()[:8]
        module_name = f"agent_module_{hash_suffix}"
        
        spec = importlib.util.spec_from_file_location(module_name, agent_file)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        self._agent_module = module
        
        # Try multiple loading patterns
        # Pattern 1: load_agent() function (our standard)
        if hasattr(module, 'load_agent'):
            self._agent = module.load_agent(str(self.bundle_path))
            logger.info(f"Successfully loaded agent via load_agent() from '{self.bundle_name}'")
        
        # Pattern 2: TradingAgent class (auto trade standard)
        elif hasattr(module, 'TradingAgent'):
            agent_class = getattr(module, 'TradingAgent')
            self._agent = agent_class(str(self.bundle_path))
            logger.info(f"Successfully loaded agent via TradingAgent class from '{self.bundle_name}'")
        
        # Pattern 3: AgentBundleModel class (another variant)
        elif hasattr(module, 'AgentBundleModel'):
            agent_class = getattr(module, 'AgentBundleModel')
            self._agent = agent_class(str(self.bundle_path))
            logger.info(f"Successfully loaded agent via AgentBundleModel class from '{self.bundle_name}'")
        
        else:
            raise AttributeError(
                f"Module '{module_name}' does not have 'load_agent' function, "
                f"'TradingAgent' class, or 'AgentBundleModel' class. "
                f"Please ensure your agent.py implements one of these patterns."
            )
    
    def _compute_features_v7(self, df: pd.DataFrame) -> np.ndarray:
        """
        Compute features for AI_MODEL_V7 based on feature_schema.json
        """
        # Ensure sufficient data
        if len(df) < 50:
            logger.warning(f"Insufficient data for V7 features: {len(df)} < 50")
            return np.zeros(17, dtype=np.float32)
            
        logger.info(f"Computing V7 features for {len(df)} bars")
        df = df.copy()
        close = df['close']
        
        # 1. Returns
        df['returns'] = close.pct_change()
        df['log_returns'] = np.log(close / close.shift(1))
        
        # 2. RSI (14)
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        df['rsi_normalized'] = df['rsi'] / 100.0
        
        # 3. MACD (12, 26, 9)
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        macd = ema12 - ema26
        signal = macd.ewm(span=9, adjust=False).mean()
        df['macd_hist_normalized'] = macd - signal # Raw hist for now
        
        # 4. ATR (14)
        high = df['high']
        low = df['low']
        prev_close = close.shift(1)
        tr1 = high - low
        tr2 = (high - prev_close).abs()
        tr3 = (low - prev_close).abs()
        tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        atr = tr.rolling(window=14).mean()
        df['atr_pct'] = atr / close
        
        # 5. Volatility
        df['volatility_10'] = df['returns'].rolling(10).std()
        df['volatility_20'] = df['returns'].rolling(20).std()
        
        # 6. Trend
        sma10 = close.rolling(10).mean()
        sma20 = close.rolling(20).mean()
        df['trend_10_20'] = (sma10 / sma20) - 1.0
        
        # 7. Momentum
        df['momentum_5'] = close / close.shift(5) - 1.0
        df['momentum_10'] = close / close.shift(10) - 1.0
        
        # 8. Price Position
        roll_min = close.rolling(10).min()
        roll_max = close.rolling(10).max()
        df['price_position_10'] = (close - roll_min) / (roll_max - roll_min + 1e-9)
        
        # 9. Time
        df['hour'] = df.index.hour
        df['dayofweek'] = df.index.dayofweek
        df['month'] = df.index.month
        df['quarter'] = df.index.quarter
        
        # 10. Price Month Norm (Approx 20 days)
        sma20 = close.rolling(20).mean()
        df['price_month_normalized'] = close / sma20
        
        # Select features in order
        features = [
            "returns", "log_returns", "rsi", "rsi_normalized", "macd_hist_normalized",
            "atr_pct", "volatility_10", "volatility_20", "trend_10_20",
            "momentum_5", "momentum_10", "price_position_10",
            "hour", "dayofweek", "month", "quarter", "price_month_normalized"
        ]
        
        # Get last row
        last_row = df.iloc[-1][features].fillna(0.0).values.astype(np.float32)
        return last_row

    def predict(self, model_input: ModelInput) -> ModelOutput:
        """
        Call the agent's prediction method
        """
        if self._agent is None:
            raise RuntimeError("Agent not loaded")
            
        computed_features = None
        
        # Compatibility: Compute features if missing and V7
        if (getattr(model_input, 'features', None) is None or np.all(getattr(model_input, 'features', []) == 0)) and "V7" in self.bundle_name:
             if model_input.history_candles is not None and not model_input.history_candles.empty:
                 try:
                     computed_features = self._compute_features_v7(model_input.history_candles)
                     # Try to attach to model_input for Pattern 1 (if supported)
                     try:
                         model_input.features = computed_features
                     except:
                         pass
                 except Exception as e:
                     logger.error(f"Failed to compute V7 features: {e}")

        # Pattern 1: Agent has standardized predict() method
        if hasattr(self._agent, 'predict') and callable(getattr(self._agent, 'predict')):
            try:
                # Try calling with our ModelInput
                # If V7, predict(features, price...) might be called if we pass features directly?
                # But standardized predict usually takes ModelInput.
                # If V7 agent.predict signature is (features, price...), calling it with ModelInput will fail TypeError.
                output = self._agent.predict(model_input)
                
                # If output is already ModelOutput, return it
                if isinstance(output, ModelOutput):
                    return output
                
                # Otherwise try to convert it
                return ModelOutput(
                    signal=getattr(output, 'signal', getattr(output, 'action', 'HOLD')),
                    size=getattr(output, 'size', 0.0),
                    sl=getattr(output, 'sl', None),
                    tp=getattr(output, 'tp', None),
                    confidence=getattr(output, 'confidence', 0.0),
                    tag=getattr(output, 'tag', ''),
                    extra=getattr(output, 'extra', {})
                )
            except TypeError:
                # predict() might need agent's own ModelInput format
                pass
        
        # Pattern 2: Legacy predict_from_input() method (our old agents)
        if hasattr(self._agent, 'predict_from_input'):
            # Need to convert to agent's expected format
            agent_model_input_class = getattr(self._agent_module, 'ModelInput', None)
            
            if agent_model_input_class:
                # Convert our standardized input to agent's expected format
                # Check if agent input supports 'features'
                kwargs = {
                    "timestamp": model_input.timestamp,
                    "symbol": model_input.symbol,
                    "timeframe": model_input.timeframe,
                    "price": model_input.price,
                    "position": model_input.position,
                    "bars_held": model_input.bars_held,
                    "open_trades": model_input.open_trades,
                    "entry_price": model_input.entry_price or 0.0,
                    "daily_pnl": model_input.daily_pnl,
                    "daily_drawdown": model_input.daily_drawdown,
                    "equity": model_input.equity,
                    "balance": model_input.balance,
                    "meta": model_input.meta,
                    "candle": model_input.candle
                }
                
                # Add history_candles only if supported (legacy)
                # Add features if supported (V7)
                import inspect
                sig = inspect.signature(agent_model_input_class)
                if 'history_candles' in sig.parameters:
                    kwargs['history_candles'] = model_input.history_candles
                if 'features' in sig.parameters:
                    # Use computed features if available
                    if computed_features is not None:
                        kwargs['features'] = computed_features
                    elif hasattr(model_input, 'features'):
                         kwargs['features'] = model_input.features
                    else:
                         kwargs['features'] = None

                agent_input = agent_model_input_class(**kwargs)
                
                output = self._agent.predict_from_input(agent_input)
                
                # Convert output to standardized format
                return ModelOutput(
                    signal=output.signal,
                    size=output.size,
                    sl=output.sl,
                    tp=output.tp,
                    confidence=getattr(output, 'confidence', 0.0),
                    tag=output.tag,
                    extra=getattr(output, 'extra', {})
                )
        
        raise NotImplementedError(
            f"Agent in '{self.bundle_name}' does not implement predict() or predict_from_input()"
        )
    
    def get_info(self) -> dict:
        """Return bundle metadata"""
        info = {
            "bundle_name": self.bundle_name,
            "bundle_path": str(self.bundle_path),
            "agent_type": type(self._agent).__name__ if self._agent else "Unknown"
        }
        
        # Try to load additional metadata from bundle
        config_file = self.bundle_path / "agent_config.json"
        if config_file.exists():
            import json
            with open(config_file, 'r') as f:
                config = json.load(f)
                info.update(config)
        
        return info
