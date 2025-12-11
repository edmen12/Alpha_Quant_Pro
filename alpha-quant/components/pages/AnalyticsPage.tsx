import React, { useState, useEffect, useMemo } from 'react';
import { BarChart, Activity } from 'lucide-react';
import { apiService } from '@/lib/api';
import MarketChart from '@/components/charts/MarketChart';
import { GlassPanel } from '@/components/ui/GlassComponents';

interface AnalyticsPageProps {
    isEngineRunning: boolean;
}

const AnalyticsPage = ({ isEngineRunning }: AnalyticsPageProps) => {
    const [data, setData] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        apiService.get('/analytics')
            .then(res => setData(res.data))
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    const equityData = useMemo(() => {
        if (!data?.equity_curve) return [];
        const curve = data.equity_curve;
        // Ensure we safely map the array
        if (Array.isArray(curve.equity)) {
            return curve.equity.map((val: number, i: number) => ({
                time: curve.times ? curve.times[i] : i,
                value: val
            }));
        }
        return [];
    }, [data]);

    return (
        <div className="pt-8 pb-28 px-5 h-full bg-transparent overflow-y-auto no-scrollbar">
            {/* Header */}
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-white tracking-tight">Analytics</h1>

                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full border border-white/10 bg-[#1c1c1e]/40 backdrop-blur-md shadow-sm`}>
                    <div className={`w-1.5 h-1.5 rounded-full animate-pulse ${isEngineRunning ? 'bg-[#30D158]' : 'bg-[#FFD60A]'}`}></div>
                    <span className="text-[9px] font-bold text-gray-300 uppercase tracking-widest">
                        {isEngineRunning ? 'Active' : 'Standby'}
                    </span>
                </div>
            </div>

            {loading ? (
                <div className="flex items-center justify-center h-64">
                    <div className="animate-spin rounded-full h-10 w-10 border-b-2 border-primary"></div>
                </div>
            ) : (
                <div className="animate-in slide-in-from-bottom-4 duration-700 fade-in">
                    {/* Top Stats Grid */}
                    <div className="grid grid-cols-3 gap-3 mb-3">
                        <GlassPanel className="p-3 flex flex-col justify-between h-20 active:scale-[0.98] transition-transform">
                            <div className="text-[9px] text-gray-400 uppercase font-bold tracking-widest truncate">Win Rate</div>
                            <div className="text-xl font-bold text-white font-mono">{data?.win_rate?.toFixed(1) || '0.0'}%</div>
                        </GlassPanel>
                        <GlassPanel className="p-3 flex flex-col justify-between h-20 active:scale-[0.98] transition-transform">
                            <div className="text-[9px] text-gray-400 uppercase font-bold tracking-widest truncate">Factor</div>
                            <div className="text-xl font-bold text-white font-mono">{data?.profit_factor?.toFixed(2) || '0.00'}</div>
                        </GlassPanel>
                        <GlassPanel className="p-3 flex flex-col justify-between h-20 active:scale-[0.98] transition-transform">
                            <div className="text-[9px] text-gray-400 uppercase font-bold tracking-widest truncate">Sharpe</div>
                            <div className="text-xl font-bold text-white font-mono">{data?.sharpe_ratio?.toFixed(2) || '0.00'}</div>
                        </GlassPanel>
                    </div>

                    <div className="grid grid-cols-3 gap-3 mb-6">
                        <GlassPanel className="p-3 flex flex-col justify-between h-20 active:scale-[0.98] transition-transform">
                            <div className="text-[9px] text-gray-400 uppercase font-bold tracking-widest truncate">Drawdown</div>
                            <div className="text-xl font-bold text-white font-mono">{data?.max_drawdown?.toFixed(1) || '0.0'}%</div>
                        </GlassPanel>
                        <GlassPanel className="p-3 flex flex-col justify-between h-20 col-span-2 active:scale-[0.98] transition-transform">
                            <div className="text-[9px] text-gray-400 uppercase font-bold tracking-widest truncate">Total Profit</div>
                            <div className={`text-xl font-bold font-mono ${!data || data.total_profit >= 0 ? 'text-[#30D158]' : 'text-[#FF453A]'}`}>
                                {data?.total_profit >= 0 ? '+' : ''}{data?.total_profit?.toFixed(2) || '0.00'}
                            </div>
                        </GlassPanel>
                    </div>

                    {/* Equity Curve - iOS 26 Premium Container */}
                    <div
                        className="rounded-3xl p-[1px] relative overflow-hidden"
                        style={{
                            background: 'linear-gradient(135deg, rgba(48, 209, 88, 0.3) 0%, transparent 50%, rgba(10, 132, 255, 0.2) 100%)',
                        }}
                    >
                        <div
                            className="rounded-3xl p-6 h-[360px] flex flex-col relative overflow-hidden"
                            style={{
                                background: 'rgba(28, 28, 30, 0.8)',
                                backdropFilter: 'blur(40px) saturate(180%)',
                            }}
                        >
                            <div className="flex justify-between items-center mb-4 z-10">
                                <h3 className="text-sm font-bold text-white flex items-center gap-2">
                                    <Activity size={14} className="text-[#30D158]" />
                                    Equity Curve
                                </h3>
                                <span className="text-[9px] font-bold text-gray-500 uppercase tracking-wider">All Time</span>
                            </div>
                            <div className="flex-1 w-full">
                                <MarketChart data={equityData} color="#30D158" />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default AnalyticsPage;
