import { cn } from "@/lib/utils";
import React from "react";

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
    children: React.ReactNode;
    className?: string;
    hoverEffect?: boolean;
    variant?: 'default' | 'elevated' | 'subtle';
}

export const GlassPanel = ({
    children,
    className,
    hoverEffect = false,
    variant = 'default',
    style,
    ...props
}: GlassPanelProps) => {
    const variants = {
        default: {
            background: 'rgba(28, 28, 30, 0.65)',
            backdropFilter: 'blur(40px) saturate(180%)',
            border: '1px solid rgba(255, 255, 255, 0.06)',
            boxShadow: '0 8px 32px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.04)',
        },
        elevated: {
            background: 'rgba(28, 28, 30, 0.8)',
            backdropFilter: 'blur(50px) saturate(200%)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            boxShadow: '0 20px 60px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.06)',
        },
        subtle: {
            background: 'rgba(28, 28, 30, 0.4)',
            backdropFilter: 'blur(20px) saturate(150%)',
            border: '1px solid rgba(255, 255, 255, 0.04)',
            boxShadow: '0 4px 16px rgba(0, 0, 0, 0.2)',
        },
    };

    return (
        <div
            className={cn(
                "rounded-3xl transition-all duration-300",
                hoverEffect && "active:scale-[0.97] cursor-pointer hover:bg-white/[0.02]",
                className
            )}
            style={{
                ...variants[variant],
                WebkitBackdropFilter: variants[variant].backdropFilter,
                ...style,
            }}
            {...props}
        >
            {children}
        </div>
    );
};

export const GlassInput = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
    ({ className, ...props }, ref) => {
        return (
            <input
                ref={ref}
                className={cn(
                    "w-full px-4 py-3.5 rounded-2xl text-white placeholder-gray-500 transition-all duration-200",
                    "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50",
                    className
                )}
                style={{
                    background: 'rgba(0, 0, 0, 0.35)',
                    border: '1px solid rgba(255, 255, 255, 0.08)',
                    backdropFilter: 'blur(10px)',
                }}
                {...props}
            />
        );
    }
);
GlassInput.displayName = "GlassInput";

// iOS 26 Button Component
export const GlassButton = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'secondary' | 'danger' }>(
    ({ className, variant = 'primary', children, ...props }, ref) => {
        const variants = {
            primary: 'bg-white text-black hover:bg-gray-100',
            secondary: 'bg-white/10 text-white hover:bg-white/15 border border-white/10',
            danger: 'bg-[#FF453A] text-white hover:bg-[#FF453A]/90',
        };

        return (
            <button
                ref={ref}
                className={cn(
                    "w-full py-4 rounded-2xl font-bold transition-all duration-200 active:scale-[0.97]",
                    "shadow-lg disabled:opacity-50 disabled:cursor-not-allowed",
                    variants[variant],
                    className
                )}
                {...props}
            >
                {children}
            </button>
        );
    }
);
GlassButton.displayName = "GlassButton";
