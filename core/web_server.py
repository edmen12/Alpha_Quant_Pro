import threading
import sys
import uvicorn
from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import os
import logging
import time
import secrets
import hashlib
from collections import defaultdict

# Configure logging
logger = logging.getLogger(__name__)

app = FastAPI(title="Alpha Quant Terminal Monitor")

# --- SECURITY CONFIGURATION ---
security = HTTPBearer()
PASSWORD_HASH = None # SHA-256 Hash of the password
VALID_TOKENS = set() # Active session tokens
LOGIN_ATTEMPTS = defaultdict(list) # IP -> [timestamps]
MAX_LOGIN_ATTEMPTS = 5
LOGIN_WINDOW = 60 # seconds

# Global reference to the TradingEngine
trading_engine = None
start_callback = None

# --- MIDDLEWARE ---
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'; connect-src 'self' https://cdn.jsdelivr.net; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://unpkg.com https://cdn.tailwindcss.com https://cdn.jsdelivr.net; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; font-src https://fonts.gstatic.com; img-src 'self' data:;"
    return response

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to specific domains if possible
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- AUTHENTICATION ---
class LoginRequest(BaseModel):
    password: str

def set_password(plain_password: str):
    global PASSWORD_HASH
    if plain_password:
        PASSWORD_HASH = hashlib.sha256(plain_password.encode()).hexdigest()
    else:
        PASSWORD_HASH = None # No password set = Open Access (Not recommended)

def check_rate_limit(ip: str):
    now = time.time()
    # Clean old attempts
    LOGIN_ATTEMPTS[ip] = [t for t in LOGIN_ATTEMPTS[ip] if now - t < LOGIN_WINDOW]
    
    if len(LOGIN_ATTEMPTS[ip]) >= MAX_LOGIN_ATTEMPTS:
        logger.warning(f"Brute force attempt blocked from {ip}")
        return False
    return True

async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    if PASSWORD_HASH is None:
        return True # Open access if no password configured
        
    token = credentials.credentials
    if token not in VALID_TOKENS:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return True

@app.post("/api/login")
async def login(request: Request, login_data: LoginRequest):
    client_ip = request.client.host
    
    if not check_rate_limit(client_ip):
        raise HTTPException(status_code=429, detail="Too many login attempts. Please try again later.")
    
    if PASSWORD_HASH is None:
        return {"token": "open-access"}
        
    input_hash = hashlib.sha256(login_data.password.encode()).hexdigest()
    
    # Constant time comparison to prevent timing attacks (though less critical for SHA256)
    if secrets.compare_digest(input_hash, PASSWORD_HASH):
        token = secrets.token_urlsafe(32)
        VALID_TOKENS.add(token)
        logger.info(f"Successful login from {client_ip}")
        return {"token": token}
    else:
        LOGIN_ATTEMPTS[client_ip].append(time.time())
        logger.warning(f"Failed login attempt from {client_ip}")
        raise HTTPException(status_code=401, detail="Incorrect password")

@app.post("/api/logout")
async def logout(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    if token in VALID_TOKENS:
        VALID_TOKENS.remove(token)
    return {"message": "Logged out"}

# --- ENDPOINTS ---

class StatusResponse(BaseModel):
    running: bool
    symbol: str
    equity: float
    balance: float
    daily_pnl: float
    total_profit: float
    open_positions: int
    positions: list = []
    connection: bool
    price: float
    confidence: float

@app.get("/api/status", response_model=StatusResponse, dependencies=[Depends(verify_token)])
async def get_status():
    global trading_engine
    if not trading_engine:
        # Return default stopped state instead of error
        return StatusResponse(
            running=False, symbol="--", equity=0.0, balance=0.0, 
            daily_pnl=0.0, total_profit=0.0, open_positions=0, positions=[], connection=True, price=0.0, confidence=0.0
        )
    
    try:
        # Safely get positions
        raw_positions = getattr(trading_engine, 'open_positions_cache', [])
        # Ensure they are serializable (convert objects to dicts if needed)
        safe_positions = []
        for p in raw_positions:
            if isinstance(p, dict):
                safe_positions.append(p)
            elif hasattr(p, '__dict__'):
                safe_positions.append(p.__dict__)
            else:
                safe_positions.append({"symbol": str(p), "volume": 0, "profit": 0, "type": "?"})

        return StatusResponse(
            running=trading_engine.running,
            symbol=str(trading_engine.symbols),
            equity=getattr(trading_engine, 'last_equity', 0.0),
            balance=getattr(trading_engine, 'last_balance', 0.0),
            daily_pnl=getattr(trading_engine, 'last_daily_pnl', 0.0),
            total_profit=getattr(trading_engine, 'last_total_profit', 0.0),
            open_positions=len(safe_positions),
            positions=safe_positions,
            connection=True,
            price=getattr(trading_engine, 'last_price', 0.0),
            confidence=getattr(trading_engine, 'last_confidence', 0.0)
        )
    except Exception as e:
        logger.error(f"Web Status Error: {e}")
        return StatusResponse(
            running=False, symbol="Error", equity=0, balance=0, daily_pnl=0, open_positions=0, positions=[], connection=False
        )

@app.post("/api/stop", dependencies=[Depends(verify_token)])
async def stop_engine():
    global trading_engine
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    logger.warning("REMOTE STOP REQUEST RECEIVED")
    trading_engine.running = False
    return {"message": "Engine stopping..."}

@app.post("/api/start", dependencies=[Depends(verify_token)])
async def start_engine():
    global start_callback
    if not start_callback:
        raise HTTPException(status_code=503, detail="Start callback not linked")
    
    logger.info("REMOTE START REQUEST RECEIVED")
    try:
        start_callback()
        return {"message": "Engine start signal sent"}
    except Exception as e:
        logger.error(f"Remote Start Failed: {e}")
    except Exception as e:
        logger.error(f"Remote Start Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

class CloseTradeRequest(BaseModel):
    ticket: int
    symbol: str

@app.post("/api/close_trade", dependencies=[Depends(verify_token)])
async def close_trade(req: CloseTradeRequest):
    global trading_engine
    if not trading_engine:
        raise HTTPException(status_code=503, detail="Engine not initialized")
    
    try:
        # Check if engine has close_position method (it should)
        if hasattr(trading_engine, 'close_position'):
            # Run in executor to avoid blocking
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, trading_engine.close_position, req.ticket)
            if result:
                return {"message": f"Trade {req.ticket} closed"}
            else:
                raise HTTPException(status_code=400, detail="Failed to close trade")
        else:
            # Fallback for older engine versions or if method missing
            import MetaTrader5 as mt5
            if not mt5.initialize():
                raise HTTPException(status_code=500, detail="MT5 Init Failed")
            
            # Simple close logic
            position = mt5.positions_get(ticket=req.ticket)
            if not position:
                raise HTTPException(status_code=404, detail="Position not found")
            
            pos = position[0]
            tick = mt5.symbol_info_tick(pos.symbol)
            price = tick.bid if pos.type == 0 else tick.ask # 0=Buy, 1=Sell
            
            request = {
                "action": mt5.TRADE_ACTION_DEAL,
                "position": pos.ticket,
                "symbol": pos.symbol,
                "volume": pos.volume,
                "type": mt5.ORDER_TYPE_SELL if pos.type == 0 else mt5.ORDER_TYPE_BUY,
                "price": price,
                "deviation": 20,
                "magic": 123456,
                "comment": "Web Close",
                "type_time": mt5.ORDER_TIME_GTC,
                "type_filling": mt5.ORDER_FILLING_IOC,
            }
            
            result = mt5.order_send(request)
            if result.retcode != mt5.TRADE_RETCODE_DONE:
                raise HTTPException(status_code=400, detail=f"Close Failed: {result.comment}")
                
            return {"message": f"Trade {req.ticket} closed via fallback"}
            
    except Exception as e:
        logger.error(f"Close Trade Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- CONFIGURATION ENDPOINTS ---
get_config_callback = None
set_config_callback = None

@app.get("/api/config", dependencies=[Depends(verify_token)])
async def get_config():
    global get_config_callback
    if not get_config_callback:
        raise HTTPException(status_code=503, detail="Config callback not linked")
    try:
        return get_config_callback()
    except Exception as e:
        logger.error(f"Get Config Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/config", dependencies=[Depends(verify_token)])
async def set_config(config: dict):
    global set_config_callback
    if not set_config_callback:
        raise HTTPException(status_code=503, detail="Config callback not linked")
    try:
        set_config_callback(config)
        return {"message": "Configuration updated"}
    except Exception as e:
        logger.error(f"Set Config Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# --- ANALYTICS & LOGS ENDPOINTS ---

class AnalyticsResponse(BaseModel):
    win_rate: float
    profit_factor: float
    sharpe_ratio: float
    max_drawdown: float
    total_trades: int
    avg_duration: float
    equity_curve: dict # {'times': [], 'equity': []}

@app.get("/api/analytics", response_model=AnalyticsResponse, dependencies=[Depends(verify_token)])
async def get_analytics():
    global trading_engine
    if not trading_engine:
        # Return empty analytics instead of error
        return AnalyticsResponse(
            win_rate=0.0, profit_factor=0.0, sharpe_ratio=0.0,
            max_drawdown=0.0, total_trades=0, avg_duration=0.0,
            equity_curve={'times': [], 'equity': []}
        )
    
    try:
        # Check if method exists (it does in engine_core.py)
        if hasattr(trading_engine, 'get_analytics'):
            data = await trading_engine.get_analytics()
            metrics = data.get('metrics', {})
            curve = data.get('curve', {'times': [], 'equity': []})
            
            # Helper to sanitize data for JSON serialization (handle numpy & datetime)
            def _sanitize(obj):
                if hasattr(obj, 'item'): # Numpy scalar
                    return obj.item()
                if hasattr(obj, 'tolist'): # Numpy array
                    return obj.tolist()
                if hasattr(obj, 'isoformat'): # Datetime
                    return obj.isoformat()
                return obj

            # Sanitize Metrics
            safe_metrics = {k: _sanitize(v) for k, v in metrics.items()}
            
            # Sanitize Curve
            safe_times = [_sanitize(t) for t in curve.get('times', [])]
            safe_equity = [_sanitize(e) for e in curve.get('equity', [])]
            
            return AnalyticsResponse(
                win_rate=float(safe_metrics.get('win_rate', 0.0)),
                profit_factor=float(safe_metrics.get('profit_factor', 0.0)),
                sharpe_ratio=float(safe_metrics.get('sharpe_ratio', 0.0)),
                max_drawdown=float(safe_metrics.get('max_drawdown', 0.0)),
                total_trades=int(safe_metrics.get('total_trades', 0)),
                avg_duration=float(safe_metrics.get('avg_duration', 0.0)),
                equity_curve={'times': safe_times, 'equity': safe_equity}
            )
        else:
            # Fallback
            return AnalyticsResponse(
                win_rate=0.0, profit_factor=0.0, sharpe_ratio=0.0,
                max_drawdown=0.0, total_trades=0, avg_duration=0.0,
                equity_curve={'times': [], 'equity': []}
            )
    except Exception as e:
        logger.error(f"Get Analytics Failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/history", dependencies=[Depends(verify_token)])
async def get_history():
    """
    Fetch trading history (closed trades)
    """
    global trading_engine
    if not trading_engine:
        return {"trades": []}
    
    try:
        # Get trade history from engine's performance analyzer
        if hasattr(trading_engine, 'performance_analyzer'):
            trades = trading_engine.performance_analyzer.get_trade_history(days=30)
            # Convert datetime objects to ISO strings for JSON serialization
            serializable_trades = []
            for trade in trades:
                trade_copy = trade.copy()
                if 'time' in trade_copy and trade_copy['time']:
                    trade_copy['time'] = trade_copy['time'].isoformat()
                serializable_trades.append(trade_copy)
            return {"trades": serializable_trades}
        else:
            return {"trades": []}
    except Exception as e:
        logger.error(f"Get History Failed: {e}")
        return {"trades": []}

@app.get("/api/logs", dependencies=[Depends(verify_token)])
async def get_logs():
    """
    Fetch recent logs from the log file.
    """
    try:
        # We need to find the log file path. 
        # In terminal_apple.py, it's set to app_data_dir / "AlphaQuant.log" or similar.
        # We'll try to find it via PathManager if available, or assume standard location.
        from path_manager import PathManager
        log_path = PathManager.get_logs_dir() / "AlphaQuant.log"
        
        if not log_path.exists():
            return {"logs": ["Log file not found."]}
            
        # Read last 200 lines to ensure we get enough after filtering
        logs = []
        with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
            
            # Filter noisy logs
            filtered_lines = []
            for line in lines[-200:]:
                # Skip common noisy libraries unless it's an error
                if any(x in line for x in ["pyngrok", "urllib3", "asyncio", "uvicorn", "starlette", "watchfiles"]):
                    if "ERROR" not in line and "WARNING" not in line and "CRITICAL" not in line:
                        continue
                
                # Skip specific noisy messages
                if "join connections" in line or "client_loop: send disconnect" in line:
                    continue
                    
                filtered_lines.append(line.strip())
                
            # Return last 100 of filtered logs
            logs = filtered_lines[-100:]
            
        return {"logs": logs}
    except Exception as e:
        logger.error(f"Get Logs Failed: {e}")
        return {"logs": [f"Error reading logs: {str(e)}"]}

# Global Server Instance
server_instance = None
server_thread = None

def run_server(engine_instance, host="0.0.0.0", port=8000):
    """
    Run the Uvicorn server in a separate thread.
    """
    global trading_engine, server_instance
    trading_engine = engine_instance
    
    # Determine path to web_ui
    if getattr(sys, 'frozen', False):
        # Frozen: Use sys._MEIPASS
        base_dir = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
        web_ui_dir = os.path.join(base_dir, "web_ui")
    else:
        # Dev: Relative to this file
        current_dir = os.path.dirname(os.path.abspath(__file__))
        web_ui_dir = os.path.join(os.path.dirname(current_dir), "web_ui")
    
    if not os.path.exists(web_ui_dir):
        os.makedirs(web_ui_dir, exist_ok=True)
        # Create a dummy index.html if it doesn't exist
        with open(os.path.join(web_ui_dir, "index.html"), "w") as f:
            f.write("<h1>Alpha Quant Monitor</h1><p>Frontend not found.</p>")

    # Mount static files
    # Check if mounted already to avoid error on restart
    found = False
    for route in app.routes:
        if route.path == "/": found = True
    if not found:
        app.mount("/", StaticFiles(directory=web_ui_dir, html=True), name="static")
    
    logger.info(f"Starting Web Server on {host}:{port}")
    
    try:
        config = uvicorn.Config(app, host=host, port=port, log_level="info")
        server_instance = uvicorn.Server(config)
        server_instance.run()
    except Exception as e:
        logger.error(f"CRITICAL: Web Server Failed to Start: {e}")
        import traceback
        logger.error(traceback.format_exc())

def start_background_server(engine_instance, port=8000):
    global server_thread, server_instance
    if server_instance and server_instance.started:
        logger.warning("Web Server already running")
        return

    server_thread = threading.Thread(target=run_server, args=(engine_instance, "0.0.0.0", port), daemon=True)
    server_thread.start()

def stop_background_server():
    global server_instance
    if server_instance:
        logger.info("Stopping Web Server...")
        server_instance.should_exit = True
        server_instance = None

def set_engine(engine_instance):
    global trading_engine
    trading_engine = engine_instance
    logger.info("Web Server: Engine instance updated")
