// src/pages/Learning.jsx
import { useEffect, useState } from 'react';
import { getModules, getModule, updateProgress, getProgress, convertCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';

const LANG_COLORS = { c: '#555555', python: '#3572A5', java: '#b07219' };

const formatCompletionDate = (iso) =>
  iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';

function ContentRenderer({ text }) {
  if (!text) return null;
  const paragraphs = text.split('\n\n');
  return (
    <div className="content-body">
      {paragraphs.map((para, i) => {
        const lines = para.split('\n');

        if (lines.every(l => l.trim().startsWith('|'))) {
          const [header, ...rows] = lines;
          const cols = header.split('|').filter(Boolean).map(s => s.trim());
          return (
            <table key={i} className="compare-table">
              <thead>
                <tr>{cols.map((c, j) => <th key={j}>{c}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((row, ri) => (
                  <tr key={ri}>
                    {row.split('|').filter(Boolean).map((cell, ci) => (
                      <td key={ci}>{cell.trim()}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          );
        }

        if (lines.every(l => /^\d+\./.test(l.trim()))) {
          return (
            <ol key={i} className="lesson-list">
              {lines.map((l, li) => <li key={li}>{l.replace(/^\d+\.\s*/, '')}</li>)}
            </ol>
          );
        }

        if (lines.every(l => l.trim().startsWith('- '))) {
          return (
            <ul key={i} className="lesson-list">
              {lines.map((l, li) => <li key={li}>{l.replace(/^-\s*/, '')}</li>)}
            </ul>
          );
        }

        return <p key={i}>{para}</p>;
      })}
    </div>
  );
}

// Feature 3: copy to clipboard
function CodeTabs({ code }) {
  const [active, setActive] = useState(0);
  const [copied, setCopied] = useState(false);
  let tabs;
  try {
    const parsed = JSON.parse(code);
    tabs = Object.entries(parsed).map(([lang, src]) => ({ lang, src }));
  } catch {
    tabs = [{ lang: 'code', src: code }];
  }
  if (!tabs.length) return null;

  const handleCopy = () => {
    navigator.clipboard.writeText(tabs[active].src);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="code-tabs">
      <div className="code-tab-bar">
        {tabs.map((t, i) => (
          <button
            key={t.lang}
            className={`code-tab-btn${active === i ? ' active' : ''}`}
            style={active === i ? { borderBottomColor: LANG_COLORS[t.lang] || 'var(--accent)' } : {}}
            onClick={() => setActive(i)}
          >
            {t.lang.toUpperCase()}
          </button>
        ))}
        <button
          className={`code-copy-btn${copied ? ' copied' : ''}`}
          onClick={handleCopy}
        >
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre className="example-code"><code>{tabs[active].src}</code></pre>
    </div>
  );
}

// Feature 1: Try It sandbox
function TryItSandbox({ exampleCode }) {
  const languages = Object.keys(exampleCode);
  const [sandboxCode, setSandboxCode] = useState(exampleCode[languages[0]] || '');
  const [sandboxSource, setSandboxSource] = useState(languages[0]);
  const [sandboxTarget, setSandboxTarget] = useState(languages[1] || languages[0]);
  const [sandboxOutput, setSandboxOutput] = useState('');
  const [sandboxLoading, setSandboxLoading] = useState(false);
  const [sandboxError, setSandboxError] = useState('');

  const handleSourceChange = (lang) => {
    setSandboxSource(lang);
    setSandboxCode(exampleCode[lang] || '');
    setSandboxOutput('');
    setSandboxError('');
  };

  const handleConvert = async () => {
    if (!sandboxCode.trim()) return;
    if (sandboxSource === sandboxTarget) {
      setSandboxError('Source and target languages must differ.');
      return;
    }
    setSandboxLoading(true);
    setSandboxError('');
    try {
      const { data } = await convertCode({
        source_language: sandboxSource,
        target_language: sandboxTarget,
        code: sandboxCode,
      });
      setSandboxOutput(data.output);
    } catch (err) {
      setSandboxError(err.response?.data?.error || 'Conversion failed. Try again.');
    } finally {
      setSandboxLoading(false);
    }
  };

  const handleReset = () => {
    setSandboxCode(exampleCode[sandboxSource] || '');
    setSandboxOutput('');
    setSandboxError('');
  };

  return (
    <div className="try-it-sandbox">
      <div className="sandbox-header">
        <span className="sandbox-title">Try It</span>
        <button className="btn-reset" onClick={handleReset}>Reset</button>
      </div>
      <div className="sandbox-controls">
        <LanguageSelector
          label="From:"
          value={sandboxSource}
          onChange={handleSourceChange}
          languages={languages}
        />
        <button
          className="btn-convert"
          onClick={handleConvert}
          disabled={sandboxLoading}
        >
          {sandboxLoading ? 'Converting...' : '⇒ Convert'}
        </button>
        <LanguageSelector
          label="To:"
          value={sandboxTarget}
          onChange={setSandboxTarget}
          languages={languages}
        />
      </div>
      {sandboxError && <p className="sandbox-error">{sandboxError}</p>}
      <CodeEditor
        value={sandboxCode}
        onChange={setSandboxCode}
        language={sandboxSource}
        height="200px"
      />
      {sandboxOutput && (
        <div className="sandbox-output-section">
          <div className="sandbox-output-label">{sandboxTarget.toUpperCase()} Output</div>
          <CodeEditor
            value={sandboxOutput}
            language={sandboxTarget}
            readOnly
            height="200px"
          />
        </div>
      )}
    </div>
  );
}

export default function Learning() {
  const [modules, setModules] = useState([]);
  const [activeModule, setActiveModule] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  // Feature 5: Map<lessonId, completionDateISO> instead of Set
  const [completedLessons, setCompletedLessons] = useState(new Map());
  // Feature 2: { [module_title]: completed_count }
  const [completedByModule, setCompletedByModule] = useState({});

  useEffect(() => {
    getModules().then(r => setModules(r.data));
    getProgress().then(r => {
      const completedRecords = r.data.filter(p => p.completed);
      // Feature 5: lesson_id → completion_date
      setCompletedLessons(new Map(completedRecords.map(p => [p.lesson_id, p.completion_date])));
      // Feature 2: count per module title
      const byModule = {};
      completedRecords.forEach(p => {
        byModule[p.module_title] = (byModule[p.module_title] || 0) + 1;
      });
      setCompletedByModule(byModule);
    });
  }, []);

  const openModule = async (id) => {
    const { data } = await getModule(id);
    setActiveModule(data);
    setActiveLesson(data.lessons[0] || null);
  };

  const goToNext = () => {
    if (!activeModule) return;
    const idx = activeModule.lessons.findIndex(l => l.id === activeLesson?.id);
    if (idx < activeModule.lessons.length - 1) {
      setActiveLesson(activeModule.lessons[idx + 1]);
    }
  };

  const markComplete = async (lessonId) => {
    await updateProgress(lessonId);
    // Feature 5: store completion date in Map
    setCompletedLessons(prev => new Map([...prev, [lessonId, new Date().toISOString()]]));
    // Feature 2: increment module count
    if (activeModule) {
      setCompletedByModule(prev => ({
        ...prev,
        [activeModule.title]: (prev[activeModule.title] || 0) + 1,
      }));
    }
    // Feature 4: auto-advance after 700ms if not the last lesson
    if (activeModule) {
      const idx = activeModule.lessons.findIndex(l => l.id === lessonId);
      if (idx < activeModule.lessons.length - 1) {
        setTimeout(goToNext, 700);
      }
    }
  };

  if (activeModule) {
    const total = activeModule.lessons.length;
    const done = activeModule.lessons.filter(l => completedLessons.has(l.id)).length;
    const pct = total ? Math.round((done / total) * 100) : 0;
    const isLast = activeLesson?.id === activeModule.lessons[activeModule.lessons.length - 1]?.id;
    const isCompleted = activeLesson && completedLessons.has(activeLesson.id);

    // Feature 1: parse example_code once per lesson render
    const parsedCode = (() => {
      if (!activeLesson?.example_code) return null;
      try { return JSON.parse(activeLesson.example_code); } catch { return null; }
    })();

    return (
      <div className="lesson-viewer">
        <div className="lesson-viewer-header">
          <button className="back-btn" onClick={() => setActiveModule(null)}>← Modules</button>
          <span className="module-title-sm">{activeModule.title}</span>
          <span className="progress-label">{done}/{total} complete</span>
        </div>
        <div className="progress-bar-track">
          <div className="progress-bar-fill" style={{ width: `${pct}%` }} />
        </div>
        <div className="lesson-layout">
          <div className="lesson-sidebar">
            {activeModule.lessons.map((l, idx) => {
              const isDone = completedLessons.has(l.id);
              const isActive = activeLesson?.id === l.id;
              return (
                <div
                  key={l.id}
                  className={`lesson-nav-item${isActive ? ' active' : ''}${isDone ? ' done' : ''}`}
                  onClick={() => setActiveLesson(l)}
                >
                  <span className="lesson-num">{isDone ? '✓' : idx + 1}</span>
                  {/* Feature 5: show completion date */}
                  <span className="lesson-nav-label">
                    <span className="lesson-nav-title">{l.title}</span>
                    {isDone && (
                      <span className="lesson-completion-date">
                        {formatCompletionDate(completedLessons.get(l.id))}
                      </span>
                    )}
                  </span>
                </div>
              );
            })}
          </div>
          <div className="lesson-content">
            {activeLesson ? (
              <>
                <h3>{activeLesson.title}</h3>
                <ContentRenderer text={activeLesson.content} />
                {/* Feature 1 + 3: code tabs with copy button, then sandbox */}
                {parsedCode && (
                  <CodeTabs key={`tabs-${activeLesson.id}`} code={activeLesson.example_code} />
                )}
                {parsedCode && Object.keys(parsedCode).length >= 2 && (
                  <TryItSandbox key={`sandbox-${activeLesson.id}`} exampleCode={parsedCode} />
                )}
                <div className="lesson-actions">
                  {!isCompleted && (
                    <button className="btn-complete" onClick={() => markComplete(activeLesson.id)}>
                      ✓ Mark as Complete
                    </button>
                  )}
                  {!isLast && isCompleted && (
                    <button className="btn-next" onClick={goToNext}>
                      Next Lesson →
                    </button>
                  )}
                  {isCompleted && isLast && (
                    <p className="all-done">Module complete! Head to the Converter to practice.</p>
                  )}
                </div>
              </>
            ) : (
              <p style={{ color: 'var(--text-muted)' }}>Select a lesson from the sidebar.</p>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="learning-page">
      <div className="module-list">
        <h2>Learning Modules</h2>
        {modules.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>No modules available yet.</p>
        )}
        <div className="module-grid">
          {modules.map(m => (
            <div key={m.id} className="module-card" onClick={() => openModule(m.id)}>
              <h3>{m.title}</h3>
              <p>{m.description}</p>
              {/* Feature 2: progress pill */}
              <div className="module-meta">
                <span className={`badge ${m.difficulty}`}>{m.difficulty}</span>
                <span className="lang-badge">{m.language}</span>
                <span className="badge">{m.lesson_count} lessons</span>
                <span className="module-progress-pill">
                  {completedByModule[m.title] || 0}/{m.lesson_count}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
