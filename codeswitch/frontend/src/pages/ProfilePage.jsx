import { useEffect, useRef, useState } from 'react';
import { getPublicProfile, getProfile, updateProfile } from '../api/client';
import Logo from '../components/Logo';

const LANG_COLORS = {
  python: '#3572A5', javascript: '#f1e05a', java: '#b07219', c: '#555555', cpp: '#f34b7d',
};

const MEDIA_BASE = (process.env.REACT_APP_API_URL || 'http://localhost:8000/api').replace('/api', '');

export default function ProfilePage({ username, onBack, isOwner = false }) {
  const [profile, setProfile] = useState(null);
  const [error, setError] = useState('');
  const [copied, setCopied] = useState(false);

  // Edit state
  const [editing, setEditing] = useState(false);
  const [form, setForm] = useState({ first_name: '', last_name: '', bio: '' });
  const [avatarFile, setAvatarFile] = useState(null);
  const [avatarPreview, setAvatarPreview] = useState(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState('');
  const fileInputRef = useRef(null);

  useEffect(() => {
    if (isOwner) {
      Promise.all([getProfile(), getPublicProfile(username)])
        .then(([ownData, pubData]) => {
          setProfile({ ...pubData.data, ...ownData.data });
          setForm({
            first_name: ownData.data.first_name || '',
            last_name: ownData.data.last_name || '',
            bio: ownData.data.bio || '',
          });
        })
        .catch(() => setError('Could not load profile.'));
    } else {
      getPublicProfile(username)
        .then(r => setProfile(r.data))
        .catch(() => setError('Profile not found.'));
    }
  }, [username, isOwner]);

  const handleCopyUrl = () => {
    const url = `${window.location.origin}${window.location.pathname}?profile=${username}`;
    navigator.clipboard.writeText(url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleAvatarChange = (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setAvatarFile(file);
    setAvatarPreview(URL.createObjectURL(file));
  };

  const handleSave = async () => {
    setSaving(true);
    setSaveError('');
    try {
      const fd = new FormData();
      fd.append('first_name', form.first_name);
      fd.append('last_name', form.last_name);
      fd.append('bio', form.bio);
      if (avatarFile) fd.append('avatar', avatarFile);
      const r = await updateProfile(fd);
      setProfile(prev => ({ ...prev, ...r.data }));
      setEditing(false);
      setAvatarFile(null);
      // keep preview so avatar shows immediately without full reload
    } catch {
      setSaveError('Failed to save. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleCancel = () => {
    setEditing(false);
    setSaveError('');
    setAvatarFile(null);
    setAvatarPreview(null);
    if (fileInputRef.current) fileInputRef.current.value = '';
    setForm({
      first_name: profile.first_name || '',
      last_name: profile.last_name || '',
      bio: profile.bio || '',
    });
  };

  const initials = username ? username.slice(0, 2).toUpperCase() : '??';

  const displayName = (profile?.first_name || profile?.last_name)
    ? `${profile.first_name || ''} ${profile.last_name || ''}`.trim()
    : null;

  const avatarUrl = avatarPreview
    || (profile?.avatar ? `${MEDIA_BASE}${profile.avatar}` : null);

  const joinedDate = profile?.date_joined
    ? new Date(profile.date_joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '';

  return (
    <div className={isOwner ? 'profile-page-inner' : 'profile-page'}>
      {!isOwner && (
        <nav className="share-nav">
          <div className="share-nav-brand">
            <Logo size={28} id="profile-nav" />
            <span>CodeSwitch</span>
          </div>
          <button className="share-back" onClick={onBack}>← Back</button>
        </nav>
      )}

      {error && <p className="share-error" style={{ textAlign: 'center', paddingTop: 60 }}>{error}</p>}

      {!profile && !error && (
        <div className="share-loading">Loading profile...</div>
      )}

      {profile && (
        <div className="profile-content">
          <div className="profile-hero">
            {avatarUrl
              ? <img className="profile-avatar-img" src={avatarUrl} alt="avatar" />
              : <div className="profile-avatar">{initials}</div>
            }
            <div className="profile-info">
              {displayName && <p className="profile-display-name">{displayName}</p>}
              <h2 className="profile-username">{profile.username}</h2>
              {profile.bio && !editing && <p className="profile-bio">{profile.bio}</p>}
              {joinedDate && <p className="profile-joined">Member since {joinedDate}</p>}
              <div className="profile-hero-actions">
                <button className="profile-share-btn" onClick={handleCopyUrl}>
                  {copied ? 'Copied!' : '⬆ Copy profile link'}
                </button>
                {isOwner && !editing && (
                  <button className="profile-edit-btn" onClick={() => setEditing(true)}>
                    ✏ Edit Profile
                  </button>
                )}
              </div>
            </div>
          </div>

          {isOwner && editing && (
            <div className="profile-edit-form">
              <h4>Edit Profile</h4>
              <div className="profile-form-row">
                <div className="profile-form-field">
                  <label>First Name</label>
                  <input
                    type="text"
                    value={form.first_name}
                    onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))}
                    placeholder="First name"
                  />
                </div>
                <div className="profile-form-field">
                  <label>Last Name</label>
                  <input
                    type="text"
                    value={form.last_name}
                    onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))}
                    placeholder="Last name"
                  />
                </div>
              </div>
              <div className="profile-form-field">
                <label>Bio</label>
                <textarea
                  rows={3}
                  value={form.bio}
                  onChange={e => setForm(f => ({ ...f, bio: e.target.value }))}
                  placeholder="Tell others about yourself..."
                />
              </div>
              <div className="profile-form-field">
                <label>Profile Photo</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {avatarPreview && (
                    <img className="profile-avatar-preview" src={avatarPreview} alt="preview" />
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                  />
                </div>
              </div>
              {saveError && <p className="profile-save-error">{saveError}</p>}
              <div className="profile-form-actions">
                <button className="profile-form-cancel" onClick={handleCancel}>Cancel</button>
                <button className="profile-form-save" onClick={handleSave} disabled={saving}>
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          <div className="profile-stats">
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.conversion_count ?? '—'}</span>
              <span className="profile-stat-label">Conversions</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.lessons_completed ?? '—'}</span>
              <span className="profile-stat-label">Lessons Done</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.modules_completed ?? '—'}</span>
              <span className="profile-stat-label">Modules Complete</span>
            </div>
            <div className="profile-stat-card">
              <span className="profile-stat-value">{profile.languages_used?.length ?? '—'}</span>
              <span className="profile-stat-label">Languages Used</span>
            </div>
          </div>

          {profile.languages_used?.length > 0 && (
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
