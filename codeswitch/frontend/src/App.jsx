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
import { logout } from './api/client';

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const shareSlug = params.get('share');
  const profileUsername = params.get('profile');
  const playgroundMode = params.has('playground');

  const [user, setUser] = useState(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return null;
    try {
      return JSON.parse(localStorage.getItem('user')) || { loggedIn: true };
    } catch {
      return { loggedIn: true };
    }
  });
  const [page, setPage] = useState('dashboard');
  const [theme, setTheme] = useState(() => localStorage.getItem('theme') || 'dark');
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);
  // Show landing page when no session exists; set to false once user clicks Get Started
  const [showLanding, setShowLanding] = useState(() => !localStorage.getItem('access_token'));

  const handleLogin = (userData) => {
    localStorage.setItem('user', JSON.stringify(userData));
    setUser(userData);
  };

  const handleLogout = async () => {
    const refresh = localStorage.getItem('refresh_token');
    try {
      await logout({ refresh });
    } catch {
      // Server-side blacklisting failed (e.g. token already expired), proceed anyway
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

  if (!user) {
    if (showLanding) return <Landing onGetStarted={() => setShowLanding(false)} />;
    return <Login onLogin={handleLogin} onBack={() => setShowLanding(true)} />;
  }

  const isStaff = user?.is_staff;
  const myUsername = user?.username;

  const pages = {
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
    <div className="app" data-theme={theme}>
      <nav className="sidebar">
        <div className="sidebar-brand">
          <Logo size={26} id="sidebar" />
          <h1>CodeSwitch</h1>
        </div>
        {navItems.map(({ key, label }) => (
          <button key={key} className={page === key ? 'active' : ''} onClick={() => setPage(key)}>
            {label}
          </button>
        ))}
        <button className="theme-toggle" onClick={handleToggleTheme}>
          {theme === 'dark' ? '☀ Light Mode' : '🌙 Dark Mode'}
        </button>
        <button className="logout" onClick={handleLogout}>🚪 Logout</button>
      </nav>
      <main className="content">{pages[page]}</main>
    </div>
  );
}
