// src/pages/ProfilePage.jsx
import { useEffect, useState } from 'react';
import { getPublicProfile } from '../api/client';
import Logo from '../components/Logo';

const LANG_COLORS = {
  python: '#3572A5', javascript: '#f1e05a', java: '#b07219', c: '#555555', cpp: '#f34b7d',
};

export default function ProfilePage({ username, onBack }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    getPublicProfile(username)
      .then(r => setProfile(r.data))
      .catch(() => setError('Profile not found.'));
  }, [username]);

  const handleCopyUrl = () => {
    const url = `${window.location.origin}${window.location.pathname}?profile=${username}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const initials = username ? username.slice(0, 2).toUpperCase() : '??';

  const joinedDate = profile?.date_joined
    ? new Date(profile.date_joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '';

  return (
    <div className="profile-page">
      <nav className="share-nav">
        <div className="share-nav-brand">
          <Logo size={28} id="profile-nav" />
          <span>CodeSwitch</span>
        </div>
        <button className="share-back" onClick={onBack}>← Back</button>
      </nav>

      {error && <p className="share-error" style={{ textAlign: 'center', paddingTop: 60 }}>{error}</p>}

      {!profile && !error && (
        <div className="share-loading">Loading profile...</div>
      )}

      {profile && (
        <div className="profile-content">
          <div className="profile-hero">
            <div className="profile-avatar">{initials}</div>
            <div className="profile-info">
              <h2 className="profile-username">{profile.username}</h2>
              {joinedDate && <p className="profile-joined">Member since {joinedDate}</p>}
              <button className="profile-share-btn" onClick={handleCopyUrl}>
                {copied ? 'Copied!' : '⬆ Copy profile link'}
              </button>
            </div>
          </div>

          <div className="profile-stats">
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.conversion_count}</span>
              <span className="profile-stat-label">Conversions</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.lessons_completed}</span>
              <span className="profile-stat-label">Lessons Done</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.modules_completed}</span>
              <span className="profile-stat-label">Modules Complete</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.languages_used.length}</span>
              <span className="profile-stat-label">Languages Used</span>
            </div>
          </div>

          {profile.languages_used.length > 0 && (
            <div className="profile-langs">
              <h4>Languages Used</h4>
              <div className="profile-lang-chips">
                {profile.languages_used.map(lang => (
                  <span
                    key={lang}
                    className="profile-lang-chip"
                    style={{ borderColor: LANG_COLORS[lang] || '#8b8b8b', color: LANG_COLORS[lang] || '#8b8b8b' }}
                  >
                    {lang}
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
