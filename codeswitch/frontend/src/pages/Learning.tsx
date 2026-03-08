// src/pages/Learning.jsx
import { useEffect, useState, memo } from 'react';
import { getModules, getModule, updateProgress, getProgress, convertCode, getLessonQuiz, submitQuiz } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import { runCode, canRun } from '../api/executor';

const LANG_COLORS = { c: '#555555', python: '#3572A5', java: '#b07219' };

const formatCompletionDate = (iso) =>
  iso ? new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : '';

const ContentRenderer = memo(function ContentRenderer({ text }) {
  if (!text) return null;

  // Parse inline formatting: **bold**, *italic*, `code`
  function renderInline(str) {
    const parts = [];
    const re = /(\*\*(.+?)\*\*|\*(.+?)\*|`([^`]+?)`)/g;
    let last = 0;
    let match;
    while ((match = re.exec(str)) !== null) {
      if (match.index > last) parts.push(str.slice(last, match.index));
      if (match[2] !== undefined) parts.push(<strong key={match.index}>{match[2]}</strong>);
      else if (match[3] !== undefined) parts.push(<em key={match.index}>{match[3]}</em>);
      else if (match[4] !== undefined) parts.push(<code key={match.index} className="inline-code">{match[4]}</code>);
      last = match.index + match[0].length;
    }
    if (last < str.length) parts.push(str.slice(last));
    return parts.length > 0 ? parts : str;
  }

  const paragraphs = text.split('\n\n');
  return (
    <div className="content-body">
      {paragraphs.map((para, i) => {
        const lines = para.split('\n');

        // ## heading
        if (lines.length === 1 && lines[0].startsWith('## ')) {
          return <h4 key={i} className="lesson-heading">{lines[0].slice(3)}</h4>;
        }

        if (lines.every(l => l.trim().startsWith('|'))) {
          const [header, ...rows] = lines;
          const cols = header.split('|').filter(Boolean).map(s => s.trim());
          return (
            <table key={i} className="compare-table">
              <thead>
                <tr>{cols.map((c, j) => <th key={j}>{renderInline(c)}</th>)}</tr>
              </thead>
              <tbody>
                {rows.map((row, ri) => (
                  <tr key={ri}>
                    {row.split('|').filter(Boolean).map((cell, ci) => (
                      <td key={ci}>{renderInline(cell.trim())}</td>
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
              {lines.map((l, li) => <li key={li}>{renderInline(l.replace(/^\d+\.\s*/, ''))}</li>)}
            </ol>
          );
        }

        if (lines.every(l => l.trim().startsWith('- '))) {
          return (
            <ul key={i} className="lesson-list">
              {lines.map((l, li) => <li key={li}>{renderInline(l.replace(/^-\s*/, ''))}</li>)}
            </ul>
          );
        }

        return <p key={i}>{renderInline(para)}</p>;
      })}
    </div>
  );
});

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

  // Run state
  const [runOutput, setRunOutput] = useState(null);
  const [runLoading, setRunLoading] = useState(false);
  const [runError, setRunError] = useState('');

  const handleSourceChange = (lang) => {
    setSandboxSource(lang);
    setSandboxCode(exampleCode[lang] || '');
    setSandboxOutput('');
    setSandboxError('');
    setRunOutput(null);
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

  const handleRun = async () => {
    if (!sandboxCode.trim()) return;
    setRunLoading(true);
    setRunOutput(null);
    setRunError('');
    try {
      const result = await runCode(sandboxSource, sandboxCode);
      setRunOutput(result);
    } catch (err) {
      setRunError(err.message || 'Could not reach execution server.');
    } finally {
      setRunLoading(false);
    }
  };

  const handleReset = () => {
    setSandboxCode(exampleCode[sandboxSource] || '');
    setSandboxOutput('');
    setSandboxError('');
    setRunOutput(null);
  };

  const LANG_META = { c: { label: 'C', color: '#6c757d' }, python: { label: 'Python', color: '#3572A5' }, java: { label: 'Java', color: '#b07219' } };

  return (
    <div className="try-it-sandbox">
      <div className="sandbox-header">
        <span className="sandbox-title">Try It</span>
        <div style={{ display: 'flex', gap: 6 }}>
          <button
            className="btn-run"
            onClick={handleRun}
            disabled={runLoading || !sandboxCode.trim() || !canRun(sandboxSource)}
            title="Run code"
          >
            {runLoading ? '⏳' : '▶ Run'}
          </button>
          <button className="btn-reset" onClick={handleReset}>Reset</button>
        </div>
      </div>

      {/* ── Convert bar ── */}
      <div className="sandbox-convert-bar">
        {/* From group */}
        <div className="sandbox-lang-group">
          <span className="sandbox-lang-label">From</span>
          <div className="sandbox-lang-pills">
            {languages.map(lang => {
              const meta = LANG_META[lang] || { label: lang, color: '#555' };
              return (
                <button
                  key={lang}
                  className={`sandbox-lang-pill${sandboxSource === lang ? ' active' : ''}`}
                  style={sandboxSource === lang ? { '--pill-color': meta.color } : {}}
                  onClick={() => handleSourceChange(lang)}
                  title={meta.label}
                >
                  <span
                    className="sandbox-lang-dot"
                    style={{ background: meta.color }}
                  />
                  {meta.label}
                </button>
              );
            })}
          </div>
        </div>

        {/* Arrow + Convert button */}
        <div className="sandbox-convert-center">
          <div className="sandbox-convert-arrow">
            <svg width="36" height="12" viewBox="0 0 36 12" fill="none">
              <path d="M0 6h28M22 1l7 5-7 5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </div>
          <button
            className="btn-convert"
            onClick={handleConvert}
            disabled={sandboxLoading || sandboxSource === sandboxTarget}
            title={sandboxSource === sandboxTarget ? 'Source and target must differ' : 'Convert code'}
          >
            {sandboxLoading ? 'Converting…' : 'Convert'}
          </button>
        </div>

        {/* To group */}
        <div className="sandbox-lang-group">
          <span className="sandbox-lang-label">To</span>
          <div className="sandbox-lang-pills">
            {languages.map(lang => {
              const meta = LANG_META[lang] || { label: lang, color: '#555' };
              return (
                <button
                  key={lang}
                  className={`sandbox-lang-pill${sandboxTarget === lang ? ' active' : ''}${sandboxSource === lang ? ' disabled' : ''}`}
                  style={sandboxTarget === lang ? { '--pill-color': meta.color } : {}}
                  onClick={() => sandboxSource !== lang && setSandboxTarget(lang)}
                  title={sandboxSource === lang ? `Same as source (${meta.label})` : meta.label}
                >
                  <span
                    className="sandbox-lang-dot"
                    style={{ background: meta.color }}
                  />
                  {meta.label}
                </button>
              );
            })}
          </div>
        </div>
      </div>

      {sandboxError && <p className="sandbox-error">{sandboxError}</p>}
      <CodeEditor
        value={sandboxCode}
        onChange={setSandboxCode}
        language={sandboxSource}
        height="200px"
      />
      {/* Run output */}
      {(runOutput !== null || runError) && (
        <div className="run-output run-output-sm">
          <div className="run-output-header">
            <span>Output</span>
            <button className="run-output-close" onClick={() => { setRunOutput(null); setRunError(''); }}>×</button>
          </div>
          {runError && <pre className="run-stderr">{runError}</pre>}
          {runOutput && (
            <>
              {runOutput.stdout && <pre className="run-stdout">{runOutput.stdout}</pre>}
              {runOutput.stderr && <pre className="run-stderr">{runOutput.stderr}</pre>}
              {!runOutput.stdout && !runOutput.stderr && <pre className="run-stdout run-empty">(no output)</pre>}
            </>
          )}
        </div>
      )}
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

function QuizPanel({ lessonId, onPass }) {
  const [quiz, setQuiz] = useState(null);
  const [answers, setAnswers] = useState({});
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(true);
  const [noQuiz, setNoQuiz] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setQuiz(null);
    setAnswers({});
    setResult(null);
    setError('');
    setNoQuiz(false);
    setLoading(true);
    getLessonQuiz(lessonId)
      .then(r => setQuiz(r.data))
      .catch(() => setNoQuiz(true))
      .finally(() => setLoading(false));
  }, [lessonId]);

  const handleSubmit = async () => {
    if (!quiz) return;
    setSubmitting(true);
    try {
      const { data } = await submitQuiz(quiz.id, answers);
      setResult(data);
      if (data.passed && onPass) onPass();
    } catch {
      setError('Failed to submit quiz. Try again.');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return <p style={{ color: 'var(--text-muted)', padding: '20px 0' }}>Loading quiz...</p>;
  }

  if (noQuiz || !quiz) {
    return (
      <div className="quiz-empty">
        <span>No quiz available for this lesson.</span>
      </div>
    );
  }

  const allAnswered = quiz.questions.every(q => answers[q.id]);

  return (
    <div className="quiz-panel">
      <div className="quiz-header">
        <span className="quiz-title">Quiz: {quiz.title}</span>
        {quiz.attempt && !result && (
          <span className={`quiz-badge ${quiz.attempt.passed ? 'quiz-passed' : 'quiz-failed'}`}>
            Previous: {quiz.attempt.score}% {quiz.attempt.passed ? '✓' : '✗'}
          </span>
        )}
      </div>

      {quiz.questions.map(q => {
        const correctId = result?.correct_options?.[String(q.id)];
        const userAnswer = answers[q.id];
        return (
          <div key={q.id} className="quiz-question">
            <p className="quiz-q-text">{q.order}. {q.question_text}</p>
            <div className="quiz-options">
              {q.options.map(opt => {
                let cls = 'quiz-option';
                if (result) {
                  if (opt.id === correctId) cls += ' quiz-correct';
                  else if (opt.id === userAnswer && opt.id !== correctId) cls += ' quiz-wrong';
                } else if (opt.id === userAnswer) {
                  cls += ' quiz-selected';
                }
                const showExplanation = result && opt.id === userAnswer && opt.id !== correctId && opt.explanation;
                return (
                  <div key={opt.id}>
                    <label className={cls}>
                      <input
                        type="radio"
                        name={`q-${q.id}`}
                        value={opt.id}
                        checked={userAnswer === opt.id}
                        onChange={() => !result && setAnswers(prev => ({ ...prev, [q.id]: opt.id }))}
                        disabled={!!result}
                      />
                      {opt.option_text}
                    </label>
                    {showExplanation && (
                      <p className="quiz-option-explanation">{opt.explanation}</p>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        );
      })}

      {!result ? (
        <button
          className="quiz-submit"
          onClick={handleSubmit}
          disabled={!allAnswered || submitting}
        >
          {submitting ? 'Grading...' : 'Submit Quiz'}
        </button>
      ) : (
        <div className="quiz-result">
          <span className={`quiz-score ${result.passed ? 'quiz-passed' : 'quiz-failed'}`}>
            {result.score}% — {result.passed ? 'Passed! ✓' : 'Not passed'}
          </span>
          {!result.passed && (
            <button className="quiz-retry" onClick={() => { setAnswers({}); setResult(null); }}>
              Try Again
            </button>
          )}
        </div>
      )}

      {error && <p className="quiz-error">{error}</p>}
    </div>
  );
}

export default function Learning() {
  const [modules, setModules] = useState([]);
  const [activeModule, setActiveModule] = useState(null);
  const [activeLesson, setActiveLesson] = useState(null);
  const [activeView, setActiveView] = useState('lesson'); // 'lesson' | 'quiz'
  const [filterDifficulty, setFilterDifficulty] = useState('all');
  // Feature 5: Map<lessonId, completionDateISO> instead of Set
  const [completedLessons, setCompletedLessons] = useState(new Map());
  // Feature 2: { [module_title]: completed_count }
  const [completedByModule, setCompletedByModule] = useState({});
  const [modulesLoading, setModulesLoading] = useState(true);
  const [loadError, setLoadError] = useState('');
  const [openingId, setOpeningId] = useState<number | null>(null);

  useEffect(() => {
    Promise.all([getModules(), getProgress()])
      .then(([modRes, progRes]) => {
        setModules(modRes.data);
        const completedRecords = progRes.data.filter(p => p.completed);
        // Feature 5: lesson_id → completion_date
        setCompletedLessons(new Map(completedRecords.map(p => [p.lesson_id, p.completion_date])));
        // Feature 2: count per module title
        const byModule = {};
        completedRecords.forEach(p => {
          byModule[p.module_title] = (byModule[p.module_title] || 0) + 1;
        });
        setCompletedByModule(byModule);
      })
      .catch(() => setLoadError('Could not load learning content. Please refresh.'))
      .finally(() => setModulesLoading(false));
  }, []);

  const openModule = async (id) => {
    setOpeningId(id);
    try {
      const { data } = await getModule(id);
      setActiveModule(data);
      setActiveLesson(data.lessons[0] || null);
      setActiveView('lesson');
    } catch {
      setLoadError('Failed to load module. Please try again.');
    } finally {
      setOpeningId(null);
    }
  };

  const goToNext = () => {
    if (!activeModule) return;
    const idx = activeModule.lessons.findIndex(l => l.id === activeLesson?.id);
    if (idx < activeModule.lessons.length - 1) {
      setActiveLesson(activeModule.lessons[idx + 1]);
      setActiveView('lesson');
    }
  };

  const markComplete = async (lessonId) => {
    try {
      await updateProgress(lessonId);
    } catch {
      // best-effort — progress sync failure doesn't block UI update
    }
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
                  onClick={() => { setActiveLesson(l); setActiveView('lesson'); }}
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
                {/* Tab bar */}
                <div className="lesson-tab-bar">
                  <button
                    className={`lesson-tab${activeView === 'lesson' ? ' active' : ''}`}
                    onClick={() => setActiveView('lesson')}
                  >
                    Lesson
                  </button>
                  <button
                    className={`lesson-tab${activeView === 'quiz' ? ' active' : ''}`}
                    onClick={() => setActiveView('quiz')}
                  >
                    📝 Quiz
                  </button>
                </div>

                {/* Lesson view */}
                {activeView === 'lesson' && (
                  <>
                    <h3>{activeLesson.title}</h3>
                    <ContentRenderer text={activeLesson.content} />
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
                )}

                {/* Quiz view */}
                {activeView === 'quiz' && (
                  <div className="quiz-page-view">
                    <QuizPanel
                      key={`quiz-${activeLesson.id}`}
                      lessonId={activeLesson.id}
                      onPass={() => !completedLessons.has(activeLesson.id) && markComplete(activeLesson.id)}
                    />
                  </div>
                )}
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
        <div className="learn-filter-bar">
          {['all', 'beginner', 'intermediate', 'advanced'].map(level => (
            <button
              key={level}
              className={`learn-filter-pill${filterDifficulty === level ? ' active' : ''}`}
              onClick={() => setFilterDifficulty(level)}
            >
              {level.charAt(0).toUpperCase() + level.slice(1)}
            </button>
          ))}
        </div>
        {modulesLoading && <p style={{ color: 'var(--text-muted)' }}>Loading modules...</p>}
        {loadError && <p style={{ color: 'var(--danger)' }}>{loadError}</p>}
        {!modulesLoading && !loadError && modules.length === 0 && (
          <p style={{ color: 'var(--text-muted)' }}>No modules available yet.</p>
        )}
        <div className="module-grid">
          {modules
            .filter(m => filterDifficulty === 'all' || m.difficulty === filterDifficulty)
            .map(m => (
              <div
                key={m.id}
                className="module-card"
                style={openingId === m.id ? { opacity: 0.5, cursor: 'wait', pointerEvents: 'none' } : undefined}
                onClick={() => openingId === null && openModule(m.id)}>
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
