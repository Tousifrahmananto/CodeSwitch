import { useState } from 'react';
import { login, register } from '../api/client';

// Password requirement definitions
const PWD_REQS = [
  { id: 'len', label: 'At least 8 characters', test: p => p.length >= 8 },
  { id: 'upper', label: 'At least one uppercase letter', test: p => /[A-Z]/.test(p) },
  { id: 'lower', label: 'At least one lowercase letter', test: p => /[a-z]/.test(p) },
  { id: 'digit', label: 'At least one number', test: p => /\d/.test(p) },
  { id: 'special', label: 'At least one special character', test: p => /[!@#$%^&*()\-_=+\[\]{};:'",.<>?/\\|`~]/.test(p) },
];

const STRENGTH_LABELS = ['', 'Weak', 'Weak', 'Fair', 'Good', 'Strong'];
const STRENGTH_COLORS = ['', '#f38ba8', '#f38ba8', '#f9e2af', '#89b4fa', '#a6e3a1'];

function PasswordStrength({ password }) {
  if (!password) return null;
  const metCount = PWD_REQS.filter(r => r.test(password)).length;
  return (
    <div className="pwd-strength">
      <div className="pwd-strength-bar-track">
        <div
          className="pwd-strength-bar-fill"
          style={{
            width: `${(metCount / PWD_REQS.length) * 100}%`,
            background: STRENGTH_COLORS[metCount],
          }}
        />
      </div>
      <span className="pwd-strength-label" style={{ color: STRENGTH_COLORS[metCount] }}>
        {STRENGTH_LABELS[metCount]}
      </span>
      <ul className="pwd-req-list">
        {PWD_REQS.map(r => {
          const met = r.test(password);
          return (
            <li key={r.id} className={`pwd-req${met ? ' met' : ''}`}>
              <span className="pwd-req-icon">{met ? '✓' : '○'}</span>
              {r.label}
            </li>
          );
        })}
      </ul>
    </div>
  );
}

export default function Login({ onLogin }) {
  const [mode, setMode] = useState('login');
  const [form, setForm] = useState({ username: '', email: '', password: '', password2: '' });
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => setForm({ ...form, [e.target.name]: e.target.value });

  const switchMode = (next) => {
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
        localStorage.setItem('access_token', data.access);
        localStorage.setItem('refresh_token', data.refresh);
        onLogin(data.user);
      } else {
        await register(form);
        setSuccess('Account created! You can now sign in.');
        setMode('login');
        setForm({ username: '', email: '', password: '', password2: '' });
      }
    } catch (err) {
      const data = err.response?.data;
      if (data && typeof data === 'object') {
        // Flatten DRF validation errors
        const messages = Object.values(data).flat().join(' ');
        setError(messages || 'Something went wrong.');
      } else {
        setError('Something went wrong.');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleKey = (e) => {
    if (e.key === 'Enter') handleSubmit();
  };

  return (
    <div className="auth-page">
      <div className="auth-box">

        {/* Brand */}
        <div className="auth-brand">
          <div className="auth-logo"><span>CS</span></div>
          <h1 className="auth-app-name">CodeSwitch</h1>
          <p className="auth-tagline">Translate code across languages instantly</p>
        </div>

        {/* Tab switcher */}
        <div className="auth-tabs">
          <button
            className={mode === 'login' ? 'auth-tab active' : 'auth-tab'}
            onClick={() => switchMode('login')}
          >
            Sign In
          </button>
          <button
            className={mode === 'register' ? 'auth-tab active' : 'auth-tab'}
            onClick={() => switchMode('register')}
          >
            Register
          </button>
        </div>

        {/* Fields */}
        <div className="auth-fields">

          {/* Login: email or username; Register: username only */}
          <div className="auth-field">
            <label>{mode === 'login' ? 'Email or Username' : 'Username'}</label>
            <input
              name="username"
              placeholder={mode === 'login' ? 'Enter your email or username' : 'Choose a username'}
              value={form.username}
              onChange={handleChange}
              onKeyDown={handleKey}
              autoComplete="username"
            />
          </div>

          {mode === 'register' && (
            <div className="auth-field">
              <label>Email</label>
              <input
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

          <div className="auth-field">
            <label>Password</label>
            <input
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
            <div className="auth-field">
              <label>Confirm Password</label>
              <input
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
        {error && <p className="auth-msg auth-msg-error">{error}</p>}
        {success && <p className="auth-msg auth-msg-success">{success}</p>}

        {/* Submit */}
        <button className="auth-submit" onClick={handleSubmit} disabled={loading}>
          {loading
            ? <span className="auth-spinner" />
            : mode === 'login' ? 'Sign In' : 'Create Account'
          }
        </button>

        <p className="auth-switch">
          {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
          {' '}
          <span onClick={() => switchMode(mode === 'login' ? 'register' : 'login')}>
            {mode === 'login' ? 'Register' : 'Sign in'}
          </span>
        </p>

      </div>
    </div>
  );
}
