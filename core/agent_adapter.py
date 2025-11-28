"""
Agent Bundle Adapter - Dynamically loads and wraps agent bundles
"""
import importlib.util
import logging
import sys
from pathlib import Path
from typing import Optional

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
    
    def predict(self, model_input: ModelInput) -> ModelOutput:
        """
        Call the agent's prediction method
        
        Args:
            model_input: Standardized input
            
        Returns:
            ModelOutput: Standardized output
        """
        if self._agent is None:
            raise RuntimeError("Agent not loaded")
        
        # Pattern 1: Agent has standardized predict() method
        if hasattr(self._agent, 'predict') and callable(getattr(self._agent, 'predict')):
            try:
                # Try calling with our ModelInput
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
                agent_input = agent_model_input_class(
                    timestamp=model_input.timestamp,
                    symbol=model_input.symbol,
                    timeframe=model_input.timeframe,
                    price=model_input.price,
                    history_candles=model_input.history_candles,
                    candle=model_input.candle,
                    position=model_input.position,
                    bars_held=model_input.bars_held,
                    open_trades=model_input.open_trades,
                    entry_price=model_input.entry_price or 0.0,
                    daily_pnl=model_input.daily_pnl,
                    daily_drawdown=model_input.daily_drawdown,
                    equity=model_input.equity,
                    balance=model_input.balance,
                    meta=model_input.meta
                )
                
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
