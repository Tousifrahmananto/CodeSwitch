import { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { getProfile, getConversionHistory, getProgress, getFiles, getModules } from '../api/client';
import { resolveMediaUrl } from '../api/media';
import { getLanguageMeta } from '../constants/languages';
import type { CodeFile, ConversionRecord, LearningModule, User, UserProgress } from '../types';

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
  const meta = getLanguageMeta(lang);
  return (
    <span
      className="inline-flex items-center gap-1.5 text-xs font-semibold px-2 py-0.5 rounded-full font-mono border"
      style={{
        color: meta.color,
        background: meta.softBg,
        borderColor: `${meta.color}66`,
      }}
    >
      <span className="w-1.5 h-1.5 rounded-full" style={{ background: meta.color }} />
      {meta.label}
    </span>
  );
}

function StatCard({
  value,
  label,
  icon,
  accent,
  helper,
  action,
}: {
  value: string | number;
  label: string;
  icon: string;
  accent?: string;
  helper?: string;
  action?: { label: string; onClick: () => void };
}) {
  return (
    <div className="bg-surface border border-border rounded-xl p-5 min-h-[142px] flex flex-col gap-3 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <span className="text-xs font-semibold text-muted uppercase tracking-wide">{label}</span>
        <span className="text-muted opacity-70">{icon}</span>
      </div>
      <span
        className="text-[34px] font-bold leading-none"
        style={accent ? { color: accent } : { color: 'var(--text)' }}
      >
        {value ?? '-'}
      </span>
      {helper && <p className="text-xs text-muted leading-relaxed m-0">{helper}</p>}
      {action && (
        <button
          className="mt-auto self-start text-xs text-accent border border-accent/40 rounded-full px-3 py-1 bg-accent/5 hover:bg-accent/10 transition-colors"
          onClick={action.onClick}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}

function EmptyState({
  icon,
  title,
  body,
  actionLabel,
  onAction,
}: {
  icon: string;
  title: string;
  body: string;
  actionLabel: string;
  onAction: () => void;
}) {
  return (
    <div className="flex flex-col items-center gap-3 py-9 px-4 text-center">
      <div className="w-12 h-12 rounded-2xl bg-accent/10 border border-accent/20 flex items-center justify-center text-xl">
        {icon}
      </div>
      <div>
        <p className="text-sm font-semibold text-primary m-0">{title}</p>
        <p className="text-xs text-muted mt-1 m-0 max-w-xs leading-relaxed">{body}</p>
      </div>
      <button
        className="text-xs text-accent border border-accent/40 rounded-full px-3 py-1.5 bg-accent/5 hover:bg-accent/10 transition-colors"
        onClick={onAction}
      >
        {actionLabel}
      </button>
    </div>
  );
}

export default function Dashboard() {
  const navigate = useNavigate();
  const fresh = _dashCache.data && Date.now() - _dashCache.ts < CACHE_TTL
    ? _dashCache.data : null;

  const [profile, setProfile] = useState<User | null>(fresh?.profile ?? null);
  const [history, setHistory] = useState<ConversionRecord[]>(fresh?.history ?? []);
  const [progress, setProgress] = useState<UserProgress[]>(fresh?.progress ?? []);
  const [files, setFiles] = useState<CodeFile[]>(fresh?.files ?? []);
  const [modules, setModules] = useState<LearningModule[]>(fresh?.modules ?? []);
  const [loadError, setLoadError] = useState<string | null>(null);
  const [loading, setLoading] = useState(!fresh);
  const [avatarFailed, setAvatarFailed] = useState(false);

  useEffect(() => {
    if (fresh) {
      getProfile().then(profileRes => {
        setProfile(profileRes.data);
        setAvatarFailed(false);
        if (_dashCache.data) _dashCache.data.profile = profileRes.data;
      }).catch(() => {});
      return;
    }
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

  const moduleProgress = useMemo(() => modules
    .map(m => ({
      id: m.id,
      title: m.title,
      done: progress.filter(p => p.module_title === m.title && p.completed).length,
      total: m.lesson_count || 0,
    }))
    .filter(m => m.done > 0)
    .sort((a, b) => (b.done / Math.max(b.total, 1)) - (a.done / Math.max(a.total, 1))), [modules, progress]);

  const activeModule = moduleProgress.find(m => m.total === 0 || m.done < m.total)
    ?? modules.find(m => !moduleProgress.some(p => p.id === m.id));

  const recentLanguages = useMemo(() => {
    const seen = new Set<string>();
    history.forEach(h => {
      if (h.source_language) seen.add(h.source_language);
      if (h.target_language) seen.add(h.target_language);
    });
    return Array.from(seen).slice(0, 6);
  }, [history]);

  const initials = profile?.username ? profile.username.slice(0, 2).toUpperCase() : '..';
  const firstName = profile?.first_name?.trim();
  const greetingName = firstName || profile?.username || 'there';
  const memberSince = profile?.date_joined
    ? new Date(profile.date_joined).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
    : '';
  const avatarUrl = resolveMediaUrl(profile?.avatar);

  const activityLevel = history.length >= 25 || completedLessons >= 20
    ? 'Power Learner'
    : history.length >= 8 || completedLessons >= 5
      ? 'Builder'
      : 'Getting Started';

  useEffect(() => {
    setAvatarFailed(false);
  }, [avatarUrl]);

  return (
    <div className="w-full max-w-[1500px] mx-auto p-5 xl:p-6">
      {loading && (
        <div className="flex items-center gap-2 text-sm text-muted mb-4">
          <span className="inline-block w-3.5 h-3.5 border-2 border-muted/40 border-t-muted rounded-full animate-spin" />
          Loading dashboard...
        </div>
      )}
      {loadError && (
        <p className="bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm mb-4">{loadError}</p>
      )}

      <div className="flex flex-col lg:flex-row lg:items-end justify-between gap-4 mb-5">
        <div>
          <p className="text-xs text-muted uppercase tracking-[0.22em] font-semibold m-0">Dashboard</p>
          <h2 className="text-3xl md:text-4xl font-bold tracking-tight mt-2 mb-2">
            Welcome back, {greetingName}
          </h2>
          <p className="text-sm text-muted m-0 max-w-2xl">
            Keep converting, saving, and learning from one workspace.
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          <button
            className="bg-accent hover:bg-accent-h text-white rounded-lg px-4 py-2 text-sm font-semibold border-none transition-colors"
            onClick={() => navigate('/converter')}
          >
            + New Conversion
          </button>
          <button
            className="bg-transparent border border-border text-primary hover:bg-border rounded-lg px-4 py-2 text-sm font-medium transition-colors"
            onClick={() => navigate('/learning')}
          >
            Continue Learning
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.35fr)_minmax(320px,0.65fr)] gap-5 mb-5">
        <div className="flex items-center gap-4 p-5 bg-surface border border-border rounded-xl min-h-[132px]">
          <div className="w-16 h-16 rounded-full bg-accent flex items-center justify-center flex-shrink-0 overflow-hidden ring-4 ring-accent/10">
            {avatarUrl && !avatarFailed
              ? <img
                  src={avatarUrl}
                  alt={profile?.username ? `${profile.username}'s profile` : 'Profile'}
                  className="w-full h-full object-cover"
                  onError={() => setAvatarFailed(true)}
                />
              : <span className="text-white text-lg font-bold tracking-wide">{initials}</span>
            }
          </div>
          <div className="flex flex-col gap-1 flex-1 min-w-0">
            <div className="flex flex-wrap items-center gap-2">
              <h3 className="text-lg font-bold m-0 truncate">{profile?.username || '-'}</h3>
              <span className="text-[11px] font-semibold rounded-full border border-success/30 bg-success/10 text-success px-2 py-0.5">
                {activityLevel}
              </span>
            </div>
            {profile?.email && <p className="text-sm text-muted m-0 truncate">{profile.email}</p>}
            {memberSince && <p className="text-xs text-muted m-0">Member since {memberSince}</p>}
            <div className="flex flex-wrap gap-2 mt-2">
              {recentLanguages.length > 0
                ? recentLanguages.map(lang => <LangChip key={lang} lang={lang} />)
                : <span className="text-xs text-muted">Convert code to start building your language mix.</span>
              }
            </div>
          </div>
          <button
            className="hidden sm:flex items-center gap-1.5 text-xs text-muted border border-border rounded-lg px-3 py-1.5 bg-transparent hover:bg-border hover:text-primary transition-colors"
            onClick={() => navigate('/profile')}
          >
            Edit Profile
          </button>
        </div>

        <div className="bg-surface border border-border rounded-xl p-5 flex flex-col justify-between gap-4">
          <div>
            <p className="text-xs font-semibold text-muted uppercase tracking-wide m-0">Recommended Next</p>
            <h3 className="text-lg font-bold mt-2 mb-1">{activeModule?.title || 'Start your first module'}</h3>
            <p className="text-xs text-muted leading-relaxed m-0">
              {activeModule && 'done' in activeModule
                ? `${activeModule.done}/${activeModule.total} lessons complete. Pick up where you left off.`
                : 'Choose a learning module and your progress will show up here.'}
            </p>
          </div>
          <button
            className="self-start text-xs text-accent border border-accent/40 rounded-full px-3 py-1.5 bg-accent/5 hover:bg-accent/10 transition-colors"
            onClick={() => navigate('/learning')}
          >
            Open Learning →
          </button>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-4 mb-5">
        <StatCard
          value={history.length}
          label="Conversions"
          icon="⇄"
          accent="var(--accent)"
          helper={history.length ? 'Your recent translation activity.' : 'No conversions yet. Start with a quick translation.'}
          action={!history.length ? { label: 'Convert code', onClick: () => navigate('/converter') } : undefined}
        />
        <StatCard
          value={completedLessons}
          label="Lessons Done"
          icon="✓"
          accent="#5ba8f5"
          helper={completedLessons ? `${Math.max(totalLessons - completedLessons, 0)} lessons left across your modules.` : 'Start a lesson to turn this into progress.'}
          action={!completedLessons ? { label: 'Browse modules', onClick: () => navigate('/learning') } : undefined}
        />
        <StatCard
          value={files.length}
          label="Files Saved"
          icon="▣"
          helper={files.length ? 'Saved snippets ready to reopen.' : 'No files yet - save one from the Converter.'}
          action={!files.length ? { label: 'Create file', onClick: () => navigate('/files') } : undefined}
        />
        <StatCard
          value={`${progressPct}%`}
          label="Overall Progress"
          icon="◎"
          accent="var(--success)"
          helper={activeModule && 'done' in activeModule
            ? `${activeModule.title} - ${activeModule.done}/${activeModule.total} lessons.`
            : totalLessons ? `${completedLessons}/${totalLessons} lessons complete.` : 'Progress appears after your first lesson.'}
        />
      </div>

      <div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1.2fr)_minmax(320px,0.8fr)] gap-5 items-start">
        <div className="bg-surface border border-border rounded-xl p-4">
          <div className="flex items-center justify-between gap-3 mb-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted m-0">Recent Conversions</h3>
            {history.length > 0 && (
              <button
                className="text-xs text-muted hover:text-primary bg-transparent border-none"
                onClick={() => navigate('/converter')}
              >
                Open Converter →
              </button>
            )}
          </div>
          {history.length === 0 ? (
            <EmptyState
              icon="<>"
              title="No conversions yet"
              body="Try converting a small snippet and your history will become a useful launchpad."
              actionLabel="Open Converter →"
              onAction={() => navigate('/converter')}
            />
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
                  {history.slice(0, 10).map((h) => (
                    <tr
                      key={h.id}
                      className="cursor-pointer hover:bg-accent/5 transition-colors rounded"
                      onClick={() => navigate('/converter')}
                      title="Open in Converter"
                    >
                      <td className="py-2.5 pr-3 border-b border-border/50"><LangChip lang={h.source_language} /></td>
                      <td className="py-2.5 pr-3 border-b border-border/50"><LangChip lang={h.target_language} /></td>
                      <td className="py-2.5 border-b border-border/50 text-xs text-muted whitespace-nowrap">
                        {new Date(h.timestamp).toLocaleDateString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        <div className="grid grid-cols-1 gap-5">
          <div className="bg-surface border border-border rounded-xl p-4">
            <div className="flex items-center justify-between gap-3 mb-4">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-muted m-0">Learning Progress</h3>
              <button
                className="text-xs text-muted hover:text-primary bg-transparent border-none"
                onClick={() => navigate('/learning')}
              >
                Browse →
              </button>
            </div>
            {moduleProgress.length === 0 ? (
              <EmptyState
                icon="📖"
                title="No learning activity yet"
                body="Start a module and this card will track the exact lessons you finish."
                actionLabel="Browse Modules →"
                onAction={() => navigate('/learning')}
              />
            ) : (
              <div className="flex flex-col gap-4">
                {moduleProgress.slice(0, 4).map(({ title, done, total }) => {
                  const pct = total ? Math.round((done / total) * 100) : 0;
                  return (
                    <div key={title} className="flex flex-col gap-1.5">
                      <div className="flex justify-between items-center gap-3">
                        <span className="text-sm truncate">{title}</span>
                        <span className="text-xs text-muted tabular-nums flex-shrink-0">{done}/{total}</span>
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

          <div className="bg-surface border border-border rounded-xl p-4">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-muted mb-3">Quick Actions</h3>
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-1 gap-2">
              <button className="text-left bg-bg border border-border rounded-lg p-3 hover:border-accent/60 transition-colors" onClick={() => navigate('/converter')}>
                <span className="block text-sm font-semibold text-primary">Convert a snippet</span>
                <span className="block text-xs text-muted mt-1">Translate and compare output.</span>
              </button>
              <button className="text-left bg-bg border border-border rounded-lg p-3 hover:border-accent/60 transition-colors" onClick={() => navigate('/files')}>
                <span className="block text-sm font-semibold text-primary">Save a file</span>
                <span className="block text-xs text-muted mt-1">Keep reusable examples handy.</span>
              </button>
              <button className="text-left bg-bg border border-border rounded-lg p-3 hover:border-accent/60 transition-colors" onClick={() => navigate('/reference')}>
                <span className="block text-sm font-semibold text-primary">Open reference</span>
                <span className="block text-xs text-muted mt-1">Check syntax across languages.</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
