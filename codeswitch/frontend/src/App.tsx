import { useState, useEffect, lazy, Suspense, Component } from 'react';
import type { ErrorInfo, ReactNode, ReactElement } from 'react';
import Login from './pages/Login';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Reference from './pages/Reference';
import AdminPanel from './pages/AdminPanel';
import ShareView from './pages/ShareView';
import ProfilePage from './pages/ProfilePage';
import Playground from './pages/Playground';
import Logo from './components/Logo';
import { logout, getMe } from './api/client';
import type { User } from './types';

// Lazy-load Monaco-heavy pages — deferred until first navigation to that page.
// This removes ~5–7 MB from the initial bundle seen by Landing/Login/Dashboard.
const Converter = lazy(() => import('./pages/Converter'));
const FileManager = lazy(() => import('./pages/FileManager'));
const Learning = lazy(() => import('./pages/Learning'));

// ── Error Boundary ─────────────────────────────────────────────────────────────
// Prevents a render error in one page from crashing the entire app.
class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Page error:', error, info);
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center h-full gap-4 p-8 text-center">
          <p className="text-danger font-semibold">Something went wrong on this page.</p>
          <p className="text-sm text-muted">{this.state.error.message}</p>
          <button
            className="bg-accent text-white border-none rounded px-4 py-2 text-sm cursor-pointer"
            onClick={() => this.setState({ error: null })}
          >
            Try Again
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}

export default function App() {
  // Parse URL params as state so navigation back can reset them without a
  // full page reload (avoids re-downloading all assets and re-running auth).
  const [shareSlug, setShareSlug] = useState<string | null>(() =>
    new URLSearchParams(window.location.search).get('share')
  );
  const [profileUsername, setProfileUsername] = useState<string | null>(() =>
    new URLSearchParams(window.location.search).get('profile')
  );
  const [playgroundMode, setPlaygroundMode] = useState(() =>
    new URLSearchParams(window.location.search).has('playground')
  );

  // Initialise from localStorage immediately — returning users see the app
  // shell at once instead of a blank spinner while /api/me/ resolves.
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [page, setPage] = useState('dashboard');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  const PAGE_TITLES: Record<string, string> = {
    dashboard: 'Dashboard | CodeSwitch',
    editor: 'Code Converter | CodeSwitch',
    files: 'My Files | CodeSwitch',
    learning: 'Learning Modules | CodeSwitch',
    reference: 'Language Reference | CodeSwitch',
    profile: 'My Profile | CodeSwitch',
    admin: 'Admin | CodeSwitch',
  };

  useEffect(() => {
    document.title = PAGE_TITLES[page] ?? 'CodeSwitch';
  }, [page]);

  // Silently validate the session cookie in the background.
  // The cached user is shown immediately; this corrects it if the session has expired.
  useEffect(() => {
    if (!localStorage.getItem('user')) return;
    getMe()
      .then(r => {
        setUser(r.data);
        localStorage.setItem('user', JSON.stringify(r.data));
      })
      .catch(() => {
        setUser(null);
        localStorage.removeItem('user');
      });
  }, []);

  const [showLanding, setShowLanding] = useState(() => !localStorage.getItem('user'));

  const handleLogin = (userData: User) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    // Update UI immediately — don't wait for the server round-trip
    localStorage.clear();
    setUser(null);
    setShowLanding(true);
    // Fire-and-forget: blacklist the refresh token server-side
    logout().catch(() => { });
  };

  const handleToggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
  };

  // Clear URL special-mode params via React state — no full page reload needed.
  const clearSpecialMode = () => {
    window.history.replaceState({}, '', window.location.pathname);
    setShareSlug(null);
    setProfileUsername(null);
    setPlaygroundMode(false);
  };

  // Shared snippet — render without auth check
  if (shareSlug) return <ShareView slug={shareSlug} onBack={clearSpecialMode} />;

  // Public profile — render without auth check
  if (profileUsername) return <ProfilePage username={profileUsername} onBack={clearSpecialMode} />;

  // Public playground — render without auth check
  if (playgroundMode) return <Playground onBack={clearSpecialMode} />;

  if (!user) {
    if (showLanding) return <Landing onGetStarted={() => setShowLanding(false)} />;
    return <Login onLogin={handleLogin} onBack={() => setShowLanding(true)} />;
  }

  const isStaff = user?.is_staff;
  const myUsername = user?.username;

  const pages: Record<string, ReactElement> = {
    dashboard: <Dashboard />,
    editor: (
      <Suspense fallback={<p className="p-8 text-muted text-sm">Loading editor...</p>}>
        <Converter />
      </Suspense>
    ),
    files: (
      <Suspense fallback={<p className="p-8 text-muted text-sm">Loading files...</p>}>
        <FileManager />
      </Suspense>
    ),
    learning: (
      <Suspense fallback={<p className="p-8 text-muted text-sm">Loading modules...</p>}>
        <Learning />
      </Suspense>
    ),
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

      {/* Main content — each page is isolated in its own ErrorBoundary */}
      <main className="flex-1 overflow-y-auto p-7 px-8">
        <ErrorBoundary key={page}>
          {pages[page]}
        </ErrorBoundary>
      </main>
    </div>
  );
}
