import { useState, useEffect, lazy, Suspense, Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import {
  BrowserRouter,
  Routes,
  Route,
  Navigate,
  Outlet,
  useNavigate,
  useLocation,
  useParams,
} from 'react-router-dom';
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

// Lazy-load Monaco-heavy pages
const Converter = lazy(() => import('./pages/Converter'));
const FileManager = lazy(() => import('./pages/FileManager'));
const Learning = lazy(() => import('./pages/Learning'));

// ── Error Boundary ──────────────────────────────────────────────────────────
class ErrorBoundary extends Component<
  { children: ReactNode; resetKey?: string },
  { error: Error | null }
> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Page error:', error, info);
  }

  componentDidUpdate(prev: { resetKey?: string }) {
    if (prev.resetKey !== this.props.resetKey && this.state.error) {
      this.setState({ error: null });
    }
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

// ── Lazy fallback ───────────────────────────────────────────────────────────
function PageLoader({ label }: { label: string }) {
  return <p className="p-8 text-muted text-sm">Loading {label}…</p>;
}

// ── URL-aware wrappers for public pages ────────────────────────────────────
function ShareViewPage() {
  const { slug } = useParams<{ slug: string }>();
  const navigate = useNavigate();
  return <ShareView slug={slug!} onBack={() => navigate(-1 as any)} />;
}

function PublicProfilePage() {
  const { username } = useParams<{ username: string }>();
  const navigate = useNavigate();
  return <ProfilePage username={username!} onBack={() => navigate(-1 as any)} />;
}

// ── Protected layout: sidebar + main content ────────────────────────────────
function AppLayout({
  user,
  onLogout,
  theme,
  onThemeToggle,
}: {
  user: User;
  onLogout: () => void;
  theme: string;
  onThemeToggle: () => void;
}) {
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const isStaff = user?.is_staff;
  const myUsername = user?.username;

  // Update page title based on route
  const PAGE_TITLES: Record<string, string> = {
    '/dashboard': 'Dashboard | CodeSwitch',
    '/converter': 'Code Converter | CodeSwitch',
    '/files': 'My Files | CodeSwitch',
    '/learning': 'Learning Modules | CodeSwitch',
    '/reference': 'Language Reference | CodeSwitch',
    '/profile': 'My Profile | CodeSwitch',
    '/admin': 'Admin | CodeSwitch',
  };
  useEffect(() => {
    document.title = PAGE_TITLES[location.pathname] ?? 'CodeSwitch';
  }, [location.pathname]);

  const navItems = [
    { path: '/dashboard', label: '🏠 Dashboard' },
    { path: '/converter', label: '💻 Converter' },
    { path: '/files', label: '📁 Files' },
    { path: '/learning', label: '📚 Learn' },
    { path: '/reference', label: '📖 Reference' },
    ...(myUsername ? [{ path: '/profile', label: '👤 My Profile' }] : []),
    ...(isStaff ? [{ path: '/admin', label: '⚙️ Admin' }] : []),
  ];

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="flex h-screen overflow-hidden" data-theme={theme}>
      {/* Mobile overlay backdrop */}
      {mobileMenuOpen && (
        <div
          className="fixed inset-0 bg-black/60 z-40 md:hidden"
          onClick={() => setMobileMenuOpen(false)}
        />
      )}

      {/* Sidebar */}
      <nav
        className={`fixed md:static inset-y-0 left-0 z-50 md:z-auto w-sidebar bg-surface border-r border-border flex flex-col py-5 px-3 gap-1.5 flex-shrink-0 transition-transform duration-200 md:translate-x-0 ${
          mobileMenuOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center gap-2.5 mb-4">
          <Logo size={26} id="sidebar" />
          <h1 className="text-base font-bold text-primary tracking-tight">CodeSwitch</h1>
          <button
            className="md:hidden ml-auto bg-transparent border-none text-muted p-1 rounded hover:bg-border hover:text-primary transition-colors"
            onClick={() => setMobileMenuOpen(false)}
            aria-label="Close menu"
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" />
            </svg>
          </button>
        </div>

        {navItems.map(({ path, label }) => (
          <button
            key={path}
            className={`w-full text-left px-3 py-2.5 rounded text-[13px] transition-colors bg-transparent border-none ${
              isActive(path)
                ? 'bg-accent text-white font-semibold'
                : 'text-muted hover:bg-border hover:text-primary'
            }`}
            onClick={() => { navigate(path); setMobileMenuOpen(false); }}
          >
            {label}
          </button>
        ))}

        <button
          className="mt-2 w-full text-left px-3 py-2 rounded text-xs transition-colors bg-transparent border-none text-muted hover:bg-border hover:text-primary"
          onClick={onThemeToggle}
        >
          {theme === 'dark' ? '☀ Light Mode' : '🌙 Dark Mode'}
        </button>

        <button
          className="mt-auto w-full text-left px-3 py-2.5 rounded text-[13px] transition-colors bg-transparent border-none text-danger hover:bg-danger/10"
          onClick={onLogout}
        >
          🚪 Logout
        </button>
      </nav>

      {/* Main content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        {/* Mobile top bar */}
        <div className="md:hidden flex items-center gap-3 px-4 h-12 bg-surface border-b border-border flex-shrink-0">
          <button
            className="bg-transparent border-none text-muted p-1 rounded hover:bg-border hover:text-primary transition-colors"
            onClick={() => setMobileMenuOpen(true)}
            aria-label="Open menu"
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <line x1="3" y1="6" x2="21" y2="6" /><line x1="3" y1="12" x2="21" y2="12" /><line x1="3" y1="18" x2="21" y2="18" />
            </svg>
          </button>
          <Logo size={22} id="mobile-header" />
          <span className="font-bold text-sm text-primary">CodeSwitch</span>
        </div>

        <main className="flex-1 overflow-y-auto p-7 px-8 max-md:p-4 max-md:px-4">
          <ErrorBoundary resetKey={location.pathname}>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>
    </div>
  );
}

// ── Inner router (needs BrowserRouter context) ──────────────────────────────
function AppRoutes({
  user,
  theme,
  onLogin,
  onLogout,
  onThemeToggle,
}: {
  user: User | null;
  theme: string;
  onLogin: (u: User) => void;
  onLogout: () => void;
  onThemeToggle: () => void;
}) {
  const navigate = useNavigate();
  const isStaff = user?.is_staff;
  const myUsername = user?.username;

  const handleLogin = (u: User) => {
    onLogin(u);
    navigate('/dashboard', { replace: true });
  };

  return (
    <Routes>
      {/* Landing */}
      <Route
        path="/"
        element={
          user
            ? <Navigate to="/dashboard" replace />
            : <Landing onGetStarted={() => navigate('/login')} />
        }
      />

      {/* Auth */}
      <Route
        path="/login"
        element={
          user
            ? <Navigate to="/dashboard" replace />
            : <Login onLogin={handleLogin} onBack={() => navigate('/')} />
        }
      />

      {/* Public routes */}
      <Route path="/playground" element={<Playground onBack={() => navigate(-1 as any)} />} />
      <Route path="/share/:slug" element={<ShareViewPage />} />
      <Route path="/user/:username" element={<PublicProfilePage />} />

      {/* Protected layout */}
      <Route
        element={
          user
            ? <AppLayout user={user} onLogout={onLogout} theme={theme} onThemeToggle={onThemeToggle} />
            : <Navigate to="/login" replace />
        }
      >
        <Route path="/dashboard" element={<Dashboard />} />
        <Route
          path="/converter"
          element={
            <Suspense fallback={<PageLoader label="converter" />}>
              <Converter />
            </Suspense>
          }
        />
        <Route
          path="/files"
          element={
            <Suspense fallback={<PageLoader label="files" />}>
              <FileManager />
            </Suspense>
          }
        />
        <Route
          path="/learning"
          element={
            <Suspense fallback={<PageLoader label="modules" />}>
              <Learning />
            </Suspense>
          }
        />
        <Route path="/reference" element={<Reference />} />
        {myUsername && (
          <Route
            path="/profile"
            element={
              <ProfilePage
                username={myUsername}
                isOwner={true}
                onBack={() => navigate('/dashboard')}
              />
            }
          />
        )}
        {isStaff && <Route path="/admin" element={<AdminPanel />} />}
      </Route>

      {/* Catch-all */}
      <Route path="*" element={<Navigate to={user ? '/dashboard' : '/'} replace />} />
    </Routes>
  );
}

// ── Root App ────────────────────────────────────────────────────────────────
export default function App() {
  const [user, setUser] = useState<User | null>(() => {
    try {
      const stored = localStorage.getItem('user');
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Silently validate session on mount
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

  const handleLogin = (userData: User) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = () => {
    localStorage.clear();
    setUser(null);
    logout().catch(() => {});
  };

  const handleToggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('theme', next);
  };

  return (
    <BrowserRouter>
      <AppRoutes
        user={user}
        theme={theme}
        onLogin={handleLogin}
        onLogout={handleLogout}
        onThemeToggle={handleToggleTheme}
      />
    </BrowserRouter>
  );
}
