import { useState, useEffect } from 'react';
import Login from './pages/Login';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Converter from './pages/Converter';
import FileManager from './pages/FileManager';
import Learning from './pages/Learning';
import Reference from './pages/Reference';
import AdminPanel from './pages/AdminPanel';
import ShareView from './pages/ShareView';
import ProfilePage from './pages/ProfilePage';
import Playground from './pages/Playground';
import Logo from './components/Logo';
import { logout, getMe } from './api/client';
import type { User } from './types';

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const shareSlug = params.get('share');
  const profileUsername = params.get('profile');
  const playgroundMode = params.has('playground');

  const [user, setUser] = useState<User | null>(null);
  const [authLoading, setAuthLoading] = useState(true);
  const [page, setPage] = useState('dashboard');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Validate session via httpOnly cookie on every load
  useEffect(() => {
    getMe()
      .then(r => {
        setUser(r.data);
        localStorage.setItem('user', JSON.stringify(r.data));
      })
      .catch(() => {
        setUser(null);
        localStorage.removeItem('user');
      })
      .finally(() => setAuthLoading(false));
  }, []);

  const [showLanding, setShowLanding] = useState(() => !localStorage.getItem('user'));

  const handleLogin = (userData: User) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = async () => {
    try {
      await logout();
    } catch {
      // Cookie cleanup happens server-side; proceed regardless
    } finally {
      localStorage.clear();
      setUser(null);
      setShowLanding(true);
    }
  };

  const handleToggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
  };

  const clearUrlAndReload = () => {
    window.history.replaceState({}, '', window.location.pathname);
    window.location.reload();
  };

  // Shared snippet — render without auth check
  if (shareSlug) {
    return <ShareView slug={shareSlug} onBack={clearUrlAndReload} />;
  }

  // Public profile — render without auth check
  if (profileUsername) {
    return <ProfilePage username={profileUsername} onBack={clearUrlAndReload} />;
  }

  // Public playground — render without auth check
  if (playgroundMode) {
    return <Playground onBack={clearUrlAndReload} />;
  }

  // Don't flash login page while checking cookie auth
  if (authLoading) {
    return (
      <div className="flex h-screen items-center justify-center bg-bg">
        <span className="w-8 h-8 border-2 border-border border-t-accent rounded-full animate-spin" />
      </div>
    );
  }

  if (!user) {
    if (showLanding) return <Landing onGetStarted={() => setShowLanding(false)} />;
    return <Login onLogin={handleLogin} onBack={() => setShowLanding(true)} />;
  }

  const isStaff = user?.is_staff;
  const myUsername = user?.username;

  const pages: Record<string, React.ReactElement> = {
    dashboard: <Dashboard />,
    editor: <Converter />,
    files: <FileManager />,
    learning: <Learning />,
    reference: <Reference />,
    ...(myUsername && { profile: <ProfilePage username={myUsername} isOwner={true} onBack={() => setPage('dashboard')} /> }),
    ...(isStaff && { admin: <AdminPanel /> }),
  };

  const navItems = [
    { key: 'dashboard', label: '🏠 Dashboard' },
    { key: 'editor', label: '💻 Converter' },
    { key: 'files', label: '📁 Files' },
    { key: 'learning', label: '📚 Learn' },
    { key: 'reference', label: '📖 Reference' },
    ...(myUsername ? [{ key: 'profile', label: '👤 My Profile' }] : []),
    ...(isStaff ? [{ key: 'admin', label: '⚙️ Admin' }] : []),
  ];

  return (
    <div className="flex h-screen overflow-hidden" data-theme={theme}>
      {/* Sidebar */}
      <nav className="w-sidebar bg-surface border-r border-border flex flex-col py-5 px-3 gap-1.5 flex-shrink-0">
        {/* Brand */}
        <div className="flex items-center gap-2.5 mb-4">
          <Logo size={26} id="sidebar" />
          <h1 className="text-base font-bold text-primary tracking-tight">CodeSwitch</h1>
        </div>

        {/* Nav items */}
        {navItems.map(({ key, label }) => (
          <button
            key={key}
            className={`w-full text-left px-3 py-2.5 rounded text-[13px] transition-colors bg-transparent border-none ${page === key
                ? 'bg-accent text-white font-semibold'
                : 'text-muted hover:bg-border hover:text-primary'
              }`}
            onClick={() => setPage(key)}
          >
            {label}
          </button>
        ))}

        {/* Theme toggle */}
        <button
          className="mt-2 w-full text-left px-3 py-2 rounded text-xs transition-colors bg-transparent border-none text-muted hover:bg-border hover:text-primary"
          onClick={handleToggleTheme}
        >
          {theme === 'dark' ? '☀ Light Mode' : '🌙 Dark Mode'}
        </button>

        {/* Logout */}
        <button
          className="mt-auto w-full text-left px-3 py-2.5 rounded text-[13px] transition-colors bg-transparent border-none text-danger hover:bg-danger/10"
          onClick={handleLogout}
        >
          🚪 Logout
        </button>
      </nav>

      {/* Main content */}
      <main className="flex-1 overflow-y-auto p-7 px-8">
        {pages[page]}
      </main>
    </div>
  );
}
