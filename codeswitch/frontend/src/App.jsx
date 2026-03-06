import { useState } from 'react';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import Editor from './pages/Editor';
import FileManager from './pages/FileManager';
import Learning from './pages/Learning';
import AdminPanel from './pages/AdminPanel';
import { logout } from './api/client';

export default function App() {
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
    }
  };

  if (!user) return <Login onLogin={handleLogin} />;

  const isStaff = user?.is_staff;

  const pages = {
    dashboard: <Dashboard />,
    editor: <Editor />,
    files: <FileManager />,
    learning: <Learning />,
    ...(isStaff && { admin: <AdminPanel /> }),
  };

  const navItems = [
    { key: 'dashboard', label: '🏠 Dashboard' },
    { key: 'editor', label: '💻 Editor' },
    { key: 'files', label: '📁 Files' },
    { key: 'learning', label: '📚 Learn' },
    ...(isStaff ? [{ key: 'admin', label: '⚙️ Admin' }] : []),
  ];

  return (
    <div className="app">
      <nav className="sidebar">
        <h1>CodeSwitch</h1>
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

