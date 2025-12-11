import React, { useState } from 'react';
import { Sparkles } from 'lucide-react';
import { apiService } from '@/lib/api';
import { GlassPanel, GlassInput, GlassButton } from '@/components/ui/GlassComponents';

interface LoginScreenProps {
    onLogin: () => void;
}

const LoginScreen = ({ onLogin }: LoginScreenProps) => {
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        setError('');
        try {
            const res = await apiService.post('/login', { password });
            if (res.data.token) {
                localStorage.setItem('token', res.data.token);
                onLogin();
            } else {
                setError('Invalid Password');
            }
        } catch (e: any) {
            setError('Connection Error');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center">
            {/* iOS 26 Deep Space Background */}
            <div
                className="absolute inset-0"
                style={{
                    background: 'radial-gradient(circle at 50% 30%, rgba(48, 209, 88, 0.06) 0%, transparent 50%), radial-gradient(circle at 80% 80%, rgba(10, 132, 255, 0.04) 0%, transparent 40%), #050505',
                }}
            />
            <div className="absolute inset-0 backdrop-blur-3xl" />

            {/* Login Card */}
            <GlassPanel variant="elevated" className="relative w-full max-w-sm mx-6 p-8 animate-in zoom-in-95 fade-in duration-500">
                {/* Gradient Border Effect */}
                <div
                    className="absolute -inset-[1px] rounded-3xl -z-10"
                    style={{
                        background: 'linear-gradient(135deg, rgba(48, 209, 88, 0.3) 0%, transparent 40%, rgba(10, 132, 255, 0.2) 100%)',
                    }}
                />

                {/* Logo */}
                <div className="flex justify-center mb-8">
                    <div
                        className="w-20 h-20 rounded-[22px] flex items-center justify-center"
                        style={{
                            background: 'linear-gradient(135deg, #30D158 0%, #0A84FF 100%)',
                            boxShadow: '0 10px 40px rgba(48, 209, 88, 0.3), 0 0 0 1px rgba(255, 255, 255, 0.1) inset',
                        }}
                    >
                        <span className="text-white text-6xl font-light" style={{ fontFamily: 'serif' }}>α</span>
                    </div>
                </div>

                {/* Title */}
                <h1 className="text-3xl font-bold text-center text-white mb-1 tracking-tight">
                    Alpha Quant Pro
                </h1>
                <p className="text-center text-gray-500 mb-8 text-sm font-medium">
                    AI Trading Terminal
                </p>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <GlassInput
                        type="password"
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="text-center text-xl tracking-[0.4em] font-mono"
                        placeholder="••••••"
                        autoFocus
                    />

                    {error && (
                        <div
                            className="text-[#FF453A] text-sm text-center font-semibold px-4 py-3 rounded-xl"
                            style={{
                                background: 'rgba(255, 69, 58, 0.1)',
                                border: '1px solid rgba(255, 69, 58, 0.2)',
                            }}
                        >
                            {error}
                        </div>
                    )}

                    <GlassButton type="submit" disabled={loading}>
                        {loading ? 'Authenticating...' : 'Secure Access'}
                    </GlassButton>

                    <p className="text-center text-[10px] text-gray-600 mt-4">
                        Protected by end-to-end encryption
                    </p>
                </form>
            </GlassPanel>
        </div>
    );
};

export default LoginScreen;
