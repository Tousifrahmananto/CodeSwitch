import { useState, useRef, useEffect } from 'react';
import { convertCode, createSnippet, explainCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import DiffView from '../components/DiffView';
import { runCode, canRun } from '../api/executor';
import type { CSSProperties } from 'react';
import type { RunResult } from '../types';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'] as const;
type ConverterLanguage = (typeof LANGUAGES)[number];

const LANG_META: Record<ConverterLanguage, { label: string; color: string }> = {
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
  const [sourceLang, setSourceLang] = useState<ConverterLanguage>('python');
  const [targetLang, setTargetLang] = useState<ConverterLanguage>('c');
  const [inputCode, setInputCode] = useState('');
  const [outputCode, setOutputCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [engine, setEngine] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('editor_theme') || 'vs-dark');

  // Run source state
  const [runLoading, setRunLoading] = useState(false);
  const [runOutput, setRunOutput] = useState<RunResult | null>(null);
  const [runError, setRunError] = useState('');
  const [runStdin, setRunStdin] = useState('');

  // Run target state
  const [runLoadingTarget, setRunLoadingTarget] = useState(false);
  const [runOutputTarget, setRunOutputTarget] = useState<RunResult | null>(null);
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

  // User API key state
  const [quotaExhausted, setQuotaExhausted] = useState(false);
  const [userKeyInput, setUserKeyInput] = useState('');
  const [hasUserKey, setHasUserKey] = useState(!!sessionStorage.getItem('userApiKey'));

  // Abort controllers for in-flight AI requests — cancelled on unmount or new request
  const convertControllerRef = useRef<AbortController | null>(null);
  const explainControllerRef = useRef<AbortController | null>(null);
  const elapsedIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const [convertElapsed, setConvertElapsed] = useState(0);

  // Theme picker popover
  const [showThemePicker, setShowThemePicker] = useState(false);
  const themePickerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    return () => {
      convertControllerRef.current?.abort();
      explainControllerRef.current?.abort();
      if (elapsedIntervalRef.current) clearInterval(elapsedIntervalRef.current);
    };
  }, []);

  // Close theme picker on outside click
  useEffect(() => {
    if (!showThemePicker) return;
    const handler = (e: MouseEvent) => {
      if (themePickerRef.current && !themePickerRef.current.contains(e.target as Node)) {
        setShowThemePicker(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [showThemePicker]);

  // Keyboard shortcuts — Ctrl/Cmd+Enter to convert
  const handleConvertRef = useRef<() => void>(() => { });
  const handleRunRef = useRef<() => void>(() => { });

  const isQuotaError = (msg: string) =>
    msg.includes('All API keys exhausted') || msg.includes('AI_API_KEY not set');

  const handleConvert = async () => {
    if (!inputCode.trim()) return setError('Please enter some code.');
    if (sourceLang === targetLang) return setError('Source and target languages must differ.');
    convertControllerRef.current?.abort();
    const controller = new AbortController();
    convertControllerRef.current = controller;
    setLoading(true);
    setError('');
    setEngine('');
    setRunOutput(null);
    setRunOutputTarget(null);
    setShowDiff(false);
    setExplanation('');
    setShowExplanation(false);
    setConvertElapsed(0);
    elapsedIntervalRef.current = setInterval(() => setConvertElapsed(e => e + 1), 1000);
    try {
      const { data } = await convertCode({
        source_language: sourceLang,
        target_language: targetLang,
        code: inputCode,
      }, { signal: controller.signal });
      setOutputCode(data.output);
      setEngine(data.engine || 'rules');
    } catch (err: any) {
      if (err.name === 'CanceledError' || err.name === 'AbortError') return;
      const msg: string = err.response?.data?.error || 'Conversion failed.';
      setError(msg);
      if (isQuotaError(msg)) setQuotaExhausted(true);
    } finally {
      if (elapsedIntervalRef.current) { clearInterval(elapsedIntervalRef.current); elapsedIntervalRef.current = null; }
      setConvertElapsed(0);
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Could not reach execution server. Check your connection.';
      setRunError(message);
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
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Could not reach execution server. Check your connection.';
      setRunErrorTarget(message);
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
      const url = `${window.location.origin}/share/${data.slug}`;
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
    explainControllerRef.current?.abort();
    const controller = new AbortController();
    explainControllerRef.current = controller;
    setExplainLoading(true);
    setShowExplanation(true);
    try {
      const { data } = await explainCode({
        input_code: inputCode,
        output_code: outputCode,
        source_language: sourceLang,
        target_language: targetLang,
      }, { signal: controller.signal });
      setExplanation(data.explanation);
    } catch (err: any) {
      if (err.name === 'CanceledError' || err.name === 'AbortError') return;
      const msg: string = err.response?.data?.error || '';
      if (isQuotaError(msg)) {
        setQuotaExhausted(true);
        setExplanation('AI capacity reached — add your own API key below to continue.');
      } else {
        setExplanation('Could not generate explanation. Please try again.');
      }
    } finally {
      setExplainLoading(false);
    }
  };

  const handleThemeChange = (t: string) => {
    setTheme(t);
    localStorage.setItem('editor_theme', t);
  };

  const getPillStyle = (lang: ConverterLanguage): CSSProperties & { '--pill-color': string } => ({
    '--pill-color': LANG_META[lang].color,
  });

  const handleSaveUserKey = () => {
    const key = userKeyInput.trim();
    if (!key) return;
    sessionStorage.setItem('userApiKey', key);
    setHasUserKey(true);
    setUserKeyInput('');
    setQuotaExhausted(false);
    setError('');
    handleConvert();
  };

  const handleRemoveUserKey = () => {
    sessionStorage.removeItem('userApiKey');
    setHasUserKey(false);
  };

  // Keep shortcut refs in sync with latest handlers
  useEffect(() => { handleConvertRef.current = handleConvert; });
  useEffect(() => { handleRunRef.current = handleRun; });

  // Global keyboard shortcuts — Ctrl/Cmd+Enter to convert, Ctrl/Cmd+Shift+R to run
  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement)?.tagName?.toLowerCase();
      if (tag === 'input' || tag === 'textarea' || tag === 'select') return;
      if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        e.preventDefault();
        handleConvertRef.current();
      }
      if ((e.ctrlKey || e.metaKey) && e.shiftKey && e.key === 'R') {
        e.preventDefault();
        handleRunRef.current();
      }
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

  // Compute output match badge when both sides are run
  const bothRan = runOutput !== null && runOutputTarget !== null;
  const outputsMatch = bothRan &&
    runOutput.stdout?.trim() === runOutputTarget.stdout?.trim() &&
    runOutput.code === runOutputTarget.code;

  return (
    <div className="p-5">
      <h2>Code Converter</h2>

      <div className="flex items-center gap-4 mb-4 flex-wrap">
        <div className="sandbox-lang-group">
          <span className="sandbox-lang-label">From</span>
          <div className="sandbox-lang-pills">
            {LANGUAGES.map(lang => (
              <button
                key={lang}
                className={`sandbox-lang-pill${sourceLang === lang ? ' active' : ''}`}
                style={getPillStyle(lang)}
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
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-5 py-2 text-sm font-semibold transition-colors cursor-pointer disabled:opacity-50"
            onClick={handleConvert}
            disabled={loading}
            title="Convert (Ctrl+Enter)"
          >
            {loading
              ? convertElapsed > 3 ? `Converting… ${convertElapsed}s` : 'Converting…'
              : 'Convert'}
          </button>
        </div>

        <div className="sandbox-lang-group">
          <span className="sandbox-lang-label">To</span>
          <div className="sandbox-lang-pills">
            {LANGUAGES.map(lang => (
              <button
                key={lang}
                className={`sandbox-lang-pill${targetLang === lang ? ' active' : ''}${sourceLang === lang ? ' disabled' : ''}`}
                style={getPillStyle(lang)}
                onClick={() => sourceLang !== lang && setTargetLang(lang)}
                disabled={sourceLang === lang}
              >
                <span className="sandbox-lang-dot" />
                {LANG_META[lang].label}
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-2 ml-auto">
          {/* Theme picker — icon button with popover */}
          <div className="relative" ref={themePickerRef}>
            <button
              className="flex items-center gap-1 text-xs text-muted border border-border rounded px-2.5 py-1.5 bg-transparent hover:bg-border transition-colors"
              onClick={() => setShowThemePicker(p => !p)}
              title="Editor theme"
            >
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <circle cx="12" cy="12" r="3" />
                <path d="M12 2v2M12 20v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M2 12h2M20 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" />
              </svg>
              {THEMES.find(t => t.id === theme)?.label ?? 'Theme'}
            </button>
            {showThemePicker && (
              <div className="absolute right-0 top-full mt-1 z-50 bg-surface border border-border rounded-lg shadow-lg overflow-hidden min-w-[130px]">
                {THEMES.map(t => (
                  <button
                    key={t.id}
                    className={`w-full text-left px-3 py-2 text-xs transition-colors bg-transparent border-none ${theme === t.id
                        ? 'bg-accent/15 text-accent font-semibold'
                        : 'text-primary hover:bg-border'
                      }`}
                    onClick={() => { handleThemeChange(t.id); setShowThemePicker(false); }}
                  >
                    {t.label}
                  </button>
                ))}
              </div>
            )}
          </div>
          {hasUserKey && (
            <>
              <span className="text-xs bg-success/15 text-success border border-success/30 rounded px-2 py-1 whitespace-nowrap">✓ Your API key active</span>
              <button className="text-xs text-muted hover:text-danger bg-transparent border-none cursor-pointer p-0" onClick={handleRemoveUserKey}>Remove</button>
            </>
          )}
        </div>
      </div>

      {error && <p className="bg-danger/10 border border-danger text-danger rounded p-2.5 text-sm mb-3">{error}</p>}

      {quotaExhausted && (
        <div className="bg-surface border border-border rounded p-4 mb-4 flex flex-col gap-3">
          <div>
            <p className="text-sm font-semibold text-primary mb-1">AI capacity reached</p>
            <p className="text-xs text-muted">Our AI quota is temporarily exhausted. Add your own free API key to keep using AI-powered conversions.</p>
          </div>
          <div className="flex items-center gap-2 flex-wrap text-xs text-muted">
            <span>Get a free key:</span>
            <a href="https://console.groq.com/keys" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">Groq Console</a>
            <span>·</span>
            <a href="https://aistudio.google.com/apikey" target="_blank" rel="noopener noreferrer" className="text-accent hover:underline">Gemini Studio</a>
          </div>
          <div className="flex gap-2">
            <input
              type="password"
              className="flex-1 bg-bg border border-border rounded px-3 py-1.5 text-sm text-primary focus:outline-none focus:border-accent"
              placeholder="Paste your API key here"
              value={userKeyInput}
              onChange={e => setUserKeyInput(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && handleSaveUserKey()}
            />
            <button
              className="bg-accent hover:bg-accent-h text-white border-none rounded px-4 py-1.5 text-sm font-semibold transition-colors disabled:opacity-50"
              onClick={handleSaveUserKey}
              disabled={!userKeyInput.trim()}
            >
              Save & Retry
            </button>
            <button
              className="bg-transparent border border-border text-muted hover:text-primary rounded px-3 py-1.5 text-sm transition-colors"
              onClick={() => setQuotaExhausted(false)}
            >
              Dismiss
            </button>
          </div>
        </div>
      )}

      {engine && (
        <p className={engine === 'ai'
          ? 'inline-block text-xs font-semibold rounded px-3 py-1 mb-3 tracking-wide bg-accent/15 border border-accent text-accent-h'
          : 'inline-block text-xs font-semibold rounded px-3 py-1 mb-3 tracking-wide bg-warning/10 border border-warning text-warning'
        }>
          {engine === 'ai' ? '✦ AI-powered conversion' : '⚙ Rule-based conversion'}
        </p>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
        <div className="flex flex-col gap-2">
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
            onChange={(value) => setInputCode(value ?? '')}
            language={sourceLang}
            height="420px"
            theme={theme}
          />
        </div>

        <div className="flex flex-col gap-2">
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
