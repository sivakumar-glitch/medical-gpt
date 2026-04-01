'use client';

import { useState } from 'react';
import { login } from '@/lib/api';

interface LoginFormProps {
    onLoginSuccess: (token: string) => void;
}

export default function LoginForm({ onLoginSuccess }: LoginFormProps) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        try {
            const token = await login(email, password);
            onLoginSuccess(token);
        } catch (err) {
            setError('Invalid credentials. Use admin@example.com/admin or user@example.com/user.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="flex flex-col items-center justify-center h-screen bg-slate-50 text-slate-900">
            <div className="w-full max-w-md p-8 bg-white rounded-2xl border border-slate-200 shadow-xl">
                <h2 className="text-3xl font-bold mb-6 text-center text-slate-800">MedAI Login</h2>
                <form onSubmit={handleSubmit} className="space-y-6">
                    <div>
                        <label className="block text-sm font-medium mb-2 text-slate-600">Email</label>
                        <input
                            type="email"
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                            className="w-full bg-white border border-slate-300 rounded-lg p-3 focus:ring-2 focus:ring-slate-400 outline-none transition-all"
                            placeholder="user@example.com"
                            required
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium mb-2 text-slate-600">Password</label>
                        <input
                            type="password"
                            value={password}
                            onChange={(e) => setPassword(e.target.value)}
                            className="w-full bg-white border border-slate-300 rounded-lg p-3 focus:ring-2 focus:ring-slate-400 outline-none transition-all"
                            placeholder="user"
                            required
                        />
                    </div>
                    {error && <p className="text-red-400 text-sm text-center">{error}</p>}
                    <button
                        type="submit"
                        disabled={isLoading}
                        className="w-full bg-slate-900 hover:bg-slate-800 text-white font-bold py-3 rounded-lg transition-colors disabled:opacity-50"
                    >
                        {isLoading ? 'Signing in...' : 'Sign In'}
                    </button>
                </form>
            </div>
        </div>
    );
}
