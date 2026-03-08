import { useState } from 'react';
import { convertCode, createSnippet, explainCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import DiffView from '../components/DiffView';
import { runCode, canRun } from '../api/executor';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'];

const LANG_META = {
  python: { label: 'Python', color: '#3572A5' },
  c: { label: 'C', color: '#6c757d' },
  java: { label: 'Java', color: '#b07219' },
  javascript: { label: 'JavaScript', color: '#f1e05a' },
  cpp: { label: 'C++', color: '#f34b7d' },
};

const THEMES = [
  { id: 'vs-dark', label: 'Dark' },
  { id: 'vs', label: 'Light' },
  { id: 'hc-black', label: 'High Contrast' },
  { id: 'monokai', label: 'Monokai' },
  { id: 'dracula', label: 'Dracula' },
];

export default function Converter() {
  const [sourceLang, setSourceLang] = useState('python');
  const [targetLang, setTargetLang] = useState('c');
  const [inputCode, setInputCode] = useState('');
  const [outputCode, setOutputCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [engine, setEngine] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('editor_theme') || 'vs-dark');

  // Run source state
  const [runLoading, setRunLoading] = useState(false);
  const [runOutput, setRunOutput] = useState(null);
  const [runError, setRunError] = useState('');
  const [runStdin, setRunStdin] = useState('');

  // Run target state
  const [runLoadingTarget, setRunLoadingTarget] = useState(false);
  const [runOutputTarget, setRunOutputTarget] = useState(null);
  const [runErrorTarget, setRunErrorTarget] = useState('');

  // Diff state
  const [showDiff, setShowDiff] = useState(false);

  // Share state
  const [shareLoading, setShareLoading] = useState(false);
  const [shareToast, setShareToast] = useState('');

  // Explain state
  const [explanation, setExplanation] = useState('');
  const [explainLoading, setExplainLoading] = useState(false);
  const [showExplanation, setShowExplanation] = useState(false);

  const handleConvert = async () => {
    if (!inputCode.trim()) return setError('Please enter some code.');
    if (sourceLang === targetLang) return setError('Source and target languages must differ.');
    setLoading(true);
    setError('');
    setEngine('');
    setRunOutput(null);
    setRunOutputTarget(null);
    setShowDiff(false);
    setExplanation('');
    setShowExplanation(false);
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
      const result = await runCode(sourceLang, inputCode, runStdin);
      setRunOutput(result);
    } catch (err) {
      setRunError(err.message || 'Could not reach execution server. Check your connection.');
    } finally {
      setRunLoading(false);
    }
  };

  const handleRunTarget = async () => {
    if (!outputCode.trim()) return;
    setRunLoadingTarget(true);
    setRunOutputTarget(null);
    setRunErrorTarget('');
    try {
      const result = await runCode(targetLang, outputCode, runStdin);
      setRunOutputTarget(result);
    } catch (err) {
      setRunErrorTarget(err.message || 'Could not reach execution server. Check your connection.');
    } finally {
      setRunLoadingTarget(false);
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

  const handleExplain = async () => {
    if (!outputCode) return;
    if (showExplanation && explanation) {
      setShowExplanation(false);
      return;
    }
    setExplainLoading(true);
    setShowExplanation(true);
    try {
      const { data } = await explainCode({
        input_code: inputCode,
        output_code: outputCode,
        source_language: sourceLang,
        target_language: targetLang,
      });
      setExplanation(data.explanation);
    } catch {
      setExplanation('Could not generate explanation. Make sure your AI_API_KEY is set in .env.');
    } finally {
      setExplainLoading(false);
    }
  };

  const handleThemeChange = (t) => {
    setTheme(t);
    localStorage.setItem('editor_theme', t);
  };

  // Compute output match badge when both sides are run
  const bothRan = runOutput !== null && runOutputTarget !== null;
  const outputsMatch = bothRan &&
    runOutput.stdout?.trim() === runOutputTarget.stdout?.trim() &&
    runOutput.code === runOutputTarget.code;

  return (
    <div className="converter-page">
      <h2>Code Converter</h2>

      <div className="converter-lang-bar">
        <div className="sandbox-lang-group">
          <span className="sandbox-lang-label">From</span>
          <div className="sandbox-lang-pills">
            {LANGUAGES.map(lang => (
              <button
                key={lang}
                className={`sandbox-lang-pill${sourceLang === lang ? ' active' : ''}`}
                style={{ '--pill-color': LANG_META[lang].color }}
                onClick={() => setSourceLang(lang)}
              >
                <span className="sandbox-lang-dot" />
                {LANG_META[lang].label}
              </button>
            ))}
          </div>
        </div>

        <div className="sandbox-convert-center">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="sandbox-convert-arrow">
            <line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" />
          </svg>
          <button className="btn-convert" onClick={handleConvert} disabled={loading}>
            {loading ? 'Converting…' : 'Convert'}
          </button>
        </div>

        <div className="sandbox-lang-group">
          <span className="sandbox-lang-label">To</span>
          <div className="sandbox-lang-pills">
            {LANGUAGES.map(lang => (
              <button
                key={lang}
                className={`sandbox-lang-pill${targetLang === lang ? ' active' : ''}${sourceLang === lang ? ' disabled' : ''}`}
                style={{ '--pill-color': LANG_META[lang].color }}
                onClick={() => sourceLang !== lang && setTargetLang(lang)}
                disabled={sourceLang === lang}
              >
                <span className="sandbox-lang-dot" />
                {LANG_META[lang].label}
              </button>
            ))}
          </div>
        </div>

        <div className="converter-theme-selector">
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
              title={!canRun(sourceLang) ? 'Execution not supported for this language' : 'Run source code'}
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
                  className="btn-run"
                  onClick={handleRunTarget}
                  disabled={runLoadingTarget || !canRun(targetLang)}
                  title={!canRun(targetLang) ? 'Execution not supported for this language' : 'Run converted code'}
                >
                  {runLoadingTarget ? '⏳ Running...' : '▶ Run'}
                </button>
              )}
              {outputCode && (
                <button
                  className={`btn-diff${showDiff ? ' active' : ''}`}
                  onClick={() => setShowDiff(d => !d)}
                >
                  ⊕ Diff
                </button>
              )}
              {outputCode && (
                <button
                  className={`btn-explain${showExplanation ? ' active' : ''}`}
                  onClick={handleExplain}
                  disabled={explainLoading}
                  title="Explain this conversion"
                >
                  {explainLoading ? '...' : '💡 Explain'}
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

      {/* Stdin input */}
      <div className="run-stdin-wrap">
        <label className="run-stdin-label">Program Input (stdin)</label>
        <textarea
          className="run-stdin"
          placeholder="Enter input for your program here (one value per line)..."
          value={runStdin}
          onChange={e => setRunStdin(e.target.value)}
          rows={3}
          spellCheck={false}
        />
      </div>

      {/* Output comparison panel */}
      {(runOutput !== null || runError || runOutputTarget !== null || runErrorTarget) && (
        <div className="run-compare-panel">
          {bothRan && (
            <div className={`run-compare-badge ${outputsMatch ? 'match' : 'differ'}`}>
              {outputsMatch ? '✓ Outputs match' : '⚠ Outputs differ'}
            </div>
          )}
          <div className="run-compare-columns">
            {/* Source terminal */}
            <div className="run-output run-output-half">
              <div className="run-output-header">
                <span>{LANG_META[sourceLang].label} (Input) — Terminal</span>
                <button className="run-output-close" onClick={() => { setRunOutput(null); setRunError(''); }}>×</button>
              </div>
              {runError && <pre className="run-stderr">{runError}</pre>}
              {runOutput && (
                <>
                  {runStdin.trim() && (
                    <>
                      <pre className="run-stdin-echo">{runStdin.trim().split('\n').map(l => `> ${l}`).join('\n')}</pre>
                      <hr className="run-divider" />
                    </>
                  )}
                  {runOutput.stdout && <pre className="run-stdout">{runOutput.stdout}</pre>}
                  {runOutput.stderr && <pre className="run-stderr">{runOutput.stderr}</pre>}
                  {!runOutput.stdout && !runOutput.stderr && (
                    <pre className="run-stdout run-empty">(no output)</pre>
                  )}
                  <span className={`run-exit-code${runOutput.code === 0 ? ' run-exit-ok' : ' run-exit-err'}`}>
                    {runOutput.code === 0 ? '✓' : '✗'} exit {runOutput.code}
                  </span>
                </>
              )}
            </div>

            {/* Target terminal */}
            {(runOutputTarget !== null || runErrorTarget) && (
              <div className="run-output run-output-half">
                <div className="run-output-header">
                  <span>{LANG_META[targetLang].label} (Output) — Terminal</span>
                  <button className="run-output-close" onClick={() => { setRunOutputTarget(null); setRunErrorTarget(''); }}>×</button>
                </div>
                {runErrorTarget && <pre className="run-stderr">{runErrorTarget}</pre>}
                {runOutputTarget && (
                  <>
                    {runStdin.trim() && (
                      <>
                        <pre className="run-stdin-echo">{runStdin.trim().split('\n').map(l => `> ${l}`).join('\n')}</pre>
                        <hr className="run-divider" />
                      </>
                    )}
                    {runOutputTarget.stdout && <pre className="run-stdout">{runOutputTarget.stdout}</pre>}
                    {runOutputTarget.stderr && <pre className="run-stderr">{runOutputTarget.stderr}</pre>}
                    {!runOutputTarget.stdout && !runOutputTarget.stderr && (
                      <pre className="run-stdout run-empty">(no output)</pre>
                    )}
                    <span className={`run-exit-code${runOutputTarget.code === 0 ? ' run-exit-ok' : ' run-exit-err'}`}>
                      {runOutputTarget.code === 0 ? '✓' : '✗'} exit {runOutputTarget.code}
                    </span>
                  </>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Explanation section */}
      {showExplanation && (
        <div className="explain-section">
          <div className="explain-header">
            <span>💡 Conversion Explanation</span>
            <button className="run-output-close" onClick={() => setShowExplanation(false)}>×</button>
          </div>
          {explainLoading ? (
            <p className="explain-loading">Generating explanation…</p>
          ) : (
            <p className="explain-content">{explanation}</p>
          )}
        </div>
      )}
    </div>
  );
}
