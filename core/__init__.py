"""
Core package initialization
"""
from core.io_schema import ModelInput, ModelOutput
from core.base_model import BaseModel
from core.agent_adapter import AgentBundleAdapter
from core.dependency_manager import check_and_install_dependencies

__all__ = [
    'ModelInput',
    'ModelOutput',
    'BaseModel',
    'AgentBundleAdapter',
    'check_and_install_dependencies'
]
