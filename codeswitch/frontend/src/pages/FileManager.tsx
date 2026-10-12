// src/pages/FileManager.jsx
import { useEffect, useRef, useState } from 'react';
import { getFiles, getFile, createFile, updateFile, deleteFile } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';
import { getLanguageMeta } from '../constants/languages';
import type { CodeFileSummary } from '../types';

const LANGUAGES = ['python', 'c', 'cpp', 'java', 'javascript', 'other'];
type FileForm = { filename: string; language: string; code_content: string };
const EMPTY_FORM: FileForm = { filename: '', language: 'python', code_content: '' };

const FILE_EXT: Record<string, string> = {
  python: '.py', c: '.c', cpp: '.cpp', java: '.java', javascript: '.js', other: '.txt',
};

export default function FileManager() {
  const revisionRef = useRef(0);
  const changeForm = (next: FileForm) => { revisionRef.current += 1; setForm(next); };
  const [files, setFiles] = useState<CodeFileSummary[]>([]);
  const [selected, setSelected] = useState<CodeFileSummary | null>(null);
  const [nextPage, setNextPage] = useState<number | null>(null);
  const [loadingList, setLoadingList] = useState(false);
  const [loadingFile, setLoadingFile] = useState(false);
  const [fileLoaded, setFileLoaded] = useState(true);
  const listRequestRef = useRef(0);
  const selectionRequestRef = useRef(0);
  const [form, setForm] = useState<FileForm>(EMPTY_FORM);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const load = async (page = 1) => {
    const request = ++listRequestRef.current;
    setLoadingList(true);
    try {
      const { data } = await getFiles(page);
      if (listRequestRef.current !== request) return;
      setFiles(previous => page === 1 ? data.results : [
        ...previous, ...data.results.filter(file => !previous.some(existing => existing.id === file.id)),
      ]);
      setNextPage(data.next ? page + 1 : null);
    } catch {
      if (listRequestRef.current === request) setError('Failed to load files.');
    } finally {
      if (listRequestRef.current === request) setLoadingList(false);
    }
  };
  useEffect(() => { load(); }, []);

  const handleSave = async () => {
    setError(null);
    if (!form.filename.trim()) {
      setError('Filename is required.');
      return;
    }
    const revision = revisionRef.current;
    const snapshot = { ...form };
    setSaving(true);
    try {
      if (selected) {
        await updateFile(selected.id, snapshot);
      } else {
        await createFile(snapshot);
      }
      await load();
      if (revisionRef.current === revision) { setSelected(null); changeForm(EMPTY_FORM); }
    } catch {
      if (revisionRef.current === revision) setError('Failed to save file. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handleSelect = async (f: CodeFileSummary) => {
    const request = ++selectionRequestRef.current;
    setSelected(f);
    changeForm({ filename: f.filename, language: f.language, code_content: '' });
    const revision = revisionRef.current;
    setLoadingFile(true);
    setFileLoaded(false);
    setError(null);
    try {
      const { data } = await getFile(f.id);
      if (selectionRequestRef.current === request && revisionRef.current === revision) {
        changeForm({ filename: data.filename, language: data.language, code_content: data.code_content });
      }
      if (selectionRequestRef.current === request) setFileLoaded(true);
    } catch {
      if (selectionRequestRef.current === request) setError('Failed to open file. Select it again to retry.');
    } finally {
      if (selectionRequestRef.current === request) setLoadingFile(false);
    }
  };

  const handleDelete = async (id: number) => {
    setError(null);
    const revision = revisionRef.current;
    setDeletingId(id);
    try {
      await deleteFile(id);
      await load();
      if (selected?.id === id && revisionRef.current === revision) { setSelected(null); changeForm(EMPTY_FORM); }
    } catch {
      setError('Failed to delete file. Please try again.');
    } finally {
      setDeletingId(null);
    }
  };

  const handleNew = () => {
    selectionRequestRef.current += 1;
    setLoadingFile(false);
    setFileLoaded(true);
    setSelected(null);
    changeForm(EMPTY_FORM);
  };

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
            <span className="flex-shrink-0" style={{ color: getLanguageMeta(f.language).color }}>◆</span>
            <span className="flex-1 truncate text-sm">{f.filename || '(unnamed)'}</span>
            <button
              className="ml-auto text-muted hover:text-danger text-sm flex-shrink-0 cursor-pointer border-none bg-transparent p-0 disabled:opacity-40"
              title="Delete"
              disabled={deletingId === f.id}
              onClick={(e) => { e.stopPropagation(); handleDelete(f.id); }}
            >{deletingId === f.id ? '…' : '×'}</button>
          </div>
        ))}
        {nextPage && <button className="text-sm text-accent p-2 disabled:opacity-50" disabled={loadingList}
          onClick={() => load(nextPage)}>Load more files</button>}
      </div>

      <div className="bg-surface border border-border rounded p-4 flex flex-col gap-2.5">
        <h3 className="text-sm font-semibold text-primary">{loadingFile ? 'Opening file…' : selected ? 'Edit File' : 'New File'}</h3>
        <input
          className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-primary focus:outline-none focus:border-accent"
          placeholder="Filename (e.g. hello.py)"
          value={form.filename}
          onChange={(e) => changeForm({ ...form, filename: e.target.value })}
        />
        <LanguageSelector
          value={form.language}
          onChange={(lang) => changeForm({ ...form, language: lang })}
          languages={LANGUAGES}
        />
        <CodeEditor
          value={form.code_content}
          onChange={(val) => changeForm({ ...form, code_content: val ?? '' })}
          language={form.language}
          height="380px"
        />
        <div className="flex gap-2">
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-5 py-2 text-sm font-semibold transition-colors self-start cursor-pointer disabled:opacity-50"
            onClick={handleSave}
            disabled={saving || loadingFile || (selected !== null && !fileLoaded)}
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
