import unittest
from unittest.mock import MagicMock, patch
import sys
import os
import asyncio

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Mock mt5 before importing engine_core
sys.modules['MetaTrader5'] = MagicMock()
import MetaTrader5 as mt5

# Mock other dependencies
sys.modules['core'] = MagicMock()
sys.modules['news_calendar'] = MagicMock()
sys.modules['logger_setup'] = MagicMock()
sys.modules['database_manager'] = MagicMock()
sys.modules['performance_analyzer'] = MagicMock()

from engine_core import TradingEngine

class TestRiskManagement(unittest.TestCase):
    def setUp(self):
        self.engine = TradingEngine("dummy_bundle")
        self.engine.log = MagicMock()
        self.engine.send_alert = MagicMock()
        self.engine.close_all_positions = MagicMock()
        self.engine._run_blocking = AsyncMock() # Helper for async calls

    def test_max_daily_loss_trigger(self):
        """Test if Max Daily Loss triggers correctly"""
        self.engine.max_daily_loss = 100.0
        self.engine.min_equity = 0 # Disable equity guard for this test
        
        # Mock Account Info (Safe)
        mock_account = MagicMock()
        mock_account.equity = 10000
        mt5.account_info.return_value = mock_account
        
        # Mock Daily PnL to be LOSS of $150 (exceeds limit of $100)
        self.engine.get_daily_pnl = MagicMock(return_value=-150.0)
        
        # Run check
        result = asyncio.run(self.engine.check_risk_limits())
        
        # Assertions
        self.assertFalse(result, "Should return False (Stop Engine) when Max Daily Loss is hit")
        self.engine.close_all_positions.assert_called()
        self.engine.send_alert.assert_called()
        print("\n✅ Max Daily Loss Test Passed: Engine stopped and positions closed.")

    def test_equity_guard_trigger(self):
        """Test if Equity Guard triggers correctly"""
        self.engine.min_equity = 5000.0
        self.engine.max_daily_loss = 0 # Disable daily loss for this test
        
        # Mock Account Info (Below Min Equity)
        mock_account = MagicMock()
        mock_account.equity = 4000
        mt5.account_info.return_value = mock_account
        
        # Run check
        result = asyncio.run(self.engine.check_risk_limits())
        
        # Assertions
        self.assertFalse(result, "Should return False (Stop Engine) when Equity Guard is hit")
        self.engine.close_all_positions.assert_called()
        print("✅ Equity Guard Test Passed: Engine stopped and positions closed.")

    def test_normal_operation(self):
        """Test normal operation (no triggers)"""
        self.engine.max_daily_loss = 100.0
        self.engine.min_equity = 5000.0
        
        # Mock Account Info (Safe)
        mock_account = MagicMock()
        mock_account.equity = 10000
        mt5.account_info.return_value = mock_account
        
        # Mock Daily PnL (Safe)
        self.engine.get_daily_pnl = MagicMock(return_value=-50.0)
        
        # Run check
        result = asyncio.run(self.engine.check_risk_limits())
        
        # Assertions
        self.assertTrue(result, "Should return True (Continue) when limits are safe")
        self.engine.close_all_positions.assert_not_called()
        print("✅ Normal Operation Test Passed: Engine continues.")

# Helper for async mocks
class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        # If the first arg is a callable, call it
        if args and callable(args[0]):
            return args[0](*args[1:], **kwargs)
        return super().__call__(*args, **kwargs)

if __name__ == '__main__':
    unittest.main()
