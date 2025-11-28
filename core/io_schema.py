"""
Standardized Input/Output Schema for Trading Agents
Ensures compatibility across different agent bundles
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, List
import pandas as pd


@dataclass
class ModelInput:
    """Standard input format for all trading agents"""
    # Time & Symbol
    timestamp: datetime
    symbol: str
    timeframe: str
    price: float  # Current market price
    
    # Market Data
    history_candles: pd.DataFrame  # Historical OHLCV data
    candle: Dict[str, Any]  # Current candle as dict
    
    # Position State
    position: int = 0  # -1 (short), 0 (flat), 1 (long)
    bars_held: int = 0  # How many bars position has been held
    open_trades: int = 0  # Number of open positions
    entry_price: Optional[float] = None
    
    # Account State
    daily_pnl: float = 0.0
    daily_drawdown: float = 0.0
    equity: float = 0.0
    balance: float = 0.0
    
    # Optional Extensions
    meta: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelOutput:
    """Standard output format for all trading agents"""
    signal: str = "HOLD"  # "BUY" | "SELL" | "HOLD"
    size: float = 0.0  # Position size (0.0 - 1.0 or absolute lots)
    sl: Optional[float] = None  # Stop loss price
    tp: Optional[float] = None  # Take profit price
    confidence: float = 0.0  # Model confidence (0.0 - 1.0)
    tag: str = ""  # Strategy tag/reason
    extra: Dict[str, Any] = field(default_factory=dict)  # Additional info
