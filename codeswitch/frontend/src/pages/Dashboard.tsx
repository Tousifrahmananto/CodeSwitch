import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, getConversionHistory, getProgress, getFiles, getModules } from '../api/client';
import type { CodeFile, ConversionRecord, LearningModule, User, UserProgress } from '../types';

const LANG_COLORS: Record<string, string> = {
  c: '#aaaaaa', python: '#5ba8f5', java: '#e8a44a',
  javascript: '#f1e05a', cpp: '#f34b7d',
};
const LANG_BG: Record<string, string> = {
  c: 'rgba(170,170,170,0.12)', python: 'rgba(91,168,245,0.12)', java: 'rgba(232,164,74,0.12)',
  javascript: 'rgba(241,224,90,0.12)', cpp: 'rgba(243,75,125,0.12)',
};

const _dashCache: {
  data: {
    profile: User;
    history: ConversionRecord[];
    progress: UserProgress[];
    files: CodeFile[];
    modules: LearningModule[];
  } | null;
  ts: number;
} = { data: null, ts: 0 };
const CACHE_TTL = 5 * 60 * 1000;

function LangChip({ lang }: { lang: string }) {
  return (
    <span
      className="inline-block text-xs font-semibold px-2 py-0.5 rounded font-mono"
      style={{
        color: LANG_COLORS[lang] || 'var(--text-muted)',
        background: LANG_BG[lang] || 'rgba(136,138,171,0.12)',
      }}
    >
      {lang}
    </span>
  );
}

function StatCard({ value, label, accent, icon }: { value: string | number; label: string; accent?: string; icon: string }) {
  return (
    <div className="bg-surface border border-border rounded-lg p-5 flex flex-col gap-3">
      <div className="flex items-center justify-between">
        <span className="text-xs font-semibold text-muted uppercase tracking-wide">{label}</span>
        <span className="text-muted opacity-60">{icon}</span>
      </div>
      <span
        className="text-[32px] font-bold leading-none"
        style={accent ? { color: accent } : { color: 'var(--text)' }}
      >
        {value ?? '—'}
      </span>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const fresh = _dashCache.data && Date.now() - _dashCache.ts < CACHE_TTL
    ? _dashCache.data : null;

  const [profile, setProfile] = useState(fresh?.profile ?? null);
  const [history, setHistory] = useState<ConversionRecord[]>(fresh?.history ?? []);
  const [progress, setProgress] = useState<UserProgress[]>(fresh?.progress ?? []);
  const [files, setFiles] = useState<CodeFile[]>(fresh?.files ?? []);
  const [modules, setModules] = useState<LearningModule[]>(fresh?.modules ?? []);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!fresh);

  useEffect(() => {
    if (fresh) return;
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

  // Avatar — use uploaded image if available, else initials
  const avatarUrl = profile?.avatar ? profile.avatar : null;

  return (
    <div className="p-5 max-w-5xl">

      {loading && (
        <div className="flex items-center gap-2 text-sm text-muted mb-4">
          <span className="inline-block w-3.5 h-3.5 border-2 border-muted/40 border-t-muted rounded-full animate-spin" />
          Loading dashboard…
        </div>
      )}
      {loadError && (
        <p className="bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm mb-3">{loadError}</p>
      )}

      {/* ── Profile Header ── */}
      <div className="flex items-center gap-4 p-5 bg-surface border border-border rounded-lg mb-6">
        <div className="w-14 h-14 rounded-full bg-accent flex items-center justify-center flex-shrink-0 overflow-hidden">
          {avatarUrl
            ? <img src={avatarUrl} alt="avatar" className="w-full h-full object-cover" />
            : <span className="text-white text-lg font-bold tracking-wide">{initials}</span>
          }
        </div>
        <div className="flex flex-col gap-0.5 flex-1">
          <h2 className="text-base font-semibold m-0">{profile?.username || '—'}</h2>
          {profile?.email && <p className="text-sm text-muted m-0">{profile.email}</p>}
          {memberSince && <p className="text-xs text-muted m-0">Member since {memberSince}</p>}
        </div>
        <button
          className="hidden sm:flex items-center gap-1.5 text-xs text-muted border border-border rounded px-3 py-1.5 bg-transparent hover:bg-border transition-colors"
          onClick={() => navigate('/profile')}
        >
          Edit Profile
        </button>
      </div>

      {/* ── Stat Cards ── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
        <StatCard value={history.length} label="Conversions" icon="⇄" accent="var(--accent)" />
        <StatCard value={completedLessons} label="Lessons Done" icon="✓" accent="#3b82f6" />
        <StatCard value={files.length} label="Files Saved" icon="📁" />
        <StatCard value={`${progressPct}%`} label="Overall Progress" icon="◎" accent="var(--success)" />
      </div>

      {/* ── Bottom Two-Column ── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">

        {/* Recent Conversions */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-4">Recent Conversions</h3>
          {history.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-muted opacity-40">
                <polyline points="16 18 22 12 16 6" /><polyline points="8 6 2 12 8 18" />
              </svg>
              <div>
                <p className="text-sm font-medium text-primary m-0">No conversions yet</p>
                <p className="text-xs text-muted mt-0.5 m-0">Try converting some code to see your history here.</p>
              </div>
              <button
                className="text-xs text-accent border border-accent/40 rounded px-3 py-1.5 bg-accent/5 hover:bg-accent/10 transition-colors"
                onClick={() => navigate('/converter')}
              >
                Open Converter →
              </button>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full border-collapse text-sm">
                <thead>
                  <tr>
                    <th className="text-left pb-2 text-xs text-muted font-semibold uppercase tracking-wide">From</th>
                    <th className="text-left pb-2 text-xs text-muted font-semibold uppercase tracking-wide">To</th>
                    <th className="text-left pb-2 text-xs text-muted font-semibold uppercase tracking-wide">Date</th>
                  </tr>
                </thead>
                <tbody>
                  {history.slice(0, 8).map((h) => (
                    <tr
                      key={h.id}
                      className="cursor-pointer hover:bg-accent/5 transition-colors rounded"
                      onClick={() => navigate('/converter')}
                      title="Open in Converter"
                    >
                      <td className="py-2 pr-3 border-b border-border/50"><LangChip lang={h.source_language} /></td>
                      <td className="py-2 pr-3 border-b border-border/50"><LangChip lang={h.target_language} /></td>
                      <td className="py-2 border-b border-border/50 text-xs text-muted">
                        {new Date(h.timestamp).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Learning Progress */}
        <div className="bg-surface border border-border rounded-lg p-4">
          <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-4">Learning Progress</h3>
          {moduleProgress.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-8 text-center">
              <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-muted opacity-40">
                <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" /><path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
              </svg>
              <div>
                <p className="text-sm font-medium text-primary m-0">No learning activity yet</p>
                <p className="text-xs text-muted mt-0.5 m-0">Start a module to track your progress here.</p>
              </div>
              <button
                className="text-xs text-accent border border-accent/40 rounded px-3 py-1.5 bg-accent/5 hover:bg-accent/10 transition-colors"
                onClick={() => navigate('/learning')}
              >
                Browse Modules →
              </button>
            </div>
          ) : (
            <div className="flex flex-col gap-4">
              {moduleProgress.map(({ title, done, total }) => {
                const pct = total ? Math.round((done / total) * 100) : 0;
                return (
                  <div key={title} className="flex flex-col gap-1.5">
                    <div className="flex justify-between items-center">
                      <span className="text-sm">{title}</span>
                      <span className="text-xs text-muted tabular-nums">{done}/{total}</span>
                    </div>
                    <div className="h-2 bg-border rounded-full overflow-hidden">
                      <div
                        className="h-full bg-accent rounded-full transition-all duration-500"
                        style={{ width: `${pct}%` }}
                      />
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
