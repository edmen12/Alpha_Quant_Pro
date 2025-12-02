import time
import threading
import asyncio
import functools
from concurrent.futures import ThreadPoolExecutor
import MetaTrader5 as mt5
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import sys
import traceback
import logging

# Import professional core modules
from core import AgentBundleAdapter, ModelInput
from news_calendar import NewsCalendar
from logger_setup import LoggerSetup
from database_manager import DatabaseManager
from performance_analyzer import PerformanceAnalyzer

# Setup logging
logger = LoggerSetup.get_logger("Engine")


class TradingEngine:
    """
    专业级交易引擎核心 (Professional Trading Engine Core)
    
    负责协调所有交易活动，包括：
    1. MT5 连接与状态管理
    2. 市场数据获取与处理
    3. 信号生成 (通过 Agent Bundle)
    4. 风险管理 (Equity Guard, News Filter)
    5. 智能执行 (Smart Entry, Trailing Stop, Partial Close)
    """
    def __init__(self, bundle_path, symbols=["XAUUSD"], lot_size=0.01, mt5_path=None, 
                 max_spread=500, max_daily_loss=500.0, min_equity=0,
                 use_risk_based_sizing=False, risk_percent=0.01,
                 news_filter_enabled=False, news_buffer_minutes=30,
                 trailing_enabled=False, trailing_distance=50,
                 partial_close_enabled=False, tp1_distance=50, partial_close_percent=50,

                 callback_status=None, db_manager=None, news_calendar=None, telegram_notifier=None,
                 symbol=None, timeframe="M15"): # Legacy support
        """
        初始化交易引擎
        
        Args:
            bundle_path: Agent Bundle 路径
            symbols: 交易品种列表 (e.g. ["XAUUSD", "EURUSD"])
            symbol: (Legacy) 单个交易品种，如果提供则覆盖 symbols
            lot_size: 固定手数 (目前对所有品种生效)
            mt5_path: MT5 终端路径 (可选)
            ...
        """
        self.bundle_path = bundle_path
        
        # Handle legacy 'symbol' argument
        if symbol:
            self.symbols = [symbol]
        elif isinstance(symbols, str):
            self.symbols = [s.strip() for s in symbols.split(',')]
        else:
            self.symbols = symbols
            
        # Legacy support: Set self.symbol to the first symbol (for single-symbol logic fallback)
        self.symbol = self.symbols[0] if self.symbols else "XAUUSD"
            
        self.lot_size = lot_size
        self.mt5_path = mt5_path
        self.max_spread = max_spread
        self.max_daily_loss = max_daily_loss
        self.min_equity = min_equity
        self.use_risk_based_sizing = use_risk_based_sizing
        self.risk_percent = risk_percent
        self.timeframe = timeframe
        self.mt5_timeframe = self._get_mt5_timeframe(timeframe)
        
        self.callback_status = callback_status
        self.running = False
        self.magic_number = 123456
        self.deviation = 20
        
        # Internal state (Multi-Symbol)
        self.agent_adapter = None
        # Initialize state for ALL symbols
        self.last_signals = {s: "WAIT" for s in self.symbols}
        self.last_confs = {s: 0.0 for s in self.symbols}
        
        # News Calendar (Dependency Injection)
        if news_calendar:
            self.news_calendar = news_calendar
        else:
            self.news_calendar = NewsCalendar(buffer_minutes=news_buffer_minutes)
            
        # Ensure settings match config
        self.news_calendar.buffer_minutes = news_buffer_minutes
        self.news_calendar.enable(news_filter_enabled)
        
        # Trailing Stop
        self.trailing_enabled = trailing_enabled
        self.trailing_distance = trailing_distance
        
        # Partial Close
        self.partial_close_enabled = partial_close_enabled
        self.tp1_distance = tp1_distance
        self.partial_close_percent = partial_close_percent
        self.partially_closed_tickets = set()
        
        # Database (Dependency Injection)
        if db_manager:
            self.db = db_manager
        else:
            self.db = DatabaseManager()

        # Telegram Notifier (Dependency Injection)
        self.telegram = telegram_notifier

        # Asyncio Executor for blocking tasks (MT5, Neural Net)
        self.executor = ThreadPoolExecutor(max_workers=1) # MT5 is not thread-safe, use 1 worker for safety

        # Analytics Cache
        self.analytics_cache = None
        self.last_analytics_time = 0
        self.analytics_cache_ttl = 60 # seconds

        # Performance Analyzer
        self.performance_analyzer = PerformanceAnalyzer(symbol=self.symbol, mt5_path=self.mt5_path)

    def log(self, msg):
        logger.info(msg)

        # Telegram Notifier (Dependency Injection)
    def send_alert(self, msg):
        """Send alert via Telegram if available"""
        if self.telegram:
            # Run in background to not block
            try:
                # If we are in async loop, use run_in_executor or just fire and forget if it's threaded
                # TelegramNotifier.send_message is likely synchronous (requests).
                # We should check if we are in an async context.
                try:
                    loop = asyncio.get_running_loop()
                    loop.run_in_executor(None, self.telegram.send_message, msg)
                except RuntimeError:
                    # No running loop, call directly
                    self.telegram.send_message(msg)
            except Exception as e:
                self.log(f"Failed to send Telegram alert: {e}")

    def _send_formatted_alert(self, event_type, **kwargs):
        """Helper to format alerts based on user templates"""
        if not self.telegram: return

        try:
            msg = ""
            if event_type == "OPEN":
                # [OPEN] BUY XAUUSD Size: (lot) lots Price: (Price) SL: (Price) | TP: (Price) Time: (time) ID: (oder id）
                msg = (f"[OPEN] {kwargs.get('type')} {kwargs.get('symbol')} "
                       f"Size: {kwargs.get('volume')} lots Price: {kwargs.get('price')} "
                       f"SL: {kwargs.get('sl', 0)} | TP: {kwargs.get('tp', 0)} "
                       f"Time: {datetime.now().strftime('%H:%M:%S')} ID: {kwargs.get('id')}")
            
            elif event_type == "CLOSE":
                # [CLOSE] XAUUSD Size: (lot) lots Price: (price) P&L: (+/-amount) ID: (order id)
                msg = (f"[CLOSE] {kwargs.get('symbol')} "
                       f"Size: {kwargs.get('volume')} lots Price: {kwargs.get('price')} "
                       f"P&L: {kwargs.get('profit'):+.2f} ID: {kwargs.get('id')}")
            
            elif event_type == "TP_HIT":
                # [TP HIT] BUY XAUUSD Size: (lot) lots Close Price: (price) P&L: (+amount) ID: (order id)
                msg = (f"[TP HIT] {kwargs.get('type')} {kwargs.get('symbol')} "
                       f"Size: {kwargs.get('volume')} lots Close Price: {kwargs.get('price')} "
                       f"P&L: {kwargs.get('profit'):+.2f} ID: {kwargs.get('id')}")

            elif event_type == "SL_HIT":
                # [SL HIT] BUY XAUUSD Size: (lot) lots Close Price: (price) P&L: (-amount) ID: (order id)
                msg = (f"[SL HIT] {kwargs.get('type')} {kwargs.get('symbol')} "
                       f"Size: {kwargs.get('volume')} lots Close Price: {kwargs.get('price')} "
                       f"P&L: {kwargs.get('profit'):+.2f} ID: {kwargs.get('id')}")

            elif event_type == "ERROR":
                # [ERROR] Order Rejected Type: BUY XAUUSD Size: (lot) lots Reason: ...
                msg = (f"[ERROR] Order Rejected Type: {kwargs.get('type')} {kwargs.get('symbol')} "
                       f"Size: {kwargs.get('volume')} lots Reason: {kwargs.get('reason')}")

            elif event_type == "UPDATE":
                # [UPDATE] Trailing SL Moved ID: (oder id) Symbol: symbol New SL: (price) Locked Profit: (+amount)
                # Note: Locked Profit calculation requires current price, we might just show SL
                msg = (f"[UPDATE] Trailing SL Moved ID: {kwargs.get('id')} "
                       f"Symbol: {kwargs.get('symbol')} New SL: {kwargs.get('sl')} "
                       f"Locked Profit: {kwargs.get('profit', 'N/A')}")

            elif event_type == "RISK":
                # [RISK] High Spread Detected Symbol: XAUUSD Current Spread: (point) points Limit: (point) points Action: Entries Paused
                msg = (f"[RISK] High Spread Detected Symbol: {kwargs.get('symbol')} "
                       f"Current Spread: {kwargs.get('spread')} points "
                       f"Limit: {kwargs.get('limit')} points Action: Entries Paused")
            
            elif event_type == "MARGIN_CALL":
                # [WARNING] MARGIN CALL Account: (acc no) Level: (%) Action: Force Close (lot) XAUUSD Remaining Equity: (amount)
                msg = (f"[WARNING] MARGIN CALL Account: {kwargs.get('account')} "
                       f"Level: {kwargs.get('level')}% Action: Force Close All "
                       f"Remaining Equity: {kwargs.get('equity')}")

            elif event_type == "MAX_DAILY_LOSS":
                # [RISK ALERT] Max Daily Loss Hit Today P&L: (-Amount) Limit: (amount) Action: Trading Paused Status: Awaiting Manual Reset
                msg = (f"[RISK ALERT] Max Daily Loss Hit Today P&L: {kwargs.get('pnl')} "
                       f"Limit: {kwargs.get('limit')} Action: Trading Paused Status: Awaiting Manual Reset")

            elif event_type == "FILLED":
                # [FILLED] Buy Limit Executed ID: (order id) Price: (price) Status: Active Position
                # Note: We don't know if it was a Buy Limit specifically, but we can say "Order Executed" or stick to user template
                msg = (f"[FILLED] Order Executed ID: {kwargs.get('id')} "
                       f"Price: {kwargs.get('price')} Status: {kwargs.get('status')}")
            
            if msg:
                self.send_alert(msg)
        except Exception as e:
            self.log(f"Error formatting alert: {e}")

    def update_config(self, config):
        """
        Dynamic Config Update (Hot-Reload)
        Allows updating parameters without restarting the engine.
        """
        try:
            self.log("Reloading Configuration...")
            
            # Update simple parameters
            if "max_spread" in config: self.max_spread = int(config["max_spread"])
            if "max_loss" in config: self.max_daily_loss = float(config["max_loss"])
            if "min_equity" in config: self.min_equity = float(config["min_equity"])
            
            # Update Risk Settings
            if "risk" in config:
                self.risk_percent = float(config["risk"]) / 100.0
                # Only infer if explicit key not present (backward compatibility)
                if "use_risk_based_sizing" not in config:
                    self.use_risk_based_sizing = True if self.risk_percent > 0 else False
                self.log(f"Risk Updated: {self.risk_percent*100}%")
            
            if "use_risk_based_sizing" in config:
                self.use_risk_based_sizing = config["use_risk_based_sizing"]
                self.log(f"Sizing Mode Updated: {'Risk %' if self.use_risk_based_sizing else 'Fixed Lot'}")
            
            if "lot_size" in config: self.lot_size = float(config["lot_size"])
            
            # Update News Filter
            if "news_filter" in config:
                self.news_calendar.enable(config["news_filter"])
            if "news_buffer" in config:
                self.news_calendar.buffer_minutes = int(config["news_buffer"])
                
            # Update Trailing/Partial Close
            if "trailing_enabled" in config: self.trailing_enabled = config["trailing_enabled"]
            if "trailing_distance" in config: self.trailing_distance = int(config["trailing_distance"])
            if "partial_close_enabled" in config: self.partial_close_enabled = config["partial_close_enabled"]
            if "tp1_distance" in config: self.tp1_distance = int(config["tp1_distance"])
            if "partial_close_percent" in config: self.partial_close_percent = float(config["partial_close_percent"])
            
            self.log("Configuration Reloaded Successfully.")
            return True
        except Exception as e:
            self.log(f"Config Reload Error: {e}")
            return False

    def connect_mt5(self):
        if self.mt5_path:
            self.log(f"Connecting to MT5 at: {self.mt5_path}")
            if not mt5.initialize(path=self.mt5_path):
                self.log(f"MT5 Init Failed: {mt5.last_error()}")
                return False
        else:
            if not mt5.initialize():
                self.log(f"MT5 Init Failed: {mt5.last_error()}")
                return False
                
        self.log(f"MT5 Connected: {mt5.terminal_info().name}")
        account_info = mt5.account_info()
        if account_info:
            self.log(f"Account: {account_info.login} | Server: {account_info.server}")
        return True

    def get_daily_pnl(self, symbol=None):
        """Calculate total PnL for the current day (Realized + Floating)"""
        now = datetime.now()
        start_of_day = datetime(now.year, now.month, now.day)
        
        # Realized PnL
        deals = mt5.history_deals_get(start_of_day, now)
        realized_pnl = 0.0
        if deals:
            realized_pnl = sum(d.profit + d.commission + d.swap for d in deals)
            
        # Floating PnL
        floating_pnl = 0.0
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get() # All symbols
            
        if positions:
            floating_pnl = sum(p.profit + p.swap for p in positions)
            
        return realized_pnl + floating_pnl

    def get_history(self, n=300, symbol=None):
        target_symbol = symbol if symbol else self.symbols[0]
    def get_history(self, n=300, symbol=None):
        target_symbol = symbol if symbol else self.symbols[0]
        rates = mt5.copy_rates_from_pos(target_symbol, self.mt5_timeframe, 0, n)
        if rates is None: return pd.DataFrame()
        df = pd.DataFrame(rates)
        df['time'] = pd.to_datetime(df['time'], unit='s')
        df.rename(columns={'time': 'datetime', 'tick_volume': 'volume'}, inplace=True)
        return df

    def get_position_info(self, symbol=None):
        target_symbol = symbol if symbol else self.symbols[0]
        positions = mt5.positions_get(symbol=target_symbol)
        if positions is None or len(positions) == 0:
            return 0, 0, 0.0, 0
        
        pos = positions[0]
        direction = 1 if pos.type == 0 else -1
        duration = datetime.now().timestamp() - pos.time
        bars_held = int(duration / (15 * 60))
        return direction, bars_held, pos.price_open, pos.ticket

    def get_open_positions(self, symbol=None):
        """Get all open positions for the specified symbol (or all if None)"""
        if not mt5.terminal_info(): return []
        
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if positions is None: return []
        
        # Convert to list of dicts for easier consumption
        pos_list = []
        for p in positions:
            pos_list.append({
                'ticket': p.ticket,
                'symbol': p.symbol,
                'type': 'BUY' if p.type == 0 else 'SELL',
                'volume': p.volume,
                'price_open': p.price_open,
                'price_current': p.price_current,
                'sl': p.sl,
                'tp': p.tp,
                'profit': p.profit,
                'time': datetime.fromtimestamp(p.time).strftime('%Y-%m-%d %H:%M')
            })
        return pos_list

    def get_trade_history(self, days=30):
        """Get trading history for the last N days"""
        if not mt5.terminal_info(): return []
        
        from_date = datetime.now() - pd.Timedelta(days=days)
        to_date = datetime.now() + pd.Timedelta(days=1) # Cover future server time
        # Fetch deals for ALL symbols to support multi-symbol trading
        deals = mt5.history_deals_get(from_date, to_date)
        
        if deals:
            history = []
            for d in deals:
                # Filter by our symbols if needed, or just show all
                deal_symbol = d.symbol
                if self.symbols and deal_symbol not in self.symbols:
                    continue

                # We only care about OUT deals (Closing trades) or IN/OUT for full history
                # Usually users want to see closed PnL, so ENTRY_OUT
                if d.entry == mt5.DEAL_ENTRY_OUT: 
                    # Find Open Price from Entry Deal
                    open_price = 0.0
                    try:
                        if d.position_id > 0:
                            # Get deals for this position to find the entry
                            pos_deals = mt5.history_deals_get(position=d.position_id)
                            if pos_deals:
                                for p_deal in pos_deals:
                                    if p_deal.entry == mt5.DEAL_ENTRY_IN:
                                        open_price = p_deal.price
                                        break
                    except:
                        pass

                    history.append({
                        'ticket': d.ticket,
                        'symbol': d.symbol,
                        'time': datetime.fromtimestamp(d.time).strftime('%Y-%m-%d %H:%M:%S'),
                        'type': 'BUY' if d.type == 0 else 'SELL',
                        'volume': d.volume,
                        'price': d.price,
                        'open_price': open_price,
                        'close_price': d.price,
                        'profit': d.profit,
                        'comment': d.comment
                    })
            # Sort by time desc
            history.sort(key=lambda x: x['time'], reverse=True)
            return history
        return []

    def get_all_positions(self):
        """Get all active positions"""
        if not mt5.terminal_info(): return []
        positions = mt5.positions_get()
        if positions:
            # Convert named tuple to dict for easier handling
            return [{
                'ticket': p.ticket,
                'symbol': p.symbol,
                'type': 'BUY' if p.type == 0 else 'SELL',
                'volume': p.volume,
                'price_open': p.price_open,
                'sl': p.sl,
                'tp': p.tp,
                'profit': p.profit,
                'time': datetime.fromtimestamp(p.time).strftime('%H:%M:%S')
            } for p in positions]
        return []

    def close_position(self, ticket):
        """Close a specific position by ticket"""
        positions = mt5.positions_get(ticket=ticket)
        if not positions:
            self.log(f"Position {ticket} not found")
            return False
            
        pos = positions[0]
        
        # Get current profit BEFORE closing
        current_profit = pos.profit
        
        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": pos.symbol,
            "volume": pos.volume,
            "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
            "position": ticket,
            "price": mt5.symbol_info_tick(pos.symbol).bid if pos.type == 0 else mt5.symbol_info_tick(pos.symbol).ask,
            "deviation": self.deviation,
            "magic": self.magic_number,
            "comment": "Manual Close",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log(f"Close Failed: {result.comment}")
            return False
        else:
            self.log(f"Position {ticket} Closed Manually | Profit: ${current_profit:.2f}")
            self._send_formatted_alert("CLOSE", symbol=pos.symbol, volume=pos.volume, price=request['price'], profit=current_profit, id=ticket)
            # Update DB with actual close price and profit
            self.db.close_trade(ticket, request['price'], current_profit)
            return True

    def close_all_positions(self, symbol=None):
        """Close all active positions for this symbol (or all if None)"""
        if symbol:
            positions = mt5.positions_get(symbol=symbol)
        else:
            positions = mt5.positions_get()
            
        if not positions: return
        
        for pos in positions:
            self.close_position(pos.ticket)
    
    def check_spread(self, symbol):
        """
        智能入场检查 (Smart Entry Check)
        
        验证当前市场条件是否适合入场。目前主要检查点差，
        未来可扩展为检查市场时段、波动率等。
        
        Returns:
            bool: True 如果条件有利，False 如果应暂停交易
        """
        try:
            tick = mt5.symbol_info_tick(symbol)
            symbol_info = mt5.symbol_info(symbol)
            
            if not tick or not symbol_info:
                self.log(f"⚠️ Smart Entry: Unable to get market data for {symbol}")
                return False
            
            # Calculate current spread in points
            spread = (tick.ask - tick.bid) / symbol_info.point
            
            # Check 1: Spread Filter
            if spread > self.max_spread:
                self.log(f"❌ Smart Entry: Spread too high for {symbol} ({spread:.1f} > {self.max_spread}) | Ask: {tick.ask}, Bid: {tick.bid}, Point: {symbol_info.point}")
                self._send_formatted_alert("RISK", symbol=symbol, spread=int(spread), limit=self.max_spread)
                return False
            
            # Check 2: Market Hours (Optional - avoid low liquidity hours)
            # You can add time-based filters here if needed
            
            # Check 3: Volatility Filter (Optional)
            # You can add ATR-based checks here
            
            self.log(f"✅ Smart Entry: Conditions OK for {symbol} (Spread: {spread:.1f})")
            return True
            
        except Exception as e:
            self.log(f"Smart Entry Check Error: {e}")
            return False


    def execute_trade(self, symbol, action, sl=None, tp=None):
        volume = float(self.lot_size)
        
        # Dynamic Position Sizing
        if self.use_risk_based_sizing and sl:
            try:
                account = mt5.account_info()
                if account:
                    balance = account.balance
                    risk_amount = balance * self.risk_percent
                    
                    entry_price = mt5.symbol_info_tick(symbol).ask if action == "BUY" else mt5.symbol_info_tick(symbol).bid
                    dist = abs(entry_price - sl)
                    
                    if dist > 0:
                        # Formula: Risk = Volume * ContractSize * PriceDist
                        # Volume = Risk / (ContractSize * PriceDist)
                        # Assuming ContractSize = 100 (Standard Gold Lot)
                        calc_volume = risk_amount / (100 * dist)
                        
                        # Round to 2 decimals and clamp
                        calc_volume = round(calc_volume, 2)
                        calc_volume = max(0.01, min(calc_volume, 10.0))
                        
                        self.log(f"Dynamic Sizing: Balance=${balance:.0f} Risk={self.risk_percent*100}% SL_Dist={dist:.2f} -> Vol={calc_volume}")
                        volume = calc_volume
            except Exception as e:
                self.log(f"Sizing Error: {e}. Using default lot.")

        request = {
            "action": mt5.TRADE_ACTION_DEAL,
            "symbol": symbol,
            "volume": volume,
            "type": mt5.ORDER_TYPE_BUY if action == "BUY" else mt5.ORDER_TYPE_SELL,
            "price": mt5.symbol_info_tick(symbol).ask if action == "BUY" else mt5.symbol_info_tick(symbol).bid,
            "deviation": self.deviation,
            "magic": self.magic_number,
            "comment": "AlphaEngine",
            "type_time": mt5.ORDER_TIME_GTC,
            "type_filling": mt5.ORDER_FILLING_IOC,
        }
        if sl: request["sl"] = sl
        if tp: request["tp"] = tp
        
        result = mt5.order_send(request)
        if result.retcode != mt5.TRADE_RETCODE_DONE:
            self.log(f"Order Failed: {result.comment}")
            self._send_formatted_alert("ERROR", type=action, symbol=symbol, volume=volume, reason=result.comment)
        else:
            self.log(f"Order Executed: {action} {volume} Lots @ {request['price']}")
            self._send_formatted_alert("OPEN", type=action, symbol=symbol, volume=volume, price=request['price'], sl=sl, tp=tp, id=result.order)
            # Save to DB
            if result.order:
                trade_dict = {
                    'ticket': result.order,
                    'symbol': symbol,
                    'type': action,
                    'volume': volume,
                    'price_open': request['price'],
                    'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    'sl': sl if sl else 0.0,
                    'tp': tp if tp else 0.0,
                    'magic': self.magic_number,
                    'comment': request['comment']
                }
                self.db.save_trade(trade_dict)
        return result
    
    def update_trailing_stops(self, symbol):
        """
        更新追踪止损 (Server-side Trailing Stop)
        
        逻辑:
        - BUY: 价格上涨时，SL 向上移动，保持 trailing_distance 的距离。永远不向下移动。
        - SELL: 价格下跌时，SL 向下移动，保持 trailing_distance 的距离。永远不向上移动。
        - 目的: 锁定浮动利润，保护仓位免受反转影响。
        """
        if not self.trailing_enabled:
            return
        
        try:
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return
            
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return
            
            point = symbol_info.point
            
            for pos in positions:
                # Calculate new SL based on trailing logic
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    continue
                
                new_sl = None
                
                if pos.type == mt5.POSITION_TYPE_BUY:
                    # BUY: Trail stop upward
                    current_price = tick.bid
                    profit_points = (current_price - pos.price_open) / point
                    
                    if profit_points >= self.trailing_distance:
                        new_sl = current_price - (self.trailing_distance * point)
                        
                        # Only move SL up, never down
                        if pos.sl == 0 or new_sl > pos.sl:
                            self._modify_position_sl(pos.ticket, new_sl, symbol)
                
                elif pos.type == mt5.POSITION_TYPE_SELL:
                    # SELL: Trail stop downward
                    current_price = tick.ask
                    profit_points = (pos.price_open - current_price) / point
                    
                    if profit_points >= self.trailing_distance:
                        new_sl = current_price + (self.trailing_distance * point)
                        
                        # Only move SL down, never up
                        if pos.sl == 0 or new_sl < pos.sl:
                            self._modify_position_sl(pos.ticket, new_sl, symbol)
        
        except Exception as e:
            logger.info(f"Trailing Stop Error: {e}")
    
    def _modify_position_sl(self, ticket, new_sl, symbol):
        """Modify position's stop loss"""
        try:
            position = None
            positions = mt5.positions_get(ticket=ticket)
            if positions:
                position = positions[0]
            
            if not position:
                return False
            
            request = {
                "action": mt5.TRADE_ACTION_SLTP,
                "position": ticket,
                "sl": new_sl,
                "tp": position.tp,
                "symbol": symbol,
                "magic": self.magic_number
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                logger.info(f"✅ Trailing SL Updated: Ticket {ticket} -> SL {new_sl:.2f}")
                self.db.update_trade(ticket, {'sl': new_sl})
                self._send_formatted_alert("UPDATE", id=ticket, symbol=symbol, sl=new_sl, profit="N/A") # Profit calc needs open price
                return True
            else:
                logger.info(f"Failed to update SL: {result.comment}")
                return False
                
        except Exception as e:
            logger.info(f"Error modifying SL: {e}")
            return False

    def check_partial_close(self, symbol):
        """
        检查分批止盈 (Partial Close Check)
        
        逻辑:
        1. 遍历所有持仓
        2. 计算当前浮动盈利点数
        3. 如果盈利 >= tp1_distance 且尚未分批平仓:
           - 平掉指定百分比 (partial_close_percent) 的仓位
           - 将剩余仓位的 SL 移动到开仓价 (Break Even)
        """
        if not self.partial_close_enabled:
            return
        
        try:
            positions = mt5.positions_get(symbol=symbol)
            if not positions:
                return
            
            symbol_info = mt5.symbol_info(symbol)
            if not symbol_info:
                return
            
            point = symbol_info.point
            
            for pos in positions:
                # Skip if already partially closed
                if pos.ticket in self.partially_closed_tickets:
                    continue
                
                # Calculate profit in points
                tick = mt5.symbol_info_tick(symbol)
                if not tick:
                    continue
                
                if pos.type == mt5.POSITION_TYPE_BUY:
                    current_price = tick.bid
                    profit_points = (current_price - pos.price_open) / point
                elif pos.type == mt5.POSITION_TYPE_SELL:
                    current_price = tick.ask
                    profit_points = (pos.price_open - current_price) / point
                else:
                    continue
                
                # Check if TP1 reached
                if profit_points >= self.tp1_distance:
                    # Double check history to ensure we haven't already partially closed this ticket
                    # This prevents re-triggering after engine restart
                    if self._has_partial_close_history(pos.ticket):
                        self.partially_closed_tickets.add(pos.ticket)
                        continue
                        
                    self._execute_partial_close(pos, symbol)
        
        except Exception as e:
            self.log(f"Partial Close Check Error: {e}")
    
    def _execute_partial_close(self, position, symbol):
        """Execute partial close and move SL to break even"""
        try:
            # Calculate close volume
            close_volume = round(position.volume * (self.partial_close_percent / 100.0), 2)
            
            if close_volume < 0.01:  # Minimum volume
                self.log(f"Partial close volume too small: {close_volume}")
                return
            
            # Close partial position
            if self._close_partial_position(position.ticket, close_volume, position.type, symbol):
                # Move SL to break even
                time.sleep(0.5)  # Wait for partial close to complete
                self._modify_position_sl(position.ticket, position.price_open, symbol)
                
                # Mark as partially closed
                self.partially_closed_tickets.add(position.ticket)
                
                self.log(f"🎯 Partial Close Complete: {close_volume} Lots @ TP1, SL → Break Even")
                
                # Update DB
                self.db.update_trade(position.ticket, {
                    'sl': position.price_open,
                    'partial_close_done': True,
                    'volume': position.volume - close_volume # Approx
                })
        
        except Exception as e:
            self.log(f"Partial Close Execution Error: {e}")
    
    def _close_partial_position(self, ticket, volume, position_type, symbol):
        """Close partial volume of a position"""
        try:
            # Determine close type
            close_type = mt5.ORDER_TYPE_SELL if position_type == mt5.POSITION_TYPE_BUY else mt5.ORDER_TYPE_BUY
            
            tick = mt5.symbol_info_tick(symbol)
            if not tick:
                return False
            
            price = tick.bid if close_type == mt5.ORDER_TYPE_SELL else tick.ask
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": ticket,
                "symbol": symbol,
                "volume": volume,
                "type": close_type,
                "price": price,
                "deviation": self.deviation,
                "magic": self.magic_number,
                "comment": "Partial Close @ TP1"
            }
            
            result = mt5.order_send(request)
            if result.retcode == mt5.TRADE_RETCODE_DONE:
                self.log(f"✅ Partial Close: {volume} Lots @ {price:.2f}")
                return True
            else:
                self.log(f"Failed partial close: {result.comment}")
                return False
                
        except Exception as e:
            self.log(f"Error closing partial position: {e}")
            return False

    def _has_partial_close_history(self, ticket):
        """Check if a position has already been partially closed by checking history deals"""
        try:
            # Get deals for this ticket
            now = datetime.now()
            from_date = now - pd.Timedelta(days=30) # Look back 30 days
            deals = mt5.history_deals_get(from_date, now, position=ticket)
            
            if deals:
                for d in deals:
                    # Check for our specific comment signature
                    if d.comment and "Partial Close" in d.comment:
                        return True
            return False
        except:
            return False

    def _reconcile_state(self):
        """Reconcile local DB state with MT5 reality"""
        logger.info("Reconciling state...")
        try:
            db_trades = {t['ticket']: t for t in self.db.get_active_trades()}
            mt5_positions = {p['ticket']: p for p in self.get_open_positions()}
            
            # 1. Close trades in DB that are gone from MT5
            for ticket in db_trades:
                if ticket not in mt5_positions:
                    logger.info(f"Trade {ticket} missing in MT5. Marking as CLOSED in DB.")
                    
                    # Check why it closed (SL/TP/Manual)
                    try:
                        # Get deals for this position
                        deals = mt5.history_deals_get(position=ticket)
                        if deals:
                            # Look for the OUT deal
                            out_deal = next((d for d in deals if d.entry == mt5.DEAL_ENTRY_OUT), None)
                            if out_deal:
                                close_price = out_deal.price
                                profit = out_deal.profit + out_deal.swap + out_deal.commission
                                reason = out_deal.reason
                                
                                event_type = "CLOSE"
                                if reason == mt5.DEAL_REASON_SL: event_type = "SL_HIT"
                                elif reason == mt5.DEAL_REASON_TP: event_type = "TP_HIT"
                                
                                self._send_formatted_alert(event_type, 
                                    type='BUY' if out_deal.type == 0 else 'SELL', # Note: Deal type is opposite of Position type usually? No, Deal Type 1 is Sell. If Position was Buy, Close Deal is Sell.
                                    # Wait, user wants "BUY XAUUSD" for the trade type.
                                    # If out_deal.type is SELL (1), it means we SOLD to close. So original was BUY.
                                    # Correct logic: If out_deal.type == 1 (SELL), original was BUY.
                                    symbol=out_deal.symbol,
                                    volume=out_deal.volume,
                                    price=close_price,
                                    profit=profit,
                                    id=ticket
                                )
                    except Exception as e:
                        logger.error(f"Error checking close reason: {e}")

                    self.db.close_trade(ticket, 0.0, 0.0)
            
            # 2. Add/Update trades from MT5 to DB
            for ticket, pos in mt5_positions.items():
                if ticket not in db_trades:
                    logger.info(f"Found new trade {ticket} in MT5. Adding to DB.")
                    self.db.save_trade(pos)
                    # Alert for filled order (likely pending order filled or external trade)
                    self._send_formatted_alert("FILLED", id=ticket, price=pos['price_open'], status="Active Position")
                else:
                    # Restore strategy state
                    db_trade = db_trades[ticket]
                    if db_trade.get('partial_close_done'):
                        self.partially_closed_tickets.add(ticket)
                        
        except Exception as e:
            logger.info(f"Reconciliation Error: {e}")

    def stop(self):
        self.running = False

    async def _run_blocking(self, func, *args, **kwargs):
        """Run blocking function in executor"""
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self.executor, functools.partial(func, *args, **kwargs))

    def _calculate_analytics_internal(self, days=30):
        """Internal synchronous calculation logic"""
        try:
            # 1. Fetch history using Engine's connection (Thread-Safe context)
            history = self.get_trade_history(days)
            
            # 2. Pass data to Analyzer
            analyzer = PerformanceAnalyzer(symbol=None)
            return {
                'metrics': analyzer.get_all_metrics(days, trades_list=history),
                'curve': analyzer.get_equity_curve(days, trades_list=history)
            }
        except Exception as e:
            logger.error(f"[Analytics] Calculation Error: {e}")
            return {'metrics': {}, 'curve': {}}

    def get_analytics_sync(self, days=30):
        """
        Synchronous method to get analytics with caching.
        Safe to call from GUI thread or Executor.
        """
        current_time = time.time()
        
        # Return cached if valid
        if (self.analytics_cache and 
            current_time - self.last_analytics_time < self.analytics_cache_ttl):
            return self.analytics_cache
            
        # Calculate
        result = self._calculate_analytics_internal(days)
        
        # Update Cache
        if result and result.get('metrics'):
            self.analytics_cache = result
            self.last_analytics_time = current_time
            
        return result

    async def get_analytics(self, days=30):
        """Get performance metrics safely via executor with caching (Async wrapper)"""
        return await self._run_blocking(self.get_analytics_sync, days)

    async def check_risk_limits(self):
        """
        Check global risk limits (Equity Guard, Max Daily Loss)
        Returns:
            bool: True if safe to continue, False if hard stop triggered
        """
        try:
            # 1. Equity Guard
            if self.min_equity > 0:
                account = await self._run_blocking(mt5.account_info)
                if account and account.equity < self.min_equity:
                    logger.info(f"EQUITY GUARD TRIGGERED: ${account.equity:.2f} < ${self.min_equity:.2f}")
                    self._send_formatted_alert("MARGIN_CALL", account=account.login, level=f"{account.margin_level:.2f}", equity=f"{account.equity:.2f}")
                    await self._run_blocking(self.close_all_positions)
                    return False

            # 2. Max Daily Loss
            if self.max_daily_loss > 0:
                current_daily_pnl = await self._run_blocking(self.get_daily_pnl)
                if current_daily_pnl < -self.max_daily_loss:
                    logger.info(f"MAX DAILY LOSS TRIGGERED: PnL ${current_daily_pnl:.2f} < -${self.max_daily_loss:.2f}")
                    self._send_formatted_alert("MAX_DAILY_LOSS", pnl=f"{current_daily_pnl:.2f}", limit=f"{self.max_daily_loss:.2f}")
                    await self._run_blocking(self.close_all_positions)
                    return False
            
            return True
            
        except Exception as e:
            self.log(f"Risk Check Error: {e}")
            return True # Don't stop on error, but log it

    async def run_async(self):
        """Async Main Loop (Multi-Symbol)"""
        self.running = True
        logger.info("Starting run_async loop...")
        try:
            # Connect (Blocking is fine here, once)
            logger.info("Connecting to MT5...")
            if not await self._run_blocking(self.connect_mt5):
                logger.info("MT5 Connection Failed. Exiting run_async.")
                return

            # Reconcile State (Blocking is fine here)
            logger.info("Reconciling State...")
            await self._run_blocking(self._reconcile_state)

            # Use professional AgentBundleAdapter
            logger.info(f"Loading Agent Bundle: {Path(self.bundle_path).name}")
            # Loading model might be heavy, offload? It's once, maybe fine.
            self.agent_adapter = AgentBundleAdapter(self.bundle_path)
            logger.info("Agent Bundle Loaded.")
            
            logger.info(f"Engine Started. Symbols: {self.symbols}, Risk: {self.risk_percent*100}%")
            # self.send_alert(f"🚀 Engine Started\nSymbols: {self.symbols}\nRisk: {self.risk_percent*100}%")
            
            # Track last bar time per symbol
            last_bar_times = {s: 0 for s in self.symbols}
            
            while self.running:
                try:
                    # 1. Update Status & Check Connection
                    if not mt5.terminal_info():
                        logger.info("MT5 Disconnected. Reconnecting...")
                        if not await self._run_blocking(self.connect_mt5):
                            await asyncio.sleep(5)
                            continue
                    
                    # Global Risk Checks
                    if not await self.check_risk_limits():
                        self.running = False
                        break


                    # Get Account Info (Global)
                    account = await self._run_blocking(mt5.account_info)

                    # --- Iterate over ALL symbols ---
                    for symbol in self.symbols:
                        # 2. Get Market Data (Async)
                        tick = await self._run_blocking(mt5.symbol_info_tick, symbol)
                        if tick is None:
                            # self.log(f"No tick data for {symbol}") # Reduce spam
                            continue
                        
                        current_price = tick.bid
                        
                        # 3. Risk Management & Position Monitoring (Async)
                        # Manage Existing Positions (Trailing, Partial Close)
                        await self._run_blocking(self.update_trailing_stops, symbol)
                        await self._run_blocking(self.check_partial_close, symbol)

                        # 4. Generate Signal (Async Inference)
                        # Check for New Bar
                        # Check for New Bar
                        rates = await self._run_blocking(mt5.copy_rates_from_pos, symbol, self.mt5_timeframe, 0, 1)
                        if rates is not None:
                            current_bar_time = rates[0]['time']
                            
                            if current_bar_time != last_bar_times[symbol]:
                                self.log(f"[{symbol}] New Bar: {datetime.fromtimestamp(current_bar_time)}")
                                last_bar_times[symbol] = current_bar_time
                                
                                # Fetch data for model
                                df_hist = await self._run_blocking(self.get_history, 300, symbol)
                                
                                if not df_hist.empty:
                                    pos_dir, bars_held, entry_price, ticket = await self._run_blocking(self.get_position_info, symbol)
                                    daily_pnl = await self._run_blocking(self.get_daily_pnl, symbol) # Per symbol PnL for features? Or global? Usually per symbol.
                                    
                                    # Create standardized input
                                    model_input = ModelInput(
                                        timestamp=datetime.now(),
                                        symbol=symbol,
                                        timeframe=self.timeframe,
                                        price=current_price,
                                        history_candles=df_hist,
                                        candle=df_hist.iloc[-1].to_dict(),
                                        position=pos_dir,
                                        bars_held=bars_held,
                                        open_trades=1 if pos_dir != 0 else 0,
                                        entry_price=entry_price,
                                        daily_pnl=daily_pnl,
                                        daily_drawdown=0.0,
                                        equity=account.equity,
                                        balance=account.balance,
                                        meta={}
                                    )
                                    
                                    # Predict (CPU Heavy)
                                    output = await self._run_blocking(self.agent_adapter.predict, model_input)
                                    
                                    # Update Internal State
                                    self.last_signals[symbol] = output.signal
                                    self.last_confs[symbol] = output.confidence
                                    
                                    extra_info = ""
                                    if output.extra:
                                        p_up = output.extra.get('p_up', 0.0)
                                        p_down = output.extra.get('p_down', 0.0)
                                        extra_info = f" | Up: {p_up:.2f} Down: {p_down:.2f}"
                                    
                                    self.log(f"[{symbol}] Signal: {output.signal} | Conf: {output.confidence:.2f}{extra_info} | {output.tag}")
                                    
                                    # Execute Trade
                                    if output.signal in ["BUY", "SELL"]:
                                        # Filter: Spread
                                        if await self._run_blocking(self.check_spread, symbol):
                                            # Filter: News
                                            if not self.news_calendar.is_trading_allowed():
                                                self.log(f"[{symbol}] Signal {output.signal} ignored. High Impact News.")
                                            else:
                                                # Execute Logic
                                                if output.signal == "BUY":
                                                    if pos_dir == -1:
                                                        self.log(f"[{symbol}] Closing Short Position")
                                                        await self._run_blocking(self.execute_trade, symbol, "BUY")
                                                    elif pos_dir == 0:
                                                        self.log(f"[{symbol}] Opening Long Position")
                                                        await self._run_blocking(self.execute_trade, symbol, "BUY", sl=output.sl, tp=output.tp)
                                                elif output.signal == "SELL":
                                                    if pos_dir == 1:
                                                        self.log(f"[{symbol}] Closing Long Position")
                                                        await self._run_blocking(self.execute_trade, symbol, "SELL")
                                                    elif pos_dir == 0:
                                                        self.log(f"[{symbol}] Opening Short Position")
                                                        await self._run_blocking(self.execute_trade, symbol, "SELL", sl=output.sl, tp=output.tp)
                    
                    # 5. Callback Update (UI) - Once per loop iteration (updates with global state)
                    if self.callback_status:
                        # Get history for UI (lightweight) - Show Primary Symbol
                        primary_symbol = self.symbols[0]
                        df_ui = await self._run_blocking(self.get_history, 100, primary_symbol)
                        
                        # Get recent trades for UI (from MT5, not database)
                        trades = await self._run_blocking(self.get_trade_history, 30)
                        
                        positions = await self._run_blocking(self.get_all_positions) # Get ALL positions
                        current_pnl = sum([p['profit'] for p in positions]) if positions else 0.0
                        total_profit = await self._run_blocking(self.db.get_total_profit)
                        
                        # Use bid price of primary symbol
                        tick = mt5.symbol_info_tick(primary_symbol)
                        current_price = tick.last if tick and tick.last > 0 else (tick.bid if tick else 0.0)
                        
                        status = {
                            "price": current_price,
                            "signal": self.last_signals[primary_symbol], # Show primary signal
                            "confidence": self.last_confs[primary_symbol],
                            "balance": account.balance if account else 0,
                            "equity": account.equity if account else 0,
                            "positions": positions, # Pass full list
                            "pnl": current_pnl,
                            "total_profit": total_profit,
                            "history": df_ui,
                            "trades": trades
                        }
                        # Run callback in main thread (UI thread) usually, but here we are in async thread.
                        self.callback_status(status)

                    await asyncio.sleep(0.5) # Yield to event loop

                except Exception as e:
                    self.log(f"Loop Error: {e}")
                    traceback.print_exc()
                    await asyncio.sleep(1)
                    
        except Exception as e:
            self.log(f"Fatal Engine Error: {e}")
        finally:
            self.log("Engine Stopped")
            self.send_alert("🛑 Engine Stopped")
            mt5.shutdown()
            self.executor.shutdown(wait=False)

    def run(self):
        """Legacy wrapper for threading compatibility (if needed)"""
        asyncio.run(self.run_async())

    def _get_mt5_timeframe(self, tf_str):
        mapping = {
            "M1": mt5.TIMEFRAME_M1, "M5": mt5.TIMEFRAME_M5, "M15": mt5.TIMEFRAME_M15,
            "M30": mt5.TIMEFRAME_M30, "H1": mt5.TIMEFRAME_H1, "H4": mt5.TIMEFRAME_H4,
            "D1": mt5.TIMEFRAME_D1
        }
        return mapping.get(tf_str, mt5.TIMEFRAME_M15)
