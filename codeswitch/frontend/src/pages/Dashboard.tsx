import { useEffect, useState } from 'react';
import { getProfile, getConversionHistory, getProgress, getFiles, getModules } from '../api/client';

const LANG_COLORS = {
  c: '#aaaaaa', python: '#5ba8f5', java: '#e8a44a',
  javascript: '#f1e05a', cpp: '#f34b7d',
};
const LANG_BG = {
  c: 'rgba(170,170,170,0.12)', python: 'rgba(91,168,245,0.12)', java: 'rgba(232,164,74,0.12)',
  javascript: 'rgba(241,224,90,0.12)', cpp: 'rgba(243,75,125,0.12)',
};

// Module-level cache — survives re-mounts/navigation within the same session
const _dashCache: {
  data: { profile: any; history: any[]; progress: any[]; files: any[]; modules: any[] } | null;
  ts: number;
} = { data: null, ts: 0 };
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

function LangChip({ lang }) {
  return (
    <span
      className="inline-block text-[11px] font-semibold px-2 py-0.5 rounded font-mono"
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
    <div className="bg-surface border border-border rounded p-5 flex flex-col items-center text-center">
      <span className="text-[28px] font-bold text-accent leading-tight" style={accent ? { color: accent } : {}}>{value ?? '—'}</span>
      <span className="text-[11px] text-muted mt-1.5 uppercase tracking-wide">{label}</span>
    </div>
  );
}

export default function Dashboard() {
  const fresh = _dashCache.data && Date.now() - _dashCache.ts < CACHE_TTL
    ? _dashCache.data : null;

  const [profile, setProfile] = useState(fresh?.profile ?? null);
  const [history, setHistory] = useState(fresh?.history ?? []);
  const [progress, setProgress] = useState(fresh?.progress ?? []);
  const [files, setFiles] = useState(fresh?.files ?? []);
  const [modules, setModules] = useState(fresh?.modules ?? []);
  const [loadError, setLoadError] = useState(null);
  const [loading, setLoading] = useState(!fresh);

  useEffect(() => {
    if (fresh) return; // Serve cached data — skip the network round-trips
    Promise.all([
      getProfile(),
      getConversionHistory(),
      getProgress(),
      getFiles(),
      getModules(),
    ]).then(([profileRes, historyRes, progressRes, filesRes, modulesRes]) => {
      const data = {
        profile: profileRes.data,
        history: historyRes.data,
        progress: progressRes.data,
        files: filesRes.data,
        modules: modulesRes.data,
      };
      _dashCache.data = data;
      _dashCache.ts = Date.now();
      setProfile(data.profile);
      setHistory(data.history);
      setProgress(data.progress);
      setFiles(data.files);
      setModules(data.modules);
    }).catch(() => setLoadError('Failed to load dashboard data.'))
      .finally(() => setLoading(false));
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
    <div className="p-5">

      {loading && <p className="text-sm text-muted mb-4">Loading dashboard...</p>}
      {loadError && <p className="bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm mb-3">{loadError}</p>}

      {/* ── Profile Header ── */}
      <div className="flex items-center gap-4 p-5 bg-surface border border-border rounded mb-5">
        <div className="w-[52px] h-[52px] rounded-full bg-accent text-white text-lg font-bold flex items-center justify-center flex-shrink-0 tracking-wide">{initials}</div>
        <div className="flex flex-col gap-0.5">
          <h2 className="text-base font-semibold m-0">{profile?.username || '—'}</h2>
          {profile?.email && <p className="text-sm text-muted m-0">{profile.email}</p>}
          {memberSince && <p className="text-xs text-muted m-0">Member since {memberSince}</p>}
        </div>
      </div>

      {/* ── Stat Cards ── */}
      <div className="grid grid-cols-4 gap-3 mb-5">
        <StatCard value={history.length} label="Conversions" />
        <StatCard value={completedLessons} label="Lessons Done" />
        <StatCard value={files.length} label="Files Saved" />
        <StatCard value={`${progressPct}%`} label="Overall Progress" accent="var(--success)" />
      </div>

      {/* ── Bottom Two-Column ── */}
      <div className="grid grid-cols-2 gap-4">

        {/* Recent Conversions */}
        <div className="bg-surface border border-border rounded p-4">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted mb-3.5">Recent Conversions</h3>
          {history.length === 0 ? (
            <p className="text-sm text-muted py-2">No conversions yet. Try the Converter!</p>
          ) : (
            <table className="w-full border-collapse text-sm">
              <thead>
                <tr><th>From</th><th>To</th><th>Date</th></tr>
              </thead>
              <tbody>
                {history.slice(0, 8).map(h => (
                  <tr key={h.id}>
                    <td><LangChip lang={h.source_language} /></td>
                    <td><LangChip lang={h.target_language} /></td>
                    <td className="text-muted">{new Date(h.timestamp).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Learning Progress */}
        <div className="bg-surface border border-border rounded p-4">
          <h3 className="text-[11px] font-semibold uppercase tracking-wider text-muted mb-3.5">Learning Progress</h3>
          {moduleProgress.length === 0 ? (
            <p className="text-sm text-muted py-2">No learning activity yet. Start a module!</p>
          ) : (
            <div className="flex flex-col gap-3">
              {moduleProgress.map(({ title, done, total }) => {
                const pct = total ? Math.round((done / total) * 100) : 0;
                return (
                  <div key={title} className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">{title}</span>
                      <span className="text-xs text-muted">{done}/{total}</span>
                    </div>
                    <div className="h-1.5 bg-border rounded-full overflow-hidden">
                      <div className="h-full bg-accent rounded-full transition-all" style={{ width: `${pct}%` }} />
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
