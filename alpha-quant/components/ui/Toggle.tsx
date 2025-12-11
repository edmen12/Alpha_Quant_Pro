import React from "react";

interface ToggleProps {
    checked: boolean;
    onChange: (checked: boolean) => void;
}

export const Toggle = ({ checked, onChange }: ToggleProps) => {
    return (
        <button
            onClick={() => onChange(!checked)}
            className={`w-11 h-6 rounded-full transition-colors relative duration-300 ${checked ? 'bg-[#30D158]' : 'bg-[#3a3a3c]'
                }`}
        >
            <div
                className={`absolute top-0.5 left-0.5 w-5 h-5 bg-white rounded-full shadow-sm transition-transform duration-300 ${checked ? 'translate-x-[20px]' : 'translate-x-0'
                    }`}
            />
        </button>
    );
};
