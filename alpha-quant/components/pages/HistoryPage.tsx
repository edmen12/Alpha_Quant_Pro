import React, { useState, useEffect } from 'react';
import { ArrowUpRight, ArrowDownRight } from 'lucide-react';
import { apiService } from '@/lib/api';
import { GlassPanel } from '@/components/ui/GlassComponents';

const HistoryPage = () => {
    const [trades, setTrades] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        let isMounted = true;

        const load = async () => {
            try {
                const res = await apiService.get('/history');
                // Backend returns { trades: [...] }
                const list = res.data.trades || (Array.isArray(res.data) ? res.data : []);

                if (isMounted && Array.isArray(list)) {
                    // SORTING: Newest first (Descending)
                    const sorted = list.sort((a: any, b: any) => new Date(b.time).getTime() - new Date(a.time).getTime());
                    setTrades(sorted);
                }
            } catch (e) {
                console.error("Failed to load history:", e);
            } finally {
                if (isMounted) setLoading(false);
            }
        };

        // Initial load
        load();

        // Poll every 5 seconds
        const interval = setInterval(load, 5000);

        return () => {
            isMounted = false;
            clearInterval(interval);
        };
    }, []);

    // Calc Summaries (All Time)
    const netProfit = trades.reduce((acc, t) => acc + (t.profit || 0), 0);
    const totalTrades = trades.length;
    const totalFees = trades.reduce((acc, t) => acc + (t.commission || 0) + (t.swap || 0), 0);

    return (
        <div className="pt-8 pb-28 px-5 h-full bg-transparent overflow-y-auto no-scrollbar">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-white tracking-tight">History</h1>
            </div>

            {/* Summary Cards */}
            <div className="grid grid-cols-3 gap-3 mb-8 animate-in slide-in-from-bottom-4 duration-500">
                <GlassPanel className="p-3 flex flex-col items-center justify-center text-center min-h-[72px]">
                    <div className="text-[9px] text-gray-400 font-bold uppercase tracking-wider mb-1">Net Profit</div>
                    <div className={`text-base sm:text-lg font-bold font-mono truncate w-full ${netProfit >= 0 ? 'text-[#30D158]' : 'text-[#FF453A]'}`}>
                        {netProfit >= 0 ? '+' : ''}{netProfit >= 1000 || netProfit <= -1000
                            ? `$${netProfit.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                            : `$${netProfit.toFixed(2)}`}
                    </div>
                </GlassPanel>
                <GlassPanel className="p-3 flex flex-col items-center justify-center text-center min-h-[72px]">
                    <div className="text-[9px] text-gray-400 font-bold uppercase tracking-wider mb-1">Trades</div>
                    <div className="text-base sm:text-lg font-bold text-white font-mono">{totalTrades.toLocaleString()}</div>
                </GlassPanel>
                <GlassPanel className="p-3 flex flex-col items-center justify-center text-center min-h-[72px]">
                    <div className="text-[9px] text-gray-400 font-bold uppercase tracking-wider mb-1">Fees</div>
                    <div className="text-base sm:text-lg font-bold text-[#FF453A] font-mono truncate w-full">
                        {totalFees >= 1000
                            ? `$${totalFees.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })}`
                            : `$${totalFees.toFixed(2)}`}
                    </div>
                </GlassPanel>
            </div>

            {/* Recent Executions Header */}
            <div className="text-xs text-gray-500 font-bold uppercase tracking-widest mb-4 pl-1">
                Recent Executions
            </div>

            {/* Trade List */}
            <div className="space-y-3">
                {loading ? (
                    <div className="flex justify-center py-12">
                        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                    </div>
                ) : trades.length === 0 ? (
                    <div className="text-center text-gray-600 py-12 text-sm">No trading history found.</div>
                ) : (
                    trades.map((t, i) => (
                        <div
                            key={i}
                            className="rounded-2xl p-4 flex justify-between items-center group active:scale-[0.97] transition-all duration-200 animate-in slide-in-from-bottom-2 cursor-pointer hover:bg-white/[0.03]"
                            style={{
                                animationDelay: `${i * 30}ms`,
                                background: 'rgba(28, 28, 30, 0.6)',
                                backdropFilter: 'blur(20px)',
                                border: '1px solid rgba(255, 255, 255, 0.04)',
                            }}
                        >                            <div className="flex items-center gap-4">
                                {/* Icon Box */}
                                <div className={`w-10 h-10 rounded-full flex items-center justify-center border ${t.type === 'BUY'
                                    ? (t.profit >= 0 ? 'bg-[#30D158]/10 border-[#30D158]/20 text-[#30D158]' : 'bg-[#30D158]/10 border-[#30D158]/20 text-[#30D158]')
                                    : (t.profit >= 0 ? 'bg-[#FF453A]/10 border-[#FF453A]/20 text-[#FF453A]' : 'bg-[#FF453A]/10 border-[#FF453A]/20 text-[#FF453A]')
                                    }`}>
                                    {t.type === 'BUY' ? <ArrowUpRight size={20} /> : <ArrowDownRight size={20} />}
                                </div>

                                <div>
                                    <div className="flex items-center gap-2 mb-0.5">
                                        <span className="text-base font-bold text-white tracking-tight">{t.symbol}</span>
                                        <span className="text-[9px] bg-[#2c2c2e] text-gray-400 px-1.5 py-0.5 rounded border border-white/5 uppercase font-medium">CLOSED</span>
                                    </div>
                                    <div className="text-[10px] text-gray-500 font-mono">
                                        <span className={t.type === 'BUY' ? 'text-[#30D158]' : 'text-[#FF453A]'}>{t.type}</span>
                                        <span className="mx-1.5 opacity-30">|</span>
                                        <span>{t.volume || '0.10'} @ {t.price || '0.00'}</span>
                                    </div>
                                </div>
                            </div>

                            <div className="text-right">
                                <div className={`text-base font-bold font-mono tracking-tight ${t.profit >= 0 ? 'text-[#30D158]' : 'text-[#FF453A]'}`}>
                                    {t.profit >= 0 ? '+' : ''}${t.profit.toFixed(2)}
                                </div>
                                <div className="text-[10px] text-gray-600 font-mono mt-0.5">
                                    {new Date(t.time).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                                </div>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
};

export default HistoryPage;
