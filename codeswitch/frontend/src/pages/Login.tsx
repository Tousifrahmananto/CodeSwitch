import { useEffect, useRef, useState } from 'react';
import { googleLogin, login, register } from '../api/client';
import Logo from '../components/Logo';
import type { User } from '../types';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;
const GOOGLE_SCRIPT_SRC = 'https://accounts.google.com/gsi/client';

declare global {
  interface Window {
    google?: {
      accounts: {
        id: {
          initialize: (config: {
            client_id: string;
            callback: (response: { credential?: string }) => void;
            auto_select?: boolean;
            context?: 'signin' | 'signup' | 'use';
            itp_support?: boolean;
            ux_mode?: 'popup' | 'redirect';
            use_fedcm_for_button?: boolean;
          }) => void;
          renderButton: (
            parent: HTMLElement,
            options: {
              theme?: 'outline' | 'filled_blue' | 'filled_black';
              size?: 'large' | 'medium' | 'small';
              width?: number;
              text?: 'signin_with' | 'signup_with' | 'continue_with' | 'signin';
              shape?: 'rectangular' | 'pill' | 'circle' | 'square';
            },
          ) => void;
          cancel: () => void;
        };
      };
    };
  }
}

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
  const [googleLoading, setGoogleLoading] = useState(false);
  const [googleReady, setGoogleReady] = useState(false);
  const googleButtonRef = useRef<HTMLDivElement | null>(null);

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

  const handleGoogleCredential = async (credential?: string) => {
    setError('');
    setSuccess('');
    if (!credential) {
      setError('Google did not return a sign-in credential. Please try again.');
      return;
    }
    setGoogleLoading(true);
    try {
      const { data } = await googleLogin({ credential });
      onLogin(data.user);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string } } };
      setError(axiosErr.response?.data?.error || 'Google sign-in failed. Please try again.');
    } finally {
      setGoogleLoading(false);
    }
  };

  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !googleButtonRef.current) return;

    let cancelled = false;

    const renderGoogleButton = () => {
      if (cancelled || !window.google || !googleButtonRef.current) return;
      try {
        googleButtonRef.current.innerHTML = '';
        window.google.accounts.id.initialize({
          client_id: GOOGLE_CLIENT_ID,
          callback: response => handleGoogleCredential(response.credential),
          auto_select: false,
          context: 'signin',
          itp_support: true,
          ux_mode: 'popup',
          use_fedcm_for_button: true,
        });
        window.google.accounts.id.renderButton(googleButtonRef.current, {
          theme: 'outline',
          size: 'large',
          width: 340,
          text: 'continue_with',
          shape: 'rectangular',
        });
        setGoogleReady(true);
      } catch {
        setGoogleReady(false);
        setError('Google sign-in could not initialize. Check the Google client ID and allowed origins.');
      }
    };

    const existingScript = document.querySelector<HTMLScriptElement>(`script[src="${GOOGLE_SCRIPT_SRC}"]`);
    if (window.google) {
      renderGoogleButton();
    } else if (existingScript) {
      existingScript.addEventListener('load', renderGoogleButton, { once: true });
    } else {
      const script = document.createElement('script');
      script.src = GOOGLE_SCRIPT_SRC;
      script.async = true;
      script.defer = true;
      script.onload = renderGoogleButton;
      script.onerror = () => {
        setGoogleReady(false);
        if (!cancelled) setError('Could not load Google sign-in. Please try again later.');
      };
      document.head.appendChild(script);
    }

    return () => {
      cancelled = true;
      window.google?.accounts.id.cancel();
    };
  }, [onLogin]);

  const handleKey = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') handleSubmit();
  };

  const inputCls = 'w-full bg-bg border border-border rounded text-primary px-3 py-2.5 text-sm outline-none transition-colors focus:border-accent focus:shadow-[0_0_0_3px_rgba(79,142,247,0.16)] placeholder:text-muted';
  const labelCls = 'text-[12px] font-semibold text-muted uppercase tracking-wide';

  return (
    <div className="min-h-screen flex items-center justify-center px-4"
      style={{ background: 'radial-gradient(ellipse 80% 50% at 50% -10%, rgba(79,142,247,0.18) 0%, transparent 70%), var(--bg)' }}>
      <div className="bg-surface border border-accent/25 rounded-[16px] p-6 sm:p-10 w-full max-w-[420px] shadow-[0_24px_64px_rgba(0,0,0,0.45)]">

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
                ? 'bg-accent text-white font-semibold shadow-[0_2px_8px_rgba(79,142,247,0.32)]'
                : 'bg-transparent text-muted hover:text-primary'
                }`}
              onClick={() => switchMode(m)}
            >
              {m === 'login' ? 'Sign In' : 'Register'}
            </button>
          ))}
        </div>

        {GOOGLE_CLIENT_ID && (
          <div className="mb-6">
            <div className="flex justify-center min-h-[44px]">
              <div ref={googleButtonRef} aria-label="Continue with Google" />
            </div>
            {!googleReady && !error && (
              <p className="text-center text-xs text-muted mt-2 m-0">Loading Google sign-in...</p>
            )}
            {googleLoading && (
              <p className="text-center text-xs text-muted mt-2 m-0">Signing in with Google...</p>
            )}
            <div className="flex items-center gap-3 mt-5">
              <span className="h-px bg-border flex-1" />
              <span className="text-[11px] uppercase tracking-wide text-muted">or use email</span>
              <span className="h-px bg-border flex-1" />
            </div>
          </div>
        )}

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
