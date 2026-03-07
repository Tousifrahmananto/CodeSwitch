import { useState } from 'react';
import Login from './pages/Login';
import Landing from './pages/Landing';
import Dashboard from './pages/Dashboard';
import Editor from './pages/Editor';
import FileManager from './pages/FileManager';
import Learning from './pages/Learning';
import AdminPanel from './pages/AdminPanel';
import ShareView from './pages/ShareView';
import ProfilePage from './pages/ProfilePage';
import Logo from './components/Logo';
import { logout } from './api/client';

export default function App() {
  const params = new URLSearchParams(window.location.search);
  const shareSlug = params.get('share');
  const profileUsername = params.get('profile');

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

  if (!user) {
    if (showLanding) return <Landing onGetStarted={() => setShowLanding(false)} />;
    return <Login onLogin={handleLogin} onBack={() => setShowLanding(true)} />;
  }

  const isStaff = user?.is_staff;
  const myUsername = user?.username;

  const pages = {
    dashboard: <Dashboard />,
    editor: <Editor />,
    files: <FileManager />,
    learning: <Learning />,
    ...(myUsername && { profile: <ProfilePage username={myUsername} onBack={() => setPage('dashboard')} /> }),
    ...(isStaff && { admin: <AdminPanel /> }),
  };

  const navItems = [
    { key: 'dashboard', label: '🏠 Dashboard' },
    { key: 'editor', label: '💻 Editor' },
    { key: 'files', label: '📁 Files' },
    { key: 'learning', label: '📚 Learn' },
    ...(myUsername ? [{ key: 'profile', label: '👤 My Profile' }] : []),
    ...(isStaff ? [{ key: 'admin', label: '⚙️ Admin' }] : []),
  ];

  return (
    <div className="app">
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
        <button className="logout" onClick={handleLogout}>🚪 Logout</button>
      </nav>
      <main className="content">{pages[page]}</main>
    </div>
  );
}
