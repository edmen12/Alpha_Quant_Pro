import React from 'react';
import { LayoutDashboard, Activity, BarChart2, Clock, Settings, LucideIcon } from 'lucide-react';

interface NavigationBarProps {
    activeTab: string;
    onSwitch: (tab: string) => void;
}

interface Tab {
    id: string;
    icon: LucideIcon;
    label: string;
}

const NavigationBar = ({ activeTab, onSwitch }: NavigationBarProps) => {
    const tabs: Tab[] = [
        { id: 'dashboard', icon: LayoutDashboard, label: 'Hub' },
        { id: 'chart', icon: Activity, label: 'Market' },
        { id: 'analytics', icon: BarChart2, label: 'Stats' },
        { id: 'history', icon: Clock, label: 'History' },
        { id: 'settings', icon: Settings, label: 'Config' }
    ];

    return (
        <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
            {/* iOS 26 Floating Dock */}
            <div
                className="px-3 py-2.5 rounded-[28px] flex items-center gap-1"
                style={{
                    background: 'rgba(28, 28, 30, 0.75)',
                    backdropFilter: 'blur(50px) saturate(200%)',
                    WebkitBackdropFilter: 'blur(50px) saturate(200%)',
                    boxShadow: `
                        0 20px 60px rgba(0, 0, 0, 0.5),
                        0 0 0 1px rgba(255, 255, 255, 0.06),
                        inset 0 1px 0 rgba(255, 255, 255, 0.05)
                    `,
                }}
            >
                {tabs.map(tab => {
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => onSwitch(tab.id)}
                            className="group relative flex flex-col items-center justify-center w-14 h-14 rounded-2xl transition-all duration-300 active:scale-90"
                            style={{
                                background: isActive ? 'rgba(255, 255, 255, 0.12)' : 'transparent',
                                boxShadow: isActive ? 'inset 0 0 0 1px rgba(255, 255, 255, 0.08)' : 'none',
                            }}
                        >
                            {/* Icon */}
                            <tab.icon
                                size={22}
                                strokeWidth={isActive ? 2.2 : 1.8}
                                className={`transition-all duration-300 ${isActive ? 'text-white' : 'text-gray-500 group-hover:text-gray-300'}`}
                            />

                            {/* Label */}
                            <span className={`text-[9px] font-semibold mt-1 tracking-wide transition-all duration-300 ${isActive ? 'text-white' : 'text-gray-500 group-hover:text-gray-400'}`}>
                                {tab.label}
                            </span>

                            {/* Active Glow Dot */}
                            {isActive && (
                                <div
                                    className="absolute -bottom-0.5 w-1 h-1 rounded-full bg-white"
                                    style={{
                                        boxShadow: '0 0 8px 2px rgba(255, 255, 255, 0.6)'
                                    }}
                                />
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
};

export default NavigationBar;
