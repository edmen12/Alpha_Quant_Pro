// Core API Response Types for AlphaQuantPro Web Dashboard

export interface StatusData {
    running: boolean;
    equity: number;
    balance: number;
    profit: number;
    positions: Position[];
    price?: number;
    symbol?: string;
    total_pnl?: number;
}

export interface Position {
    ticket: number;
    symbol: string;
    type: 'BUY' | 'SELL';
    volume: number;
    price_open: number;
    price_current: number;
    sl: number;
    tp: number;
    profit: number;
    time: string;
}

export interface Trade {
    ticket: number;
    symbol: string;
    type: 'BUY' | 'SELL';
    volume: number;
    price: number;
    profit: number;
    commission: number;
    swap: number;
    time: string;
}

export interface AnalyticsData {
    total_trades: number;
    win_rate: number;
    total_profit: number;
    profit_factor: number;
    sharpe_ratio: number;
    max_drawdown: number;
    avg_trade: number;
    equity_history: { time: string; value: number }[];
}

export interface ConfigData {
    risk_guard: boolean;
    max_daily_loss: number;
    min_equity: number;
    smart_entry: boolean;
    news_filter: boolean;
    lot_size: number;
    risk: number;
    trailing_stop: boolean;
    trailing_start: number;
    trailing_step: number;
    partial_close_enabled: boolean;
    partial_close_pips: number;
    partial_close_percent: number;
}

export interface ChartBar {
    time: string | number;
    open: number;
    high: number;
    low: number;
    close: number;
}
