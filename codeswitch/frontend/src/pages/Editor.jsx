import { useState } from 'react';
import { convertCode, createSnippet } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';
import DiffView from '../components/DiffView';
import { runCode, canRun } from '../api/executor';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'];

const THEMES = [
  { id: 'vs-dark', label: 'Dark' },
  { id: 'vs', label: 'Light' },
  { id: 'hc-black', label: 'High Contrast' },
  { id: 'monokai', label: 'Monokai' },
  { id: 'dracula', label: 'Dracula' },
];

export default function Editor() {
  const [sourceLang, setSourceLang] = useState('python');
  const [targetLang, setTargetLang] = useState('c');
  const [inputCode, setInputCode] = useState('');
  const [outputCode, setOutputCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [engine, setEngine] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('editor_theme') || 'vs-dark');

  // Run state
  const [runLoading, setRunLoading] = useState(false);
  const [runOutput, setRunOutput] = useState(null);
  const [runError, setRunError] = useState('');

  // Diff state
  const [showDiff, setShowDiff] = useState(false);

  // Share state
  const [shareLoading, setShareLoading] = useState(false);
  const [shareToast, setShareToast] = useState('');

  const handleConvert = async () => {
    if (!inputCode.trim()) return setError('Please enter some code.');
    if (sourceLang === targetLang) return setError('Source and target languages must differ.');
    setLoading(true);
    setError('');
    setEngine('');
    setRunOutput(null);
    setShowDiff(false);
    try {
      const { data } = await convertCode({
        source_language: sourceLang,
        target_language: targetLang,
        code: inputCode,
      });
      setOutputCode(data.output);
      setEngine(data.engine || 'rules');
    } catch (err) {
      setError(err.response?.data?.error || 'Conversion failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleRun = async () => {
    if (!inputCode.trim()) return;
    setRunLoading(true);
    setRunOutput(null);
    setRunError('');
    try {
      const result = await runCode(sourceLang, inputCode);
      setRunOutput(result);
    } catch (err) {
      setRunError(err.message || 'Could not reach execution server. Check your connection.');
    } finally {
      setRunLoading(false);
    }
  };

  const handleShare = async () => {
    if (!outputCode) return;
    setShareLoading(true);
    try {
      const { data } = await createSnippet({
        source_language: sourceLang,
        target_language: targetLang,
        input_code: inputCode,
        output_code: outputCode,
        engine,
      });
      const url = `${window.location.origin}${window.location.pathname}?share=${data.slug}`;
      await navigator.clipboard.writeText(url);
      setShareToast('Link copied!');
      setTimeout(() => setShareToast(''), 2500);
    } catch {
      setShareToast('Failed to create link.');
      setTimeout(() => setShareToast(''), 2500);
    } finally {
      setShareLoading(false);
    }
  };

  const handleThemeChange = (t) => {
    setTheme(t);
    localStorage.setItem('editor_theme', t);
  };

  return (
    <div className="editor-page">
      <h2>Code Converter</h2>

      <div className="lang-selectors">
        <LanguageSelector label="From:" value={sourceLang} onChange={setSourceLang} languages={LANGUAGES} />

        <button className="btn-convert" onClick={handleConvert} disabled={loading}>
          {loading ? 'Converting...' : '⇒ Convert'}
        </button>

        <LanguageSelector label="To:" value={targetLang} onChange={setTargetLang} languages={LANGUAGES} />

        <div className="theme-selector">
          <label>Theme</label>
          <select value={theme} onChange={e => handleThemeChange(e.target.value)}>
            {THEMES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {engine && (
        <p className={`engine-badge ${engine === 'ai' ? 'badge-ai' : 'badge-rules'}`}>
          {engine === 'ai' ? '✦ AI-powered conversion' : '⚙ Rule-based conversion (set AI_API_KEY in .env to enable AI)'}
        </p>
      )}

      <div className="editor-panels">
        <div className="panel">
          <div className="panel-header">
            <h4>{sourceLang} (Input)</h4>
            <button
              className="btn-run"
              onClick={handleRun}
              disabled={runLoading || !inputCode.trim() || !canRun(sourceLang)}
              title={!canRun(sourceLang) ? 'Execution not supported for this language' : 'Run code'}
            >
              {runLoading ? '⏳ Running...' : '▶ Run'}
            </button>
          </div>
          <CodeEditor
            value={inputCode}
            onChange={setInputCode}
            language={sourceLang}
            height="420px"
            theme={theme}
          />
        </div>

        <div className="panel">
          <div className="panel-header">
            <h4>{targetLang} (Output)</h4>
            <div className="panel-header-actions">
              {outputCode && (
                <button
                  className={`btn-diff${showDiff ? ' active' : ''}`}
                  onClick={() => setShowDiff(d => !d)}
                >
                  ⊕ Diff
                </button>
              )}
              {outputCode && (
                <button className="btn-share" onClick={handleShare} disabled={shareLoading}>
                  {shareLoading ? '...' : '⬆ Share'}
                </button>
              )}
              {shareToast && <span className="share-toast">{shareToast}</span>}
            </div>
          </div>
          {showDiff ? (
            <DiffView before={inputCode} after={outputCode} height="420px" />
          ) : (
            <CodeEditor
              value={outputCode}
              language={targetLang}
              readOnly
              height="420px"
              theme={theme}
            />
          )}
        </div>
      </div>

      {/* Run output terminal */}
      {(runOutput !== null || runError) && (
        <div className="run-output">
          <div className="run-output-header">
            <span>Terminal</span>
            <button className="run-output-close" onClick={() => { setRunOutput(null); setRunError(''); }}>×</button>
          </div>
          {runError && <pre className="run-stderr">{runError}</pre>}
          {runOutput && (
            <>
              {runOutput.stdout && <pre className="run-stdout">{runOutput.stdout}</pre>}
              {runOutput.stderr && <pre className="run-stderr">{runOutput.stderr}</pre>}
              {!runOutput.stdout && !runOutput.stderr && (
                <pre className="run-stdout run-empty">(no output)</pre>
              )}
              <span className="run-exit-code">exit code: {runOutput.code}</span>
            </>
          )}
        </div>
      )}
    </div>
  );
}
