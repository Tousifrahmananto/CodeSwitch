// src/pages/ShareView.jsx
import { useEffect, useState } from 'react';
import { getSnippet } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import Logo from '../components/Logo';

export default function ShareView({ slug, onBack }) {
  const [snippet, setSnippet] = useState(null);
  const [error, setError] = useState('');

  useEffect(() => {
    getSnippet(slug)
      .then(r => setSnippet(r.data))
      .catch(() => setError('Snippet not found or has expired.'));
  }, [slug]);

  return (
    <div className="min-h-screen">
      <nav className="flex items-center justify-between px-5 py-3 border-b border-border">
        <div className="flex items-center gap-2 font-semibold">
          <Logo size={28} id="share" />
          <span>CodeSwitch</span>
        </div>
        <button
          className="text-sm text-muted hover:text-primary cursor-pointer border border-border rounded px-3 py-1.5 transition-colors bg-transparent"
          onClick={onBack}
        >
          {onBack ? '← Back to app' : '← Home'}
        </button>
      </nav>

      {error && <p className="bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm m-5">{error}</p>}

      {snippet && (
        <div className="p-5">
          <div className="flex items-center gap-3 mb-4">
            <span className="text-xs font-semibold bg-border text-primary px-2.5 py-1 rounded">{snippet.source_language} → {snippet.target_language}</span>
            <span className={snippet.engine === 'ai'
              ? 'inline-block text-xs font-semibold rounded px-3 py-1 tracking-wide bg-accent/15 border border-accent text-accent-h'
              : 'inline-block text-xs font-semibold rounded px-3 py-1 tracking-wide bg-warning/10 border border-warning text-warning'
            }>
              {snippet.engine === 'ai' ? '✦ AI conversion' : '⚙ Rule-based'}
            </span>
          </div>
          <div className="grid grid-cols-2 gap-4">
            <div className="flex flex-col gap-2">
              <h4>{snippet.source_language} (Input)</h4>
              <CodeEditor
                value={snippet.input_code}
                language={snippet.source_language}
                readOnly
                height="420px"
              />
            </div>
            <div className="flex flex-col gap-2">
              <h4>{snippet.target_language} (Output)</h4>
              <CodeEditor
                value={snippet.output_code}
                language={snippet.target_language}
                readOnly
                height="420px"
              />
            </div>
          </div>
        </div>
      )}

      {!snippet && !error && (
        <div className="flex items-center justify-center p-12 text-muted text-sm">Loading snippet...</div>
      )}
    </div>
  );
}
