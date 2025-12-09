
import unittest
import sys
import os
import shutil
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock MT5
sys.modules["MetaTrader5"] = MagicMock()
import MetaTrader5 as mt5
mt5.initialize.return_value = True
mt5.terminal_info.return_value = MagicMock(name="AlphaTerm")
mt5.account_info.return_value = MagicMock(balance=10000, equity=10000)

# Setup Temp Environment for Logging
test_env = os.environ.copy()
temp_dir = tempfile.mkdtemp()
test_env["LOCALAPPDATA"] = temp_dir
print(f"DEBUG: Using Temp LOCALAPPDATA: {temp_dir}")

# Apply Patch and Import
try:
    with patch.dict(os.environ, test_env):
        from config_manager import ConfigManager
        from database_manager import DatabaseManager
        from feature_engineering import FeatureEngineerV2 as FeatureEngineer
        from core.agent_adapter import AgentBundleAdapter
        from terminal_apple import TerminalApple
        from engine_core import TradingEngine
except Exception as e:
    with open("error.log", "w") as f:
        import traceback
        traceback.print_exc(file=f)
    print(f"CRITICAL IMPORT ERROR: {e}")
    sys.exit(1)

print("Modules Imported Successfully.")

class TestFullSystem(unittest.TestCase):
    
    @classmethod
    def setUpClass(cls):
        pass

    def test_01_config_manager(self):
        """Test Config Read/Write"""
        print("\n[TEST] Config Manager...")
        cm = ConfigManager()
        config = cm.load()
        self.assertIsInstance(config, dict)
        print("  -> Config Structure OK")

    def test_02_database_manager(self):
        """Test Database Initialization"""
        print("\n[TEST] Database Manager...")
        # Point to memory or temp DB to avoid conflicts
        db = DatabaseManager(db_name=":memory:")
        db.create_tables()
        print("  -> DB Schema Checked")

    def test_03_engine_instantiation(self):
        """Test Trading Engine"""
        print("\n[TEST] Trading Engine...")
        engine = TradingEngine("dummy_bundle", symbols=["XAUUSD"])
        self.assertEqual(engine.lot_size, 0.01)
        print("  -> Engine Initialized OK")

    @patch("terminal_apple.ctk.CTk.mainloop", return_value=None)
    def test_04_ui_initialization(self, mock_loop):
        """Test UI Structure (Headless)"""
        print("\n[TEST] UI Initialization...")
        with patch.dict(os.environ, test_env): # Apply env patch again for runtime access if needed
            app = TerminalApple()
            app.withdraw()
            self.assertIn("dashboard", app.views)
            app.destroy()
        print("  -> UI Views Verified")

    def test_05_agent_adapter(self):
        """Test Agent Adapter"""
        print("\n[TEST] Agent Adapter...")
        self.assertTrue(hasattr(AgentBundleAdapter, "predict"))
        print("  -> Adapter Interface OK")

if __name__ == '__main__':
    unittest.main(verbosity=0)
