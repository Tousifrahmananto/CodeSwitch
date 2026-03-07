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
    <div className="share-page">
      <nav className="share-nav">
        <div className="share-nav-brand">
          <Logo size={28} id="share" />
          <span>CodeSwitch</span>
        </div>
        <button className="share-back" onClick={onBack}>
          {onBack ? '← Back to app' : '← Home'}
        </button>
      </nav>

      {error && <p className="share-error">{error}</p>}

      {snippet && (
        <div className="share-content">
          <div className="share-meta">
            <span className="share-badge">{snippet.source_language} → {snippet.target_language}</span>
            <span className={`engine-badge ${snippet.engine === 'ai' ? 'badge-ai' : 'badge-rules'}`}>
              {snippet.engine === 'ai' ? '✦ AI conversion' : '⚙ Rule-based'}
            </span>
          </div>
          <div className="editor-panels">
            <div className="panel">
              <h4>{snippet.source_language} (Input)</h4>
              <CodeEditor
                value={snippet.input_code}
                language={snippet.source_language}
                readOnly
                height="420px"
              />
            </div>
            <div className="panel">
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
        <div className="share-loading">Loading snippet...</div>
      )}
    </div>
  );
}
