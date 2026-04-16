// src/pages/AdminPanel.jsx
// Staff-only admin dashboard: stats, user management, conversion log, modules CRUD.

import { useState, useEffect, useCallback } from 'react';
import type { CSSProperties, ReactNode } from 'react';
import {
  adminGetStats, adminGetUsers, adminUpdateUser, adminDeleteUser,
  adminGetConversions, adminGetModules, adminCreateModule,
  adminUpdateModule, adminDeleteModule,
  adminGetModuleLessons, adminGetLesson, adminCreateLesson,
  adminUpdateLesson, adminDeleteLesson,
} from '../api/client';
import type { AdminConversion, AdminLesson, AdminStats, AdminUser, LearningModule, Lesson, TabName } from '../types';

const TABS: readonly TabName[] = ['Overview', 'Users', 'Conversions', 'Modules'];

const LANGUAGES = ['python', 'c', 'java', 'general'] as const;
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced'] as const;

type ModuleForm = Pick<LearningModule, 'title' | 'description' | 'language' | 'difficulty'>;
type LessonForm = Pick<Lesson, 'title' | 'content' | 'example_code' | 'order'>;

function getErrorMessage(error: unknown, fallback: string): string {
  const maybe = error as { response?: { data?: { error?: string } }; message?: string };
  return maybe.response?.data?.error || maybe.message || fallback;
}

// ── small helpers ─────────────────────────────────────────────────────────────

function StatCard({ label, value, sub }: { label: string; value: string | number | null | undefined; sub?: string }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardValue}>{value ?? '—'}</div>
      <div style={styles.cardLabel}>{label}</div>
      {sub && <div style={styles.cardSub}>{sub}</div>}
    </div>
  );
}

function Badge({ children, color = '#555' }: { children: ReactNode; color?: string }) {
  return (
    <span style={{ ...styles.badge, background: color }}>{children}</span>
  );
}

function ActionBtn({ children, onClick, danger = false, small = false }: { children: ReactNode; onClick: () => void; danger?: boolean; small?: boolean }) {
  return (
    <button
      onClick={onClick}
      style={{
        ...styles.btn,
        ...(danger ? styles.btnDanger : styles.btnSecondary),
        ...(small ? styles.btnSmall : {}),
      }}
    >
      {children}
    </button>
  );
}

// ── tabs ──────────────────────────────────────────────────────────────────────

function OverviewTab({ stats }: { stats: AdminStats | null }) {
  if (!stats) return <p style={styles.muted}>Loading stats…</p>;
  return (
    <div>
      <h2 style={styles.sectionTitle}>Platform Overview</h2>
      <div style={styles.statsGrid}>
        <StatCard label="Total Users" value={stats.total_users} sub={`+${stats.new_users_this_week} this week`} />
        <StatCard label="Total Conversions" value={stats.total_conversions} sub={`+${stats.conversions_this_week} this week`} />
        <StatCard label="Saved Files" value={stats.total_files} />
        <StatCard label="Learning Modules" value={stats.total_modules} />
      </div>
    </div>
  );
}

function UsersTab({ users, onUpdate, onDelete }: {
  users: AdminUser[] | null;
  onUpdate: (id: number, patch: Partial<AdminUser>) => void;
  onDelete: (id: number, username: string) => void;
}) {
  if (!users) return <p style={styles.muted}>Loading users…</p>;

  return (
    <div>
      <h2 style={styles.sectionTitle}>User Management ({users.length})</h2>
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              {['ID', 'Username', 'Email', 'Conversions', 'Joined', 'Staff', 'Active', 'Actions'].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {users.map(u => (
              <tr key={u.id} style={styles.tr}>
                <td style={styles.td}>{u.id}</td>
                <td style={styles.td}><strong>{u.username}</strong></td>
                <td style={styles.td}>{u.email || '—'}</td>
                <td style={styles.td}>{u.conversion_count}</td>
                <td style={styles.td}>{new Date(u.date_joined).toLocaleDateString()}</td>
                <td style={styles.td}>
                  <Badge color={u.is_staff ? '#7c3aed' : '#374151'}>{u.is_staff ? 'Yes' : 'No'}</Badge>
                </td>
                <td style={styles.td}>
                  <Badge color={u.is_active ? '#065f46' : '#7f1d1d'}>{u.is_active ? 'Yes' : 'No'}</Badge>
                </td>
                <td style={{ ...styles.td, display: 'flex', gap: 6 }}>
                  <ActionBtn small onClick={() => onUpdate(u.id, { is_staff: !u.is_staff })}>
                    {u.is_staff ? 'Revoke Staff' : 'Make Staff'}
                  </ActionBtn>
                  <ActionBtn small onClick={() => onUpdate(u.id, { is_active: !u.is_active })}>
                    {u.is_active ? 'Disable' : 'Enable'}
                  </ActionBtn>
                  <ActionBtn small danger onClick={() => onDelete(u.id, u.username)}>Delete</ActionBtn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ConversionsTab({ conversions }: { conversions: AdminConversion[] | null }) {
  if (!conversions) return <p style={styles.muted}>Loading conversions…</p>;

  const langColor: Record<string, string> = { python: '#3b7bbf', c: '#b45309', java: '#1d6b3a' };

  return (
    <div>
      <h2 style={styles.sectionTitle}>Recent Conversions (last 100)</h2>
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              {['ID', 'User', 'From', 'To', 'When'].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {conversions.map(c => (
              <tr key={c.id} style={styles.tr}>
                <td style={styles.td}>{c.id}</td>
                <td style={styles.td}>{c.user}</td>
                <td style={styles.td}><Badge color={langColor[c.source_language] || '#555'}>{c.source_language}</Badge></td>
                <td style={styles.td}><Badge color={langColor[c.target_language] || '#555'}>{c.target_language}</Badge></td>
                <td style={styles.td}>{new Date(c.timestamp).toLocaleString()}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function LessonsPanel({ moduleId, onDone }: { moduleId: number; onDone: () => void }) {
  const emptyLesson: LessonForm = { title: '', content: '', example_code: '{}', order: 1 };
  const [lessons, setLessons] = useState<AdminLesson[] | null>(null);
  const [editingId, setEditingId] = useState<number | null>(null); // null = new, number = existing
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState<LessonForm>(emptyLesson);
  const [formErr, setFormErr] = useState('');
  const [saving, setSaving] = useState(false);

  const loadLessons = useCallback(async () => {
    try {
      const { data } = await adminGetModuleLessons(moduleId);
      setLessons(data);
    } catch {
      setLessons([]);
    }
  }, [moduleId]);

  useEffect(() => { loadLessons(); }, [loadLessons]);

  const startNew = () => {
    setEditingId(null);
    setForm({ ...emptyLesson, order: (lessons?.length ?? 0) + 1 });
    setFormErr('');
    setShowForm(true);
  };

  const startEdit = async (lessonId: number) => {
    try {
      const { data } = await adminGetLesson(lessonId);
      setEditingId(lessonId);
      setForm({ title: data.title, content: data.content, example_code: data.example_code, order: data.order });
      setFormErr('');
      setShowForm(true);
    } catch {
      alert('Could not load lesson.');
    }
  };

  const cancelForm = () => { setShowForm(false); setEditingId(null); setForm(emptyLesson); setFormErr(''); };

  const handleSave = async () => {
    if (!form.title.trim()) { setFormErr('Title is required.'); return; }
    setSaving(true); setFormErr('');
    try {
      if (editingId) {
        await adminUpdateLesson(editingId, form);
      } else {
        await adminCreateLesson(moduleId, form);
      }
      cancelForm();
      loadLessons();
      onDone();
    } catch (e: unknown) {
      setFormErr(getErrorMessage(e, 'Save failed.'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!window.confirm(`Delete lesson "${title}"?`)) return;
    try {
      await adminDeleteLesson(id);
      loadLessons();
      onDone();
    } catch {
      alert('Delete failed.');
    }
  };

  return (
    <div style={styles.lessonsPanel}>
      <div style={styles.lessonsPanelHeader}>
        <span style={{ fontWeight: 600, fontSize: 13 }}>Lessons ({lessons?.length ?? '…'})</span>
        <button style={{ ...styles.btn, ...styles.btnSmall }} onClick={startNew}>+ Add Lesson</button>
      </div>

      {/* Lesson form */}
      {showForm && (
        <div style={styles.lessonForm}>
          <p style={{ margin: '0 0 10px', fontSize: 13, fontWeight: 600 }}>
            {editingId ? 'Edit Lesson' : 'New Lesson'}
          </p>
          {formErr && <p style={styles.errorText}>{formErr}</p>}
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            <input
              style={styles.input}
              placeholder="Title *"
              value={form.title}
              onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
            />
            <input
              style={styles.input}
              placeholder="Order (number)"
              type="number"
              value={form.order}
              onChange={e => setForm(f => ({ ...f, order: Number(e.target.value) || 0 }))}
            />
            <textarea
              style={{ ...styles.input, height: 120, resize: 'vertical', lineHeight: 1.5 }}
              placeholder="Content (lesson explanation text)"
              value={form.content}
              onChange={e => setForm(f => ({ ...f, content: e.target.value }))}
            />
            <textarea
              style={{ ...styles.input, height: 80, resize: 'vertical', fontFamily: 'monospace', fontSize: 12 }}
              placeholder='Example code JSON: {"c": "...", "python": "...", "java": "..."}'
              value={form.example_code}
              onChange={e => setForm(f => ({ ...f, example_code: e.target.value }))}
            />
          </div>
          <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
            <button style={styles.btn} onClick={handleSave} disabled={saving}>
              {saving ? 'Saving…' : 'Save'}
            </button>
            <ActionBtn onClick={cancelForm}>Cancel</ActionBtn>
          </div>
        </div>
      )}

      {/* Lessons list */}
      {lessons === null && <p style={styles.muted}>Loading…</p>}
      {lessons?.length === 0 && !showForm && (
        <p style={styles.muted}>No lessons yet. Click "+ Add Lesson" to create one.</p>
      )}
      {lessons?.map(l => (
        <div key={l.id} style={styles.lessonRow}>
          <span style={{ color: '#6b7280', fontSize: 12, minWidth: 24 }}>{l.order}.</span>
          <span style={{ flex: 1, fontSize: 13 }}>{l.title}</span>
          {l.has_quiz && <span style={{ ...styles.badge, background: '#065f46', fontSize: 11, marginRight: 6 }}>Quiz</span>}
          <ActionBtn small onClick={() => startEdit(l.id)}>Edit</ActionBtn>
          <ActionBtn small danger onClick={() => handleDelete(l.id, l.title)}>Delete</ActionBtn>
        </div>
      ))}
    </div>
  );
}

function ModulesTab({ modules, onRefresh }: { modules: LearningModule[] | null; onRefresh: () => void }) {
  const emptyForm: ModuleForm = { title: '', description: '', language: 'general', difficulty: 'beginner' };
  const [form, setForm] = useState<ModuleForm>(emptyForm);
  const [editing, setEditing] = useState<number | null>(null); // module id being edited
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const [expandedModuleId, setExpandedModuleId] = useState<number | null>(null);

  const toggleLessons = (id: number) => setExpandedModuleId(prev => prev === id ? null : id);

  const startEdit = (mod: LearningModule) => {
    setEditing(mod.id);
    setForm({ title: mod.title, description: mod.description, language: mod.language, difficulty: mod.difficulty });
    setError('');
  };

  const cancelEdit = () => { setEditing(null); setForm(emptyForm); setError(''); };

  const handleSave = async () => {
    if (!form.title.trim()) { setError('Title is required.'); return; }
    setSaving(true);
    setError('');
    try {
      if (editing) {
        await adminUpdateModule(editing, form);
      } else {
        await adminCreateModule(form);
      }
      cancelEdit();
      onRefresh();
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Save failed.'));
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number, title: string) => {
    if (!window.confirm(`Delete module "${title}"? This will also remove all its lessons.`)) return;
    try {
      await adminDeleteModule(id);
      onRefresh();
    } catch {
      alert('Delete failed.');
    }
  };

  if (!modules) return <p style={styles.muted}>Loading modules…</p>;

  return (
    <div>
      <h2 style={styles.sectionTitle}>Learning Modules ({modules.length})</h2>

      {/* Add / Edit form */}
      <div style={styles.formBox}>
        <h3 style={{ margin: '0 0 12px', fontSize: 15 }}>{editing ? 'Edit Module' : 'Add Module'}</h3>
        {error && <p style={styles.errorText}>{error}</p>}
        <div style={styles.formGrid}>
          <input
            style={styles.input}
            placeholder="Title *"
            value={form.title}
            onChange={e => setForm(f => ({ ...f, title: e.target.value }))}
          />
          <input
            style={styles.input}
            placeholder="Description"
            value={form.description}
            onChange={e => setForm(f => ({ ...f, description: e.target.value }))}
          />
          <select style={styles.input} value={form.language} onChange={e => setForm(f => ({ ...f, language: e.target.value }))}>
            {LANGUAGES.map(l => <option key={l} value={l}>{l}</option>)}
          </select>
          <select style={styles.input} value={form.difficulty} onChange={e => setForm(f => ({ ...f, difficulty: e.target.value as ModuleForm['difficulty'] }))}>
            {DIFFICULTIES.map(d => <option key={d} value={d}>{d}</option>)}
          </select>
        </div>
        <div style={{ marginTop: 10, display: 'flex', gap: 8 }}>
          <button style={styles.btn} onClick={handleSave} disabled={saving}>
            {saving ? 'Saving…' : editing ? 'Update' : 'Create'}
          </button>
          {editing && <ActionBtn onClick={cancelEdit}>Cancel</ActionBtn>}
        </div>
      </div>

      {/* Modules list */}
      <div style={styles.tableWrap}>
        <table style={styles.table}>
          <thead>
            <tr>
              {['ID', 'Title', 'Language', 'Difficulty', 'Lessons', 'Actions'].map(h => (
                <th key={h} style={styles.th}>{h}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {modules.map(mod => (
              <>
                <tr key={mod.id} style={styles.tr}>
                  <td style={styles.td}>{mod.id}</td>
                  <td style={styles.td}><strong>{mod.title}</strong><br /><span style={styles.muted}>{mod.description}</span></td>
                  <td style={styles.td}><Badge>{mod.language}</Badge></td>
                  <td style={styles.td}><Badge color={mod.difficulty === 'beginner' ? '#065f46' : mod.difficulty === 'intermediate' ? '#92400e' : '#7f1d1d'}>{mod.difficulty}</Badge></td>
                  <td style={styles.td}>{mod.lesson_count}</td>
                  <td style={{ ...styles.td, display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                    <ActionBtn small onClick={() => toggleLessons(mod.id)}>
                      {expandedModuleId === mod.id ? '▲ Lessons' : '▼ Lessons'}
                    </ActionBtn>
                    <ActionBtn small onClick={() => startEdit(mod)}>Edit</ActionBtn>
                    <ActionBtn small danger onClick={() => handleDelete(mod.id, mod.title)}>Delete</ActionBtn>
                  </td>
                </tr>
                {expandedModuleId === mod.id && (
                  <tr key={`lessons-${mod.id}`} style={{ background: '#0d1117' }}>
                    <td colSpan={6} style={{ padding: 0 }}>
                      <LessonsPanel moduleId={mod.id} onDone={() => onRefresh()} />
                    </td>
                  </tr>
                )}
              </>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export default function AdminPanel() {
  const [tab, setTab] = useState<TabName>('Overview');
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [users, setUsers] = useState<AdminUser[] | null>(null);
  const [conversions, setConversions] = useState<AdminConversion[] | null>(null);
  const [modules, setModules] = useState<LearningModule[] | null>(null);
  const [error, setError] = useState('');

  const load = useCallback(async (which: TabName | 'all') => {
    setError('');
    try {
      if (which === 'Overview' || which === 'all') {
        const { data } = await adminGetStats();
        setStats(data);
      }
      if (which === 'Users' || which === 'all') {
        const { data } = await adminGetUsers();
        setUsers(data);
      }
      if (which === 'Conversions' || which === 'all') {
        const { data } = await adminGetConversions();
        setConversions(data);
      }
      if (which === 'Modules' || which === 'all') {
        const { data } = await adminGetModules();
        setModules(data);
      }
    } catch (e: unknown) {
      setError(getErrorMessage(e, 'Failed to load data.'));
    }
  }, []);

  // Load overview on mount, lazy-load tabs on first visit
  useEffect(() => { load('Overview'); }, [load]);

  const handleTabChange = (t: TabName) => {
    setTab(t);
    const needsLoad =
      (t === 'Users' && !users) ||
      (t === 'Conversions' && !conversions) ||
      (t === 'Modules' && !modules);
    if (needsLoad) load(t);
  };

  const handleUserUpdate = async (id: number, patch: Partial<AdminUser>) => {
    try {
      const { data } = await adminUpdateUser(id, patch);
      setUsers(prev => (prev ? prev.map(u => (u.id === id ? { ...u, ...data } : u)) : prev));
    } catch (e: unknown) {
      alert(getErrorMessage(e, 'Update failed.'));
    }
  };

  const handleUserDelete = async (id: number, username: string) => {
    if (!window.confirm(`Permanently delete user "${username}"?`)) return;
    try {
      await adminDeleteUser(id);
      setUsers(prev => (prev ? prev.filter(u => u.id !== id) : prev));
    } catch (e: unknown) {
      alert(getErrorMessage(e, 'Delete failed.'));
    }
  };

  return (
    <div style={styles.root}>
      <div style={styles.header}>
        <h1 style={styles.title}>Admin Panel</h1>
        <button style={{ ...styles.btn, ...styles.btnSmall }} onClick={() => load(tab)}>Refresh</button>
      </div>

      {error && <div style={styles.errorBanner}>{error}</div>}

      {/* Tab bar */}
      <div style={styles.tabBar}>
        {TABS.map(t => (
          <button
            key={t}
            style={{ ...styles.tabBtn, ...(tab === t ? styles.tabBtnActive : {}) }}
            onClick={() => handleTabChange(t)}
          >
            {t}
          </button>
        ))}
      </div>

      {/* Tab content */}
      <div style={styles.tabContent}>
        {tab === 'Overview' && <OverviewTab stats={stats} />}
        {tab === 'Users' && <UsersTab users={users} onUpdate={handleUserUpdate} onDelete={handleUserDelete} />}
        {tab === 'Conversions' && <ConversionsTab conversions={conversions} />}
        {tab === 'Modules' && <ModulesTab modules={modules} onRefresh={() => load('Modules')} />}
      </div>
    </div>
  );
}

// ── styles ────────────────────────────────────────────────────────────────────

const styles: Record<string, CSSProperties> = {
  root: { padding: '24px', color: 'var(--text)', maxWidth: 1100 },
  header: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  title: { margin: 0, fontSize: 22, fontWeight: 700 },
  sectionTitle: { fontSize: 16, fontWeight: 600, margin: '0 0 16px' },

  statsGrid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16, marginBottom: 24 },
  card: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: '20px 16px', textAlign: 'center' },
  cardValue: { fontSize: 32, fontWeight: 700, color: 'var(--accent)' },
  cardLabel: { fontSize: 13, color: 'var(--text-muted)', marginTop: 4 },
  cardSub: { fontSize: 11, color: 'var(--text-muted)', marginTop: 6 },

  tabBar: { display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid var(--border)', paddingBottom: 0 },
  tabBtn: { background: 'none', border: 'none', color: 'var(--text-muted)', padding: '10px 18px', cursor: 'pointer', fontSize: 14, borderBottom: '2px solid transparent', borderRadius: '4px 4px 0 0' },
  tabBtnActive: { color: 'var(--accent)', borderBottom: '2px solid var(--accent)', fontWeight: 600 },
  tabContent: { minHeight: 300 },

  tableWrap: { overflowX: 'auto' },
  table: { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th: { textAlign: 'left', padding: '10px 12px', background: 'var(--surface)', color: 'var(--text-muted)', fontWeight: 600, whiteSpace: 'nowrap' },
  tr: { borderBottom: '1px solid var(--border)' },
  td: { padding: '10px 12px', verticalAlign: 'middle' },

  badge: { display: 'inline-block', padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600, color: '#fff' },

  btn: { background: 'var(--accent)', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  btnSecondary: { background: 'var(--border)' },
  btnDanger: { background: 'var(--danger)' },
  btnSmall: { padding: '4px 10px', fontSize: 12 },

  formBox: { background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 10, padding: 20, marginBottom: 24 },
  formGrid: { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  input: { background: 'var(--bg)', border: '1px solid var(--border)', color: 'var(--text)', borderRadius: 6, padding: '8px 12px', fontSize: 13, width: '100%', boxSizing: 'border-box' },

  errorBanner: { background: 'rgba(243,56,56,0.12)', color: 'var(--danger)', padding: '10px 16px', borderRadius: 8, marginBottom: 16, fontSize: 13, border: '1px solid var(--danger)' },
  errorText: { color: 'var(--danger)', fontSize: 13, margin: '0 0 8px' },
  muted: { color: 'var(--text-muted)', fontSize: 13 },

  lessonsPanel: { padding: '16px 20px', borderTop: '1px solid var(--border)' },
  lessonsPanelHeader: { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 12 },
  lessonForm: { background: 'var(--bg)', border: '1px solid var(--border)', borderRadius: 8, padding: 16, marginBottom: 12 },
  lessonRow: { display: 'flex', alignItems: 'center', gap: 8, padding: '7px 0', borderBottom: '1px solid var(--border)' },
};
