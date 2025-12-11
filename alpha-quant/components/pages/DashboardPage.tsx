import React, { useState } from 'react';
import { Cpu, Briefcase, Square, Play } from 'lucide-react';
import { apiService } from '@/lib/api';
import TickerTape from '@/components/TickerTape';
import { GlassPanel } from '@/components/ui/GlassComponents';

interface DashboardPageProps {
    isEngineRunning: boolean;
    toggleEngine: (running: boolean) => void;
    statusData: any;
    refreshStatus: () => void;
}

const DashboardPage = ({ isEngineRunning, toggleEngine, statusData, refreshStatus }: DashboardPageProps) => {
    const totalPnL = statusData?.daily_pnl || 0;
    const equity = statusData?.equity || 0;
    const balance = statusData?.balance || 0;
    const positions = statusData?.positions || [];

    const formattedPnL = (totalPnL >= 0 ? '+' : '') + totalPnL.toFixed(2);
    const pnlColor = totalPnL >= 0 ? 'text-[#30D158]' : 'text-[#FF453A]';
    const shadowColor = totalPnL >= 0 ? 'rgba(48,209,88,0.2)' : 'rgba(255,69,58,0.2)';

    const handleClose = async (ticket: number, symbol: string) => {
        if (confirm(`Close trade ${ticket}?`)) {
            try {
                await apiService.post('/close_trade', { ticket, symbol });
                refreshStatus();
            } catch (e: any) {
                alert(e.response?.data?.detail || e.message);
            }
        }
    };

    return (
        <div className="pt-8 pb-32 h-full bg-transparent overflow-y-auto no-scrollbar flex flex-col">
            {/* Header */}
            <div className="px-6 flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white tracking-tight">Monitor</h1>
                    <p className="text-xs text-gray-400 font-medium mt-1">AI TRADING TERMINAL</p>
                </div>
                <div className={`flex items-center gap-2 px-4 py-2 rounded-full border bg-[#1c1c1e]/40 backdrop-blur-xl transition-all duration-500 ${isEngineRunning ? 'border-success/30 shadow-glow-green' : 'border-warning/30'}`}>
                    <div className="relative flex h-2 w-2">
                        <span className={`absolute inline-flex h-full w-full rounded-full opacity-75 transition-colors duration-300 ${isEngineRunning ? 'animate-ping bg-success' : 'bg-warning'}`}></span>
                        <span className={`relative inline-flex rounded-full h-2 w-2 transition-colors duration-300 ${isEngineRunning ? 'bg-success' : 'bg-warning'}`}></span>
                    </div>
                    <span className={`text-[10px] font-bold tracking-wider transition-colors duration-500 ${isEngineRunning ? 'text-success' : 'text-warning'}`}>
                        {isEngineRunning ? 'SYSTEM ONLINE' : 'STANDBY MODE'}
                    </span>
                </div>
            </div>

            <TickerTape isRunning={isEngineRunning} price={statusData?.price} symbol={statusData?.symbol} />

            <div className="px-5 flex-1 flex flex-col">
                {/* Main Monitor Card */}
                <div className={`rounded-3xl p-8 mb-8 text-center glass-panel relative overflow-hidden group transition-all duration-700 border border-white/10 ${isEngineRunning ? 'border-[#30D158]/20' : 'grayscale opacity-80'}`}>
                    <div className={`absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent ${totalPnL >= 0 ? 'via-[#30D158]' : 'via-[#FF453A]'} to-transparent opacity-40`}></div>
                    <div className="flex items-center justify-center gap-2 mb-6 opacity-60">
                        <Cpu size={14} className="text-gray-400" />
                        <span className="text-[10px] font-mono text-gray-400 tracking-wider">
                            {isEngineRunning ? 'NEURAL ENGINE ACTIVE' : 'ENGINE DISCONNECTED'}
                        </span>
                    </div>

                    <div className="py-4">
                        <h3 className="text-[11px] font-bold text-gray-500 uppercase tracking-[0.2em] mb-2">Daily Performance</h3>
                        <div className={`text-6xl font-bold font-mono tracking-tighter transition-all duration-500 ${isEngineRunning ? `drop-shadow-[0_0_30px_${shadowColor}] ${pnlColor}` : 'text-gray-500'}`}>
                            {formattedPnL}
                        </div>
                    </div>

                    <div className="flex justify-center gap-12 mt-8 pt-8 border-t border-white/5">
                        <div className="text-center group-hover:transform group-hover:scale-105 transition-transform duration-300">
                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-2">Balance</div>
                            <div className="text-lg font-mono text-white font-bold">${balance.toFixed(2)}</div>
                        </div>
                        <div className="w-px bg-white/10 h-10"></div>
                        <div className="text-center group-hover:transform group-hover:scale-105 transition-transform duration-300">
                            <div className="text-[10px] text-gray-500 uppercase font-bold tracking-wider mb-2">Equity</div>
                            <div className="text-lg font-mono text-white font-bold">${equity.toFixed(2)}</div>
                        </div>
                    </div>
                </div>

                {/* Active Positions List */}
                <div className="mb-8 flex-1">
                    <div className="flex justify-between items-center mb-4 px-2">
                        <h3 className="text-sm font-bold text-white flex items-center gap-2">
                            <Briefcase size={16} className="text-primary" />
                            Active Positions
                        </h3>
                        <span className="text-[10px] font-bold text-gray-400 bg-black/20 px-2 py-1 rounded-md">{positions.length}</span>
                    </div>

                    <div className="space-y-3">
                        {positions.length === 0 && (
                            <div className="text-center text-gray-600 text-xs py-12 border border-dashed border-white/10 rounded-3xl bg-white/5">
                                No active executions
                            </div>
                        )}
                        {positions.map((pos: any) => (
                            <GlassPanel key={pos.ticket} className={`p-4 flex justify-between items-center relative overflow-hidden group transition-all duration-500 ${isEngineRunning ? '' : 'grayscale opacity-60'}`}>
                                <div className={`absolute left-0 top-0 bottom-0 w-1 transition-colors duration-500 ${pos.profit >= 0 ? 'bg-success' : 'bg-danger'}`}></div>

                                <div className="pl-3">
                                    <div className="flex items-center gap-3 mb-1">
                                        <span className="font-bold text-white text-base tracking-tight">{pos.symbol}</span>
                                        <span className={`text-[9px] font-bold px-1.5 py-0.5 rounded border font-mono ${pos.type === 'BUY'
                                            ? 'bg-primary/10 text-primary border-primary/20'
                                            : 'bg-danger/10 text-danger border-danger/20'
                                            }`}>
                                            {pos.type}
                                        </span>
                                    </div>
                                    <div className="flex items-center gap-3 text-[11px] text-gray-500 font-mono">
                                        <span>SIZE: <span className="text-gray-300">{pos.volume}</span></span>
                                        <span className="text-gray-700">|</span>
                                        <span>ENTRY: <span className="text-gray-300">{pos.price_open}</span></span>
                                    </div>
                                </div>

                                <div className="text-right flex flex-col items-end gap-2">
                                    <div className={`text-lg font-bold font-mono ${pos.profit >= 0 ? 'text-success drop-shadow-sm' : 'text-danger'}`}>
                                        {pos.profit >= 0 ? '+' : ''}{pos.profit.toFixed(2)}
                                    </div>
                                    <button
                                        onClick={() => handleClose(pos.ticket, pos.symbol)}
                                        className="text-[9px] font-bold text-white bg-white/5 hover:bg-danger/20 border border-white/10 hover:border-danger/30 px-3 py-1.5 rounded transition-all"
                                    >
                                        CLOSE
                                    </button>
                                </div>
                            </GlassPanel>
                        ))}
                    </div>
                </div>

                {/* Engine Control */}
                <div className="mt-auto pt-4 pb-8">
                    <button
                        onClick={() => toggleEngine(!isEngineRunning)}
                        className={`w-full relative group overflow-hidden border transition-all duration-500 active:scale-[0.98] py-5 rounded-2xl flex items-center justify-center gap-3 shadow-lg ${isEngineRunning
                            ? 'bg-surface border-danger/30 text-danger hover:bg-danger/10 hover:shadow-glow-red'
                            : 'bg-surface border-success/30 text-success hover:bg-success/10 hover:shadow-glow-green'
                            }`}
                    >
                        <div className={`absolute inset-0 bg-gradient-to-r from-transparent via-white/5 to-transparent skew-x-12 translate-x-[-200%] transition-transform duration-1000 ${isEngineRunning ? 'group-hover:animate-pulse' : ''}`}></div>

                        {isEngineRunning ? (
                            <>
                                <Square size={18} fill="currentColor" className="animate-pulse" />
                                <span className="text-sm font-bold uppercase tracking-[0.2em]">Stop Engine</span>
                            </>
                        ) : (
                            <>
                                <Play size={20} fill="currentColor" />
                                <span className="text-sm font-bold uppercase tracking-[0.2em]">Start Engine</span>
                            </>
                        )}
                    </button>
                    <div className="text-center mt-4">
                        <span className="text-[9px] font-bold text-gray-600 uppercase tracking-widest flex justify-center items-center gap-2">
                            <div className={`w-1.5 h-1.5 rounded-full ${isEngineRunning ? 'bg-success animate-pulse' : 'bg-gray-600'}`}></div>
                            {isEngineRunning ? 'Algorithm Execution Active' : 'Execution Suspended'}
                        </span>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default DashboardPage;
