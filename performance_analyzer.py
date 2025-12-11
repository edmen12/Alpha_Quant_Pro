"""
Performance Analyzer Module
Calculates key trading performance metrics from MT5 history.
"""
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class PerformanceAnalyzer:
    """
    绩效分析器 (Performance Analyzer)
    
    负责从 MT5 历史数据中计算关键交易指标，用于评估策略表现。
    包含：胜率、盈亏比、夏普比率、最大回撤、平均持仓时间等。
    """
    def __init__(self, symbol=None, mt5_path=None):
        """
        Initialize Performance Analyzer
        
        Args:
            symbol: Trading symbol (default: None = All Symbols)
            mt5_path: Path to MT5 terminal (optional)
        """
        self.symbol = symbol
        self.mt5_path = mt5_path
        
    def get_trade_history(self, days=30):
        """
        Get closed trades from MT5 history
        
        Args:
            days: Number of days to look back (default: 30)
            
        Returns:
            List of trade dictionaries
        """
        try:
            if not mt5.terminal_info():
                # Try to initialize with specific path if provided
                if self.mt5_path:
                    if not mt5.initialize(path=self.mt5_path):
                        logger.warning(f"MT5 init failed with path: {self.mt5_path}")
                        return []
                else:
                    # Try default init
                    if not mt5.initialize():
                        logger.warning("MT5 not connected and initialize failed")
                        return []
            
            from_date = datetime.now() - timedelta(days=days)
            # Use 'tomorrow' as end date to handle Broker Time > Local Time issues
            to_date = datetime.now() + timedelta(days=1)
            deals = mt5.history_deals_get(from_date, to_date)
            
            if not deals:
                return []
            
            trades = []
            for d in deals:
                # Only OUT deals (closing trades)
                if d.entry == mt5.DEAL_ENTRY_OUT:
                    # Filter by symbol if specified
                    # if self.symbol and d.symbol != self.symbol:
                    #     continue
                        
                    # Filter out non-trading deals (Balance, Credit, etc.)
                    if d.type not in [0, 1]: # 0=BUY, 1=SELL
                        continue

                    trades.append({
                        'ticket': d.ticket,
                        'time': datetime.fromtimestamp(d.time),
                        # Logic Inverted: A closing SELL deal (1) means the position was a BUY.
                        # A closing BUY deal (0) means the position was a SELL.
                        'type': 'SELL' if d.type == 0 else 'BUY',
                        'volume': d.volume,
                        'price': d.price,
                        'profit': d.profit,
                        'commission': d.commission,
                        'swap': d.swap,
                        'symbol': d.symbol
                    })
                    logger.info(f"History Debug: Ticket={d.ticket}, Type={d.type} (0=Buy,1=Sell), Entry={d.entry}, Mapped={'SELL' if d.type == 0 else 'BUY'}")
            
            return trades
            
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            return []
    
    def calculate_win_rate(self, trades):
        """
        计算胜率 (Win Rate)
        
        公式: 盈利交易数 / 总交易数 * 100%
        
        Args:
            trades: 交易记录列表
            
        Returns:
            float: 胜率 (0-100)
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for t in trades if t['profit'] > 0)
        return (winning_trades / len(trades)) * 100
    
    def calculate_profit_factor(self, trades):
        """
        计算盈亏比 (Profit Factor)
        
        公式: 总盈利金额 / 总亏损金额绝对值
        
        Args:
            trades: 交易记录列表
            
        Returns:
            float: 盈亏比 (通常 > 1.5 为优秀)
        """
        if not trades:
            return 0.0
        
        gross_profit = sum(t['profit'] for t in trades if t['profit'] > 0)
        gross_loss = abs(sum(t['profit'] for t in trades if t['profit'] < 0))
        
        if gross_loss == 0:
            return float('inf') if gross_profit > 0 else 0.0
            
        return gross_profit / gross_loss

    def calculate_sharpe_ratio(self, trades, risk_free_rate=0.0):
        """
        计算夏普比率 (Sharpe Ratio) - 基于日收益
        
        公式: (平均日收益 - 无风险利率) / 日收益标准差 * sqrt(252)
        
        Args:
            trades: 交易记录列表
            risk_free_rate: 年化无风险利率 (默认: 0)
            
        Returns:
            float: 夏普比率
        """
        if not trades:
            return 0.0
            
        try:
            # Convert to DataFrame
            df = pd.DataFrame(trades)
            if df.empty or 'time' not in df.columns or 'profit' not in df.columns:
                return 0.0
                
            # Ensure time is datetime
            df['time'] = pd.to_datetime(df['time'])
            
            # Group by Date to get Daily PnL
            daily_pnl = df.groupby(df['time'].dt.date)['profit'].sum()
            
            if len(daily_pnl) < 2:
                return 0.0
                
            # Calculate Sharpe on Daily PnL
            mean_daily_return = daily_pnl.mean()
            std_daily_return = daily_pnl.std()
            
            if std_daily_return == 0:
                return 0.0
                
            return (mean_daily_return - risk_free_rate) / std_daily_return * np.sqrt(252)
            
        except Exception as e:
            logger.error(f"Sharpe Calc Error: {e}")
            return 0.0
    
    def calculate_max_drawdown(self, trades, initial_balance=0.0):
        """
        计算最大回撤 (Max Drawdown)
        
        逻辑:
        1. 构建资金曲线 (Equity Curve)
        2. 计算每个点的回撤: (当前净值 - 历史最高净值) / 历史最高净值
        3. 取最大值 (绝对值)
        
        Args:
            trades: 交易记录列表 (按时间排序)
            initial_balance: 初始资金 (默认: 0.0)
            
        Returns:
            float: 最大回撤百分比 (例如 15.5 代表 15.5%)
        """
        if not trades:
            return 0.0
        
        # Build equity curve starting from initial_balance
        equity = [initial_balance]
        for t in sorted(trades, key=lambda x: x['time']):
            equity.append(equity[-1] + t['profit'])
        
        # Calculate drawdown
        peak = equity[0]
        max_dd = 0
        
        for value in equity:
            if value > peak:
                peak = value
            
            if peak > 0:
                dd = (peak - value) / peak * 100
            else:
                # If peak is <= 0 (e.g. account in debt), drawdown is undefined or 0
                dd = 0
                
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def calculate_avg_trade_duration(self, days=30):
        """
        Calculate average trade duration in hours
        
        Args:
            days: Number of days to analyze
            
        Returns:
            float: Average duration in hours
        """
        try:
            if not mt5.terminal_info():
                return 0.0
            
            from_date = datetime.now() - timedelta(days=days)
            deals = mt5.history_deals_get(from_date, datetime.now())
            
            if not deals:
                return 0.0
            
            # Group deals by position ticket
            positions = {}
            for d in deals:
                if d.symbol != self.symbol:
                    continue
                    
                pos_id = d.position_id
                if pos_id not in positions:
                    positions[pos_id] = []
                positions[pos_id].append(d)
            
            # Calculate durations
            durations = []
            for pos_deals in positions.values():
                if len(pos_deals) < 2:
                    continue
                    
                entry_time = min(d.time for d in pos_deals)
                exit_time = max(d.time for d in pos_deals)
                duration = (exit_time - entry_time) / 3600  # Convert to hours
                durations.append(duration)
            
            return np.mean(durations) if durations else 0.0
            
        except Exception as e:
            logger.error(f"Failed to calculate avg duration: {e}")
            return 0.0
    
    def get_equity_curve(self, days=30, trades_list=None):
        """
        获取资金曲线数据 (Equity Curve Data)
        
        Args:
            days: 分析天数
            trades_list: Optional list of trades to analyze (overrides internal fetch)
            
        Returns:
            dict: {'times': [时间列表], 'equity': [累计盈亏列表]}
        """
        trades = trades_list if trades_list is not None else self.get_trade_history(days)
        
        if not trades:
            return {'times': [], 'equity': []}
        
        # Sort by time
        trades_sorted = sorted(trades, key=lambda x: x['time'])
        
        # Build cumulative equity
        times = []
        equity = []
        cumulative = 0
        
        for t in trades_sorted:
            times.append(t['time'])
            cumulative += t['profit']
            equity.append(cumulative)
        
        return {'times': times, 'equity': equity}
    
    def get_all_metrics(self, days=30, trades_list=None):
        """
        Get all performance metrics
        
        Args:
            days: Number of days to analyze
            trades_list: Optional list of trades to analyze (overrides internal fetch)
            
        Returns:
            dict: All metrics
        """
        trades = trades_list if trades_list is not None else self.get_trade_history(days)
        
        # Calculate total profit first as it is needed
        total_profit = sum(t.get('profit', 0) + t.get('commission', 0) + t.get('swap', 0) for t in trades) if trades else 0.0
        
        # Estimate initial balance for Drawdown Calc
        current_balance = 0.0
        try:
            if mt5.terminal_info():
                acct = mt5.account_info()
                if acct:
                    current_balance = acct.balance
        except:
            pass
        
        initial_balance = current_balance - total_profit if current_balance > 0 else 10000.0 # Fallback

        return {
            "win_rate": self.calculate_win_rate(trades),
            "profit_factor": self.calculate_profit_factor(trades),
            "sharpe_ratio": self.calculate_sharpe_ratio(trades),
            "max_drawdown": self.calculate_max_drawdown(trades, initial_balance),
            "total_trades": len(trades),
            "avg_duration": self.calculate_avg_trade_duration(days),
            "total_profit": total_profit,
            "avg_profit": np.mean([t['profit'] for t in trades]) if trades else 0.0
        }

    def get_analytics(self, days=30):
        """
        Get combined analytics data (Metrics + Equity Curve)
        Used by TradingEngine for Web Dashboard
        """
        try:
            return {
                "metrics": self.get_all_metrics(days=days),
                "curve": self.get_equity_curve(days=days)
            }
        except Exception as e:
            logger.error(f"Error calculating analytics: {e}")
            return {"metrics": {}, "curve": {'times': [], 'equity': []}}


if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    
    # Initialize MT5
    if not mt5.initialize():
        print("MT5 initialization failed")
        exit()
    
    analyzer = PerformanceAnalyzer("XAUUSD")
    metrics = analyzer.get_all_metrics(days=30)
    
    print("\n=== Performance Metrics (Last 30 Days) ===")
    print(f"Total Trades: {metrics['total_trades']}")
    print(f"Win Rate: {metrics['win_rate']:.1f}%")
    print(f"Profit Factor: {metrics['profit_factor']:.2f}")
    print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
    print(f"Max Drawdown: {metrics['max_drawdown']:.2f}%")
    print(f"Avg Trade Duration: {metrics['avg_duration']:.1f} hours")
    print(f"Total Profit: ${metrics['total_profit']:.2f}")
    
    mt5.shutdown()
