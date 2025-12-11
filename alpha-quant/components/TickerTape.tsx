import React, { useMemo } from 'react';
import { cn } from '@/lib/utils';

interface TickerTapeProps {
    price?: number;
    symbol?: string;
    isRunning?: boolean;
}

const TickerTape = ({ isRunning, price, symbol }: TickerTapeProps) => {
    // Memoize both the base items AND the doubled array to prevent recreation
    const displayItems = useMemo(() => {
        const text = ` ${symbol || 'XAUUSD'} ${price?.toFixed(2) || '0.00'} `;
        // Create 20 items then double for seamless loop = 40 total
        return Array(40).fill(text);
    }, [symbol, price]);

    return (
        <div className="w-full overflow-hidden mb-6 relative group cursor-default">
            <div className={cn(
                "absolute inset-0 z-10 pointer-events-none bg-gradient-to-r from-background via-transparent to-background",
                isRunning ? 'opacity-100' : 'opacity-80'
            )}></div>

            <div className={cn(
                "flex whitespace-nowrap",
                isRunning ? "animate-scroll" : "opacity-30"
            )}>
                {displayItems.map((text, i) => (
                    <span key={i} className="mx-4 text-xs font-mono font-bold text-white/20">
                        {text} • LIVE MARKET DATA •
                    </span>
                ))}
            </div>
        </div>
    );
};

export default TickerTape;
