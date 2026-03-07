// src/pages/FileManager.jsx
import { useEffect, useState } from 'react';
import { getFiles, createFile, updateFile, deleteFile } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'other'];
const EMPTY_FORM = { filename: '', language: 'python', code_content: '' };

const LANG_COLORS = {
  python: '#3572A5',
  javascript: '#f1e05a',
  java: '#b07219',
  c: '#555555',
  other: '#8b8b8b',
};

const FILE_EXT = {
  python: '.py', c: '.c', java: '.java', javascript: '.js', other: '.txt',
};

export default function FileManager() {
  const [files, setFiles] = useState([]);
  const [selected, setSelected] = useState(null);
  const [form, setForm] = useState(EMPTY_FORM);
  const [error, setError] = useState(null);

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
    try {
      if (selected) {
        await updateFile(selected.id, form);
      } else {
        await createFile(form);
      }
      setSelected(null);
      setForm(EMPTY_FORM);
      await load();
    } catch {
      setError('Failed to save file. Please try again.');
    }
  };

  const handleSelect = (f) => {
    setSelected(f);
    setForm({ filename: f.filename, language: f.language, code_content: f.code_content });
  };

  const handleDelete = async (id) => {
    setError(null);
    try {
      await deleteFile(id);
      await load();
    } catch {
      setError('Failed to delete file. Please try again.');
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
    <div className="file-manager">
      {error && <p className="error">{error}</p>}
      <div className="file-list">
        <h3>My Files</h3>
        <button onClick={handleNew}>+ New File</button>
        {files.map((f) => (
          <div key={f.id} className={`file-item${selected?.id === f.id ? ' active' : ''}`} onClick={() => handleSelect(f)}>
            <span className="file-icon" style={{ color: LANG_COLORS[f.language] || '#8b8b8b' }}>◆</span>
            <span className="file-name">{f.filename || '(unnamed)'}</span>
            <button className="file-delete" title="Delete" onClick={(e) => { e.stopPropagation(); handleDelete(f.id); }}>×</button>
          </div>
        ))}
      </div>

      <div className="file-editor">
        <h3>{selected ? 'Edit File' : 'New File'}</h3>
        <input
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
          onChange={(val) => setForm({ ...form, code_content: val })}
          language={form.language}
          height="380px"
        />
        <div className="file-editor-actions">
          <button className="btn-save" onClick={handleSave}>💾 Save</button>
          <button className="btn-download" onClick={handleDownload} disabled={!form.code_content}>⬇ Download</button>
        </div>
      </div>
    </div>
  );
}
