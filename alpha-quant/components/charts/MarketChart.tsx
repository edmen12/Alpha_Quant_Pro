import React, { useEffect, useRef } from 'react';
import { createChart, ColorType, CrosshairMode, AreaSeries } from 'lightweight-charts';

interface MarketChartProps {
    data: { time: string | number; value: number }[];
    color?: string;
    showGrid?: boolean;
}

const MarketChart = ({ data, color = '#30D158', showGrid = false }: MarketChartProps) => {
    const chartContainerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<any>(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // iOS 26 Premium Chart Configuration
        const chart: any = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: 'transparent' },
                textColor: 'rgba(255, 255, 255, 0.4)',
                fontFamily: "'SF Pro Display', -apple-system, BlinkMacSystemFont, 'Inter', sans-serif",
                fontSize: 10,
            },
            grid: {
                vertLines: { visible: showGrid, color: 'rgba(255, 255, 255, 0.03)' },
                horzLines: { visible: showGrid, color: 'rgba(255, 255, 255, 0.03)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: chartContainerRef.current.clientHeight,
            timeScale: {
                borderVisible: false,
                timeVisible: true,
                secondsVisible: false,
                fixLeftEdge: true,
                fixRightEdge: true,
            },
            rightPriceScale: {
                borderVisible: false,
                scaleMargins: { top: 0.1, bottom: 0.1 },
            },
            crosshair: {
                mode: CrosshairMode.Magnet,
                vertLine: {
                    color: 'rgba(255, 255, 255, 0.2)',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: 'rgba(28, 28, 30, 0.9)',
                },
                horzLine: {
                    color: 'rgba(255, 255, 255, 0.2)',
                    width: 1,
                    style: 2,
                    labelBackgroundColor: 'rgba(28, 28, 30, 0.9)',
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

        // Determine gradient colors based on main color
        const isGreen = color === '#30D158' || color.toLowerCase().includes('30d158');
        const topGradient = isGreen
            ? 'rgba(48, 209, 88, 0.4)'
            : color.replace(')', ', 0.4)').replace('rgb', 'rgba');
        const bottomGradient = 'rgba(0, 0, 0, 0)';

        const areaSeries = chart.addSeries(AreaSeries, {
            lineColor: color,
            topColor: topGradient,
            bottomColor: bottomGradient,
            lineWidth: 2,
            lineType: 2, // Curved line
            priceLineVisible: false,
            lastValueVisible: true,
            crosshairMarkerVisible: true,
            crosshairMarkerRadius: 4,
            crosshairMarkerBorderColor: '#ffffff',
            crosshairMarkerBackgroundColor: color,
        });

        // Sort data by time and convert to Unix timestamps (seconds)
        const sortedData = [...data]
            .map(d => ({
                time: typeof d.time === 'string'
                    ? Math.floor(new Date(d.time).getTime() / 1000)
                    : d.time,
                value: d.value,
            }))
            .filter(d => !isNaN(d.time) && d.time > 0)
            .sort((a, b) => a.time - b.time);

        if (sortedData.length > 0) {
            areaSeries.setData(sortedData as any);
            chart.timeScale().fitContent();
        }

        chartRef.current = chart;

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

        return () => {
            window.removeEventListener('resize', handleResize);
            resizeObserver.disconnect();
            chart.remove();
        };
    }, [data, color, showGrid]);

    return (
        <div
            ref={chartContainerRef}
            className="w-full h-full relative"
            style={{
                // Hide TradingView watermark with CSS
                '--tw-opacity': 1,
            } as React.CSSProperties}
        />
    );
};

export default MarketChart;
