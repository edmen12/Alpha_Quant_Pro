"""
Alpha Quant Terminal - iOS 26 Concept Edition
Design Philosophy: "OLED Black", "Super Ellipse", "Floating Interface"
"""

import customtkinter as ctk
from datetime import datetime
import threading
import time
import json
from pathlib import Path
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import asyncio
import pandas as pd
import shutil
from tkinter import filedialog, messagebox
import queue

# Import Core Modules
from engine_core import TradingEngine
from telegram_notifier import TelegramNotifier
from logger_setup import LoggerSetup
from config_manager import ConfigManager
from database_manager import DatabaseManager
from news_calendar import NewsCalendar
from update_checker import UpdateChecker
from path_manager import PathManager

# Setup Logger
LoggerSetup.setup_logging()
logger = LoggerSetup.get_logger("Terminal")

# ============================================================================
# 1. Design System (iOS 26 Future)
# ============================================================================

class DS:
    """Design System - The DNA of the app"""
    
    # Colors (Dark Mode Only)
    BG_MAIN = "#000000"         # Pure Black
    BG_CARD = "#161618"         # Deep Grey (Floating)
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

        # Stats Grid
        self.stats_grid = ctk.CTkFrame(self, fg_color="transparent")
        self.stats_grid.pack(fill="x", pady=(0, 30))
        self.stats_grid.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.stat_pnl = StatIsland(self.stats_grid, "P&L", "+$0.00", color=DS.ACCENT_GREEN)
        self.stat_pnl.grid(row=0, column=0, padx=(0, 10), sticky="ew")
        
        # self.stat_signal removed as per request
        
        self.stat_price = StatIsland(self.stats_grid, "PRICE", "$0.00", color=DS.ACCENT_BLUE)
        self.stat_price.grid(row=0, column=1, padx=10, sticky="ew") # Shifted column
        
        self.stat_balance = StatIsland(self.stats_grid, "BALANCE", "$0.00")
        self.stat_balance.grid(row=0, column=2, padx=10, sticky="ew") # Shifted column
        
        self.stat_equity = StatIsland(self.stats_grid, "EQUITY", "$0.00")
        self.stat_equity.grid(row=0, column=3, padx=(10, 0), sticky="ew") # Shifted column
        
        # Positions Card
        self.pos_card = AppleCard(self)
        self.pos_card.pack(fill="both", expand=True)
        
        ctk.CTkLabel(self.pos_card, text="OPEN POSITIONS", 
                    font=ctk.CTkFont(family="Segoe UI", size=12, weight="bold"),
                    text_color=DS.TEXT_SECONDARY).pack(pady=(20, 10), anchor="w", padx=20)
        
        self.btn_close_all = ctk.CTkButton(self.pos_card, text="CLOSE ALL", width=80, height=24,
                                         fg_color="#3A3A3C", hover_color="#48484A", # Grey color
                                         font=ctk.CTkFont(size=11, weight="bold"),
                                         command=self._close_all)
        self.btn_close_all.place(relx=0.95, rely=0.05, anchor="ne")

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
        
        font_thin = ctk.CTkFont(family="Segoe UI", size=12) # Normal weight
        
        ctk.CTkLabel(hist_header, text="TIME", width=110, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="SYMBOL", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="TYPE", width=50, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="VOL", width=50, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="OPEN", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="CLOSE", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)
        ctk.CTkLabel(hist_header, text="PROFIT", width=70, anchor="w", text_color=DS.TEXT_SECONDARY, font=font_thin).pack(side="left", expand=True)

        self.list_container = ctk.CTkScrollableFrame(self.trades_card, fg_color="transparent")
        self.list_container.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        self.empty_label = ctk.CTkLabel(self.list_container, text="No trades yet.", text_color=DS.TEXT_TERTIARY)
        self.empty_label.pack(pady=40)

        self.last_trade_count = 0
        self.last_top_ticket = None
        self.pos_rows = {}

    def update_stats(self, signal, conf, price, balance, equity, pnl):
        self.stat_pnl.update(f"${pnl:,.2f}", DS.ACCENT_GREEN if pnl >= 0 else DS.ACCENT_RED)
        
        # self.stat_signal removed
        
        self.stat_price.update(f"${price:,.2f}", DS.ACCENT_BLUE)
        self.stat_balance.update(f"${balance:,.2f}")
        self.stat_equity.update(f"${equity:,.2f}")
        
        if signal == "BUY":
            self.status_badge.configure(text=f"● BUY ({conf*100:.0f}%)", text_color=DS.ACCENT_GREEN)
        elif signal == "SELL":
            self.status_badge.configure(text=f"● SELL ({conf*100:.0f}%)", text_color=DS.ACCENT_RED)
        else:
            self.status_badge.configure(text=f"● SCANNING ({conf*100:.0f}%)", text_color=DS.ACCENT_BLUE)

    def update_trades(self, trades):
        if not trades:
            if self.last_trade_count > 0:
                self.last_trade_count = 0
                for widget in self.list_container.winfo_children(): widget.destroy()
                self.empty_label.pack(pady=40)
            return

        # Check if latest trade is different or count changed
        latest_ticket = trades[0]['ticket'] if trades else None
        if len(trades) == self.last_trade_count and latest_ticket == self.last_top_ticket:
            return
            
        self.last_trade_count = len(trades)
        self.last_top_ticket = latest_ticket

        for widget in self.list_container.winfo_children():
            if isinstance(widget, ctk.CTkFrame): widget.destroy()
        
        if not trades:
            self.empty_label.pack(pady=40)
            return
        self.empty_label.pack_forget()
        
        for trade in trades:
            row = ctk.CTkFrame(self.list_container, fg_color="transparent")
            row.pack(fill="x", pady=5)
            
            # Show full date time
            time_str = str(trade['time'])
            ctk.CTkLabel(row, text=time_str, width=110, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)
            
            ctk.CTkLabel(row, text=trade.get('symbol', 'XAUUSD'), width=70, anchor="w", text_color=DS.TEXT_SECONDARY).pack(side="left", expand=True)
            
            is_buy = trade['type'] == 'BUY'
            color = DS.ACCENT_GREEN if is_buy else DS.ACCENT_RED
            ctk.CTkLabel(row, text=trade['type'], width=50, anchor="w", text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="left", expand=True)
            
            # Volume
            vol = trade.get('volume', 0.0)
            ctk.CTkLabel(row, text=f"{vol:.2f}", width=50, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)
            
            # Open Price
            open_price = trade.get('open_price', 0.0)
            ctk.CTkLabel(row, text=f"{open_price:.2f}", width=70, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)

            # Close Price
            close_price = trade.get('close_price', 0.0)
            ctk.CTkLabel(row, text=f"{close_price:.2f}", width=70, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)
            
            pnl = trade['profit']
            pnl_color = DS.ACCENT_GREEN if pnl >= 0 else DS.ACCENT_RED
            ctk.CTkLabel(row, text=f"${pnl:.2f}", width=70, anchor="w", text_color=pnl_color).pack(side="left", expand=True)

    def update_positions(self, positions):
        if not positions:
            for ticket in list(self.pos_rows.keys()): self.pos_rows[ticket]['frame'].destroy()
            self.pos_rows.clear()
            self.empty_pos_label.pack(pady=20)
            return
        self.empty_pos_label.pack_forget()
        
        current_tickets = set(t['ticket'] for t in positions)
        for ticket in list(self.pos_rows.keys()):
            if ticket not in current_tickets:
                self.pos_rows[ticket]['frame'].destroy()
                del self.pos_rows[ticket]
        
        for trade in positions:
            ticket = trade['ticket']
            pnl = trade['profit']
            pnl_color = DS.ACCENT_GREEN if pnl >= 0 else DS.ACCENT_RED
            
            if ticket in self.pos_rows:
                self.pos_rows[ticket]['pnl_label'].configure(text=f"${pnl:.2f}", text_color=pnl_color)
            else:
                row = ctk.CTkFrame(self.pos_container, fg_color="transparent")
                row.pack(fill="x", pady=5)
                
                ctk.CTkLabel(row, text=trade.get('time', '-'), width=110, anchor="w", text_color=DS.TEXT_SECONDARY).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=trade['symbol'], width=70, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)
                
                is_buy = trade['type'] == 'BUY'
                color = DS.ACCENT_GREEN if is_buy else DS.ACCENT_RED
                ctk.CTkLabel(row, text=trade['type'], width=50, anchor="w", text_color=color, font=ctk.CTkFont(weight="bold")).pack(side="left", expand=True)
                
                ctk.CTkLabel(row, text=f"{trade['volume']:.2f}", width=50, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=f"{trade['price_open']:.2f}", width=70, anchor="w", text_color=DS.TEXT_PRIMARY).pack(side="left", expand=True)
                
                ctk.CTkLabel(row, text=f"{trade.get('sl', 0):.2f}", width=60, anchor="w", text_color=DS.TEXT_SECONDARY).pack(side="left", expand=True)
                ctk.CTkLabel(row, text=f"{trade.get('tp', 0):.2f}", width=60, anchor="w", text_color=DS.TEXT_SECONDARY).pack(side="left", expand=True)

                pnl_label = ctk.CTkLabel(row, text=f"${pnl:.2f}", width=70, anchor="w", text_color=pnl_color)
                pnl_label.pack(side="left", expand=True)
                
                btn = ctk.CTkButton(row, text="CLOSE", width=60, height=24, 
                                  fg_color=DS.BG_ISLAND, hover_color=DS.ACCENT_RED,
                                  font=ctk.CTkFont(size=10),
                                  command=lambda t=ticket: self._close_trade(t))
                btn.pack(side="left", expand=True)
                
                self.pos_rows[ticket] = {'frame': row, 'pnl_label': pnl_label}

    def _close_trade(self, ticket):
        app = self.winfo_toplevel()
        if app.engine: app.engine.close_position(ticket)

    def _close_all(self):
        app = self.winfo_toplevel()
        if app.engine:
            if messagebox.askyesno("Confirm", "Close ALL Positions?"):
                app.engine.close_all_positions()

class ViewLogs(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(0, 20))
        ctk.CTkLabel(header, text="System Logs", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        
        self.log_text = ctk.CTkTextbox(self, font=ctk.CTkFont(family="Consolas", size=12),
                                     fg_color=DS.BG_ISLAND, text_color=DS.TEXT_SECONDARY)
        self.log_text.pack(fill="both", expand=True)
        self.log_text.configure(state="disabled")
        
        self._poll_logs()

    def _poll_logs(self):
        try:
            log_queue = LoggerSetup.get_log_queue()
            while not log_queue.empty():
                record = log_queue.get_nowait()
                msg = record.getMessage()
                formatted = f"[{record.levelname}] {msg}\n"
                
                self.log_text.configure(state="normal")
                self.log_text.insert("end", formatted)
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
        if app.engine and app.engine.running:
            # Submit task to engine's executor
            future = app.engine.executor.submit(self._run_analysis_task)
            self.after(100, lambda: self._check_analysis_result(future))
        else:
            # Retry later
            if hasattr(self, 'btn_refresh'):
                self.btn_refresh.configure(state="normal", text="Refresh")
            self.refresh_timer = self.after(5000, self._refresh_metrics)

    def _run_analysis_task(self):
        """Run analysis in background thread"""
        try:
            app = self.winfo_toplevel()
            # 1. Fetch history using Engine's method (running in executor)
            history = app.engine.get_trade_history(days=30)
            
            from performance_analyzer import PerformanceAnalyzer
            analyzer = PerformanceAnalyzer(symbol=None)
            
            # 2. Pass history to analyzer
            return {
                'metrics': analyzer.get_all_metrics(days=30, trades_list=history),
                'curve': analyzer.get_equity_curve(days=30, trades_list=history)
            }
        except Exception as e:
            logger.error(f"[Analytics] Task Error: {e}")
            return {'metrics': {}, 'curve': {}}

    def _check_analysis_result(self, future):
        """Check if analysis is complete"""
        if future.done():
            try:
                data = future.result()
                self._update_ui_with_data(data)
            except Exception as e:
                logger.error(f"Analysis Task Failed: {e}")
            
            self.btn_refresh.configure(state="normal", text="Refresh")
            # Schedule next refresh
            self.refresh_timer = self.after(30000, self._refresh_metrics) # Refresh every 30s
        else:
            # Keep checking
            self.after(100, lambda: self._check_analysis_result(future))

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
                # Use pd.to_datetime then to_pydatetime to ensure Matplotlib compatibility
                times = [pd.to_datetime(t).to_pydatetime() for t in curve_data['times']]
                self.ax.plot(times, curve_data['equity'], color=DS.ACCENT_BLUE)
                # Format date on x-axis
                import matplotlib.dates as mdates
                self.ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d %H:%M'))
                self.fig.autofmt_xdate()
            
            self.canvas.draw()
            
        except Exception as e:
            logger.error(f"UI Update Error: {e}")

class ViewAgents(ctk.CTkFrame):
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        ctk.CTkLabel(self, text="Configuration", font=DS.font_display_l(), text_color=DS.TEXT_PRIMARY).pack(anchor="w", pady=(0, 30))
        
        # Use Scrollable Frame
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)
        
        self.card = AppleCard(self.scroll)
        self.card.pack(fill="x")
        
        self._create_bundle_selector(self.card)
        self.symbol_entry = self._create_input_row(self.card, "Symbols (comma sep)", "XAUUSD")
        
        mode_row = ctk.CTkFrame(self.card, fg_color="transparent")
        mode_row.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(mode_row, text="Sizing Mode", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        
        self.mode_var = ctk.StringVar(value="Fixed Lot")
        self.mode_seg = ctk.CTkSegmentedButton(mode_row, values=["Fixed Lot", "Risk %"], 
                                             variable=self.mode_var, command=self._update_inputs)
        self.mode_seg.pack(side="right")
        
        self.lot_row, self.lot_entry = self._create_input_row(self.card, "Lot Size", "0.01", return_row=True)
        self.risk_row, self.risk_entry = self._create_input_row(self.card, "Risk %", "1.0", return_row=True)
        self._update_inputs("Fixed Lot")
        
        self.max_spread_entry = self._create_input_row(self.card, "Smart Entry (Max Spread)", "50")
        self._add_desc(self.card, "Maximum allowed spread in points to enter a trade.")
        
        self.max_loss_entry = self._create_input_row(self.card, "Max Daily Loss", "500")
        self.min_equity_entry = self._create_input_row(self.card, "Min Equity (Guard)", "0")
        
        news_row = ctk.CTkFrame(self.card, fg_color="transparent")
        news_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(news_row, text="News Filter", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.news_filter_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(news_row, text="Enable", variable=self.news_filter_var, fg_color=DS.ACCENT_BLUE).pack(side="right")
        self.news_buffer_entry = self._create_input_row(self.card, "News Buffer (min)", "30")
        self._add_desc(self.card, "Pause trading before/after high-impact news events.")
        
        trailing_row = ctk.CTkFrame(self.card, fg_color="transparent")
        trailing_row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(trailing_row, text="Trailing Stop", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.trailing_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(trailing_row, text="Enable", variable=self.trailing_var, fg_color=DS.ACCENT_GREEN).pack(side="right")
        self.trailing_distance_entry = self._create_input_row(self.card, "Trailing Distance (points)", "50")
        self._add_desc(self.card, "Move Stop Loss to lock in profits as price moves favorably.")
        
        partial_row = ctk.CTkFrame(self.card, fg_color="transparent")
        partial_row.pack(fill="x", padx=20, pady=(15, 5))
        ctk.CTkLabel(partial_row, text="Partial Close", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.partial_close_var = ctk.BooleanVar(value=False)
        ctk.CTkCheckBox(partial_row, text="Enable", variable=self.partial_close_var, fg_color=DS.ACCENT_PURPLE).pack(side="right")
        self.tp1_distance_entry = self._create_input_row(self.card, "TP1 Distance (points)", "50")
        self.partial_close_percent_entry = self._create_input_row(self.card, "Partial Close %", "50")
        self._add_desc(self.card, "Close a portion of the position at TP1 and move SL to Break Even.")
        
        self._create_mt5_selector(self.card)
        self._load_saved_config()

    def _add_desc(self, parent, text):
        ctk.CTkLabel(parent, text=text, font=ctk.CTkFont(size=11), text_color=DS.TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(0, 5))

    def _load_saved_config(self):
        config = ConfigManager.load()
        if config.get("bundle"): self.bundle_var.set(config["bundle"])
        if config.get("symbol"): self.symbol_entry.delete(0, "end"); self.symbol_entry.insert(0, config["symbol"])
        if config.get("mt5"): 
            self.mt5_var.set(config["mt5"])
            if config["mt5"] != "auto":
                self.mt5_path_entry.delete(0, "end"); self.mt5_path_entry.insert(0, config["mt5"])
        
        if float(config.get("risk", 0)) > 0:
            self.mode_var.set("Risk %")
            self.risk_entry.delete(0, "end"); self.risk_entry.insert(0, config["risk"])
            self._update_inputs("Risk %")
        else:
            self.mode_var.set("Fixed Lot")
            self.lot_entry.delete(0, "end"); self.lot_entry.insert(0, config["lot_size"])
            self._update_inputs("Fixed Lot")
            
        if config.get("max_spread"): self.max_spread_entry.delete(0, "end"); self.max_spread_entry.insert(0, str(config["max_spread"]))
        if config.get("max_loss"): self.max_loss_entry.delete(0, "end"); self.max_loss_entry.insert(0, str(config["max_loss"]))
        if config.get("min_equity"): self.min_equity_entry.delete(0, "end"); self.min_equity_entry.insert(0, str(config["min_equity"]))
        if config.get("news_filter"): self.news_filter_var.set(True)
        if config.get("news_buffer"): self.news_buffer_entry.delete(0, "end"); self.news_buffer_entry.insert(0, str(config["news_buffer"]))
        if config.get("trailing_enabled"): self.trailing_var.set(True)
        if config.get("trailing_distance"): self.trailing_distance_entry.delete(0, "end"); self.trailing_distance_entry.insert(0, str(config["trailing_distance"]))
        if config.get("partial_close_enabled"): self.partial_close_var.set(True)
        if config.get("tp1_distance"): self.tp1_distance_entry.delete(0, "end"); self.tp1_distance_entry.insert(0, str(config["tp1_distance"]))
        if config.get("partial_close_percent"): self.partial_close_percent_entry.delete(0, "end"); self.partial_close_percent_entry.insert(0, str(config["partial_close_percent"]))

    def _create_bundle_selector(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(row, text="Agent Bundle", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        btn_frame = ctk.CTkFrame(row, fg_color="transparent")
        btn_frame.pack(side="right")
        self.bundle_var = ctk.StringVar(value="Select Bundle")
        self.bundle_menu = ctk.CTkOptionMenu(btn_frame, variable=self.bundle_var, fg_color=DS.BG_ISLAND, button_color=DS.ACCENT_BLUE, width=200)
        self.bundle_menu.pack(side="left", padx=5)
        ctk.CTkButton(btn_frame, text="Import", width=60, fg_color=DS.BG_ISLAND, command=self._import_bundle).pack(side="left")
        self._refresh_bundles()

    def _create_mt5_selector(self, parent):
        row = ctk.CTkFrame(parent, fg_color="transparent")
        row.pack(fill="x", padx=20, pady=15)
        ctk.CTkLabel(row, text="MT5 Path", font=DS.font_body(), text_color=DS.TEXT_PRIMARY).pack(side="left")
        self.mt5_var = ctk.StringVar(value="auto")
        self.mt5_path_entry = ctk.CTkEntry(row, textvariable=self.mt5_var, width=140, fg_color=DS.BG_MAIN, border_width=1, border_color="#333", font=DS.font_input_mono())
        self.mt5_path_entry.pack(side="right")
        ctk.CTkButton(row, text="...", width=40, fg_color=DS.BG_ISLAND, command=self._select_mt5).pack(side="right", padx=5)

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
        agents_dir = Path("agents")
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
            dest = Path("agents") / src.name
            if dest.exists():
                if not messagebox.askyesno("Exists", "Overwrite?"): return
                shutil.rmtree(dest)
            shutil.copytree(src, dest)
            self._refresh_bundles()
            self.bundle_var.set(src.name)

    def _select_mt5(self):
        filename = filedialog.askopenfilename(filetypes=[("Executable", "*.exe")])
        if filename:
            self.mt5_var.set(filename)

    def get_config(self):
        mode = self.mode_var.get()
        risk_val = self.risk_entry.get() if mode == "Risk %" else "0"
        return {
            "bundle": self.bundle_var.get(),
            "symbol": self.symbol_entry.get(),
            "lot_size": self.lot_entry.get(),
            "risk": risk_val,
            "mt5": self.mt5_var.get(),
            "max_spread": self.max_spread_entry.get(),
            "max_loss": self.max_loss_entry.get(),
            "min_equity": self.min_equity_entry.get(),
            "news_filter": self.news_filter_var.get(),
            "news_buffer": self.news_buffer_entry.get(),
            "trailing_enabled": self.trailing_var.get(),
            "trailing_distance": self.trailing_distance_entry.get(),
            "partial_close_enabled": self.partial_close_var.get(),
            "tp1_distance": self.tp1_distance_entry.get(),
            "partial_close_percent": self.partial_close_percent_entry.get()
        }

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
        self.sw_enable.pack(anchor="w", padx=20, pady=(0, 10))
        self.token_entry = self._create_input(self.card, "Bot Token")
        self.chat_entry = self._create_input(self.card, "Chat ID")
        
        btn_row = ctk.CTkFrame(self.card, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=10)
        self.btn_test = CapsuleButton(btn_row, "Test Connection", color=DS.ACCENT_PURPLE, width=150, command=self._test_tg)
        self.btn_test.pack(side="left")
        
        info_text = "配置说明：\n1. 在 Telegram 搜索 @BotFather，创建新机器人获取 Bot Token\n2. 向机器人发送任意消息激活\n3. 在 Telegram 搜索 @userinfobot，获取您的 Chat ID"
        ctk.CTkLabel(self.card, text=info_text, font=DS.font_body(), text_color=DS.TEXT_SECONDARY, justify="left").pack(anchor="w", padx=20, pady=10)

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
                token = self.token_entry.get()
                chat = self.chat_entry.get()
                if token and chat:
                    app.telegram.configure(token, chat)
                    app.telegram.enable()
                    app.telegram.start_command_listener(app._handle_telegram_command)
                else:
                    self.sw_enable.deselect()
                    messagebox.showwarning("Config", "Please enter Token and Chat ID")
            else:
                app.telegram.disable()
                if hasattr(app.telegram, 'stop_command_listener'): app.telegram.stop_command_listener()

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

class TerminalApple(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Alpha Quant Pro - iOS 26")
        self.geometry("1400x900")
        self.configure(fg_color=DS.BG_MAIN)
        self.engine = None
        self.last_chart_update = 0
        self.telegram = TelegramNotifier()
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._init_ui()
        self._check_for_updates()
        
    def _init_ui(self):
        self.views = {}
        self.current_view = None
        self.sidebar = ctk.CTkFrame(self, width=300, fg_color=DS.BG_MAIN, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=30, pady=30)
        self.sidebar.grid_propagate(False)
        ctk.CTkLabel(self.sidebar, text="α Alpha\nQuant.", font=DS.font_display_xl(), text_color=DS.TEXT_PRIMARY, justify="left", anchor="w").pack(anchor="w", pady=(40, 60))
        self._create_menu_item("⊞  Dashboard", "dashboard", active=True)
        self._create_menu_item("∿  Live Chart", "chart")
        self._create_menu_item("♟  Agents", "agents")
        self._create_menu_item("≡  Logs", "logs")
        self._create_menu_item("📊  Analytics", "analytics")
        self._create_menu_item("⚙  Settings", "settings")
        self.action_area = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.action_area.pack(side="bottom", fill="x", pady=20)
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
        self._show_view("dashboard")

    def _create_menu_item(self, text, view_name=None, active=False):
        color = DS.TEXT_PRIMARY if active else DS.TEXT_SECONDARY
        font = ctk.CTkFont(family="Segoe UI", size=16, weight="bold" if active else "normal")
        btn = ctk.CTkButton(self.sidebar, text=text, fg_color=DS.BG_ISLAND if active else "transparent", text_color=color, anchor="w", font=font, hover_color=DS.BG_ISLAND, height=44, corner_radius=12)
        btn.pack(fill="x", pady=4)
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

    def _start(self):
        config = self.views["agents"].get_config()
        ConfigManager.save(config)
        self.views["dashboard"].status_badge.configure(text="● INITIALIZING...", text_color=DS.ACCENT_ORANGE)
        self.btn_start.configure(state="disabled", fg_color=DS.BG_ISLAND)
        threading.Thread(target=self._run_engine, args=(config,), daemon=True).start()
        
    def _run_engine(self, config):
        try:
            telegram_notifier = None
            if config.get("telegram_enabled", False):
                telegram_notifier = TelegramNotifier(
                    token=config.get("telegram_token", ""),
                    chat_id=config.get("telegram_chat_id", "")
                )
            
            # Parse symbols
            symbols_str = config["symbol"]
            if "," in symbols_str:
                symbols = [s.strip() for s in symbols_str.split(",")]
            else:
                symbols = [symbols_str.strip()]

            self.engine = TradingEngine(
                bundle_path=str(bundle_path),
                symbols=symbols,
                lot_size=float(config["lot_size"]),
                mt5_path=config["mt5"] if config["mt5"] != "auto" else None,
                max_spread=int(config.get("max_spread", 50)),
                max_daily_loss=float(config.get("max_loss", 500.0)),
                min_equity=float(config.get("min_equity", 0)),
                use_risk_based_sizing=True if float(config["risk"]) > 0 else False,
                risk_percent=float(config["risk"]) / 100.0,
                news_filter_enabled=config.get("news_filter", False),
                news_buffer_minutes=int(config.get("news_buffer", 30)),
                trailing_enabled=config.get("trailing_enabled", False),
                trailing_distance=int(config.get("trailing_distance", 50)),
                partial_close_enabled=config.get("partial_close_enabled", False),
                tp1_distance=int(config.get("tp1_distance", 50)),
                partial_close_percent=float(config.get("partial_close_percent", 50)),
                callback_status=self._on_status_update,
                db_manager=db_manager,
                news_calendar=news_calendar,
                telegram_notifier=telegram_notifier
            )
            # Run Async Engine
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.engine.run_async())
            loop.close()
            
            # self.engine.start() # Legacy Thread Start
            # self.after(0, lambda: self.views["dashboard"].status_badge.configure(text="● ENGINE ACTIVE", text_color=DS.ACCENT_BLUE))
            # self.after(0, lambda: self.btn_stop.configure(state="normal"))
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Engine Start Error: {error_msg}")
            self.after(0, lambda: self.views["dashboard"].status_badge.configure(text="● ERROR", text_color=DS.ACCENT_RED))
            self.after(0, lambda: self.btn_start.configure(state="normal", fg_color=DS.ACCENT_BLUE))
            self.after(0, lambda: messagebox.showerror("Start Failed", error_msg))

    def _stop(self):
        if self.engine:
            self.engine.stop()
            self.engine = None
        self.views["dashboard"].status_badge.configure(text="● STOPPED", text_color=DS.ACCENT_RED)
        self.btn_start.configure(state="normal", fg_color=DS.ACCENT_BLUE)
        self.btn_stop.configure(state="disabled")
            
    def _on_status_update(self, status):
        try:
            current_time = time.time()
            if current_time - self.last_chart_update >= 1.0:
                if "chart" in self.views and "history" in status:
                    self.views["chart"].update_chart(status["history"])
                self.last_chart_update = current_time
            if "dashboard" in self.views:
                price = status.get("price", 0.0)
                signal = status.get("signal", "HOLD")
                conf = status.get("confidence", 0.0)
                balance = status.get("balance", 0.0)
                equity = status.get("equity", 0.0)
                pnl = equity - balance
                self.views["dashboard"].update_stats(signal, conf, price, balance, equity, pnl)
                if "trades" in status: self.views["dashboard"].update_trades(status["trades"])
                positions = []
                if self.engine: positions = self.engine.get_open_positions()
                self.views["dashboard"].update_positions(positions)
        except Exception as e:
            logger.error(f"UI Update Error: {e}")
    
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
            webbrowser.open(download_url)
            dialog.destroy()
        
        CapsuleButton(btn_frame, "立即下载", color=DS.ACCENT_BLUE, 
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

if __name__ == "__main__":
    ctk.set_appearance_mode("Dark")
    app = TerminalApple()
    app.mainloop()
