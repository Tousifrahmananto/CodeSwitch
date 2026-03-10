import { useState } from 'react';
import { login, register } from '../api/client';
import Logo from '../components/Logo';
import type { User } from '../types';

// Password requirement definitions
const PWD_REQS = [
  { id: 'len', label: 'At least 8 characters', test: (p: string) => p.length >= 8 },
  { id: 'upper', label: 'At least one uppercase letter', test: (p: string) => /[A-Z]/.test(p) },
  { id: 'lower', label: 'At least one lowercase letter', test: (p: string) => /[a-z]/.test(p) },
  { id: 'digit', label: 'At least one number', test: (p: string) => /\d/.test(p) },
  { id: 'special', label: 'At least one special character', test: (p: string) => /[!@#$%^&*()\-_=+[\]{};:'",.<>?/\\|`~]/.test(p) },
];

const STRENGTH_LABELS = ['', 'Weak', 'Weak', 'Fair', 'Good', 'Strong'];
const STRENGTH_COLORS = ['', '#f38ba8', '#f38ba8', '#f9e2af', '#89b4fa', '#a6e3a1'];

function PasswordStrength({ password }: { password: string }) {
  if (!password) return null;
  const metCount = PWD_REQS.filter(r => r.test(password)).length;
  return (
    <div className="mt-2">
      {/* Strength bar */}
      <div className="h-[3px] bg-border rounded-sm overflow-hidden mb-1.5">
        <div
          className="h-full rounded-sm transition-all duration-300"
          style={{ width: `${(metCount / PWD_REQS.length) * 100}%`, background: STRENGTH_COLORS[metCount] }}
        />
      </div>
      <span className="block text-[11px] font-semibold uppercase tracking-wide mb-1.5" style={{ color: STRENGTH_COLORS[metCount] }}>
        {STRENGTH_LABELS[metCount]}
      </span>
      <ul className="flex flex-col gap-0.5 list-none">
        {PWD_REQS.map(r => {
          const met = r.test(password);
          return (
            <li key={r.id} className={`flex items-center gap-1.5 text-[11px] transition-colors ${met ? 'text-success' : 'text-muted'}`}>
              <span className="text-[10px] w-3 text-center flex-shrink-0">{met ? '✓' : '○'}</span>
              {r.label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

interface LoginProps {
  onLogin: (user: User) => void;
  onBack?: () => void;
}

export default function Login({ onLogin, onBack }: LoginProps) {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [form, setForm] = useState({ username: '', email: '', password: '', password2: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm({ ...form, [e.target.name]: e.target.value });

  const switchMode = (next: 'login' | 'register') => {
    setMode(next);
    setError('');
    setSuccess('');
  };

  const handleSubmit = async () => {
    setError('');
    setSuccess('');
    setLoading(true);
    try {
      if (mode === 'login') {
        const { data } = await login({ username: form.username, password: form.password });
        // Tokens are set as httpOnly cookies by the server — only store user object
        onLogin(data.user);
      } else {
        await register(form);
        setSuccess('Account created! You can now sign in.');
        setMode('login');
        setForm({ username: '', email: '', password: '', password2: '' });
      }
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: unknown } };
      const data = axiosErr.response?.data;
      if (data && typeof data === 'object') {
        const messages = Object.values(data as Record<string, unknown[]>).flat().join(' ');
        setError(messages || 'Something went wrong.');
      } else {
        setError('Something went wrong.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit();
  };

  const inputCls = 'w-full bg-bg border border-border rounded text-primary px-3 py-2.5 text-sm outline-none transition-colors focus:border-accent focus:shadow-[0_0_0_3px_rgba(124,106,247,0.15)] placeholder:text-[#555570]';
  const labelCls = 'text-[12px] font-semibold text-muted uppercase tracking-wide';

  return (
    <div className="min-h-screen flex items-center justify-center"
      style={{ background: 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(124,106,247,0.18) 0%, transparent 70%), var(--bg)' }}>
      <div className="bg-surface border border-accent/25 rounded-[16px] p-10 w-[420px] shadow-[0_24px_64px_rgba(0,0,0,0.45)]">

        {/* Back to landing */}
        {onBack && (
          <button
            className="inline-flex items-center gap-1.5 bg-transparent border-none text-muted text-xs font-medium pb-4 cursor-pointer hover:text-primary transition-colors"
            onClick={onBack}
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M19 12H5M12 5l-7 7 7 7" />
            </svg>
            Back to home
          </button>
        )}

        {/* Brand */}
        <div className="flex flex-col items-center mb-7 gap-2">
          <Logo size={48} id="auth" />
          <h1 className="text-[22px] font-bold text-primary tracking-tight">CodeSwitch</h1>
          <p className="text-[13px] text-muted text-center">Translate code across languages instantly</p>
        </div>

        {/* Tab switcher */}
        <div className="flex bg-bg border border-border rounded-[10px] p-1 mb-6 gap-1">
          {(['login', 'register'] as const).map(m => (
            <button
              key={m}
              className={`flex-1 border-none rounded-[7px] py-2 text-[13px] font-medium transition-colors ${mode === m
                ? 'bg-accent text-white font-semibold shadow-[0_2px_8px_rgba(124,106,247,0.35)]'
                : 'bg-transparent text-muted hover:text-primary'
                }`}
              onClick={() => switchMode(m)}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        {/* Fields */}
        <div className="flex flex-col gap-3.5 mb-4">
          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>{mode === 'login' ? 'Email or Username' : 'Username'}</label>
            <input
              className={inputCls}
              name="username"
              placeholder={mode === 'login' ? 'Enter your email or username' : 'Choose a username'}
              value={form.username}
              onChange={handleChange}
              onKeyDown={handleKey}
              autoComplete="username"
            />
          </div>

          {mode === 'register' && (
            <div className="flex flex-col gap-1.5">
              <label className={labelCls}>Email</label>
              <input
                className={inputCls}
                name="email"
                type="email"
                placeholder="Enter your email"
                value={form.email}
                onChange={handleChange}
                onKeyDown={handleKey}
                autoComplete="email"
              />
            </div>
          )}

          <div className="flex flex-col gap-1.5">
            <label className={labelCls}>Password</label>
            <input
              className={inputCls}
              name="password"
              type="password"
              placeholder={mode === 'login' ? 'Enter your password' : 'Create a strong password'}
              value={form.password}
              onChange={handleChange}
              onKeyDown={handleKey}
              autoComplete={mode === 'login' ? 'current-password' : 'new-password'}
            />
            {mode === 'register' && <PasswordStrength password={form.password} />}
          </div>

          {mode === 'register' && (
            <div className="flex flex-col gap-1.5">
              <label className={labelCls}>Confirm Password</label>
              <input
                className={inputCls}
                name="password2"
                type="password"
                placeholder="Re-enter your password"
                value={form.password2}
                onChange={handleChange}
                onKeyDown={handleKey}
                autoComplete="new-password"
              />
            </div>
          )}
        </div>

        {/* Messages */}
        {error && (
          <p className="text-[13px] rounded p-2.5 mb-3 bg-danger/10 border border-danger text-danger">
            {error}
          </p>
        )}
        {success && (
          <p className="text-[13px] rounded p-2.5 mb-3 bg-success/10 border border-success text-success">
            {success}
          </p>
        )}

        {/* Submit */}
        <button
          className="w-full bg-accent hover:bg-accent-h text-white border-none rounded py-[11px] text-sm font-semibold tracking-wide transition-colors flex items-center justify-center min-h-[42px] disabled:opacity-60 disabled:cursor-default"
          onClick={handleSubmit}
          disabled={loading}
        >
          {loading
            ? <span className="w-[17px] h-[17px] border-2 border-white/30 border-t-white rounded-full animate-spin inline-block" />
            : mode === 'login' ? 'Sign In' : 'Create Account'
          }
        </button>

        <p className="text-center text-[13px] text-muted mt-4">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
          {' '}
          <span
            className="text-accent cursor-pointer font-semibold hover:text-accent-h hover:underline"
            onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}
          >
            {mode === 'login' ? 'Register' : 'Sign in'}
          </span>
        </p>

      </div>
    </div>
  );
}
