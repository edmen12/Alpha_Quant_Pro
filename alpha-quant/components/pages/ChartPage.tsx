import React, { useState, useEffect, useRef } from 'react';
import { createChart, ColorType, LineStyle, CrosshairMode, CandlestickSeries } from 'lightweight-charts';
import { Target, RefreshCw } from 'lucide-react';
import { apiService } from '@/lib/api';

interface ChartPageProps {
    statusData: any;
}

const ChartPage = ({ statusData }: ChartPageProps) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<any>(null);
    const candleSeriesRef = useRef<any>(null);
    const [showTPSL, setShowTPSL] = useState(true);
    const [timeframe, setTimeframe] = useState('M15');
    const [symbol, setSymbol] = useState('XAUUSD');

    // Lines References
    const tpLineRef = useRef<any>(null);
    const slLineRef = useRef<any>(null);
    const entryLineRef = useRef<any>(null);

    const fetchData = async () => {
        try {
            const res = await apiService.get(`/chart_data?symbol=${symbol}&timeframe=${timeframe}`);
            // Backend may return { data: [...] } or { rates: [...] }
            const chartData = res.data?.data || res.data?.rates || [];

            if (chartData.length > 0 && candleSeriesRef.current) {
                // Ensure data is sorted by time and convert to proper format
                const sortedRates = chartData
                    .map((bar: any) => ({
                        time: typeof bar.time === 'string' ? Math.floor(new Date(bar.time).getTime() / 1000) : bar.time,
                        open: bar.open,
                        high: bar.high,
                        low: bar.low,
                        close: bar.close,
                    }))
                    .sort((a: any, b: any) => a.time - b.time);

                candleSeriesRef.current.setData(sortedRates);

                // Restore saved view or fit content
                const STORAGE_KEY = `chart_view_${symbol}_${timeframe}`;
                const saved = localStorage.getItem(STORAGE_KEY);
                if (saved) {
                    try {
                        const { from, to } = JSON.parse(saved);
                        if (from && to) {
                            chartRef.current?.timeScale().setVisibleRange({ from, to });
                        }
                    } catch {
                        chartRef.current?.timeScale().fitContent();
                    }
                } else {
                    chartRef.current?.timeScale().fitContent();
                }
            }
        } catch (e) {
            console.error("Fetch Chart Data Failed", e);
        }
    };

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // iOS 26 Premium Chart Configuration
        const chart: any = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: 'rgba(255, 255, 255, 0.4)',
                fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif",
                fontSize: 11,
            },
            grid: {
                vertLines: { visible: true, color: 'rgba(255, 255, 255, 0.03)' },
                horzLines: { visible: true, color: 'rgba(255, 255, 255, 0.03)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                borderVisible: false,
                timeVisible: true,
                secondsVisible: false,
            },
            rightPriceScale: {
                borderVisible: false,
                scaleMargins: { top: 0.05, bottom: 0.05 },
                autoScale: true,
                mode: 0, // Normal mode (allows manual scaling)
            },
            crosshair: {
                mode: CrosshairMode.Magnet,
                vertLine: {
                    color: 'rgba(255, 255, 255, 0.15)',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: 'rgba(28, 28, 30, 0.95)',
                },
                horzLine: {
                    color: 'rgba(255, 255, 255, 0.15)',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: 'rgba(28, 28, 30, 0.95)',
                },
            },
            // Enable user interaction
            handleScale: {
                mouseWheel: true,
                pinch: true,
                axisPressedMouseMove: true,
                axisDoubleClickReset: true,
            },
            handleScroll: {
                mouseWheel: true,
                pressedMouseMove: true,
                horzTouchDrag: true,
                vertTouchDrag: true, // Enable vertical touch for price axis
            },
        });

        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: '#30D158',
            downColor: '#FF453A',
            borderVisible: false,
            wickUpColor: '#30D158',
            wickDownColor: '#FF453A',
        });

        chartRef.current = chart;
        candleSeriesRef.current = candleSeries;

        // Initial Fetch
        fetchData();

        // Resize Handler
        const handleResize = () => {
            if (chartContainerRef.current) {
                chart.applyOptions({
                    width: chartContainerRef.current.clientWidth,
                    height: chartContainerRef.current.clientHeight,
                });
            }
        };
        window.addEventListener('resize', handleResize);
        const resizeObserver = new ResizeObserver(() => handleResize());
        resizeObserver.observe(chartContainerRef.current);

        // --- View State Persistence (Save on change) ---
        const STORAGE_KEY = `chart_view_${symbol}_${timeframe}`;
        let saveTimeout: NodeJS.Timeout;
        const handleVisibleRangeChange = () => {
            clearTimeout(saveTimeout);
            saveTimeout = setTimeout(() => {
                try {
                    const range = chart.timeScale().getVisibleRange();
                    if (range) {
                        localStorage.setItem(STORAGE_KEY, JSON.stringify(range));
                    }
                } catch (e) {
                    // Ignore errors
                }
            }, 500); // Debounce 500ms
        };

        chart.timeScale().subscribeVisibleTimeRangeChange(handleVisibleRangeChange);

        return () => {
            clearTimeout(saveTimeout);
            window.removeEventListener('resize', handleResize);
            resizeObserver.disconnect();
            chart.remove();
        };
    }, [timeframe, symbol]); // Re-init on TF change? Usually just re-fetch. But here we recreate for simplicity.

    // 2. TP/SL Lines Logic
    useEffect(() => {
        if (!candleSeriesRef.current || !statusData) return;
        const series = candleSeriesRef.current;

        // Clear existing
        if (tpLineRef.current) { series.removePriceLine(tpLineRef.current); tpLineRef.current = null; }
        if (slLineRef.current) { series.removePriceLine(slLineRef.current); slLineRef.current = null; }
        if (entryLineRef.current) { series.removePriceLine(entryLineRef.current); entryLineRef.current = null; }

        if (showTPSL && statusData.positions) {
            const activeTrade = statusData.positions.find((p: any) => p.symbol === symbol);
            if (activeTrade) {
                // Entry
                entryLineRef.current = series.createPriceLine({
                    price: parseFloat(activeTrade.price_open),
                    color: '#FFFFFF',
                    lineWidth: 1,
                    lineStyle: LineStyle.Dotted, // 2
                    axisLabelVisible: true,
                    title: 'ENTRY',
                });

                // TP
                if (activeTrade.tp > 0) {
                    tpLineRef.current = series.createPriceLine({
                        price: parseFloat(activeTrade.tp),
                        color: '#30D158',
                        lineWidth: 2,
                        lineStyle: LineStyle.Dashed, // 1
                        axisLabelVisible: true,
                        title: 'TP',
                    });
                }

                // SL
                if (activeTrade.sl > 0) {
                    slLineRef.current = series.createPriceLine({
                        price: parseFloat(activeTrade.sl),
                        color: '#FF453A',
                        lineWidth: 2,
                        lineStyle: LineStyle.Dashed, // 1
                        axisLabelVisible: true,
                        title: 'SL',
                    });
                }
            }
        }

    }, [statusData, showTPSL, symbol]);

    return (
        <div className="flex flex-col h-full bg-[#050505] relative">
            {/* Toolbar */}
            <div className="flex items-center justify-between px-4 py-3 border-b border-white/5 bg-[#050505]/80 backdrop-blur-xl z-10">
                <div className="flex items-center gap-2">
                    <div className="flex bg-black/20 p-1 rounded-lg border border-white/5">
                        {['M1', 'M5', 'M15', 'H1'].map(tf => (
                            <button
                                key={tf}
                                onClick={() => setTimeframe(tf)}
                                className={`px-3 py-1 rounded-md text-[10px] font-bold transition-all ${timeframe === tf ? 'bg-white/10 text-white shadow-sm' : 'text-gray-500 hover:text-gray-300'}`}
                            >
                                {tf}
                            </button>
                        ))}
                    </div>
                    <div className="h-4 w-px bg-white/10 mx-1"></div>
                    <span className="text-xs font-bold text-gray-400">{symbol}</span>
                </div>

                {/* Tools */}
                <div className="flex items-center gap-1 pr-1">
                    <button
                        onClick={() => setShowTPSL(!showTPSL)}
                        className={`p-1.5 rounded-full transition-colors ${showTPSL ? 'bg-[#30D158]/20 text-[#30D158]' : 'text-gray-500 hover:text-white'}`}
                        title="Toggle TP/SL Lines"
                    >
                        <Target size={14} />
                    </button>
                    <button
                        onClick={fetchData}
                        className="p-1.5 text-gray-400 hover:text-white rounded-full hover:bg-white/5 active:scale-95 transition-all"
                    >
                        <RefreshCw size={14} />
                    </button>
                </div>
            </div>

            {/* Live Indicator (Floating Top Right) */}
            <div className="absolute top-16 right-6 z-20 flex items-center gap-2 px-3 py-1.5 rounded-full bg-black/40 backdrop-blur-md border border-white/5">
                <div className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full rounded-full bg-[#30D158] opacity-75 animate-ping"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-[#30D158]"></span>
                </div>
                <span className="text-[9px] font-bold text-[#30D158]">LIVE DATA</span>
            </div>

            {/* Chart Container */}
            <div className="flex-1 relative w-full h-full" ref={chartContainerRef}>
                {/* Overlay Stats */}
                <div className="absolute top-4 left-4 z-20 flex flex-col gap-1 pointer-events-none">
                    <div className="text-2xl font-bold font-mono text-white tracking-tighter">
                        {statusData?.price ? statusData.price.toFixed(2) : '---'}
                    </div>
                </div>
            </div>
        </div >
    );
};

export default ChartPage;
