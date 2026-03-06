import { useEffect, useState } from 'react';
import { getProfile, getConversionHistory, getProgress, getFiles, getModules } from '../api/client';

const LANG_COLORS = { c: '#aaaaaa', python: '#5ba8f5', java: '#e8a44a' };
const LANG_BG = { c: 'rgba(170,170,170,0.12)', python: 'rgba(91,168,245,0.12)', java: 'rgba(232,164,74,0.12)' };

function LangChip({ lang }) {
  return (
    <span
      className="lang-chip"
      style={{
        color: LANG_COLORS[lang] || 'var(--text-muted)',
        background: LANG_BG[lang] || 'rgba(136,138,171,0.12)',
      }}
    >
      {lang}
    </span>
  );
}

function StatCard({ value, label, accent }) {
  return (
    <div className="stat-card">
      <span className="stat-value" style={accent ? { color: accent } : {}}>{value ?? '—'}</span>
      <span className="stat-label">{label}</span>
    </div>
  );
}

export default function Dashboard() {
  const [profile, setProfile] = useState(null);
  const [history, setHistory] = useState([]);
  const [progress, setProgress] = useState([]);
  const [files, setFiles] = useState([]);
  const [modules, setModules] = useState([]);
  const [loadError, setLoadError] = useState(null);

  useEffect(() => {
    getProfile()
      .then(r => setProfile(r.data))
      .catch(() => setLoadError('Failed to load profile.'));
    getConversionHistory().then(r => setHistory(r.data)).catch(() => { });
    getProgress().then(r => setProgress(r.data)).catch(() => { });
    getFiles().then(r => setFiles(r.data)).catch(() => { });
    getModules().then(r => setModules(r.data)).catch(() => { });
  }, []);

  const completedLessons = progress.filter(p => p.completed).length;
  const totalLessons = modules.reduce((sum, m) => sum + (m.lesson_count || 0), 0);
  const progressPct = totalLessons ? Math.round((completedLessons / totalLessons) * 100) : 0;

  // Per-module progress — only show modules that have started lessons
  const moduleProgress = modules
    .map(m => ({
      title: m.title,
      done: progress.filter(p => p.module_title === m.title && p.completed).length,
      total: m.lesson_count || 0,
    }))
    .filter(m => m.done > 0);

  const initials = profile?.username ? profile.username.slice(0, 2).toUpperCase() : '..';
  const memberSince = profile?.date_joined
    ? new Date(profile.date_joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '';

  return (
    <div className="dashboard">

      {/* ── Profile Header ── */}
      <div className="dash-profile">
        <div className="dash-avatar">{initials}</div>
        <div className="dash-profile-info">
          <h2 className="dash-username">{profile?.username || '—'}</h2>
          {profile?.email && <p className="dash-email">{profile.email}</p>}
          {memberSince && <p className="dash-joined">Member since {memberSince}</p>}
        </div>
      </div>

      {loadError && <p className="error" style={{ marginBottom: 16 }}>{loadError}</p>}

      {/* ── Stat Cards ── */}
      <div className="stats-grid">
        <StatCard value={history.length} label="Conversions" />
        <StatCard value={completedLessons} label="Lessons Done" />
        <StatCard value={files.length} label="Files Saved" />
        <StatCard value={`${progressPct}%`} label="Overall Progress" accent="var(--success)" />
      </div>

      {/* ── Bottom Two-Column ── */}
      <div className="dash-bottom">

        {/* Recent Conversions */}
        <div className="dash-section">
          <h3 className="dash-section-title">Recent Conversions</h3>
          {history.length === 0 ? (
            <p className="dash-empty">No conversions yet. Try the Converter!</p>
          ) : (
            <table className="history-table">
              <thead>
                <tr><th>From</th><th>To</th><th>Date</th></tr>
              </thead>
              <tbody>
                {history.slice(0, 8).map(h => (
                  <tr key={h.id}>
                    <td><LangChip lang={h.source_language} /></td>
                    <td><LangChip lang={h.target_language} /></td>
                    <td className="td-muted">{new Date(h.timestamp).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Learning Progress */}
        <div className="dash-section">
          <h3 className="dash-section-title">Learning Progress</h3>
          {moduleProgress.length === 0 ? (
            <p className="dash-empty">No learning activity yet. Start a module!</p>
          ) : (
            <div className="module-progress-list">
              {moduleProgress.map(({ title, done, total }) => {
                const pct = total ? Math.round((done / total) * 100) : 0;
                return (
                  <div key={title} className="module-progress-item">
                    <div className="module-progress-header">
                      <span className="module-progress-name">{title}</span>
                      <span className="module-progress-count">{done}/{total}</span>
                    </div>
                    <div className="module-progress-track">
                      <div className="module-progress-fill" style={{ width: `${pct}%` }} />
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
