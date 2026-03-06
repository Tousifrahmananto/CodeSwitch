// src/pages/AdminPanel.jsx
// Staff-only admin dashboard: stats, user management, conversion log, modules CRUD.

import { useState, useEffect, useCallback } from 'react';
import {
  adminGetStats, adminGetUsers, adminUpdateUser, adminDeleteUser,
  adminGetConversions, adminGetModules, adminCreateModule,
  adminUpdateModule, adminDeleteModule,
} from '../api/client';

const TABS = ['Overview', 'Users', 'Conversions', 'Modules'];

const LANGUAGES = ['python', 'c', 'java', 'general'];
const DIFFICULTIES = ['beginner', 'intermediate', 'advanced'];

// ── small helpers ─────────────────────────────────────────────────────────────

function StatCard({ label, value, sub }) {
  return (
    <div style={styles.card}>
      <div style={styles.cardValue}>{value ?? '—'}</div>
      <div style={styles.cardLabel}>{label}</div>
      {sub && <div style={styles.cardSub}>{sub}</div>}
    </div>
  );
}

function Badge({ children, color = '#555' }) {
  return (
    <span style={{ ...styles.badge, background: color }}>{children}</span>
  );
}

function ActionBtn({ children, onClick, danger, small }) {
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

function OverviewTab({ stats }) {
  if (!stats) return <p style={styles.muted}>Loading stats…</p>;
  return (
    <div>
      <h2 style={styles.sectionTitle}>Platform Overview</h2>
      <div style={styles.statsGrid}>
        <StatCard label="Total Users"       value={stats.total_users}           sub={`+${stats.new_users_this_week} this week`} />
        <StatCard label="Total Conversions" value={stats.total_conversions}     sub={`+${stats.conversions_this_week} this week`} />
        <StatCard label="Saved Files"       value={stats.total_files} />
        <StatCard label="Learning Modules"  value={stats.total_modules} />
      </div>
    </div>
  );
}

function UsersTab({ users, onUpdate, onDelete }) {
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

function ConversionsTab({ conversions }) {
  if (!conversions) return <p style={styles.muted}>Loading conversions…</p>;

  const langColor = { python: '#3b7bbf', c: '#b45309', java: '#1d6b3a' };

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

function ModulesTab({ modules, onRefresh }) {
  const emptyForm = { title: '', description: '', language: 'general', difficulty: 'beginner' };
  const [form, setForm] = useState(emptyForm);
  const [editing, setEditing] = useState(null); // module id being edited
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  const startEdit = (mod) => {
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
    } catch (e) {
      setError(e.response?.data?.error || 'Save failed.');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id, title) => {
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
          <select style={styles.input} value={form.difficulty} onChange={e => setForm(f => ({ ...f, difficulty: e.target.value }))}>
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
              <tr key={mod.id} style={styles.tr}>
                <td style={styles.td}>{mod.id}</td>
                <td style={styles.td}><strong>{mod.title}</strong><br /><span style={styles.muted}>{mod.description}</span></td>
                <td style={styles.td}><Badge>{mod.language}</Badge></td>
                <td style={styles.td}><Badge color={mod.difficulty === 'beginner' ? '#065f46' : mod.difficulty === 'intermediate' ? '#92400e' : '#7f1d1d'}>{mod.difficulty}</Badge></td>
                <td style={styles.td}>{mod.lesson_count}</td>
                <td style={{ ...styles.td, display: 'flex', gap: 6 }}>
                  <ActionBtn small onClick={() => startEdit(mod)}>Edit</ActionBtn>
                  <ActionBtn small danger onClick={() => handleDelete(mod.id, mod.title)}>Delete</ActionBtn>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── main component ────────────────────────────────────────────────────────────

export default function AdminPanel() {
  const [tab, setTab] = useState('Overview');
  const [stats, setStats] = useState(null);
  const [users, setUsers] = useState(null);
  const [conversions, setConversions] = useState(null);
  const [modules, setModules] = useState(null);
  const [error, setError] = useState('');

  const load = useCallback(async (which) => {
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
    } catch (e) {
      setError(e.response?.data?.error || 'Failed to load data.');
    }
  }, []);

  // Load overview on mount, lazy-load tabs on first visit
  useEffect(() => { load('Overview'); }, [load]);

  const handleTabChange = (t) => {
    setTab(t);
    const needsLoad =
      (t === 'Users'       && !users)       ||
      (t === 'Conversions' && !conversions)  ||
      (t === 'Modules'     && !modules);
    if (needsLoad) load(t);
  };

  const handleUserUpdate = async (id, patch) => {
    try {
      const { data } = await adminUpdateUser(id, patch);
      setUsers(prev => prev.map(u => u.id === id ? { ...u, ...data } : u));
    } catch (e) {
      alert(e.response?.data?.error || 'Update failed.');
    }
  };

  const handleUserDelete = async (id, username) => {
    if (!window.confirm(`Permanently delete user "${username}"?`)) return;
    try {
      await adminDeleteUser(id);
      setUsers(prev => prev.filter(u => u.id !== id));
    } catch (e) {
      alert(e.response?.data?.error || 'Delete failed.');
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
        {tab === 'Overview'     && <OverviewTab   stats={stats} />}
        {tab === 'Users'        && <UsersTab       users={users}       onUpdate={handleUserUpdate} onDelete={handleUserDelete} />}
        {tab === 'Conversions'  && <ConversionsTab conversions={conversions} />}
        {tab === 'Modules'      && <ModulesTab     modules={modules}   onRefresh={() => load('Modules')} />}
      </div>
    </div>
  );
}

// ── styles ────────────────────────────────────────────────────────────────────

const styles = {
  root:         { padding: '24px', color: '#e5e7eb', maxWidth: 1100 },
  header:       { display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 },
  title:        { margin: 0, fontSize: 22, fontWeight: 700 },
  sectionTitle: { fontSize: 16, fontWeight: 600, margin: '0 0 16px' },

  statsGrid:    { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(180px, 1fr))', gap: 16, marginBottom: 24 },
  card:         { background: '#1e2433', borderRadius: 10, padding: '20px 16px', textAlign: 'center' },
  cardValue:    { fontSize: 32, fontWeight: 700, color: '#a78bfa' },
  cardLabel:    { fontSize: 13, color: '#9ca3af', marginTop: 4 },
  cardSub:      { fontSize: 11, color: '#6b7280', marginTop: 6 },

  tabBar:       { display: 'flex', gap: 4, marginBottom: 24, borderBottom: '1px solid #374151', paddingBottom: 0 },
  tabBtn:       { background: 'none', border: 'none', color: '#9ca3af', padding: '10px 18px', cursor: 'pointer', fontSize: 14, borderBottom: '2px solid transparent', borderRadius: '4px 4px 0 0' },
  tabBtnActive: { color: '#a78bfa', borderBottom: '2px solid #a78bfa', fontWeight: 600 },
  tabContent:   { minHeight: 300 },

  tableWrap:    { overflowX: 'auto' },
  table:        { width: '100%', borderCollapse: 'collapse', fontSize: 13 },
  th:           { textAlign: 'left', padding: '10px 12px', background: '#1e2433', color: '#9ca3af', fontWeight: 600, whiteSpace: 'nowrap' },
  tr:           { borderBottom: '1px solid #1f2937' },
  td:           { padding: '10px 12px', verticalAlign: 'middle' },

  badge:        { display: 'inline-block', padding: '2px 8px', borderRadius: 12, fontSize: 11, fontWeight: 600, color: '#fff' },

  btn:          { background: '#7c3aed', color: '#fff', border: 'none', borderRadius: 6, padding: '8px 16px', cursor: 'pointer', fontSize: 13, fontWeight: 500 },
  btnSecondary: { background: '#374151' },
  btnDanger:    { background: '#b91c1c' },
  btnSmall:     { padding: '4px 10px', fontSize: 12 },

  formBox:      { background: '#1e2433', borderRadius: 10, padding: 20, marginBottom: 24 },
  formGrid:     { display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 },
  input:        { background: '#111827', border: '1px solid #374151', color: '#e5e7eb', borderRadius: 6, padding: '8px 12px', fontSize: 13, width: '100%', boxSizing: 'border-box' },

  errorBanner:  { background: '#7f1d1d', color: '#fca5a5', padding: '10px 16px', borderRadius: 8, marginBottom: 16, fontSize: 13 },
  errorText:    { color: '#fca5a5', fontSize: 13, margin: '0 0 8px' },
  muted:        { color: '#6b7280', fontSize: 13 },
};
