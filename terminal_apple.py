"""
Alpha Quant Terminal - iOS 26 Concept Edition
Design Philosophy: "OLED Black", "Super Ellipse", "Floating Interface"
"""

import os
import sys
# sys.setrecursionlimit(5000) # Removed: Fixed underlying recursion issue
import onnxruntime
import shutil
from pathlib import Path
import core.web_server
import threading
import time
import tkinter as tk

# Fix for embedded Python Tkinter
# Use AppData for logging to avoid PermissionError in Program Files
app_data_dir = Path(os.environ.get('LOCALAPPDATA', Path.home())) / "AlphaQuantPro" / "logs"
app_data_dir.mkdir(parents=True, exist_ok=True)
log_path = app_data_dir / "debug_log.txt"

with open(log_path, "w") as f:
    f.write(f"STARTING\n")
    f.write(f"sys.executable: {sys.executable}\n")

# Redirect stdout/stderr to log file in frozen mode to capture crashes
if getattr(sys, 'frozen', False):
    sys.stdout = open(log_path, "a", buffering=1)
    sys.stderr = open(log_path, "a", buffering=1)
    
# Robust Tcl/Tk detection
if True:
    with open(log_path, "a") as f:
        f.write("Inside Frozen Block (Forced)\n")
    
    # Try to find tcl relative to executable, or CWD
    base_dir = Path(sys.executable).parent
    if not (base_dir / 'tcl').exists():
        base_dir = Path.cwd()
        
    tcl_dir = base_dir / 'tcl'
    print(f"DEBUG: Checking tcl_dir = {tcl_dir}, exists={tcl_dir.exists()}")
    if tcl_dir.exists():
        tcl_lib = next(tcl_dir.glob('tcl8*'), None)
        tk_lib = next(tcl_dir.glob('tk8*'), None)
        print(f"DEBUG: tcl_lib={tcl_lib}, tk_lib={tk_lib}")
        if tcl_lib: 
            os.environ['TCL_LIBRARY'] = str(tcl_lib)
            print(f"DEBUG: Set TCL_LIBRARY={os.environ['TCL_LIBRARY']}")
        if tk_lib: 
            os.environ['TK_LIBRARY'] = str(tk_lib)
            print(f"DEBUG: Set TK_LIBRARY={os.environ['TK_LIBRARY']}")

    import traceback

    try:
        with open(log_path, "a") as f: f.write("Importing customtkinter...\n")
        import customtkinter as ctk

        with open(log_path, "a") as f: f.write("Importing LoggerSetup...\n")
        from logger_setup import LoggerSetup
        
        with open(log_path, "a") as f: f.write("Importing ConfigManager...\n")
        from config_manager import ConfigManager
        
        with open(log_path, "a") as f: f.write("Importing DatabaseManager...\n")
        from database_manager import DatabaseManager
        
        with open(log_path, "a") as f: f.write("Importing NewsCalendar...\n")
        from news_calendar import NewsCalendar
        
        with open(log_path, "a") as f: f.write("Importing UpdateChecker...\n")
        from update_checker import UpdateChecker
        
        with open(log_path, "a") as f: f.write("Importing PathManager...\n")
        from path_manager import PathManager
        
        with open(log_path, "a") as f: f.write("Importing TelegramNotifier...\n")
        from telegram_notifier import TelegramNotifier
        
        with open(log_path, "a") as f: f.write("Importing TradingEngine...\n")
        from engine_core import TradingEngine
        from performance_analyzer import PerformanceAnalyzer
        
        with open(log_path, "a") as f: f.write("Importing queue/time/asyncio/threading...\n")
        import queue
        import time
        import asyncio
        import threading
        
        with open(log_path, "a") as f: f.write("Importing pandas...\n")
        import pandas as pd
        
        with open(log_path, "a") as f: f.write("Importing matplotlib...\n")
        import matplotlib.pyplot as plt
        from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
        
        with open(log_path, "a") as f: f.write("Importing tkinter...\n")
        from tkinter import messagebox, filedialog
        
        with open(log_path, "a") as f: f.write("Imports COMPLETED.\n")

    except Exception as e:
        with open(log_path, "a") as f:
            f.write(f"\nCRITICAL IMPORT ERROR:\n")
            f.write(traceback.format_exc())
            f.write(f"\n")
        # Re-raise to ensure app crashes visibly if needed, or handle gracefully
        raise e

# Setup Logger
LoggerSetup.setup_logging()
logger = LoggerSetup.get_logger("Terminal")

# License Manager
try:
    from core.license_manager import LicenseManager
except ImportError:
    # Fallback if not found (during dev before compile?)
    # or creates a dummy if excluded? 
    # Better to fail secure if missing.
    logger.critical("License Manager Missing!")
    LicenseManager = None


# ============================================================================
# 1. Design System (iOS 26 Future)
# ============================================================================

class DS:
    """Design System - The DNA of the app"""
    
    # Colors (Dark Mode Only)
    BG_MAIN = "#000000"         # Pure Black
    BG_CARD = "#161618"         # Deep Grey (Floating)
    BG_SIDEBAR = "#121212"      # Sidebar Background
    BG_ISLAND = "#2C2C2E"       # Dynamic Island Color
    
    # Accents
    ACCENT_BLUE = "#0A84FF"     # iOS Neon Blue
    ACCENT_PURPLE = "#BF5AF2"   # iOS Neon Purple
    ACCENT_RED = "#FF453A"      # iOS Neon Red
    ACCENT_GREEN = "#30D158"    # iOS Neon Green
    ACCENT_ORANGE = "#FF9F0A"   # iOS Neon Orange
    
    # Text
    TEXT_PRIMARY = "#FFFFFF"
    TEXT_SECONDARY = "#8E8E93"  # Steel Grey
    TEXT_TERTIARY = "#48484A"
    
    # Dimensions
    RADIUS_L = 24
    RADIUS_M = 16
    RADIUS_S = 12
    
    BTN_HEIGHT = 48
    
    # Typography (Bold / Heavy Style)
    @staticmethod
    def font_display_xl(): return ctk.CTkFont(family="Segoe UI Semibold", size=42)
    @staticmethod
    def font_display_l(): return ctk.CTkFont(family="Segoe UI Semibold", size=28)
    @staticmethod
    def font_title(): return ctk.CTkFont(family="Segoe UI", size=16, weight="bold")
    @staticmethod
    def font_body(): return ctk.CTkFont(family="Segoe UI", size=15, weight="bold")
    @staticmethod
    def font_normal(): return ctk.CTkFont(family="Segoe UI", size=14, weight="normal") # Non-bold for long text
    @staticmethod
    def font_mono(): return ctk.CTkFont(family="Consolas", size=26, weight="bold")
    @staticmethod
    def font_input_mono(): return ctk.CTkFont(family="Consolas", size=14, weight="bold")

# ============================================================================
# 2. Custom Components
# ============================================================================

class AppleCard(ctk.CTkFrame):
    def __init__(self, parent, **kwargs):
        super().__init__(parent, 
                         fg_color=DS.BG_CARD, 
                         corner_radius=DS.RADIUS_L,
                         border_width=1,
                         border_color="#2C2C2E",
                         **kwargs)

class CapsuleButton(ctk.CTkButton):
    def __init__(self, parent, text, color=DS.ACCENT_BLUE, **kwargs):
        hover_color = kwargs.pop("hover_color", color)
        super().__init__(parent,
                         text=text,
                         fg_color=color,
                         hover_color=hover_color,
                         height=DS.BTN_HEIGHT,
                         corner_radius=DS.BTN_HEIGHT/2,
                         font=ctk.CTkFont(family="Segoe UI", size=15, weight="bold"),
                         **kwargs)

class StatIsland(ctk.CTkFrame):
    def __init__(self, parent, label, value, color=DS.TEXT_PRIMARY):
        super().__init__(parent, fg_color=DS.BG_CARD, corner_radius=DS.RADIUS_M)
        self.label = ctk.CTkLabel(self, text=label.upper(), 
                                font=ctk.CTkFont(family="Segoe UI", size=11, weight="bold"),
                                text_color=DS.TEXT_SECONDARY)
        self.label.pack(padx=20, pady=(15, 0), anchor="w")
        self.value = ctk.CTkLabel(self, text=value, 
                                font=DS.font_mono(),
                                text_color=color)
        self.value.pack(padx=20, pady=(5, 15), anchor="w")

    def update(self, new_value, new_color=None):
        self.value.configure(text=new_value)
        if new_color:
            self.value.configure(text_color=new_color)

# ============================================================================
# 3. Views
# ============================================================================

class ViewDashboard(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Header
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.pack(fill="x", pady=(20, 40))
        ctk.CTkLabel(self.header, text="Overview", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        
        # Status Badge
        self.status_badge = ctk.CTkButton(self.header, text="● READY TO START", 
                                        fg_color=DS.BG_ISLAND, 
                                        text_color=DS.TEXT_SECONDARY,
                                        hover=False,
                                        height=32,
                                        corner_radius=16,
                                        font=ctk.CTkFont(size=12, weight="bold"),
                                        width=120)
        self.status_badge.pack(side="right")
        
        # AI Status Line (New Feature)
        self.lbl_ai_status = ctk.CTkLabel(self, text="AI Waiting...", 
                                        font=ctk.CTkFont(family="Consolas", size=13, weight="bold"),
                                        text_color=DS.ACCENT_PURPLE,
                                        anchor="w")
        self.lbl_ai_status.pack(fill="x", padx=0, pady=(0, 20))

        # Stats Grid
        self.stats_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_grid.pack(fill="x", pady=(0, 30))
        self.stats_grid.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.stat_pnl = StatIsland(self.stats_grid, "P&L", "+$0.00", color=DS.ACCENT_GREEN)
        self.stat_pnl.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.stat_price = StatIsland(self.stats_grid, "PRICE", "$0.00", color=DS.ACCENT_BLUE)
        self.stat_price.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.stat_balance = StatIsland(self.stats_grid, "BALANCE", "$0.00")
        self.stat_balance.grid(row=0, column=2, padx=10, sticky="ew")
        
        self.stat_equity = StatIsland(self.stats_grid, "EQUITY", "$0.00")
        self.stat_equity.grid(row=0, column=3, padx=(10, 0), sticky="ew")
        
        # Positions Card
        self.pos_card = AppleCard(self)
        self.pos_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.pos_card, text="OPEN POSITIONS", 
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color=DS.TEXT_SECONDARY).pack(pady=(20, 10), anchor="w", padx=20)
        
        self.btn_close_all = ctk.CTkButton(self.pos_card, text="CLOSE ALL", width=80, height=24,
                                         fg_color="#3A3A3C", hover_color="#48484A",
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         command=self._close_all)
        self.btn_close_all.place(relx=0.95, rely=0.05, anchor="ne")

        # Positions Header
        pos_header = ctk.CTkFrame(self.pos_card, fg_color="transparent")
        pos_header.pack(fill="x", padx=20, pady=(0, 5))
        
        font_thin = ctk.CTkFont(family="Segoe UI", size=12) # Normal weight
        
        ctk.CTkLabel(pos_header, text="TIME", width=110, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="SYMBOL", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="TYPE", width=50, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="VOL", width=50, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="OPEN", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="SL", width=60, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="TP", width=60, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="P/L", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(pos_header, text="ACTION", width=60, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)

        self.pos_container = ctk.CTkScrollableFrame(self.pos_card, fg_color="transparent", height=150)
        self.pos_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.empty_pos_label = ctk.CTkLabel(self.pos_container, text="No open positions.", text_color=DS.TEXT_TERTIARY)
        self.empty_pos_label.pack(pady=20)

        # Trades Card
        self.trades_card = AppleCard(self)
        self.trades_card.pack(fill="both", expand=True, pady=(20, 0))
        
        ctk.CTkLabel(self.trades_card, text="TRADING HISTORY", 
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color=DS.TEXT_SECONDARY).pack(pady=(20, 10), anchor="w", padx=20)

        # History Header
        hist_header = ctk.CTkFrame(self.trades_card, fg_color="transparent")
        hist_header.pack(fill="x", padx=20, pady=(0, 5))
        
        ctk.CTkLabel(hist_header, text="TIME", width=110, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="SYMBOL", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="TYPE", width=50, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="VOL", width=50, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="OPEN", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="CLOSE", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="PROFIT", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)

        self.trades_container = ctk.CTkScrollableFrame(self.trades_card, fg_color="transparent", height=150)
        self.trades_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.empty_trades_label = ctk.CTkLabel(self.trades_container, text="No trades yet.", text_color=DS.TEXT_TERTIARY)
        self.empty_trades_label.pack(pady=20)
        
        self.pos_rows = {}
        self.last_history_sig = None

    def _close_all(self):
        app = self.winfo_toplevel()
        if hasattr(app, 'engine') and app.engine:
            if messagebox.askyesno("Confirm", "Close ALL Positions?"):
                app.engine.close_all_positions()

    def update_status(self, status):
        # Update connection status
        connected = status.get("connected", False)
        if connected:
            self.status_badge.configure(text="● CONNECTED", text_color=DS.ACCENT_GREEN)
            
            # Update Stats
            profit = status.get("profit", 0.0)
            self.stat_pnl.update(f"{profit:+.2f}", DS.ACCENT_GREEN if profit >= 0 else DS.ACCENT_RED)
            
            price = status.get("price", 0.0)
            self.stat_price.update(f"{price:.2f}")
            
            self.stat_balance.update(f"${status.get('balance', 0):,.2f}")
            self.stat_equity.update(f"${status.get('equity', 0):,.2f}")
            
            # Update Tables
            positions = status.get("positions", [])
            self._update_positions(positions)
            
            # Update Trades 
            history = status.get("history", [])
            self._update_trades(history)
            
            # Update AI Status (New Feature)
            ai_status = status.get("ai_status", "AI Idle")
            self.lbl_ai_status.configure(text=f"{ai_status}")
            
        else:
            self.status_badge.configure(text="● DISCONNECTED", text_color=DS.ACCENT_RED)
            self.lbl_ai_status.configure(text="Engine Offline")
    
    def _update_positions(self, positions):
        # 1. Identify stale tickets
        current_tickets = {p.get('ticket') for p in positions if p.get('ticket')}
        existing_tickets = set(self.pos_rows.keys())
        
        # Remove stale
        for t in existing_tickets - current_tickets:
            self.pos_rows[t]['frame'].destroy()
            del self.pos_rows[t]
        
        if not positions:
            self.empty_pos_label.pack(pady=20)
            return
        self.empty_pos_label.pack_forget()

        font_mono = ctk.CTkFont(family="Consolas", size=12)
        
        for pos in positions:
            t = pos.get("ticket")
            if not t: continue
            
            # Extract Data
            pnl = pos.get("profit", 0.0)
            pnl_color = DS.ACCENT_GREEN if pnl >= 0 else DS.ACCENT_RED
            pnl_text = f"{pnl:+.2f}"
            price_current = f"{pos.get('price_current', 0.0):.2f}"
            
            if t in self.pos_rows:
                # SMART UPDATE
                cache = self.pos_rows[t]
                try:
                    cache['lbl_pnl'].configure(text=pnl_text, text_color=pnl_color)
                except Exception:
                     pass
            else:
                # CREATE NEW ROW
                row = ctk.CTkFrame(self.pos_container, fg_color="transparent")
                row.pack(fill="x", pady=2)
                
                time_str = str(pos.get("time", ""))
                symbol = pos.get("symbol", "")
                
                raw_type = pos.get("type")
                if isinstance(raw_type, int):
                    type_str = "BUY" if raw_type == 0 else "SELL"
                else:
                    type_str = str(raw_type)
                    
                type_color = DS.ACCENT_GREEN if type_str == "BUY" else DS.ACCENT_RED
                vol = f"{pos.get('volume', 0.0):.2f}"
                open_price = f"{pos.get('price_open', 0.0):.2f}"
                if 'price_open' not in pos: open_price = f"{pos.get('price', 0.0):.2f}"
                
                sl = f"{pos.get('sl', 0.0):.2f}"
                tp = f"{pos.get('tp', 0.0):.2f}"
                
                ctk.CTkLabel(row, text=time_str, width=110, anchor="w", font=font_mono).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=symbol, width=70, anchor="w", font=font_mono).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=type_str, width=50, anchor="w", text_color=type_color, font=font_mono).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=vol, width=50, anchor="w", font=font_mono).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=open_price, width=70, anchor="w", font=font_mono).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=sl, width=60, anchor="w", font=font_mono).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=tp, width=60, anchor="w", font=font_mono).pack(side="left", expand=True)
                
                lbl_pnl = ctk.CTkLabel(row, text=pnl_text, width=70, anchor="w", text_color=pnl_color, font=font_mono)
                lbl_pnl.pack(side="left", expand=True)
                
                close_btn = ctk.CTkButton(row, text="×", width=30, height=24, fg_color=DS.BG_ISLAND, hover_color="#3A3A3C",
                                        command=lambda t=t: self._close_position(t))
                close_btn.pack(side="left", padx=(0, 10))
                
                self.pos_rows[t] = {
                    'frame': row,
                    'lbl_pnl': lbl_pnl
                }

    def _update_trades(self, history):
        # CACHE CHECK
        if not history:
             current_sig = "empty"
        else:
             current_sig = f"{len(history)}_{history[0].get('ticket')}"
             
        if current_sig == self.last_history_sig:
            return
        self.last_history_sig = current_sig

        # Destroy all except empty_label
        for widget in self.trades_container.winfo_children():
            if widget == self.empty_trades_label:
                widget.pack_forget()
            else:
                try:
                    widget.destroy()
                except:
                    pass
            
        if not history:
            self.empty_trades_label.pack(pady=20)
            return
        
        font_mono = ctk.CTkFont(family="Consolas", size=12)
        display_history = history[:50]
        
        for trade in display_history:
            row = ctk.CTkFrame(self.trades_container, fg_color="transparent")
            row.pack(fill="x", pady=2)
            
            symbol = trade.get("symbol", "")
            
            raw_type = trade.get("type", "BUY")
            if isinstance(raw_type, int):
                 type_str = "BUY" if raw_type == 0 else "SELL" if raw_type == 1 else str(raw_type)
            else:
                 type_str = str(raw_type)

            type_color = DS.ACCENT_GREEN if type_str == "BUY" else DS.ACCENT_RED
            vol = f"{trade.get('volume', 0.0):.2f}"
            open_price = f"{trade.get('open_price', 0.0):.2f}"
            if 'open_price' not in trade: open_price = f"{trade.get('price', 0.0):.2f}"
            
            close_price = f"{trade.get('price_close', 0.0):.2f}"
            if 'price_close' not in trade: close_price = "0.00"
                
            profit = trade.get("profit", 0.0)
            pnl_str = f"{profit:+.2f}"
            pnl_color = DS.ACCENT_GREEN if profit >= 0 else DS.ACCENT_RED
            
            ctk.CTkLabel(row, text=str(trade.get("time", "")), width=110, anchor="w", font=font_mono).pack(side="left", expand=True)
            ctk.CTkLabel(row, text=symbol, width=70, anchor="w", font=font_mono).pack(side="left", expand=True)
            ctk.CTkLabel(row, text=type_str, width=50, anchor="w", text_color=type_color, font=font_mono).pack(side="left", expand=True)
            ctk.CTkLabel(row, text=vol, width=50, anchor="w", font=font_mono).pack(side="left", expand=True)
            ctk.CTkLabel(row, text=open_price, width=70, anchor="w", font=font_mono).pack(side="left", expand=True)
            ctk.CTkLabel(row, text=close_price, width=70, anchor="w", font=font_mono).pack(side="left", expand=True)
            ctk.CTkLabel(row, text=pnl_str, width=70, anchor="w", text_color=pnl_color, font=font_mono).pack(side="left", expand=True)

    def _close_position(self, ticket):
        app = self.winfo_toplevel()
        if hasattr(app, 'engine') and app.engine:
            app.engine.close_position(ticket)



class ViewLogs(ctk.CTkFrame):
    MAX_LOG_LINES = 1000  # 最大日志行数，防止内存泄漏
    
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="System Logs", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        
        # 添加清空日志按钮
        self.btn_clear = ctk.CTkButton(header, text="Clear Logs", width=100, height=32,
                                      fg_color=DS.BG_ISLAND, hover_color="#3A3A3C",
                                      font=ctk.CTkFont(size=12, weight="bold"),
                                      command=self._clear_logs)
        self.btn_clear.pack(side="right")
        
        self.log_text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12),
                                     fg_color=DS.BG_ISLAND, text_color=DS.TEXT_SECONDARY)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        
        self.log_line_count = 0  # 追踪日志行数
        self._poll_logs()

    def _clear_logs(self):
        """清空日志显示"""
        self.log_text.configure(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.configure(state="disabled")
        self.log_line_count = 0

    def _poll_logs(self):
        try:
            log_queue = LoggerSetup.get_log_queue()
            while not log_queue.empty():
                record = log_queue.get_nowait()
                msg = record.getMessage()
                formatted = f"[{record.levelname}] {msg}\n"
                
                self.log_text.configure(state="normal")
                self.log_text.insert("end", formatted)
                self.log_line_count += 1
                
                # 限制日志行数，删除旧日志
                if self.log_line_count > self.MAX_LOG_LINES:
                    # 删除最旧的100行，避免频繁删除
                    self.log_text.delete("1.0", "101.0")
                    self.log_line_count -= 100
                
                self.log_text.see("end")
                self.log_text.configure(state="disabled")
        except queue.Empty:
            pass
        finally:
            self.after(100, self._poll_logs)

class ViewAnalytics(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 30))
        ctk.CTkLabel(header, text="Performance Analytics", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        
        # Refresh Button
        self.btn_refresh = CapsuleButton(header, "Refresh", width=100, 
                                       color=DS.BG_ISLAND, hover_color=DS.ACCENT_BLUE,
                                       command=self._manual_refresh)
        self.btn_refresh.pack(side="right")
        
        # Metrics Grid
        self.metrics_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.metrics_grid.pack(fill="x", pady=(0, 30))
        self.metrics_grid.grid_columnconfigure((0,1,2), weight=1)
        
        self.win_rate_card = StatIsland(self.metrics_grid, "WIN RATE", "0.0%", color=DS.ACCENT_GREEN)
        self.win_rate_card.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        self.pf_card = StatIsland(self.metrics_grid, "PROFIT FACTOR", "0.00", color=DS.ACCENT_BLUE)
        self.pf_card.grid(row=0, column=1, padx=10, sticky="ew")
        
        self.sharpe_card = StatIsland(self.metrics_grid, "SHARPE RATIO", "0.00", color=DS.ACCENT_PURPLE)
        self.sharpe_card.grid(row=0, column=2, padx=(10, 0), sticky="ew")
        
        self.dd_card = StatIsland(self.metrics_grid, "MAX DRAWDOWN", "0.0%", color=DS.ACCENT_RED)
        self.dd_card.grid(row=1, column=0, padx=(0, 10), pady=(20, 0), sticky="ew")
        
        self.trades_card = StatIsland(self.metrics_grid, "TOTAL TRADES", "0")
        self.trades_card.grid(row=1, column=1, padx=10, pady=(20, 0), sticky="ew")
        
        self.duration_card = StatIsland(self.metrics_grid, "AVG DURATION", "0.0h")
        self.duration_card.grid(row=1, column=2, padx=(10, 0), pady=(20, 0), sticky="ew")

        # Equity Curve
        self.chart_card = AppleCard(self)
        self.chart_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.chart_card, text="EQUITY CURVE", 
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color=DS.TEXT_SECONDARY).pack(pady=(20, 10), anchor="w", padx=20)
        
        self.fig, self.ax = plt.subplots(figsize=(10, 4), dpi=100)
        self.fig.patch.set_facecolor(DS.BG_CARD)
        self.ax.set_facecolor(DS.BG_CARD)
        self.ax.tick_params(axis='x', colors=DS.TEXT_SECONDARY)
        self.ax.tick_params(axis='y', colors=DS.TEXT_SECONDARY)
        for spine in self.ax.spines.values(): spine.set_color(DS.TEXT_TERTIARY)
        
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.chart_card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
        # Start refresh loop
        self.refresh_timer = self.after(1000, self._refresh_metrics)

    def _manual_refresh(self):
        """Manually trigger refresh"""
        if self.refresh_timer:
            self.after_cancel(self.refresh_timer)
            self.refresh_timer = None
        self._refresh_metrics()

    def _refresh_metrics(self):
        """Trigger background analysis"""
        if hasattr(self, 'btn_refresh'):
            self.btn_refresh.configure(state="disabled", text="Loading...")
            
        app = self.winfo_toplevel()
        if hasattr(app, 'engine') and app.engine and app.engine.running:
            # Submit task to engine's executor
            try:
                # Pass engine instance to the task
                future = app.engine.executor.submit(self._run_analysis_task, app.engine)
                self.after(100, lambda: self._check_analysis_result(future))
            except RuntimeError:
                # Executor might be shutdown
                if hasattr(self, 'btn_refresh'):
                    self.btn_refresh.configure(state="normal", text="Refresh")
        else:
            # Retry later if engine not running
            self.refresh_timer = self.after(5000, self._refresh_metrics)

    def _check_analysis_result(self, future):
        if future.done():
            try:
                data = future.result()
                self._update_ui_with_data(data)
            except Exception as e:
                logger.error(f"Analysis Task Failed: {e}")
            finally:
                if hasattr(self, 'btn_refresh'):
                    self.btn_refresh.configure(state="normal", text="Refresh")
                # Schedule next refresh
                self.refresh_timer = self.after(30000, self._refresh_metrics)
        else:
            # Keep checking
            self.after(100, lambda: self._check_analysis_result(future))

    def _run_analysis_task(self, engine):
        # This runs in background thread
        try:
            # Use cached sync method from engine
            return engine.get_analytics_sync(30)
        except Exception as e:
            logger.error(f"Analysis Calculation Error: {e}")
            return {
                'metrics': {
                    'win_rate': 0.0, 'profit_factor': 0.0, 'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0, 'total_trades': 0, 'avg_duration': 0.0
                },
                'curve': {'times': [], 'equity': []}
            }

    def _update_ui_with_data(self, data):
        """Update UI elements with fetched data"""
        try:
            metrics = data['metrics']
            curve_data = data['curve']
            
            self.win_rate_card.update(f"{metrics['win_rate']:.1f}%")
            self.pf_card.update(f"{metrics['profit_factor']:.2f}")
            self.sharpe_card.update(f"{metrics['sharpe_ratio']:.2f}")
            self.dd_card.update(f"{metrics['max_drawdown']:.1f}%")
            self.trades_card.update(str(metrics['total_trades']))
            self.duration_card.update(f"{metrics['avg_duration']:.1f}h")
            
            self.ax.clear()
            self.ax.set_facecolor(DS.BG_CARD)
            
            if curve_data['times'] and curve_data['equity']:
                # Convert strings to datetime for plotting if needed
                import matplotlib.dates as mdates
                
                times = [pd.to_datetime(t).to_pydatetime() for t in curve_data['times']]
                equity = curve_data['equity']
                
                # 1. Plot Main Line (Thicker, Smoother look)
                self.ax.plot(times, equity, color=DS.ACCENT_BLUE, linewidth=2, alpha=0.9)
                
                # 2. Add Area Fill (Premium Look)
                # Find a baseline that makes sense (min value slightly buffered)
                baseline = min(equity) * 0.9995 if equity else 0
                self.ax.fill_between(times, equity, baseline, color=DS.ACCENT_BLUE, alpha=0.15)
                
                # 3. Highlight Last Data Point
                if times:
                    self.ax.plot(times[-1], equity[-1], marker='o', color=DS.ACCENT_BLUE, markersize=6, alpha=1.0)
                    # Optional: Add text annotation for last value
                    # self.ax.text(times[-1], equity[-1], f" {equity[-1]:.2f}", color=DS.ACCENT_BLUE, ...)

                # 4. Refined Grid & Spines
                self.ax.grid(True, which='major', linestyle=':', color='white', alpha=0.08)
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                self.fig.autofmt_xdate()
                
                # Remove borders for cleaner look
                self.ax.spines['top'].set_visible(False)
                self.ax.spines['right'].set_visible(False)
                self.ax.spines['left'].set_visible(False) # Optional: Remove left axis line
                self.ax.spines['bottom'].set_color(DS.TEXT_TERTIARY)
            
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"UI Update Error: {e}")

class ViewAgents(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        # Resolve agents directory (Frozen vs Dev)
        if getattr(sys, 'frozen', False):
            # Frozen: Check for "agents" folder next to the executable first (Portable Mode)
            exe_dir = Path(sys.executable).parent
            local_agents = exe_dir / "agents"
            
            if local_agents.exists():
                self.agents_dir = local_agents
                logger.info(f"Using portable agents directory: {self.agents_dir}")
            else:
                # Fallback: Use AppData for persistence
                self.agents_dir = Path(os.environ.get('LOCALAPPDATA', Path.home())) / "AlphaQuantPro" / "agents"
                self.agents_dir.mkdir(parents=True, exist_ok=True)
                
                # Copy built-in agents from MEIPASS if not present (and if they exist in bundle)
                try:
                    bundled_agents = Path(sys._MEIPASS) / "agents"
                    if bundled_agents.exists():
                        for item in bundled_agents.iterdir():
                            if item.is_dir() and not (self.agents_dir / item.name).exists():
                                shutil.copytree(item, self.agents_dir / item.name, dirs_exist_ok=True)
                except Exception as e:
                    logger.error(f"Failed to copy bundled agents: {e}")
        else:
            # Dev: Use local agents folder
            self.agents_dir = Path("agents")
            
        ctk.CTkLabel(self, text="Configuration", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(anchor="w", pady=(0, 30))
        
        # Use Scrollable Frame
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        
        self.card = AppleCard(self.scroll)
        self.card.pack(fill="x")
        
        self._create_bundle_selector(self.card)
        self._add_desc(self.card, "Select the AI agent bundle containing your trained model, feature config, and strategy rules.")
        
        self.symbol_entry = self._create_input_row(self.card, "Symbols (comma sep)", "XAUUSD")
        self._add_desc(self.card, "Trading symbols to monitor. Use comma to separate multiple symbols (e.g., XAUUSD,EURUSD).")
        
        # Timeframe Selector
        tf_row = ctk.CTkFrame(self.card, fg_color="transparent")
        tf_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(tf_row, text="Timeframe", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.timeframe_var = ctk.StringVar(value="M15")
        self.timeframe_menu = ctk.CTkOptionMenu(tf_row, variable=self.timeframe_var, values=["M1", "M5", "M15", "M30", "H1", "H4", "D1"], 
                                                fg_color=DS.BG_ISLAND, button_color=DS.ACCENT_BLUE, width=100)
        self.timeframe_menu.pack(side="right")
        self._add_desc(self.card, "Chart timeframe for analysis. Lower timeframes = more trades but more noise. M15 is recommended for most strategies.")
        
        mode_row = ctk.CTkFrame(self.card, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(mode_row, text="Sizing Mode", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        
        self.mode_var = ctk.StringVar(value="Fixed Lot")
        self.mode_seg = ctk.CTkSegmentedButton(mode_row, values=["Fixed Lot", "Risk %"], 
                                             variable=self.mode_var, command=self._update_inputs)
        self.mode_seg.pack(side="right")
        
        self.lot_row, self.lot_entry = self._create_input_row(self.card, "Lot Size", "0.01", return_row=True)
        self._add_desc(self.card, "Fixed position size per trade. 0.01 lot = 1 micro lot = $0.01/pip for XAUUSD.")
        
        self.risk_row, self.risk_entry = self._create_input_row(self.card, "Risk %", "1.0", return_row=True)
        self._add_desc(self.card, "Percentage of account equity to risk per trade. Position size will be calculated dynamically based on stop loss distance.")
        
        self._update_inputs("Fixed Lot")
        
        self.max_spread_entry = self._create_input_row(self.card, "Smart Entry (Max Spread)", "500")
        self._add_desc(self.card, "Only enter trades when spread is below this threshold (in points). High spreads during volatile periods or low liquidity can significantly impact entry price and reduce profitability. Recommended: 30-50 for major pairs, 100-200 for gold.")
        
        self.max_loss_entry = self._create_input_row(self.card, "Max Daily Loss", "500")
        self._add_desc(self.card, "Maximum allowed daily loss in account currency. When reached, all positions will be closed and trading will stop until next day.")
        
        self.min_equity_entry = self._create_input_row(self.card, "Min Equity (Guard)", "0")
        self._add_desc(self.card, "Emergency equity floor. If account equity drops below this value, all positions will be immediately closed to prevent further losses.")
        
        news_row = ctk.CTkFrame(self.card, fg_color="transparent")
        news_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(news_row, text="News Filter", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.news_filter_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(news_row, text="Enable", variable=self.news_filter_var, fg_color=DS.ACCENT_BLUE).pack(side="right")
        self.news_buffer_entry = self._create_input_row(self.card, "News Buffer (min)", "30")
        self._add_desc(self.card, "Time buffer in minutes before and after high-impact economic news events (NFP, CPI, FOMC). During this window, new trades are blocked to avoid volatility spikes and unpredictable price movements. Set to 0 to disable time-based filtering.")
        
        trailing_row = ctk.CTkFrame(self.card, fg_color="transparent")
        trailing_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(trailing_row, text="Trailing Stop", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.trailing_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(trailing_row, text="Enable", variable=self.trailing_var, fg_color=DS.ACCENT_GREEN).pack(side="right")
        self.trailing_distance_entry = self._create_input_row(self.card, "Trailing Distance (points)", "50")
        self._add_desc(self.card, "Trailing stop activation distance in points. When price moves in your favor by this amount, stop loss begins following price at this fixed distance. Works like a ratchet - only moves in profitable direction, never backwards. Smaller values = tighter protection but may exit too early on normal retracements.")
        
        partial_row = ctk.CTkFrame(self.card, fg_color="transparent")
        partial_row.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(partial_row, text="Partial Close", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.partial_close_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(partial_row, text="Enable", variable=self.partial_close_var, fg_color=DS.ACCENT_PURPLE).pack(side="right")
        self.tp1_distance_entry = self._create_input_row(self.card, "TP1 Distance (points)", "50")
        self._add_desc(self.card, "First take-profit target distance from entry in points. When price reaches this level, partial close is triggered.")
        
        self.partial_close_percent_entry = self._create_input_row(self.card, "Partial Close %", "50")
        self._add_desc(self.card, "Percentage of position to close at TP1. After partial close, remaining position's stop loss is moved to break-even (entry price), creating a risk-free trade. Example: 50% closes half at TP1, remaining half runs with zero-risk.")
        
        self._create_mt5_selector(self.card)
        self._load_saved_config()

    def _add_desc(self, parent, text):
        label = ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11), text_color=DS.TEXT_SECONDARY, 
                            wraplength=600, justify="left", anchor="w")
        label.pack(anchor="w", padx=20, pady=(0, 10), fill="x")

    def _load_saved_config(self):
        config = ConfigManager.load()
        if config.get("bundle"): self.bundle_var.set(config["bundle"])
        if config.get("symbol"): self.symbol_entry.delete(0, "end"); self.symbol_entry.insert(0, config["symbol"])
        if config.get("timeframe"): self.timeframe_var.set(config["timeframe"])
        
        # Load sizing mode and lot size
        if config.get("risk_mode") == "fixed":
            self.mode_var.set("Fixed Lot")
            self._update_inputs("Fixed Lot")
        elif config.get("risk_mode") == "percent":
            self.mode_var.set("Risk %")
            self._update_inputs("Risk %")
        
        if config.get("lot_size"):
            self.lot_entry.delete(0, "end")
            self.lot_entry.insert(0, str(config["lot_size"]))
        if config.get("risk"):
            self.risk_entry.delete(0, "end")
            self.risk_entry.insert(0, str(config["risk"]))
        
        if config.get("news_buffer"): self.news_buffer_entry.delete(0, "end"); self.news_buffer_entry.insert(0, str(config["news_buffer"]))
        if config.get("trailing_enabled"): self.trailing_var.set(True)
        if config.get("trailing_distance"): self.trailing_distance_entry.delete(0, "end"); self.trailing_distance_entry.insert(0, str(config["trailing_distance"]))
        if config.get("partial_close_enabled"): self.partial_close_var.set(True)
        if config.get("tp1_distance"): self.tp1_distance_entry.delete(0, "end"); self.tp1_distance_entry.insert(0, str(config["tp1_distance"]))
        if config.get("partial_close_percent"): self.partial_close_percent_entry.delete(0, "end"); self.partial_close_percent_entry.insert(0, str(config["partial_close_percent"]))
        
        # Load MT5 Path
        if config.get("mt5"): self.mt5_var.set(config["mt5"])

    def _create_bundle_selector(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(row, text="Agent Bundle", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right")
        self.bundle_var = ctk.StringVar(value="Select Bundle")
        self.bundle_menu = ctk.CTkOptionMenu(btn_frame, variable=self.bundle_var, fg_color=DS.BG_ISLAND, button_color=DS.ACCENT_BLUE, width=200)
        self.bundle_menu.pack(side="left", padx=5)
        self.bundle_menu.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Import", width=60, fg_color=DS.BG_ISLAND, command=self._import_bundle).pack(side="left", padx=(0, 5))
        ctk.CTkButton(btn_frame, text="Delete", width=60, fg_color=DS.BG_ISLAND, command=self._delete_bundle).pack(side="left")
        self._refresh_bundles()

    def _create_mt5_selector(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(row, text="MT5 Path", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.mt5_var = ctk.StringVar(value="auto")
        self.mt5_path_entry = ctk.CTkEntry(row, textvariable=self.mt5_var, width=140, fg_color=DS.BG_MAIN, border_width=1, border_color="#333", font=DS.font_input_mono())
        self.mt5_path_entry.pack(side="right")
        ctk.CTkButton(row, text="...", width=40, fg_color=DS.BG_ISLAND, command=self._select_mt5).pack(side="right", padx=5)
        self._add_desc(parent, "Path to MetaTrader 5 terminal executable. Use 'auto' for automatic detection (recommended). If you have multiple MT5 installations, click '...' to select the specific terminal64.exe you want to use.")

    def _create_input_row(self, parent, label, default, return_row=False):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(row, text=label, font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        entry = ctk.CTkEntry(row, width=200, height=36, fg_color=DS.BG_MAIN, border_width=1, border_color="#333", text_color=DS.TEXT_PRIMARY, font=DS.font_input_mono())
        entry.pack(side="right")
        entry.insert(0, default)
        if return_row: return row, entry
        return entry

    def _update_inputs(self, value):
        if value == "Fixed Lot":
            self.lot_entry.configure(state="normal", fg_color=DS.BG_MAIN)
            self.risk_entry.configure(state="disabled", fg_color=DS.BG_ISLAND)
        else:
            self.lot_entry.configure(state="disabled", fg_color=DS.BG_ISLAND)
            self.risk_entry.configure(state="normal", fg_color=DS.BG_MAIN)

    def _refresh_bundles(self):
        agents_dir = self.agents_dir
        if not agents_dir.exists(): bundles = ["No Bundles"]
        else: bundles = [d.name for d in agents_dir.iterdir() if d.is_dir() and d.name.startswith("agent_bundle")]
        if not bundles: bundles = ["No Bundles"]
        self.bundle_menu.configure(values=bundles)
        self.bundle_var.set(bundles[0])

    def _import_bundle(self):
        path = filedialog.askdirectory(title="Select Bundle Folder")
        if path:
            src = Path(path)
            if not src.name.startswith("agent_bundle"):
                messagebox.showerror("Error", "Folder must start with 'agent_bundle'")
                return
            
            try:
                dst = self.agents_dir / src.name
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
                self._refresh_bundles()
                self.bundle_var.set(src.name)
                messagebox.showinfo("Success", f"Imported {src.name}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def _delete_bundle(self):
        bundle_name = self.bundle_var.get()
        if bundle_name == "Select Bundle" or bundle_name == "No Bundles":
            return
            
        # Safety: Check if Engine is running
        if hasattr(self, 'engine') and self.engine and self.engine.running:
            messagebox.showwarning("Busy", "Cannot delete bundle while Trading Engine is active.\nPlease stop the engine first.")
            return
        
        if messagebox.askyesno("Delete Bundle", f"Are you sure you want to delete '{bundle_name}'?"):
            try:
                bundle_path = self.agents_dir / bundle_name
                if bundle_path.exists() and bundle_path.is_dir():
                    shutil.rmtree(bundle_path)
                    self._refresh_bundles()
                    messagebox.showinfo("Success", "Bundle deleted.")
                else:
                    messagebox.showerror("Error", "Bundle not found.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to delete bundle: {e}")
                return


    def _select_mt5(self):
        filename = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if filename:
            self.mt5_var.set(filename)

    def get_config(self):
        return {
            "bundle": self.bundle_var.get(),
            "symbol": self.symbol_entry.get(),
            "timeframe": self.timeframe_menu.get(),
            "lot_size": self.lot_entry.get(),
            "risk": self.risk_entry.get(),
            "max_loss": self.max_loss_entry.get(),
            "max_daily_loss": self.max_loss_entry.get(),
            "min_equity": self.min_equity_entry.get(),
            "mt5": self.mt5_var.get(),
            "news_filter": self.news_filter_var.get(),
            "trailing_enabled": self.trailing_var.get(),
            "partial_close_enabled": self.partial_close_var.get(),
            "max_spread": self.max_spread_entry.get(),
            "news_buffer": self.news_buffer_entry.get(),
            "trailing_distance": self.trailing_distance_entry.get(),
            "tp1_distance": self.tp1_distance_entry.get(),
            "partial_close_percent": self.partial_close_percent_entry.get(),
            "risk_mode": "risk" if self.risk_entry.cget("state") == "normal" else "fixed"
        }

    def validate_config(self, config):
        """
        验证配置有效性
        Returns: (bool, str) - (是否有效, 错误信息)
        """
        # 1. Bundle检查
        if not config.get("bundle") or config["bundle"] == "Select Bundle":
            return False, "请选择一个有效的 Agent Bundle"
        
        # 2. Symbol检查
        symbol = config.get("symbol", "").strip()
        if not symbol:
            return False, "请输入交易品种（如 XAUUSD）"
        
        # 3. 数字参数验证
        try:
            lot_size = float(config["lot_size"])
            if lot_size <= 0 or lot_size > 100:
                return False, f"手数必须在 0.01 - 100 之间（当前: {lot_size}）"
        except ValueError:
            return False, f"手数必须是数字（当前: {config['lot_size']}）"
        
        try:
            risk = float(config["risk"])
            if risk < 0 or risk > 100:
                return False, f"风险百分比必须在 0 - 100 之间（当前: {risk}）"
        except ValueError:
            return False, f"风险百分比必须是数字（当前: {config['risk']}）"
        
        try:
            max_spread = int(config["max_spread"])
            if max_spread <= 0:
                return False, f"最大点差必须大于 0（当前: {max_spread}）"
        except ValueError:
            return False, f"最大点差必须是整数（当前: {config['max_spread']}）"
        
        try:
            max_loss = float(config["max_loss"])
            if max_loss < 0:
                return False, f"最大亏损不能为负数（当前: {max_loss}）"
        except ValueError:
            return False, f"最大亏损必须是数字（当前: {config['max_loss']}）"
        
        try:
            min_equity = float(config["min_equity"])
            if min_equity < 0:
                return False, f"最小权益不能为负数（当前: {min_equity}）"
        except ValueError:
            return False, f"最小权益必须是数字（当前: {config['min_equity']}）"
        
        try:
            news_buffer = int(config["news_buffer"])
            if news_buffer < 0 or news_buffer > 120:
                return False, f"新闻缓冲时间必须在 0 - 120 分钟之间（当前: {news_buffer}）"
        except ValueError:
            return False, f"新闻缓冲时间必须是整数（当前: {config['news_buffer']}）"
        
        try:
            trailing_dist = int(config["trailing_distance"])
            if trailing_dist < 0:
                return False, f"追踪距离不能为负数（当前: {trailing_dist}）"
        except ValueError:
            return False, f"追踪距离必须是整数（当前: {config['trailing_distance']}）"
        
        try:
            tp1_dist = int(config["tp1_distance"])
            if tp1_dist <= 0:
                return False, f"TP1 距离必须大于 0（当前: {tp1_dist}）"
        except ValueError:
            return False, f"TP1 距离必须是整数（当前: {config['tp1_distance']}）"
        
        try:
            partial_pct = float(config["partial_close_percent"])
            if partial_pct <= 0 or partial_pct > 100:
                return False, f"分批平仓百分比必须在 1 - 100 之间（当前: {partial_pct}）"
        except ValueError:
            return False, f"分批平仓百分比必须是数字（当前: {config['partial_close_percent']}）"
        
        return True, ""


class ViewSettings(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Settings", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(anchor="w", pady=(0, 30))
        
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        self.card = AppleCard(self.scroll)
        self.card.pack(fill="x")
        
        ctk.CTkLabel(self.card, text="TELEGRAM NOTIFICATIONS", font=ctk.CTkFont(size=12, weight="bold"), text_color=DS.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(20, 10))
        self.sw_enable = ctk.CTkSwitch(self.card, text="Enable Notifications", progress_color=DS.ACCENT_PURPLE, command=self._toggle_telegram)
        self.sw_enable.pack(anchor="w", padx=20, pady=(0, 10), fill="x")
        self.token_entry = self._create_input(self.card, "Bot Token")
        self.chat_entry = self._create_input(self.card, "Chat ID")

        # Removed: Test Connection button
        
        info_text = "Configuration Guide:\n1. Search @BotFather in Telegram, create a new bot to get Bot Token\n2. Send any message to your bot to activate it\n3. Search @userinfobot in Telegram to get your Chat ID"
        ctk.CTkLabel(self.card, text=info_text, font=DS.font_normal(), text_color=DS.TEXT_SECONDARY, justify="left").pack(anchor="w", padx=20, pady=10)
        
        ctk.CTkLabel(self.card, text="REMOTE ACCESS SECURITY", font=ctk.CTkFont(size=12, weight="bold"), text_color=DS.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(32, 10))
        
        self.sw_web_enable = ctk.CTkSwitch(self.card, text="Enable Web Dashboard", progress_color=DS.ACCENT_BLUE, command=self._toggle_web)
        self.sw_web_enable.pack(anchor="w", padx=20, pady=(0, 10), fill="x")
        
        self.web_password_entry = self._create_input(self.card, "Web Dashboard Password")
        
        ctk.CTkLabel(self.card, text="REMOTE TUNNEL (NGROK)", font=ctk.CTkFont(size=12, weight="bold"), text_color=DS.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(32, 10))
        self.sw_ngrok_enable = ctk.CTkSwitch(self.card, text="Enable Ngrok Tunnel", progress_color=DS.ACCENT_ORANGE, command=self._toggle_ngrok)
        self.sw_ngrok_enable.pack(anchor="w", padx=20, pady=(0, 10), fill="x")
        self.ngrok_token_entry = self._create_input(self.card, "Ngrok Auth Token")
        
        ngrok_info = "Configuration Guide:\n1. Register/Login at dashboard.ngrok.com\n2. Find 'Your Authtoken' in left menu\n3. Copy Token and paste above\n4. Public URL will be sent to Telegram upon activation\n⚠️ Note: Telegram notifications must be configured first"
        ctk.CTkLabel(self.card, text=ngrok_info, font=DS.font_normal(), text_color=DS.TEXT_SECONDARY, justify="left").pack(anchor="w", padx=20, pady=(5, 20))

        ctk.CTkLabel(self.card, text="FINANCIAL DATA API (FMP)", font=ctk.CTkFont(size=12, weight="bold"), text_color=DS.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(32, 10))
        self.fmp_key_entry = self._create_input(self.card, "FMP API Key (Optional)")
        fmp_info = "Configuration Guide:\n1. Register free account at financialmodelingprep.com\n2. Get API Key and paste above\n3. FMP (more stable) will be used if provided, otherwise fallback to scraper"
        ctk.CTkLabel(self.card, text=fmp_info, font=DS.font_normal(), text_color=DS.TEXT_SECONDARY, justify="left").pack(anchor="w", padx=20, pady=(5, 20))
        
        # About Section
        ctk.CTkLabel(self.card, text="ABOUT", font=ctk.CTkFont(size=12, weight="bold"), text_color=DS.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(32, 10))
        
        about_frame = ctk.CTkFrame(self.card, fg_color=DS.BG_ISLAND, corner_radius=DS.RADIUS_M)
        about_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        ctk.CTkLabel(about_frame, text="Alpha Quant Pro", font=ctk.CTkFont(size=18, weight="bold"), text_color=DS.TEXT_PRIMARY).pack(anchor="w", padx=15, pady=(15, 5))
        ctk.CTkLabel(about_frame, text="Version 2.1.0", font=DS.font_body(), text_color=DS.ACCENT_BLUE).pack(anchor="w", padx=15, pady=(0, 10))
        
        desc_text = "AI-Powered Quantitative Trading Terminal\nProfessional trading automation with real-time analysis"
        ctk.CTkLabel(about_frame, text=desc_text, font=DS.font_body(), text_color=DS.TEXT_SECONDARY, justify="left").pack(anchor="w", padx=15, pady=(0, 10))
        
        ctk.CTkLabel(about_frame, text="© 2024-2025 Alpha Quant Team. All rights reserved.", font=ctk.CTkFont(size=11), text_color=DS.TEXT_TERTIARY).pack(anchor="w", padx=15, pady=(0, 15))
        
        
        # Save Button
        save_btn_frame = ctk.CTkFrame(self.card, fg_color="transparent")
        save_btn_frame.pack(fill="x", padx=20, pady=(10, 20))
        self.btn_save = CapsuleButton(save_btn_frame, "SAVE SETTINGS", color=DS.ACCENT_BLUE, command=self._on_save_clicked)
        self.btn_save.pack(fill="x")

        self.sw_web_enable.select() if ConfigManager.load().get("web_enabled") else None # Pre-load fix
        
        self._load_saved_config()
        
    def _on_save_clicked(self):
        app = self.winfo_toplevel()
        if hasattr(app, 'save_all_settings'):
            app.save_all_settings()



    def _create_input(self, parent, placeholder):
        entry = ctk.CTkEntry(parent, placeholder_text=placeholder, height=40, fg_color=DS.BG_MAIN, border_color="#333", font=DS.font_input_mono())
        entry.pack(fill="x", padx=20, pady=5)
        return entry

    def _test_tg(self):
        token = self.token_entry.get()
        chat = self.chat_entry.get()
        if not token or not chat:
            messagebox.showerror("Error", "Missing Token or Chat ID")
            return
        app = self.winfo_toplevel()
        if hasattr(app, 'telegram'):
            app.telegram.configure(token, chat)
            if app.telegram.test_connection(): messagebox.showinfo("Success", "Telegram Connected!")
            else: messagebox.showerror("Failed", "Connection Failed")

    def _toggle_telegram(self):
        app = self.winfo_toplevel()
        if hasattr(app, 'telegram'):
            if self.sw_enable.get():
                token = self.token_entry.get().strip()
                chat = self.chat_entry.get().strip()
                if not token or not chat:
                    self.sw_enable.deselect()
                    messagebox.showwarning("配置缺失", "请先填写 Bot Token 和 Chat ID\n\n提示：\n1. 搜索 @BotFather 创建机器人获取 Token\n2. 搜索 @userinfobot 获取 Chat ID")
                    return
                app.telegram.configure(token, chat)
                app.telegram.enable()
                app.telegram.start_command_listener(app._handle_telegram_command)
                logger.info("Telegram notifications enabled")
            else:
                app.telegram.disable()
                logger.info("Telegram notifications disabled")

    def _toggle_web(self):
        password = self.web_password_entry.get().strip()
        if self.sw_web_enable.get():
            if not password:
                messagebox.showwarning("安全警告", "Web Dashboard 需要设置密码\n\n密码用于保护您的远程访问安全")
                self.sw_web_enable.deselect()
                return
            
            if len(password) < 6:
                messagebox.showwarning("密码太弱", "密码长度至少为 6 位\n\n建议使用包含数字和字母的组合")
                self.sw_web_enable.deselect()
                return
            
            # Delegate to Main App
            app = self.winfo_toplevel()
            if hasattr(app, "_start_web_persistent"):
                app._start_web_persistent(password)
            else:
                logger.error("App does not support persistent web server")
                
        else:
            # Delegate to Main App
            app = self.winfo_toplevel()
            if hasattr(app, "_stop_web_persistent"):
                app._stop_web_persistent()

    def _toggle_ngrok(self):
        if self.sw_ngrok_enable.get():
            token = self.ngrok_token_entry.get().strip()
            if not token:
                messagebox.showwarning("配置缺失", "请填写 Ngrok Auth Token\n\n您可以从 dashboard.ngrok.com 获取免费 Token")
                self.sw_ngrok_enable.deselect()
                return
            
            # Delegate to Main App
            app = self.winfo_toplevel()
            if hasattr(app, "_start_ngrok_persistent"):
                app._start_ngrok_persistent()
            else:
                logger.error("App does not support persistent ngrok")
                
        else:
            # Delegate to Main App
            app = self.winfo_toplevel()
            if hasattr(app, "_stop_ngrok_persistent"):
                app._stop_ngrok_persistent()

    def _load_saved_config(self):
        config = ConfigManager.load()
        if config.get("telegram_token"): self.token_entry.delete(0, "end"); self.token_entry.insert(0, config["telegram_token"])
        if config.get("telegram_chat_id"): self.chat_entry.delete(0, "end"); self.chat_entry.insert(0, config["telegram_chat_id"])
        if config.get("telegram_enabled"): self.sw_enable.select()
        
        if config.get("web_enabled"): self.sw_web_enable.select()
        if config.get("web_password"): self.web_password_entry.delete(0, "end"); self.web_password_entry.insert(0, config["web_password"])
        
        if config.get("ngrok_enabled"): self.sw_ngrok_enable.select()
        if config.get("ngrok_token"): self.ngrok_token_entry.delete(0, "end"); self.ngrok_token_entry.insert(0, config["ngrok_token"])
        
        if config.get("fmp_api_key"): self.fmp_key_entry.delete(0, "end"); self.fmp_key_entry.insert(0, config["fmp_api_key"])

    def get_config(self):
        return {
            "telegram_enabled": self.sw_enable.get(),
            "telegram_token": self.token_entry.get(),
            "telegram_chat_id": self.chat_entry.get(),
            "web_enabled": self.sw_web_enable.get(),
            "web_password": self.web_password_entry.get(),
            "ngrok_enabled": self.sw_ngrok_enable.get(),
            "ngrok_token": self.ngrok_token_entry.get(),
            "fmp_api_key": self.fmp_key_entry.get()
        }

class ViewChart(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Live Chart", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(anchor="w", pady=(0, 30))
        self.card = AppleCard(self)
        self.card.pack(fill="both", expand=True)
        self.fig, self.ax = plt.subplots(figsize=(10, 6), dpi=100)
        self.fig.patch.set_facecolor(DS.BG_CARD)
        self.ax.set_facecolor(DS.BG_CARD)
        self.ax.tick_params(axis='x', colors=DS.TEXT_SECONDARY)
        self.ax.tick_params(axis='y', colors=DS.TEXT_SECONDARY)
        self.ax.spines['bottom'].set_color(DS.TEXT_TERTIARY)
        self.ax.spines['top'].set_color(DS.BG_CARD) 
        self.ax.spines['right'].set_color(DS.BG_CARD)
        self.ax.spines['left'].set_color(DS.TEXT_TERTIARY)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.card)
        self.canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=10)
        
    def update_chart(self, df):
        self.ax.clear()
        if df.empty: return
        df_reset = df.reset_index(drop=True)
        up_color = DS.ACCENT_GREEN
        down_color = DS.ACCENT_RED
        width = 0.6
        for i, row in df_reset.iterrows():
            color = up_color if row['close'] >= row['open'] else down_color
            self.ax.plot([i, i], [row['low'], row['high']], color=color, linewidth=1, alpha=0.8)
            height = abs(row['close'] - row['open'])
            if height == 0: height = 0.01
            bottom = min(row['open'], row['close'])
            rect = plt.Rectangle((i - width/2, bottom), width, height, facecolor=color, edgecolor=color, alpha=0.9)
            self.ax.add_patch(rect)
        last_price = df.iloc[-1]['close']
        self.ax.axhline(y=last_price, color=DS.ACCENT_BLUE, linestyle='--', linewidth=1, alpha=0.5)
        self.ax.text(len(df), last_price, f" {last_price:.2f}", color=DS.ACCENT_BLUE, verticalalignment='center', fontsize=10, fontweight='bold')
        self.ax.set_facecolor(DS.BG_CARD)
        self.ax.grid(True, color=DS.TEXT_TERTIARY, alpha=0.1)
        self.ax.set_xlim(-1, len(df) + 2)
        ticks = range(0, len(df), 5)
        labels = [df.iloc[i]['time'].strftime("%H:%M") if 'time' in df.columns else str(i) for i in ticks]
        self.ax.set_xticks(ticks)
        self.ax.set_xticklabels(labels, rotation=0, fontsize=8)
        self.canvas.draw()

# --------------------------------------------------------------------------------------
# SMART GLOBAL SUBPROCESS PATCH
# --------------------------------------------------------------------------------------
def patch_subprocess_for_ngrok():
    """
    Globally patches subprocess.Popen to enforce hidden window flags 
    WHENEVER 'ngrok' is detected in the command args.
    """
    import subprocess
    if not hasattr(subprocess, 'STARTUPINFO'):
        return

    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = subprocess.SW_HIDE
    
    original_popen = subprocess.Popen

    def smart_popen(*args, **kwargs):
        # Check if 'ngrok' is in the arguments (usually args[0] list)
        is_ngrok = False
        if args and isinstance(args[0], (list, tuple)):
            # args[0] is ['path/to/ngrok', 'start', ...]
            cmd_args = args[0]
            if any("ngrok" in str(arg).lower() for arg in cmd_args):
                is_ngrok = True
        elif kwargs.get("args") and isinstance(kwargs["args"], (list, tuple)):
             if any("ngrok" in str(arg).lower() for arg in kwargs["args"]):
                is_ngrok = True
        
        if is_ngrok:
            # Force hidden flags
            kwargs['startupinfo'] = si
            kwargs['creationflags'] = 0x08000000 | subprocess.CREATE_NO_WINDOW
            
            # Suppress Console Shell
            if kwargs.get('shell'): 
                kwargs['shell'] = False
            
            # Redirect Streams
            if 'stdin' not in kwargs: kwargs['stdin'] = subprocess.DEVNULL
            if 'stdout' not in kwargs: kwargs['stdout'] = subprocess.DEVNULL
            if 'stderr' not in kwargs: kwargs['stderr'] = subprocess.DEVNULL
            
        return original_popen(*args, **kwargs)

    # Apply Patch Globally
    subprocess.Popen = smart_popen
    
    # Also patch pyngrok's references if already imported
    try:
        import sys
        if 'pyngrok' in sys.modules:
            pass # No need, it shares 'subprocess' module reference
        # But if they did 'from subprocess import Popen', we can't easily reach it 
        # unless we iterate modules. But standard pyngrok usage is 'import subprocess'.
        
        # Explicitly patch internal modules just in case (e.g. installer)
        # We can't import them here if they aren't loaded, so we just rely on global patch.
        # However, to be safe, we can try to pre-import and patch.
        import pyngrok.process
        import pyngrok.installer
        if hasattr(pyngrok.process, 'subprocess'):
            pyngrok.process.subprocess.Popen = smart_popen
        if hasattr(pyngrok.installer, 'subprocess'):
            pyngrok.installer.subprocess.Popen = smart_popen
            
    except ImportError:
        pass # pyngrok not installed yet or not needed
    except Exception as e:
        print(f"Subprocess Patch Warning: {e}")


class TerminalApple(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        # [CRITICAL] Apply Smart Patch immediately
        patch_subprocess_for_ngrok()

        # Engine & State
        self.engine = None
        self.engine_thread = None
        self.views = {}
        self.current_view = None
        self.current_view_name = None
        self.engine = None
        self.title("Alpha Quant Pro v2.1.1")
        self.configure(fg_color=DS.BG_MAIN)
        self.protocol("WM_DELETE_WINDOW", self._on_closing)

        
        # Adaptive Window Size & Centering
        self.update_idletasks()
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # Use 90% of screen or desired size, whichever is smaller
        win_w = min(1400, int(screen_w * 0.9))
        win_h = min(900, int(screen_h * 0.9))
        
        x = (screen_w - win_w) // 2
        y = (screen_h - win_h) // 2
        self.geometry(f"{win_w}x{win_h}+{x}+{y}")
        
        # Set Icon
        try:
            if getattr(sys, 'frozen', False):
                # Frozen: Icon is in the same directory or MEIPASS
                icon_path = Path(sys.executable).parent / "terminal_icon.ico"
                if not icon_path.exists():
                    icon_path = Path(sys._MEIPASS) / "terminal_icon.ico"
            else:
                # Dev: Icon is in current directory
                icon_path = Path("terminal_icon.ico")
            
            if icon_path.exists():
                self.iconbitmap(icon_path)
        except Exception:
            pass

        # FIX: Configure grid weights to allow main content to expand
        self.grid_columnconfigure(0, weight=0) # Sidebar fits content
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color=DS.BG_MAIN)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(4, weight=1)
        self.sidebar.pack_propagate(False) # Fixed width for premium feel
        
        # Logo with padding to define sidebar width naturally
        ctk.CTkLabel(self.sidebar, text="α Alpha\nQuant.", font=DS.font_display_xl(), text_color=DS.TEXT_PRIMARY, justify="left", anchor="w").pack(anchor="w", padx=20, pady=(40, 60))
        
        # Menu Items
        self._create_menu_item("⊞  Dashboard", "dashboard", active=True)
        self._create_menu_item("∿  Live Chart", "chart")
        self._create_menu_item("♟  Agents", "agents")
        self._create_menu_item("≡  Logs", "logs")
        self._create_menu_item("📊  Analytics", "analytics")
        self._create_menu_item("⚙  Settings", "settings")
        
        self.action_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_area.pack(side="bottom", fill="x", pady=20, padx=20)
        self.btn_start = CapsuleButton(self.action_area, "START ENGINE", color=DS.ACCENT_BLUE, command=self._start)
        self.btn_start.pack(fill="x", pady=10)
        self.btn_stop = CapsuleButton(self.action_area, "STOP", color=DS.BG_ISLAND, text_color=DS.ACCENT_RED, hover_color="#3A3A3C", command=self._stop)
        self.btn_stop.pack(fill="x")
        self.main = ctk.CTkFrame(self, fg_color="transparent")
        self.main.grid(row=0, column=1, sticky="nsew", padx=(0, 30), pady=30)
        self.views["dashboard"] = ViewDashboard(self.main)
        self.views["chart"] = ViewChart(self.main)
        self.views["agents"] = ViewAgents(self.main)
        self.views["logs"] = ViewLogs(self.main)
        self.views["analytics"] = ViewAnalytics(self.main)
        self.views["settings"] = ViewSettings(self.main)
        
        # License Check (Phase 8 Security)
        self._check_license()
        
        self._show_view("dashboard")
        
        # Auto-start Web Server if enabled
        if self.views["settings"].sw_web_enable.get():
            self.views["settings"]._toggle_web()

        # Check Risk Disclaimer
        self.after(100, self.check_risk_disclaimer)

        # Register Start Callback for Web Server
        core.web_server.start_callback = lambda: self.after(0, self._start)
        
        # Start Engine State Monitor
        self._monitor_engine_state()

        # Bind Close Event
        self.protocol("WM_DELETE_WINDOW", self.on_closing)

    def _start_web_persistent(self, password):
        """Start the web server with the given password"""
        try:
            core.web_server.set_password(password)
            core.web_server.start_background_server(self.engine)
            logger.info(f"Web Dashboard started on port 8000")
        except Exception as e:
            logger.error(f"Failed to start web server: {e}")
    
    def _stop_web_persistent(self):
        """Stop the web server"""
        try:
            core.web_server.stop_background_server()
            logger.info("Web Dashboard stopped")
        except Exception as e:
            logger.error(f"Failed to stop web server: {e}")

    def _start_ngrok_persistent(self):
        """Start Ngrok tunnel (Threaded)"""
        def _run():
            try:
                token = self.views["settings"].ngrok_token_entry.get().strip()
                if not token:
                    logger.warning("Ngrok start skipped: No token")
                    return
                    
                from pyngrok import ngrok, conf
                import logging
                
                # Suppress verbose Ngrok logs
                logging.getLogger("pyngrok").setLevel(logging.WARNING)
                
                # Configure
                conf.get_default().auth_token = token
                conf.get_default().region = "us" 
                
                # Close existing
                tunnels = ngrok.get_tunnels()
                for t in tunnels:
                    ngrok.disconnect(t.public_url)
                
                # Connect with Window Hiding Hack (Reverted to Monkeypatch as PyngrokConfig failed)
                import subprocess
                
                try:
                    # Connection is already patched via global subprocess monkeypatch
                    tunnel = ngrok.connect(8000, bind_tls=True)
                except Exception as e:
                    logger.error(f"Ngrok connect failed: {e}")
                    # Try to set flag to show failure
                    self.after(0, lambda: self._on_ngrok_fail(str(e)))
                    return

                public_url = tunnel.public_url
                
                logger.info(f"Ngrok Tunnel Started: {public_url}")
                
                # Notify via UI (Thread safe)
                self.after(0, lambda: self._on_ngrok_success(public_url))
                
                # Notify via Telegram if available
                telegram_enabled = False
                notifier = None
                
                # Case 1: Engine running
                if self.engine and self.engine.telegram and self.engine.telegram.enabled:
                    notifier = self.engine.telegram
                    telegram_enabled = True
                
                # Case 2: Engine not running (App Startup), check config
                elif self.views.get("settings"):
                    try:
                        # Access settings via UI variables safely
                        # Note: We are in a thread, accessing Tkinter vars is risky if not careful, 
                        # but reading .get() on primitives usually ok, or we should use logic from config file.
                        # Safer: Load config from file since we are in a thread
                        saved_config = ConfigManager.load()
                        if saved_config.get("telegram_enabled"):
                            notifier = TelegramNotifier(
                                bot_token=saved_config.get("telegram_token", ""),
                                chat_id=saved_config.get("telegram_chat_id", "")
                            )
                            notifier.enable() # Put into enabled state
                            telegram_enabled = True
                    except Exception as e:
                        logger.error(f"Failed to init temp telegram: {e}")

                if telegram_enabled and notifier:
                    # Get password safely
                    # If UI access fails in thread, use config
                    try: 
                        web_password = self.views["settings"].password_entry.get().strip() 
                    except: 
                        web_password = ConfigManager.load().get("web_password", "")
                        
                    msg = (
                        f"[Remote Dashboard]: {public_url}\n"
                        f"[Password]: {web_password}"
                    )
                    notifier.send_message(msg)
                
            except Exception as e:
                logger.error(f"Failed to start Ngrok: {e}")
                self.after(0, lambda: self._on_ngrok_fail(str(e)))

        threading.Thread(target=_run, daemon=True).start()

    def _on_ngrok_success(self, public_url):
        messagebox.showinfo("Ngrok Started", f"Remote Access URL:\n{public_url}\n\n(Copied to Clipboard & Sent to Telegram)")
        self.clipboard_clear()
        self.clipboard_append(public_url)

    def _on_ngrok_fail(self, error):
        messagebox.showerror("Ngrok Error", error)
        self.views["settings"].sw_ngrok_enable.deselect()

    def _stop_ngrok_persistent(self):
        """Stop Ngrok tunnel"""
        try:
            from pyngrok import ngrok
            # Graceful kill via library
            ngrok.kill()
            
            # Force kill any lingering system processes
            import subprocess
            subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"], 
                         stdout=subprocess.DEVNULL, 
                         stderr=subprocess.DEVNULL)
            
            logger.info("Ngrok Tunnel Stopped (Force Cleaned)")
            # Small delay to allow port release
            import time
            time.sleep(1)
        except Exception as e:
            logger.error(f"Failed to stop Ngrok: {e}")

    def on_closing(self):
        """Handle application closure"""
        try:
            if self.engine and self.engine.running:
                self.engine.stop()
            
            # Kill Ngrok
            try:
                from pyngrok import ngrok
                ngrok.kill()
            except:
                pass
                
            self.destroy()
            sys.exit(0)
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")
            sys.exit(1)

    def _monitor_engine_state(self):
        """Poll engine state to sync with remote stop requests"""
        if self.engine and not self.engine.running:
            # Engine exists but is not running -> It was stopped (possibly remotely)
            logger.info("Engine stopped detected by monitor. Syncing UI...")
            self._stop() # Update UI
        
        self.after(1000, self._monitor_engine_state)

    def _create_menu_item(self, text, view_name=None, active=False):
        color = DS.TEXT_PRIMARY if active else DS.TEXT_SECONDARY
        font = ctk.CTkFont(family="Segoe UI", size=16, weight="bold" if active else "normal")
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color=DS.BG_ISLAND if active else "transparent", text_color=color, anchor="w", font=font, hover_color=DS.BG_ISLAND, height=44, corner_radius=12)
        btn.pack(fill="x", pady=4, padx=20)
        if view_name:
            btn.configure(command=lambda: self._show_view(view_name))
            self.views[view_name + "_btn"] = btn

    def _show_view(self, name):
        if self.current_view:
            self.current_view.pack_forget()
            prev_btn = self.views.get(self.current_view_name + "_btn")
            if prev_btn: prev_btn.configure(fg_color="transparent", text_color=DS.TEXT_SECONDARY, font=ctk.CTkFont(family="Segoe UI", size=16, weight="normal"))
        view = self.views.get(name)
        if view:
            view.pack(fill="both", expand=True)
            self.current_view = view
            self.current_view_name = name
            new_btn = self.views.get(name + "_btn")
            if new_btn: new_btn.configure(fg_color=DS.BG_ISLAND, text_color=DS.TEXT_PRIMARY, font=ctk.CTkFont(family="Segoe UI", size=16, weight="bold"))

    def _get_web_config(self):
        """Gather configuration from UI"""
        config = self.views["agents"].get_config()
        settings = self.views["settings"].get_config()
        config.update(settings)
        return config

    def _start(self):
        """Start the trading engine"""
        try:
            config = self._get_web_config()
            
            # 验证配置
            is_valid, error_msg = self.views["agents"].validate_config(config)
            if not is_valid:
                messagebox.showerror("配置错误", error_msg)
                return
            
            # 保存配置到文件
            ConfigManager.save(config)
            
            # Update UI
            self.views["dashboard"].status_badge.configure(text="● STARTING", text_color=DS.ACCENT_ORANGE)
            self.btn_start.configure(state="disabled", fg_color=DS.BG_ISLAND)
            self.btn_stop.configure(state="normal", fg_color=DS.ACCENT_RED, text_color=DS.TEXT_PRIMARY)
            
            # Clear previous engine if exists
            if self.engine:
                self.engine = None
                
            # Run Engine in Thread to prevent UI freeze
            # However, _run_engine starts with non-blocking setup, but engine.run() might be blocking? 
            # engine.run() in engine_core.py usually starts a loop.
            # We should run the setup and then let the engine's internal loop handle it.
            # But here `_run_engine` implementation below handles the thread.
            
            # Using 'after' to allow UI to update first
            self.after(100, lambda: self._run_engine(config))
            
        except Exception as e:
            logger.error(f"Start Error: {e}")
            messagebox.showerror("启动失败", str(e))
            self._stop()

    def save_all_settings(self):
        """Save all current settings to disk"""
        try:
            config = self._get_web_config()
            ConfigManager.save(config)
            messagebox.showinfo("Saved", "Settings saved successfully.")
        except Exception as e:
            logger.error(f"Save Error: {e}")
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _on_closing(self):
        """Handle App Closure"""
        try:
            # Auto-Save on Exit
            config = self._get_web_config()
            ConfigManager.save(config)
            
            # Stop Services
            if self.engine:
                self.engine.stop()
            
            self._stop_web_persistent()
            self._stop_ngrok_persistent()
            
        except Exception as e:
            logger.error(f"Closing Error: {e}")
        finally:
            self.quit()
            self.destroy()


    def _run_engine(self, config):
        try:
            telegram_notifier = None
            if config.get("telegram_enabled", False):
                telegram_notifier = TelegramNotifier(
                    bot_token=config.get("telegram_token", ""),
                    chat_id=config.get("telegram_chat_id", "")
                )
                telegram_notifier.enable()

            # Enable Ngrok/Web if configured (Persistent Ensure)
            if config.get("web_enabled", False):
                 if hasattr(self, "_start_web_persistent"):
                     self._start_web_persistent(config.get("web_password", ""))
                 
                 if config.get("ngrok_enabled", False) and hasattr(self, "_start_ngrok_persistent"):
                     self._start_ngrok_persistent()

            # Parse symbols
            symbols_str = config["symbol"]
            if "," in symbols_str:
                symbols = [s.strip() for s in symbols_str.split(",")]
            else:
                symbols = [symbols_str.strip()]

            # Define bundle path
            if config["bundle"] == "Select Bundle":
                raise ValueError("Please select a valid Agent Bundle in Settings.")
                
            # Use the same agents directory as the ViewAgents (where we copied them)
            bundle_path = self.views["agents"].agents_dir / config["bundle"]
            
            # Initialize Managers
            self.db_manager = DatabaseManager()
            self.news_calendar = NewsCalendar()

            self.engine = TradingEngine(
                bundle_path=str(bundle_path),
                db_manager=self.db_manager,
                news_calendar=self.news_calendar,
                telegram_notifier=telegram_notifier if 'telegram_notifier' in locals() else None,
                symbols=symbols,
                timeframe=config.get("timeframe", "M15"),
                lot_size=float(config["lot_size"]),
                mt5_path=config["mt5"] if config["mt5"] != "auto" else None,
                max_spread=int(config.get("max_spread", 50)),
                max_daily_loss=float(config.get("max_daily_loss", config.get("max_loss", 500.0))),
                min_equity=float(config.get("min_equity", 0)),
                use_risk_based_sizing=(config.get("risk_mode") == "risk"),
                risk_percent=float(config["risk"]) / 100.0,
                news_filter_enabled=config.get("news_filter", False),
                news_buffer_minutes=int(config.get("news_buffer", 30)),
                trailing_enabled=config.get("trailing_enabled", False),
                trailing_distance=int(config.get("trailing_distance", 50)),
                partial_close_enabled=config.get("partial_close_enabled", False),
                tp1_distance=int(config.get("tp1_distance", 50)),
                partial_close_percent=float(config.get("partial_close_percent", 50)),
                callback_status=self._on_status_update
            )
            
            # Sync Engine with Web Server
            try:
                core.web_server.set_engine(self.engine)
                # Fix 503 Error: Link Config Callbacks
                self.last_config = config
                core.web_server.get_config_callback = lambda: self.last_config
                
                def _apply_web_config(new_config):
                    # Logic to safely apply config from Web to UI/Engine
                    # 1. Update UI Vars (Thread Safe Schedule)
                    def _update_ui():
                        try:
                            if "lot_size" in new_config:
                                self.views["agents"].lot_entry.delete(0, "end")
                                self.views["agents"].lot_entry.insert(0, str(new_config["lot_size"]))
                            if "risk" in new_config:
                                self.views["agents"].risk_entry.delete(0, "end")
                                self.views["agents"].risk_entry.insert(0, str(new_config["risk"]))
                            
                            # --- Fix for Settings Persistence (Sync UI Vars) ---
                            # Booleans (Agents View)
                            if "news_filter" in new_config:
                                self.views["agents"].news_filter_var.set(new_config["news_filter"])
                            if "trailing_enabled" in new_config:
                                self.views["agents"].trailing_var.set(new_config["trailing_enabled"])
                            if "partial_close_enabled" in new_config:
                                self.views["agents"].partial_close_var.set(new_config["partial_close_enabled"])
                                
                            # Detail Fields (Agents View)
                            if "max_daily_loss" in new_config:
                                self.views["agents"].max_loss_entry.delete(0, "end")
                                self.views["agents"].max_loss_entry.insert(0, str(new_config["max_daily_loss"]))
                            if "min_equity" in new_config:
                                self.views["agents"].min_equity_entry.delete(0, "end")
                                self.views["agents"].min_equity_entry.insert(0, str(new_config["min_equity"]))
                            if "trailing_distance" in new_config:
                                self.views["agents"].trailing_distance_entry.delete(0, "end")
                                self.views["agents"].trailing_distance_entry.insert(0, str(new_config["trailing_distance"]))
                            if "partial_close_percent" in new_config:
                                self.views["agents"].partial_close_percent_entry.delete(0, "end")
                                self.views["agents"].partial_close_percent_entry.insert(0, str(new_config["partial_close_percent"]))
                            
                            # Settings View Vars
                            if "telegram_enabled" in new_config:
                                self.views["settings"].sw_tg_enable.select() if new_config["telegram_enabled"] else self.views["settings"].sw_tg_enable.deselect()
                            if "web_enabled" in new_config:
                                self.views["settings"].sw_web_enable.select() if new_config["web_enabled"] else self.views["settings"].sw_web_enable.deselect()
                            if "ngrok_enabled" in new_config:
                                self.views["settings"].sw_ngrok_enable.select() if new_config["ngrok_enabled"] else self.views["settings"].sw_ngrok_enable.deselect()
                            
                            # ... Add other fields as needed ...
                            
                            # 2. Update Engine via Hot-Reload if available
                            if self.engine and hasattr(self.engine, "update_config"):
                                self.engine.update_config(new_config)
                                logger.info("Engine Config Updated via Web")
                                
                            # 3. Update last_config
                            self.last_config.update(new_config)
                            
                            # 4. Persist to Disk (Fixes Settings Lost Issue)
                            ConfigManager.save(self.last_config)
                            logger.info("Configuration saved to disk via Web Update")
                            
                        except Exception as e:
                            logger.error(f"Failed to apply web config: {e}")
                            
                    self.after(0, _update_ui)
                    
                core.web_server.set_config_callback = _apply_web_config
            except Exception as e:
                logger.error(f"Failed to sync engine with web server: {e}")
                
            # Send Notification (Clean - Engine Only)
            if telegram_notifier:
                # [SYSTEM] Engine Started Account: (acc no) Equity: (amount） Symbols: (symbol)
                acc_no = "Unknown"
                equity = "Unknown"
                try:
                    import MetaTrader5 as mt5
                    # Use the same path as the engine
                    mt5_path = self.engine.mt5_path
                    if mt5_path:
                        if not mt5.initialize(path=mt5_path):
                             logger.warning(f"MT5 Init failed for Tg Msg: {mt5.last_error()}")
                    else:
                        if not mt5.initialize():
                            logger.warning(f"MT5 Init failed for Tg Msg: {mt5.last_error()}")
                            
                    acc_info = mt5.account_info()
                    if acc_info:
                        acc_no = acc_info.login
                        equity = acc_info.equity
                except Exception as e:
                    logger.error(f"Failed to get acc info for Tg: {e}")
                    
                msg = (
                    f"🚀 [SYSTEM] Engine Started\n"
                    f"💳 Account: {acc_no}\n"
                    f"💰 Equity: ${equity}\n"
                    f"📈 Symbols: {config.get('symbol', 'XAUUSD')}"
                )
                telegram_notifier.send_message(msg)

            # Run Engine (Synchronous wrapper around async loop)
            # Starting thread handled by engine? No, engine.run() is blocking.
            # We must wrap it in a thread.
            
            def run_in_thread():
                self.engine.run()
                
            self.engine_thread = threading.Thread(target=run_in_thread, daemon=True)
            self.engine_thread.start()
            
            self.after(0, lambda: self.btn_stop.configure(state="normal"))

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Engine Start Error: {error_msg}")
            self.after(0, lambda: self.views["dashboard"].status_badge.configure(text="● ERROR", text_color=DS.ACCENT_RED))
            self.after(0, lambda: self.btn_start.configure(state="normal", fg_color=DS.ACCENT_BLUE))
            self.after(0, lambda: messagebox.showerror("启动失败", f"引擎启动失败:\n\n{error_msg}\n\n请检查:\n1. MT5 是否已打开并登录\n2. Agent Bundle 是否有效\n3. 网络连接是否正常\n4. 查看 Logs 面板获取详细错误信息"))

    def _on_status_update(self, status):
        # Ensure UI updates run on main thread to avoid Race Conditions and "bad window path" errors
        self.after(0, lambda: self._safe_status_update(status))

    def _safe_status_update(self, status):
        try:
            # Debug Log (Throttle to avoid spam?)
            # logger.info(f"UI Update: Pos={len(status.get('positions',[]))} Hist={len(status.get('history',[]))}")
            
            # Update Dashboard
            if self.views.get("dashboard"):
                self.views["dashboard"].update_status(status)
                
            # Update Chart
            if self.views.get("chart"):
                chart_data = status.get("chart_data")
                if chart_data is not None and not chart_data.empty:
                    self.views["chart"].update_chart(chart_data)
                
        except Exception as e:
            logger.error(f"UI Update Error: {e}")

    def _stop(self):
        if self.engine:
            self.engine.stop()
            self.engine = None
            
        # Sync with Web Server
        try:
            core.web_server.set_engine(None)
        except: pass
            
        self.views["dashboard"].status_badge.configure(text="● STOPPED", text_color=DS.ACCENT_RED)
        self.btn_start.configure(state="normal", fg_color=DS.ACCENT_BLUE)
        self.btn_stop.configure(state="disabled", fg_color=DS.BG_ISLAND, text_color=DS.ACCENT_RED)
    
    def _check_for_updates(self):
        """Check for updates on startup"""
        def on_update_checked(update_available, latest_version, download_url, changelog):
            if update_available and download_url:
                self.after(1000, lambda: self._show_update_dialog(latest_version, download_url, changelog))
        
        checker = UpdateChecker()
        checker.check_for_updates(callback=on_update_checked)
    
    def _show_update_dialog(self, latest_version, download_url, changelog):
        """Show update notification dialog"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("新版本可用")
        dialog.geometry("500x400")
        dialog.configure(fg_color=DS.BG_MAIN)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center dialog
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f"+{x}+{y}")
        
        # Content
        card = AppleCard(dialog)
        card.pack(fill="both", expand=True, padx=30, pady=30)
        
        # Title
        ctk.CTkLabel(card, text="🎉 发现新版本", 
                    font=ctk.CTkFont(size=24, weight="bold"),
                    text_color=DS.TEXT_PRIMARY).pack(pady=(30, 10))
        
        # Version
        ctk.CTkLabel(card, text=f"v{latest_version}", 
                    font=ctk.CTkFont(size=18),
                    text_color=DS.ACCENT_BLUE).pack(pady=5)
        
        # Changelog
        if changelog:
            changelog_text = ctk.CTkTextbox(card, height=150, fg_color=DS.BG_ISLAND)
            changelog_text.pack(fill="both", expand=True, padx=20, pady=20)
            changelog_text.insert("1.0", changelog)
            changelog_text.configure(state="disabled")
        
        # Buttons
        btn_frame = ctk.CTkFrame(card, fg_color="transparent")
        btn_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        def download_update():
            import webbrowser
            import os
            import subprocess
            
            if os.path.exists(download_url): # It's a local file
                try:
                    subprocess.Popen(download_url)
                    dialog.destroy()
                    self.destroy() # Close app to allow update
                    sys.exit(0)
                except Exception as e:
                    logger.error(f"Failed to launch installer: {e}")
                    webbrowser.open(download_url) # Fallback (unlikely to work for file path in browser)
            else:
                webbrowser.open(download_url)
                dialog.destroy()
        
        btn_text = "立即安装" if os.path.exists(download_url) else "立即下载"
        CapsuleButton(btn_frame, btn_text, color=DS.ACCENT_BLUE, 
                     command=download_update).pack(side="left", expand=True, padx=5)
        CapsuleButton(btn_frame, "稍后提醒", color=DS.BG_ISLAND, 
                     text_color=DS.TEXT_SECONDARY,
                     command=dialog.destroy).pack(side="left", expand=True, padx=5)
    
    def _handle_telegram_command(self, command: str) -> str:
        command = command.strip().lower()
        if command == "/status":
            if not self.engine or not self.engine.running: return "⏹ 引擎已停止\n\n使用 /start 启动引擎"
            import MetaTrader5 as mt5
            account = mt5.account_info()
            positions = mt5.positions_get()
            if account:
                pnl = sum([p.profit for p in positions]) if positions else 0.0
                return f"📊 <b>系统状态</b>\n\n<b>引擎:</b> ✅ 运行中\n<b>余额:</b> ${account.balance:,.2f}\n<b>净值:</b> ${account.equity:,.2f}\n<b>浮动盈亏:</b> ${pnl:+.2f}\n<b>持仓数:</b> {len(positions) if positions else 0}\n\n--\nAlpha Quant Terminal"
            else: return "❌ 无法获取账户信息"
        elif command == "/stop":
            if self.engine and self.engine.running:
                self.after(0, self._stop)
                return "⏹ 引擎正在停止..."
            else: return "⏹ 引擎已经停止"
        elif command == "/close_all" or command == "/closeall":
            if not self.engine or not self.engine.running: return "❌ 引擎未运行"
            positions = self.engine.get_open_positions()
            if not positions: return "ℹ️ 当前无持仓"
            count = len(positions)
            self.engine.close_all_positions()
            return f"✅ 已平仓 {count} 个持仓"
        elif command == "/help" or command == "/start":
            return "🤖 <b>可用命令</b>\n\n/status - 查看系统状态\n/stop - 停止引擎\n/close_all - 平掉所有持仓\n/help - 显示此帮助信息\n\n--\nAlpha Quant Terminal"
        else: return f"❓ 未知命令: {command}\n\n发送 /help 查看可用命令"

    def check_risk_disclaimer(self):
        """Show Risk Disclaimer on startup if not accepted"""
        config = ConfigManager.load()
        if config.get("risk_accepted", False):
            return

        # Create Dialog
        dialog = ctk.CTkToplevel(self)
        dialog.title("Risk Disclosure Statement")
        dialog.geometry("600x500")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set() # Modal

        # Center Dialog on Screen
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        x = (screen_w // 2) - (600 // 2)
        y = (screen_h // 2) - (500 // 2)
        dialog.geometry(f"600x500+{x}+{y}")
        
        # Content Frame
        frame = ctk.CTkFrame(dialog, fg_color=DS.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=2, pady=2) # Thin border effect if dialog bg is different
        
        # Header
        header_frame = ctk.CTkFrame(frame, fg_color=DS.BG_CARD, height=60)
        header_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(header_frame, text="⚠️  RISK DISCLOSURE", font=ctk.CTkFont(family="Segoe UI", size=20, weight="bold"), 
                     text_color=DS.ACCENT_RED).pack(side="left", padx=20, pady=15)
        
        # Load Text
        try:
            if getattr(sys, 'frozen', False):
                base_dir = Path(sys.executable).parent
                if not (base_dir / "RISK_DISCLAIMER.txt").exists():
                     base_dir = Path(sys._MEIPASS)
            else:
                base_dir = Path.cwd()
                
            with open(base_dir / "RISK_DISCLAIMER.txt", "r", encoding="utf-8") as f:
                disclaimer_text = f.read()
        except Exception:
            disclaimer_text = "Trading involves high risk. You could lose all your money.\n\n(Full disclaimer file missing)"

        # Text Area
        textbox = ctk.CTkTextbox(frame, font=ctk.CTkFont(family="Consolas", size=13), text_color=DS.TEXT_PRIMARY, fg_color=DS.BG_CARD)
        textbox.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        textbox.insert("0.0", disclaimer_text)
        textbox.configure(state="disabled")
        
        # Checkbox & Buttons
        action_frame = ctk.CTkFrame(frame, fg_color="transparent")
        action_frame.pack(fill="x", padx=20, pady=(0, 20))
        
        check_var = ctk.BooleanVar(value=False)
        
        def toggle_accept():
            if check_var.get():
                btn_accept.configure(state="normal", fg_color=DS.ACCENT_BLUE)
            else:
                btn_accept.configure(state="disabled", fg_color=DS.BG_ISLAND)

        chk = ctk.CTkCheckBox(action_frame, text="I have read, understood, and accept the risks above.", 
                             variable=check_var, command=toggle_accept,
                             font=ctk.CTkFont(size=13), text_color=DS.TEXT_SECONDARY,
                             fg_color=DS.ACCENT_BLUE, hover_color=DS.ACCENT_BLUE)
        chk.pack(side="top", anchor="w", pady=(0, 15))
        
        def accept():
            config["risk_accepted"] = True
            ConfigManager.save(config)
            dialog.destroy()
            
        def reject():
            dialog.destroy()
            self.destroy()
            sys.exit(0)
            
        ctk.CTkButton(action_frame, text="EXIT APPLICATION", fg_color=DS.BG_ISLAND, text_color=DS.ACCENT_RED, 
                     hover_color="#3A3A3C", width=120, command=reject).pack(side="left")
                     
        btn_accept = ctk.CTkButton(action_frame, text="CONTINUE", fg_color=DS.BG_ISLAND, text_color="white", 
                                  state="disabled", width=120, command=accept)
        btn_accept.pack(side="right")
        
        dialog.protocol("WM_DELETE_WINDOW", reject)
        self.wait_window(dialog)

    # ----------------------------------------------------------------
    # SECURITY & ACTIVATION (Phase 8)
    # ----------------------------------------------------------------
    def _check_license(self):
        """
        Validates HWID binding on startup.
        Blocks UI if invalid.
        """
        if LicenseManager is None:
            return # Dev mode fallback
            
        self.lm = LicenseManager()
        saved_key = self.lm.load_license()
        hwid = self.lm.get_hwid()
        
        logger.info(f"Checking License for HWID: {hwid}")
        
        if self.lm.validate_license(saved_key):
            logger.info("License Verified ✅")
            return
            
        # Not valid, show dialog
        self._show_activation_dialog(hwid)
        
    def _show_activation_dialog(self, hwid):
        """Modal Dialog for Activation Code"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("Alpha Quant Pro Activation")
        dialog.geometry("500x450")
        dialog.resizable(False, False)
        dialog.attributes("-topmost", True)
        dialog.transient(self)
        dialog.grab_set()
        
        # Center on Screen (not parent, as parent may not be visible yet)
        dialog.update_idletasks()
        screen_w = dialog.winfo_screenwidth()
        screen_h = dialog.winfo_screenheight()
        x = (screen_w - 500) // 2
        y = (screen_h - 450) // 2
        dialog.geometry(f"500x450+{x}+{y}")
        
        frame = ctk.CTkFrame(dialog, fg_color=DS.BG_MAIN)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Icon/Title
        ctk.CTkLabel(frame, text="🔒 PRODUCT ACTIVATION", font=ctk.CTkFont(size=20, weight="bold"), 
                    text_color=DS.ACCENT_BLUE).pack(pady=(30, 10))
                    
        ctk.CTkLabel(frame, text="This copy is locked to this machine.", font=DS.font_body(), 
                    text_color=DS.TEXT_SECONDARY).pack()
                    
        # HWID Display
        hwid_frame = ctk.CTkFrame(frame, fg_color=DS.BG_ISLAND)
        hwid_frame.pack(fill="x", padx=40, pady=20)
        ctk.CTkLabel(hwid_frame, text="Your Machine ID:", font=ctk.CTkFont(size=12), text_color=DS.TEXT_TERTIARY).pack(pady=(10, 0))
        
        # Click to Copy Logic
        def copy_hwid():
            self.clipboard_clear()
            self.clipboard_append(hwid)
            btn_copy.configure(text="COPIED!")
            self.after(2000, lambda: btn_copy.configure(text=hwid))
            
        btn_copy = ctk.CTkButton(hwid_frame, text=hwid, fg_color="transparent", hover_color=DS.BG_CARD, 
                                font=ctk.CTkFont(family="Consolas", size=14, weight="bold"),
                                text_color=DS.ACCENT_ORANGE, command=copy_hwid, width=300)
        btn_copy.pack(pady=(0, 10))
        
        # Auto-Send Status Label
        send_status_lbl = ctk.CTkLabel(hwid_frame, text="Connecting to Admin...", font=ctk.CTkFont(size=11), text_color=DS.ACCENT_ORANGE)
        send_status_lbl.pack(pady=(0, 5))

        # Background Thread for Auto-Send
        def auto_send():
            if self.lm.send_registration_request(hwid):
                 self.after(0, lambda: send_status_lbl.configure(text="✅ Request Sent! Admin Notified.", text_color=DS.ACCENT_GREEN))
            else:
                 self.after(0, lambda: send_status_lbl.configure(text="⚠️ Auto-Send Failed. Please Copy ID Manually.", text_color=DS.TEXT_TERTIARY))
        
        import threading
        threading.Thread(target=auto_send, daemon=True).start()


        # Input
        entry = ctk.CTkEntry(frame, placeholder_text="Enter Activation Key (starts with AQ-)", 
                            height=45, font=DS.font_input_mono(), justify="center")
        entry.pack(fill="x", padx=40, pady=(0, 20))
        
        status_lbl = ctk.CTkLabel(frame, text="", text_color=DS.ACCENT_RED)
        status_lbl.pack()
        
        def try_activate():
            key = entry.get().strip()
            if self.lm.validate_license(key):
                self.lm.save_license(key)
                status_lbl.configure(text="Activation Success! Executing...", text_color=DS.ACCENT_GREEN)
                dialog.after(1000, dialog.destroy)
            else:
                status_lbl.configure(text="Invalid Key or HWID Mismatch.", text_color=DS.ACCENT_RED)
                entry.configure(border_color=DS.ACCENT_RED)
        
        def quit_app():
            sys.exit(0)
            
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(pady=20)
        
        ctk.CTkButton(btn_frame, text="Exit", fg_color=DS.BG_ISLAND, width=100, command=quit_app).pack(side="left", padx=10)
        ctk.CTkButton(btn_frame, text="ACTIVATE", fg_color=DS.ACCENT_BLUE, width=150, command=try_activate).pack(side="left", padx=10)
        
        dialog.protocol("WM_DELETE_WINDOW", quit_app)
        self.wait_window(dialog)



def main():
    ctk.set_appearance_mode("Dark")
    app = TerminalApple()
    try:
        app.mainloop()
    except (tk.TclError, KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        logger.error(f"Application crashed: {e}")

if __name__ == "__main__":
    main()

