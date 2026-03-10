import { useEffect, useRef, useState } from 'react';
import { getPublicProfile, getProfile, updateProfile } from '../api/client';
import Logo from '../components/Logo';

const LANG_COLORS = {
  python: '#3572A5', javascript: '#f1e05a', java: '#b07219', c: '#555555', cpp: '#f34b7d',
};

const MEDIA_BASE = (import.meta.env.VITE_API_URL || 'http://localhost:8000/api').replace('/api', '');

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
    const url = `${window.location.origin}/user/${username}`;
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
    <div className={isOwner ? '' : 'min-h-screen'}>
      {!isOwner && (
        <nav className="flex items-center justify-between px-5 py-3 border-b border-border">
          <div className="flex items-center gap-2 font-semibold">
            <Logo size={28} id="profile-nav" />
            <span>CodeSwitch</span>
          </div>
          <button
            className="text-sm text-muted hover:text-primary cursor-pointer border border-border rounded px-3 py-1.5 transition-colors bg-transparent"
            onClick={onBack}
          >← Back</button>
        </nav>
      )}

      {error && <p className="bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm m-5" style={{ textAlign: 'center', paddingTop: 60 }}>{error}</p>}

      {!profile && !error && (
        <div className="flex items-center justify-center p-12 text-muted text-sm">Loading profile...</div>
      )}

      {profile && (
        <div className="max-w-2xl mx-auto p-5 flex flex-col gap-5">
          <div className="flex items-center gap-5 bg-surface border border-border rounded p-5">
            {avatarUrl
              ? <img className="w-[72px] h-[72px] rounded-full object-cover flex-shrink-0" src={avatarUrl} alt="avatar" />
              : <div className="w-[72px] h-[72px] rounded-full bg-accent text-white text-xl font-bold flex items-center justify-center flex-shrink-0 tracking-wide">{initials}</div>
            }
            <div className="flex flex-col gap-1">
              {displayName && <p className="text-base font-semibold m-0">{displayName}</p>}
              <h2 className="text-xl font-bold m-0">{profile.username}</h2>
              {profile.bio && !editing && <p className="text-sm text-muted m-0">{profile.bio}</p>}
              {joinedDate && <p className="text-xs text-muted m-0">Member since {joinedDate}</p>}
              <div className="flex gap-2 mt-2">
                <button
                  className="text-xs border border-border rounded px-3 py-1.5 text-muted hover:text-primary cursor-pointer bg-transparent transition-colors"
                  onClick={handleCopyUrl}
                >
                  {copied ? 'Copied!' : '⬆ Copy profile link'}
                </button>
                {isOwner && !editing && (
                  <button
                    className="text-xs border border-accent rounded px-3 py-1.5 text-accent hover:bg-accent/10 cursor-pointer bg-transparent transition-colors"
                    onClick={() => setEditing(true)}
                  >
                    ✏ Edit Profile
                  </button>
                )}
              </div>
            </div>
          </div>

          {isOwner && editing && (
            <div className="bg-surface border border-border rounded p-4 flex flex-col gap-3">
              <h4>Edit Profile</h4>
              <div className="grid grid-cols-2 gap-3">
                <div className="flex flex-col gap-1">
                  <label>First Name</label>
                  <input
                    type="text"
                    value={form.first_name}
                    onChange={e => setForm(f => ({ ...f, first_name: e.target.value }))}
                    placeholder="First name"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label>Last Name</label>
                  <input
                    type="text"
                    value={form.last_name}
                    onChange={e => setForm(f => ({ ...f, last_name: e.target.value }))}
                    placeholder="Last name"
                  />
                </div>
              </div>
              <div className="flex flex-col gap-1">
                <label>Bio</label>
                <textarea
                  rows={3}
                  value={form.bio}
                  onChange={e => setForm(f => ({ ...f, bio: e.target.value }))}
                  placeholder="Tell others about yourself..."
                />
              </div>
              <div className="flex flex-col gap-1">
                <label>Profile Photo</label>
                <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
                  {avatarPreview && (
                    <img className="w-12 h-12 rounded-full object-cover" src={avatarPreview} alt="preview" />
                  )}
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleAvatarChange}
                  />
                </div>
              </div>
              {saveError && <p className="text-sm text-danger m-0">{saveError}</p>}
              <div className="flex gap-2 justify-end">
                <button
                  className="px-4 py-2 text-sm border border-border rounded text-muted hover:text-primary cursor-pointer bg-transparent transition-colors"
                  onClick={handleCancel}
                >Cancel</button>
                <button
                  className="px-4 py-2 text-sm bg-accent hover:bg-accent-h text-white rounded border-none cursor-pointer transition-colors disabled:opacity-50"
                  onClick={handleSave}
                  disabled={saving}
                >
                  {saving ? 'Saving...' : 'Save Changes'}
                </button>
              </div>
            </div>
          )}

          <div className="grid grid-cols-4 gap-3">
            <div className="bg-surface border border-border rounded p-4 flex flex-col items-center text-center">
              <span className="text-[28px] font-bold text-accent leading-tight">{profile.conversion_count ?? '—'}</span>
              <span className="text-[11px] text-muted mt-1 uppercase tracking-wide">Conversions</span>
            </div>
            <div className="bg-surface border border-border rounded p-4 flex flex-col items-center text-center">
              <span className="text-[28px] font-bold text-accent leading-tight">{profile.lessons_completed ?? '—'}</span>
              <span className="text-[11px] text-muted mt-1 uppercase tracking-wide">Lessons Done</span>
            </div>
            <div className="bg-surface border border-border rounded p-4 flex flex-col items-center text-center">
              <span className="text-[28px] font-bold text-accent leading-tight">{profile.modules_completed ?? '—'}</span>
              <span className="text-[11px] text-muted mt-1 uppercase tracking-wide">Modules Complete</span>
            </div>
            <div className="bg-surface border border-border rounded p-4 flex flex-col items-center text-center">
              <span className="text-[28px] font-bold text-accent leading-tight">{profile.languages_used?.length ?? '—'}</span>
              <span className="text-[11px] text-muted mt-1 uppercase tracking-wide">Languages Used</span>
            </div>
          </div>

          {profile.languages_used?.length > 0 && (
            <div className="bg-surface border border-border rounded p-4">
              <h4>Languages Used</h4>
              <div className="flex flex-wrap gap-2 mt-2">
                {profile.languages_used.map(lang => (
                  <span
                    key={lang}
                    className="text-xs px-2.5 py-1 rounded-full border font-mono font-semibold"
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
