import os
import sys
from pathlib import Path

class PathManager:
    """
    Centralized path management for Industry-Grade Architecture.
    Handles separation of Read-Only Program Files and Read-Write AppData.
    """
    
    APP_NAME = "Alpha Quant Pro"
    
    @staticmethod
    def is_production():
        """Check if running in production mode"""
        # Check for environment variable set by launcher or compiled state
        return os.environ.get("ALPHA_QUANT_PROD") == "1" or getattr(sys, 'frozen', False)

    @staticmethod
    def get_app_data_dir():
        """Get writable AppData/Roaming directory for config/models"""
        if PathManager.is_production():
            path = Path(os.getenv('APPDATA')) / PathManager.APP_NAME
        else:
            # Development: Use local directory
            path = Path.cwd()
        
        path.mkdir(parents=True, exist_ok=True)
        return path

    @staticmethod
    def get_local_data_dir():
        """Get writable AppData/Local directory for logs/cache"""
        if PathManager.is_production():
            path = Path(os.getenv('LOCALAPPDATA')) / PathManager.APP_NAME
        else:
            # Development: Use local directory
            path = Path.cwd()
            
        path.mkdir(parents=True, exist_ok=True)
        return path
        
    @staticmethod
    def get_config_path():
        return PathManager.get_app_data_dir() / "configs" / "terminal_config.json"
        
    @staticmethod
    def get_logs_dir():
        return PathManager.get_local_data_dir() / "logs"
        
    @staticmethod
    def get_models_dir():
        return PathManager.get_app_data_dir() / "models"

    @staticmethod
    def get_database_path():
        return PathManager.get_app_data_dir() / "workspace" / "terminal_data.db"
