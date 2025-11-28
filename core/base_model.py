"""
Base Model Interface - All trading agents must implement this
"""
from abc import ABC, abstractmethod
from core.io_schema import ModelInput, ModelOutput


class BaseModel(ABC):
    """Abstract base class for all trading models"""
    
    @abstractmethod
    def predict(self, model_input: ModelInput) -> ModelOutput:
        """
        Main prediction method
        
        Args:
            model_input: Standardized input data
            
        Returns:
            ModelOutput: Trading signal and metadata
        """
        pass
    
    @abstractmethod
    def get_info(self) -> dict:
        """
        Return model metadata
        
        Returns:
            dict: Model name, version, description, etc.
        """
        pass
