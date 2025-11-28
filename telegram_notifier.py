"""
Telegram Notification Module
Send trading alerts to Telegram
"""
import requests
import json
import logging
from datetime import datetime
from typing import Optional

# Setup logging
logger = logging.getLogger(__name__)


class TelegramNotifier:
    """
    Telegram 通知模块 (Telegram Notifier)
    
    负责发送交易信号、执行警报和账户状态更新到 Telegram。
    同时支持接收远程控制命令 (/status, /stop, /close_all)。
    """
    
    def __init__(self, bot_token: str = "", chat_id: str = ""):
        """
        Initialize Telegram notifier
        
        Args:
            bot_token: Telegram Bot Token (from @BotFather)
            chat_id: Your Telegram Chat ID (from @userinfobot)
        """
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.enabled = False
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
    def configure(self, bot_token: str, chat_id: str):
        """Update configuration"""
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.base_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        
    def enable(self):
        """Enable notifications"""
        if self.bot_token and self.chat_id:
            self.enabled = True
            return True
        return False
    
    def disable(self):
        """Disable notifications"""
        self.enabled = False
        
    def test_connection(self) -> bool:
        """Test Telegram connection"""
        return self.send_message("✅ Telegram 连接测试成功！\n\nAlpha Quant Terminal 已就绪。")
    
    def send_message(self, message: str, parse_mode: str = "HTML") -> bool:
        """
        发送消息到 Telegram (Send Message)
        
        Args:
            message: 消息内容
            parse_mode: 解析模式 ("HTML" 或 "Markdown")
            
        Returns:
            bool: 发送是否成功
        """
        if not self.enabled:
            return False
            
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured")
            return False
        
        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": parse_mode
            }
            
            response = requests.post(self.base_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                logger.info("Telegram message sent successfully")
                return True
            else:
                logger.error(f"Telegram error: {response.status_code} - {response.text}")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("Telegram request timeout")
            return False
        except Exception as e:
            logger.error(f"Failed to send Telegram message: {e}")
            return False
    
    def send_signal_alert(self, signal: str, confidence: float, price: float, symbol: str = "XAUUSD"):
        """
        发送交易信号警报 (Send Signal Alert)
        
        格式化为易读的 HTML 消息，包含信号方向、置信度和当前价格。
        """
        emoji = "🟢" if signal == "BUY" else "🔴" if signal == "SELL" else "⚪"
        
        message = f"""
{emoji} <b>交易信号</b>

<b>品种:</b> {symbol}
<b>信号:</b> {signal}
<b>置信度:</b> {confidence*100:.1f}%
<b>价格:</b> ${price:.2f}
<b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--
Alpha Quant Terminal
"""
        return self.send_message(message)
    
    def send_trade_alert(self, action: str, symbol: str, price: float, lot_size: float):
        """Send trade execution alert"""
        emoji = "✅" if action in ["BUY", "SELL"] else "⏹"
        
        message = f"""
{emoji} <b>交易执行</b>

<b>操作:</b> {action}
<b>品种:</b> {symbol}
<b>数量:</b> {lot_size} Lots
<b>价格:</b> ${price:.2f}
<b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--
Alpha Quant Terminal
"""
        return self.send_message(message)
    
    def send_pnl_alert(self, pnl: float, balance: float, equity: float):
        """Send P&L update"""
        emoji = "📈" if pnl > 0 else "📉" if pnl < 0 else "➖"
        
        message = f"""
{emoji} <b>账户状态</b>

<b>浮动盈亏:</b> ${pnl:+.2f}
<b>余额:</b> ${balance:,.2f}
<b>净值:</b> ${equity:,.2f}
<b>时间:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

--
Alpha Quant Terminal
"""
        return self.send_message(message)
    
    def start_command_listener(self, command_callback):
        """
        启动命令监听器 (Start Command Listener)
        
        在独立线程中启动长轮询 (Long Polling)，监听来自用户的命令。
        
        Args:
            command_callback: 收到命令时的回调函数
                             Signature: callback(command: str) -> str (response)
        """
        import threading
        
        self.command_callback = command_callback
        self.listening = True
        self.last_update_id = 0
        
        listener_thread = threading.Thread(target=self._poll_updates, daemon=True)
        listener_thread.start()
        
        logger.info("Telegram command listener started")
    
    def stop_command_listener(self):
        """Stop listening for commands"""
        self.listening = False
        logger.info("Telegram command listener stopped")
    
    def _poll_updates(self):
        """
        轮询更新 (Poll Updates)
        
        使用 getUpdates API 进行长轮询。
        运行在后台守护线程中，不会阻塞主程序。
        """
        get_updates_url = f"https://api.telegram.org/bot{self.bot_token}/getUpdates"
        
        while self.listening:
            try:
                params = {
                    'offset': self.last_update_id + 1,
                    'timeout': 30,
                    'allowed_updates': ['message']
                }
                
                response = requests.get(get_updates_url, params=params, timeout=35)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    if data.get('ok') and data.get('result'):
                        for update in data['result']:
                            self.last_update_id = update['update_id']
                            
                            # Process message
                            if 'message' in update and 'text' in update['message']:
                                message_text = update['message']['text']
                                chat_id = str(update['message']['chat']['id'])
                                
                                # Only respond to configured chat
                                if chat_id == self.chat_id:
                                    self._handle_command(message_text)
                
            except requests.exceptions.Timeout:
                # Timeout is expected, continue polling
                continue
            except Exception as e:
                logger.error(f"Error polling Telegram updates: {e}")
                import time
                time.sleep(5)  # Wait before retry
    
    def _handle_command(self, command_text: str):
        """Handle incoming command"""
        command = command_text.strip().lower()
        
        logger.info(f"Received Telegram command: {command}")
        
        # Call the registered callback
        if hasattr(self, 'command_callback') and self.command_callback:
            try:
                response = self.command_callback(command)
                if response:
                    self.send_message(response)
            except Exception as e:
                logger.error(f"Error handling command: {e}")
                self.send_message(f"❌ 命令执行失败: {str(e)}")
