// src/pages/FileManager.jsx
import { useEffect, useState } from 'react';
import { getFiles, createFile, updateFile, deleteFile } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';
import type { CodeFile } from '../types';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'other'];
type FileForm = { filename: string; language: string; code_content: string };
const EMPTY_FORM: FileForm = { filename: '', language: 'python', code_content: '' };

const LANG_COLORS: Record<string, string> = {
  python: '#3572A5',
  javascript: '#f1e05a',
  java: '#b07219',
  c: '#555555',
  other: '#8b8b8b',
};

const FILE_EXT: Record<string, string> = {
  python: '.py', c: '.c', java: '.java', javascript: '.js', other: '.txt',
};

export default function FileManager() {
  const [files, setFiles] = useState<CodeFile[]>([]);
  const [selected, setSelected] = useState<CodeFile | null>(null);
  const [form, setForm] = useState<FileForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = async () => {
    try {
      const r = await getFiles();
      setFiles(r.data);
    } catch {
      setError('Failed to load files.');
    }
  };
  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    setError(null);
    if (!form.filename.trim()) {
      setError('Filename is required.');
      return;
    }
    setSaving(true);
    try {
      if (selected) {
        await updateFile(selected.id, form);
        setFiles(prev => prev.map(f => f.id === selected.id ? { ...f, ...form } : f));
      } else {
        const { data: newFile } = await createFile(form);
        setFiles(prev => [...prev, newFile]);
      }
      setSelected(null);
      setForm(EMPTY_FORM);
    } catch {
      setError('Failed to save file. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSelect = (f: CodeFile) => {
    setSelected(f);
    setForm({ filename: f.filename, language: f.language, code_content: f.code_content });
  };

  const handleDelete = async (id: number) => {
    setError(null);
    setDeletingId(id);
    try {
      await deleteFile(id);
      setFiles(prev => prev.filter(f => f.id !== id));
      if (selected?.id === id) { setSelected(null); setForm(EMPTY_FORM); }
    } catch {
      setError('Failed to delete file. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleNew = () => { setSelected(null); setForm(EMPTY_FORM); };

  const handleDownload = () => {
    if (!form.code_content) return;
    const ext = FILE_EXT[form.language] || '.txt';
    const name = form.filename || `code${ext}`;
    const blob = new Blob([form.code_content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = name.includes('.') ? name : name + ext;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="file-manager-grid gap-5 h-[calc(100vh-56px)]">
      {error && <p className="col-span-full bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm mb-3">{error}</p>}
      <div className="bg-surface border border-border rounded p-4 overflow-y-auto">
        <h3 className="text-sm font-semibold text-primary mb-3">My Files</h3>
        <button
          className="w-full text-left px-2 py-1.5 mb-2 text-sm border border-border text-muted hover:text-primary hover:bg-border rounded transition-colors bg-transparent"
          onClick={handleNew}
        >+ New File</button>
        {files.map((f) => (
          <div
            key={f.id}
            className={`flex items-center px-2 py-0.5 rounded cursor-pointer gap-1.5 transition-colors min-h-[24px] text-primary hover:bg-border${selected?.id === f.id ? ' bg-accent/15' : ''}`}
            onClick={() => handleSelect(f)}
          >
            <span className="flex-shrink-0" style={{ color: LANG_COLORS[f.language] || '#8b8b8b' }}>◆</span>
            <span className="flex-1 truncate text-sm">{f.filename || '(unnamed)'}</span>
            <button
              className="ml-auto text-muted hover:text-danger text-sm flex-shrink-0 cursor-pointer border-none bg-transparent p-0 disabled:opacity-40"
              title="Delete"
              disabled={deletingId === f.id}
              onClick={(e) => { e.stopPropagation(); handleDelete(f.id); }}
            >{deletingId === f.id ? '…' : '×'}</button>
          </div>
        ))}
      </div>

      <div className="bg-surface border border-border rounded p-4 flex flex-col gap-2.5">
        <h3 className="text-sm font-semibold text-primary">{selected ? 'Edit File' : 'New File'}</h3>
        <input
          className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-primary focus:outline-none focus:border-accent"
          placeholder="Filename (e.g. hello.py)"
          value={form.filename}
          onChange={(e) => setForm({ ...form, filename: e.target.value })}
        />
        <LanguageSelector
          value={form.language}
          onChange={(lang) => setForm({ ...form, language: lang })}
          languages={LANGUAGES}
        />
        <CodeEditor
          value={form.code_content}
          onChange={(val) => setForm({ ...form, code_content: val ?? '' })}
          language={form.language}
          height="380px"
        />
        <div className="flex gap-2">
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-5 py-2 text-sm font-semibold transition-colors self-start cursor-pointer disabled:opacity-50"
            onClick={handleSave}
            disabled={saving}
          >{saving ? 'Saving…' : '💾 Save'}</button>
          <button
            className="bg-transparent border border-border text-primary hover:bg-border rounded px-5 py-2 text-sm font-medium transition-colors self-start cursor-pointer disabled:opacity-40"
            onClick={handleDownload}
            disabled={!form.code_content}
          >⬇ Download</button>
        </div>
      </div>
    </div>
  );
}
