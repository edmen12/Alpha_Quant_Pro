# Alpha 35: The "Pure XGBoost" Agent

## Overview
Alpha 35 is a high-performance trading agent based on a **Pure XGBoost** strategy, bypassing the PPO reinforcement learning layer. It directly utilizes the strong predictive power of the XGBoost models (AUC ~0.88) to generate trading signals.

## Performance
- **Backtest Sharpe Ratio**: **7.31** (2015-2024)
- **Verified Lower Bound**: **2.75** (Independent "Clean Room" Verification)
- **2025 Out-of-Sample**: **Profitable** (Verified with 2025 MT5 Data)

## Strategy Logic
- **Signal Source**: Dual XGBoost Classifiers (Up/Down) using 39 features (including WTI/Gold/Macro).
- **Entry Condition**: `Signal Probability > 0.6` (for either Up or Down).
- **Exit Conditions**:
    1.  **Time Exit**: Force close after **12 bars** (approx 3 hours).
    2.  **Stop Loss**: **0.2%** fixed percentage from entry price.
    3.  **Take Profit**: None (Rely on Time Exit).

## Configuration
- **Threshold**: 0.6 (Configurable in `agent.py`)
- **Horizon**: 12 bars
- **Stop Loss**: 0.002 (0.2%)

## Usage
Load this bundle using the standard `AgentFactory` or `load_agent` interface.
```python
from New_model.agent_bundle_alpha_35.agent import load_agent
agent = load_agent("path/to/New_model/agent_bundle_alpha_35")
output = agent.predict_from_input(model_input)
```

## Files
- `agent.py`: Core logic implementation.
- `models/`: Contains `xgb_up.json` and `xgb_down.json`.
- `feature_schema.json`: Defines the 39 input features.
- `feature_stats.json`: Normalization statistics (Mean/Std).
