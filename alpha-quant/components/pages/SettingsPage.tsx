import React, { useState, useEffect } from 'react';
import { apiService } from '@/lib/api';
import { Toggle } from '@/components/ui/Toggle';
import { GlassPanel, GlassInput, GlassButton } from '@/components/ui/GlassComponents';

const SettingsPage = () => {
    const [config, setConfig] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.get('/config')
            .then(res => setConfig(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const updateConfig = (key: string, val: any) => {
        setConfig((prev: any) => ({ ...prev, [key]: val }));
    };

    const saveConfig = async () => {
        try {
            await apiService.post('/config', config);
            alert('Configuration Saved');
        } catch (e) {
            alert('Failed to save configuration');
        }
    };

    if (loading || !config) return <div className="p-10 text-center text-gray-500">Loading Configuration...</div>;

    return (
        <div className="pt-8 pb-32 px-5 h-full bg-transparent overflow-y-auto no-scrollbar">
            {/* iOS 26 Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-white tracking-tight">Configuration</h1>
                <p className="text-sm text-gray-500 mt-1">Agent & Trading Parameters</p>
            </div>

            <div className="space-y-6">
                {/* Trading Symbol */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">Trading Setup</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div>
                            <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Symbol</label>
                            <GlassInput
                                value={config.symbol || 'XAUUSD'}
                                onChange={(e) => updateConfig('symbol', e.target.value)}
                                className="w-full font-mono"
                                placeholder="XAUUSD"
                            />
                            <div className="text-[9px] text-gray-500 mt-1">Comma-separated for multiple (e.g., XAUUSD,EURUSD)</div>
                        </div>
                        <div>
                            <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Timeframe</label>
                            <div className="flex gap-2">
                                {['M1', 'M5', 'M15', 'M30', 'H1', 'H4', 'D1'].map(tf => (
                                    <button
                                        key={tf}
                                        onClick={() => updateConfig('timeframe', tf)}
                                        className={`px-3 py-1.5 rounded-lg text-[10px] font-bold transition-all ${config.timeframe === tf
                                            ? 'bg-white/15 text-white border border-white/20'
                                            : 'bg-white/5 text-gray-500 border border-transparent hover:bg-white/10'
                                            }`}
                                    >
                                        {tf}
                                    </button>
                                ))}
                            </div>
                        </div>
                    </GlassPanel>
                </section>

                {/* Position Sizing */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">Position Sizing</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div className="flex gap-2 mb-4">
                            <button
                                onClick={() => updateConfig('sizing_mode', 'fixed')}
                                className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${config.sizing_mode !== 'risk'
                                    ? 'bg-[#0A84FF] text-white'
                                    : 'bg-white/5 text-gray-400'
                                    }`}
                            >
                                Fixed Lot
                            </button>
                            <button
                                onClick={() => updateConfig('sizing_mode', 'risk')}
                                className={`flex-1 py-2 rounded-lg text-xs font-bold transition-all ${config.sizing_mode === 'risk'
                                    ? 'bg-[#0A84FF] text-white'
                                    : 'bg-white/5 text-gray-400'
                                    }`}
                            >
                                Risk %
                            </button>
                        </div>
                        <div className="grid grid-cols-2 gap-4">
                            <div className={config.sizing_mode === 'risk' ? 'opacity-30' : ''}>
                                <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Lot Size</label>
                                <GlassInput
                                    type="number" step="0.01"
                                    value={config.lot_size || 0.01}
                                    onChange={(e) => updateConfig('lot_size', parseFloat(e.target.value))}
                                    className="w-full text-right font-mono"
                                    disabled={config.sizing_mode === 'risk'}
                                />
                            </div>
                            <div className={config.sizing_mode !== 'risk' ? 'opacity-30' : ''}>
                                <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Risk %</label>
                                <GlassInput
                                    type="number" step="0.1"
                                    value={config.risk || 1.0}
                                    onChange={(e) => updateConfig('risk', parseFloat(e.target.value))}
                                    className="w-full text-right font-mono"
                                    disabled={config.sizing_mode !== 'risk'}
                                />
                            </div>
                        </div>
                    </GlassPanel>
                </section>

                {/* Smart Entry */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">Smart Entry</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div>
                            <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Max Spread (points)</label>
                            <GlassInput
                                type="number"
                                value={config.max_spread || 500}
                                onChange={(e) => updateConfig('max_spread', parseInt(e.target.value))}
                                className="w-full text-right font-mono"
                            />
                            <div className="text-[9px] text-gray-500 mt-1">Only enter when spread is below this. Recommended: 30-50 for FX, 100-200 for Gold</div>
                        </div>
                    </GlassPanel>
                </section>

                {/* Risk Management */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">Risk Management</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Max Daily Loss ($)</label>
                                <GlassInput
                                    type="number"
                                    value={config.max_daily_loss || 500}
                                    onChange={(e) => updateConfig('max_daily_loss', parseFloat(e.target.value))}
                                    className="w-full text-right font-mono"
                                />
                            </div>
                            <div>
                                <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Min Equity Guard ($)</label>
                                <GlassInput
                                    type="number"
                                    value={config.min_equity || 0}
                                    onChange={(e) => updateConfig('min_equity', parseFloat(e.target.value))}
                                    className="w-full text-right font-mono"
                                />
                            </div>
                        </div>
                    </GlassPanel>
                </section>

                {/* News Filter */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">News Filter</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div className="flex justify-between items-center">
                            <div>
                                <div className="text-sm font-bold text-white">News Filter</div>
                                <div className="text-[10px] text-gray-400">Block trades during high-impact news</div>
                            </div>
                            <Toggle checked={config.news_filter || false} onChange={(c) => updateConfig('news_filter', c)} />
                        </div>
                        <div className={!config.news_filter ? 'opacity-30' : ''}>
                            <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">News Buffer (minutes)</label>
                            <GlassInput
                                type="number"
                                value={config.news_buffer || 30}
                                onChange={(e) => updateConfig('news_buffer', parseInt(e.target.value))}
                                className="w-full text-right font-mono"
                                disabled={!config.news_filter}
                            />
                            <div className="text-[9px] text-gray-500 mt-1">Time before/after news to block trades</div>
                        </div>
                    </GlassPanel>
                </section>

                {/* Trailing Stop */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">Trailing Stop</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div className="flex justify-between items-center">
                            <div>
                                <div className="text-sm font-bold text-white">Trailing Stop</div>
                                <div className="text-[10px] text-gray-400">Dynamic SL that follows price</div>
                            </div>
                            <Toggle checked={config.trailing_enabled || false} onChange={(c) => updateConfig('trailing_enabled', c)} />
                        </div>
                        <div className={!config.trailing_enabled ? 'opacity-30' : ''}>
                            <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Trailing Distance (points)</label>
                            <GlassInput
                                type="number"
                                value={config.trailing_distance || 50}
                                onChange={(e) => updateConfig('trailing_distance', parseInt(e.target.value))}
                                className="w-full text-right font-mono"
                                disabled={!config.trailing_enabled}
                            />
                        </div>
                    </GlassPanel>
                </section>

                {/* Partial Close */}
                <section>
                    <h3 className="text-[10px] font-bold text-gray-400 uppercase tracking-[0.15em] mb-3 ml-1">Partial Close</h3>
                    <GlassPanel className="p-5 space-y-4">
                        <div className="flex justify-between items-center">
                            <div>
                                <div className="text-sm font-bold text-white">Partial Close</div>
                                <div className="text-[10px] text-gray-400">Secure profits at TP1</div>
                            </div>
                            <Toggle checked={config.partial_close_enabled || false} onChange={(c) => updateConfig('partial_close_enabled', c)} />
                        </div>
                        <div className={!config.partial_close_enabled ? 'opacity-30' : ''}>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">TP1 Distance (points)</label>
                                    <GlassInput
                                        type="number"
                                        value={config.tp1_distance || 50}
                                        onChange={(e) => updateConfig('tp1_distance', parseInt(e.target.value))}
                                        className="w-full text-right font-mono"
                                        disabled={!config.partial_close_enabled}
                                    />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase font-bold text-gray-400 mb-1 block">Close %</label>
                                    <GlassInput
                                        type="number"
                                        value={config.partial_close_percent || 50}
                                        onChange={(e) => updateConfig('partial_close_percent', parseInt(e.target.value))}
                                        className="w-full text-right font-mono"
                                        disabled={!config.partial_close_enabled}
                                    />
                                </div>
                            </div>
                            <div className="text-[9px] text-gray-500 mt-2">Close % of position at TP1, move SL to break-even</div>
                        </div>
                    </GlassPanel>
                </section>

                <GlassButton onClick={saveConfig} className="mb-4">
                    Save Configuration
                </GlassButton>

                {/* Logout Button */}
                <button
                    onClick={() => {
                        // Call logout API
                        apiService.post('/logout', {}).catch(() => { });
                        // Clear local token
                        localStorage.removeItem('token');
                        // Reload page to show login
                        window.location.reload();
                    }}
                    className="w-full py-3 rounded-2xl text-sm font-bold text-[#FF453A] bg-[#FF453A]/10 border border-[#FF453A]/20 hover:bg-[#FF453A]/20 transition-colors mb-8"
                >
                    Log Out
                </button>
            </div>
        </div>
    );
};

export default SettingsPage;
