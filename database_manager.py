"""
Database Manager Module
Handles SQLite database operations for state persistence and trade history.
"""
import sqlite3
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
from path_manager import PathManager

logger = logging.getLogger(__name__)

import threading

class DatabaseManager:
    """
    数据库管理器 (Database Manager)
    
    负责所有 SQLite 数据库交互，包括：
    1. 初始化数据库和表结构
    2. 保存和更新交易记录
    3. 加载活动交易（用于系统恢复）
    4. 查询历史记录
    """
    
    DB_FILE = "terminal_data.db"
    
    def __init__(self, db_path: str = None):
        """
        Initialize Database Manager
        
        Args:
            db_path: Path to SQLite database file (default: AppData/Roaming/workspace/terminal_data.db)
        """
        if db_path:
            self.db_path = db_path
        else:
            self.db_path = str(PathManager.get_database_path())
            
        # Ensure directory exists
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Cloud Sync Risk Check
        self._check_cloud_sync_risk(self.db_path)
        
        # Auto-Backup on Startup
        self._backup_db()
        
        # Thread Lock for Write Operations
        self.lock = threading.Lock()
            
        self._init_db()
        
    def _check_cloud_sync_risk(self, path_str):
        """Check if DB is in a cloud sync folder (OneDrive/Dropbox)"""
        path_lower = path_str.lower()
        if "onedrive" in path_lower or "dropbox" in path_lower or "google drive" in path_lower:
            logger.warning(f"⚠️ DATABASE RISK: Database is located in a Cloud Sync folder: {path_str}")
            logger.warning("This may cause file lock issues or corruption. Please move the workspace.")

    def _backup_db(self):
        """Create a backup of the database file"""
        try:
            db_file = Path(self.db_path)
            if db_file.exists():
                import shutil
                backup_path = db_file.with_suffix('.db.bak')
                shutil.copy2(db_file, backup_path)
                logger.info(f"Database backup created: {backup_path}")
        except Exception as e:
            logger.error(f"Failed to backup database: {e}")
        
    def _get_connection(self):
        """Get SQLite connection with row factory"""
        # check_same_thread=False allows sharing connection across threads (with manual locking)
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
        
    def _init_db(self):
        """Initialize database schema"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Trades Table
                # Stores both Open and Closed trades
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS trades (
                    ticket INTEGER PRIMARY KEY,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    lot_size REAL NOT NULL,
                    open_price REAL NOT NULL,
                    open_time TEXT NOT NULL,
                    sl REAL,
                    tp REAL,
                    close_price REAL,
                    close_time TEXT,
                    profit REAL DEFAULT 0.0,
                    status TEXT NOT NULL,  -- 'OPEN', 'CLOSED'
                    magic_number INTEGER,
                    comment TEXT,
                    extra_data TEXT        -- JSON for strategy state (partial_close, trailing, etc.)
                )
                """)
                
                # Create index for faster queries
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_status ON trades(status)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_open_time ON trades(open_time)")
                
                conn.commit()
                logger.info(f"Database initialized at {self.db_path}")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    def save_trade(self, trade_data: Dict[str, Any]):
        """
        保存新交易 (Save New Trade)
        
        Args:
            trade_data: Dictionary containing trade details
        """
        with self.lock:
            try:
                # Prepare extra data (strategy state)
                extra_data = {
                    k: v for k, v in trade_data.items() 
                    if k not in ['ticket', 'symbol', 'type', 'volume', 'price_open', 'time', 'sl', 'tp', 'magic', 'comment']
                }
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    INSERT OR REPLACE INTO trades (
                        ticket, symbol, type, lot_size, open_price, open_time, 
                        sl, tp, status, magic_number, comment, extra_data
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        trade_data['ticket'],
                        trade_data['symbol'],
                        trade_data['type'],
                        trade_data['volume'],
                        trade_data['price_open'],
                        trade_data.get('time', datetime.now().strftime('%Y-%m-%d %H:%M:%S')),
                        trade_data.get('sl', 0.0),
                        trade_data.get('tp', 0.0),
                        'OPEN',
                        trade_data.get('magic', 0),
                        trade_data.get('comment', ''),
                        json.dumps(extra_data)
                    ))
                    conn.commit()
                    logger.info(f"Trade saved: {trade_data['ticket']}")
                    
            except Exception as e:
                logger.error(f"Failed to save trade {trade_data.get('ticket')}: {e}")

    def update_trade(self, ticket: int, updates: Dict[str, Any]):
        """
        更新交易状态 (Update Trade)
        
        用于更新 SL/TP, Partial Close 状态等。
        """
        with self.lock:
            try:
                # Separate standard columns from extra_data
                columns = ['sl', 'tp', 'close_price', 'close_time', 'profit', 'status']
                std_updates = {k: v for k, v in updates.items() if k in columns}
                extra_updates = {k: v for k, v in updates.items() if k not in columns}
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    
                    # Update standard columns
                    if std_updates:
                        set_clause = ", ".join([f"{k} = ?" for k in std_updates.keys()])
                        values = list(std_updates.values())
                        values.append(ticket)
                        cursor.execute(f"UPDATE trades SET {set_clause} WHERE ticket = ?", values)
                    
                    # Update extra_data if needed
                    if extra_updates:
                        # First fetch existing extra_data
                        cursor.execute("SELECT extra_data FROM trades WHERE ticket = ?", (ticket,))
                        row = cursor.fetchone()
                        if row:
                            current_extra = json.loads(row['extra_data']) if row['extra_data'] else {}
                            current_extra.update(extra_updates)
                            cursor.execute("UPDATE trades SET extra_data = ? WHERE ticket = ?", 
                                         (json.dumps(current_extra), ticket))
                    
                    conn.commit()
                    # logger.debug(f"Trade updated: {ticket}")
                    
            except Exception as e:
                logger.error(f"Failed to update trade {ticket}: {e}")

    def close_trade(self, ticket: int, close_price: float, profit: float):
        """
        关闭交易 (Close Trade)
        
        Mark trade as CLOSED and update final metrics.
        """
        with self.lock:
            try:
                close_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                    UPDATE trades 
                    SET status = 'CLOSED', close_price = ?, profit = ?, close_time = ?
                    WHERE ticket = ?
                    """, (close_price, profit, close_time, ticket))
                    conn.commit()
                    logger.info(f"Trade closed in DB: {ticket} (P/L: {profit:.2f})")
            except Exception as e:
                logger.error(f"Failed to close trade {ticket}: {e}")

    def get_active_trades(self) -> List[Dict]:
        """
        获取所有活动交易 (Get Active Trades)
        
        用于系统启动时恢复状态。
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM trades WHERE status = 'OPEN'")
                rows = cursor.fetchall()
                
                trades = []
                for row in rows:
                    trade = dict(row)
                    # Parse extra_data and merge it back
                    if trade['extra_data']:
                        extra = json.loads(trade['extra_data'])
                        trade.update(extra)
                    del trade['extra_data']
                    trades.append(trade)
                    
                return trades
        except Exception as e:
            logger.error(f"Failed to get active trades: {e}")
            return []

    def get_trade_history(self, limit: int = 100) -> List[Dict]:
        """获取历史交易记录"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT * FROM trades 
                WHERE status = 'CLOSED' 
                ORDER BY close_time DESC 
                LIMIT ?
                """, (limit,))
                rows = cursor.fetchall()
                
                trades = []
                for row in rows:
                    trade = dict(row)
                    if trade['extra_data']:
                        extra = json.loads(trade['extra_data'])
                        trade.update(extra)
                    del trade['extra_data']
                    
                    # Map fields for UI compatibility
                    trade['time'] = trade.get('close_time', trade.get('open_time', ''))
                    trade['price'] = trade.get('close_price', trade.get('open_price', 0.0))
                    
                    trades.append(trade)
                return trades
        except Exception as e:
            logger.error(f"Failed to get trade history: {e}")
            return []

    def get_total_profit(self) -> float:
        """Get total realized profit from all closed trades"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT SUM(profit) FROM trades WHERE status = 'CLOSED'")
                result = cursor.fetchone()[0]
                return result if result else 0.0
        except Exception as e:
            logger.error(f"Failed to get total profit: {e}")
            return 0.0

if __name__ == "__main__":
    # Test
    logging.basicConfig(level=logging.INFO)
    db = DatabaseManager("test.db")
    
    # Mock Trade
    trade = {
        'ticket': 12345,
        'symbol': 'XAUUSD',
        'type': 'BUY',
        'volume': 0.1,
        'price_open': 2000.0,
        'sl': 1990.0,
        'tp': 2020.0,
        'magic': 1001,
        'comment': 'Test Trade',
        'partial_close_done': False
    }
    
    print("Saving trade...")
    db.save_trade(trade)
    
    print("Active trades:", db.get_active_trades())
    
    print("Updating trade...")
    db.update_trade(12345, {'sl': 1995.0, 'partial_close_done': True})
    
    print("Closing trade...")
    db.close_trade(12345, 2010.0, 100.0)
    
    print("History:", db.get_trade_history())
    
    # Cleanup
    import os
    os.remove("test.db")
