import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { visualizeCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import { getLanguageMeta } from '../constants/languages';
import type { CSSProperties } from 'react';
import type { VisualizationStep, VisualizationTimeline } from '../types';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'] as const;
type VisualizerLanguage = (typeof LANGUAGES)[number];
type VisualizerLocationState = {
  language?: string;
  code?: string;
  source?: string;
};

const EXAMPLES: Record<VisualizerLanguage, string> = {
  python: 'total = 0\nfor n in [1, 2, 3]:\n    total = total + n\nprint(total)',
  c: 'int total = 0;\nfor (int n = 1; n <= 3; n++) {\n  total = total + n;\n}\nprintf("%d", total);',
  java: 'public class Main {\n  public static void main(String[] args) {\n    int total = 0;\n    for (int n = 1; n <= 3; n++) {\n      total = total + n;\n    }\n    System.out.println(total);\n  }\n}',
  javascript: 'let total = 0;\nfor (let n of [1, 2, 3]) {\n  total = total + n;\n}\nconsole.log(total);',
  cpp: '#include <iostream>\nusing namespace std;\n\nint main() {\n  int total = 0;\n  for (int n = 1; n <= 3; n++) {\n    total = total + n;\n  }\n  cout << total;\n}',
};

const KIND_META: Record<string, { icon: string; label: string; color: string }> = {
  function: { icon: 'ƒ', label: 'Function', color: '#a78bfa' },
  loop: { icon: '↻', label: 'Loop', color: '#38bdf8' },
  condition: { icon: '?', label: 'Branch', color: '#f59e0b' },
  assignment: { icon: '=', label: 'Variable', color: '#4f8ef7' },
  array: { icon: '[]', label: 'Collection', color: '#34d399' },
  return: { icon: '↩', label: 'Return', color: '#a78bfa' },
  output: { icon: '▸', label: 'Output', color: '#22c55e' },
  call: { icon: '()', label: 'Call', color: '#818cf8' },
  statement: { icon: '•', label: 'Statement', color: '#94a3b8' },
};

function kindMeta(kind: string) {
  return KIND_META[kind] || KIND_META.statement;
}

function langStyle(lang: VisualizerLanguage): CSSProperties & { '--pill-color': string } {
  return { '--pill-color': getLanguageMeta(lang).color };
}

function normalizeIncomingLanguage(language?: string): VisualizerLanguage {
  const normalized = language?.toLowerCase().trim();
  if (normalized === 'js') return 'javascript';
  if (normalized === 'c++') return 'cpp';
  return LANGUAGES.includes(normalized as VisualizerLanguage)
    ? normalized as VisualizerLanguage
    : 'python';
}

function inferLanguageFromCode(code: string, fallback: VisualizerLanguage): VisualizerLanguage {
  const trimmed = code.trim();
  if (/^def\s+\w+\s*\(/m.test(trimmed) || /\bprint\s*\(/.test(trimmed) || /:\n\s+/.test(trimmed)) {
    return 'python';
  }
  if (/\bconsole\.log\s*\(/.test(trimmed) || /\b(let|const|var)\s+\w+/.test(trimmed)) {
    return 'javascript';
  }
  if (/\bpublic\s+class\b|\bSystem\.out\.print/.test(trimmed)) {
    return 'java';
  }
  if (/#include\s*<iostream>|\bstd::|cout\s*<</.test(trimmed)) {
    return 'cpp';
  }
  if (/#include\s*<stdio\.h>|printf\s*\(/.test(trimmed)) {
    return 'c';
  }
  return fallback;
}

function VisualCanvas({ step, total, index }: { step?: VisualizationStep; total: number; index: number }) {
  const meta = kindMeta(step?.kind || 'statement');
  const variables = step?.visual.variables || [];
  const nodes = variables.length ? variables : [{ name: 'code', value: step ? step.kind : 'ready' }];
  const stack = step?.visual.stack || [];
  const output = step?.visual.output || [];

  return (
    <div className="viz-canvas">
      <div className="viz-canvas-glow" style={{ background: meta.color }} />
      <div className={`viz-core viz-pulse-${step?.visual.pulse || step?.kind || 'idle'}`} style={{ borderColor: meta.color }}>
        <span className="viz-core-icon" style={{ color: meta.color }}>{meta.icon}</span>
        <strong>{meta.label}</strong>
        <small>Step {Math.min(index + 1, total || 1)} / {total || 1}</small>
      </div>

      <div className="viz-orbit viz-orbit-a" />
      <div className="viz-orbit viz-orbit-b" />

      <div className="viz-node-cloud">
        {nodes.slice(0, 6).map((variable, i) => (
          <div
            key={`${variable.name}-${i}`}
            className="viz-node"
            style={{
              '--node-color': i === nodes.length - 1 ? meta.color : '#4f8ef7',
              '--node-delay': `${i * 90}ms`,
            } as CSSProperties & { '--node-color': string; '--node-delay': string }}
          >
            <span>{variable.name}</span>
            <code>{variable.value}</code>
          </div>
        ))}
      </div>

      {step?.kind === 'condition' && (
        <div className="viz-branch">
          <span>TRUE</span>
          <span>FALSE</span>
        </div>
      )}

      {step?.kind === 'output' && (
        <div className="viz-output-beam">output</div>
      )}

      {(stack.length > 0 || output.length > 0 || step?.visual.return_value !== undefined) && (
        <div className="viz-python-tutor-panel">
          <div className="viz-stack-panel">
            <span className="viz-panel-title">Stack</span>
            {stack.map(frame => (
              <div key={frame.name} className="viz-frame">
                <strong>{frame.name}</strong>
                {frame.variables.length ? frame.variables.map(variable => (
                  <p key={`${frame.name}-${variable.name}`}>
                    <span>{variable.name}</span>
                    <code>{variable.value}</code>
                  </p>
                )) : <p><span>empty</span><code>{'{}'}</code></p>}
              </div>
            ))}
          </div>
          <div className="viz-output-panel">
            <span className="viz-panel-title">Output</span>
            <pre>{output.length ? output.join('\n') : '(no output yet)'}</pre>
            {step?.visual.return_value !== undefined && (
              <div className="viz-return-value">
                <span>return</span>
                <code>{step.visual.return_value}</code>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

function TutorTraceBoard({
  step,
  total,
  index,
  codeLines,
}: {
  step?: VisualizationStep;
  total: number;
  index: number;
  codeLines: string[];
}) {
  const meta = kindMeta(step?.kind || 'statement');
  const stack = step?.visual.stack || [];
  const output = step?.visual.output || [];
  const activeLine = step?.line;

  return (
    <div className="viz-tutor-board">
      <div className="viz-tutor-code">
        <div className="viz-tutor-section-title">
          <span>Code</span>
          <small>{activeLine ? `Now executing line ${activeLine}` : 'Generate a trace to begin'}</small>
        </div>
        <pre>
          {codeLines.map((line, lineIndex) => {
            const lineNumber = lineIndex + 1;
            const active = activeLine === lineNumber;
            return (
              <span key={`${lineNumber}-${line}`} className={active ? 'active' : ''}>
                <b>{active ? '➜' : ' '}</b>
                <em>{lineNumber}</em>
                <code>{line || ' '}</code>
              </span>
            );
          })}
        </pre>
      </div>

      <div className="viz-tutor-state">
        <div className="viz-tutor-explainer" style={{ '--step-color': meta.color } as CSSProperties & { '--step-color': string }}>
          <div>
            <span>{kindMeta(step?.kind || 'statement').label}</span>
            <strong>{step?.title || 'Ready to trace'}</strong>
          </div>
          <p>{step?.description || 'Generate the animation to walk through the code one executed step at a time.'}</p>
          <small>Step {Math.min(index + 1, total || 1)} of {total || 1}</small>
        </div>

        <div className="viz-tutor-memory">
          <div className="viz-tutor-section-title">
            <span>Frames / Variables</span>
            <small>call stack</small>
          </div>
          {stack.length ? stack.map((frame, frameIndex) => (
            <div key={`${frame.name}-${frameIndex}`} className="viz-tutor-frame">
              <strong>{frame.name}</strong>
              {frame.variables.length ? frame.variables.map(variable => (
                <p key={`${frame.name}-${variable.name}`}>
                  <span>{variable.name}</span>
                  <code>{variable.value}</code>
                </p>
              )) : (
                <p>
                  <span>empty</span>
                  <code>{'{}'}</code>
                </p>
              )}
            </div>
          )) : (
            <div className="viz-tutor-empty">No frame data yet.</div>
          )}
        </div>

        <div className="viz-tutor-output">
          <div className="viz-tutor-section-title">
            <span>Output</span>
            <small>printed text</small>
          </div>
          <pre>{output.length ? output.join('\n') : '(nothing printed yet)'}</pre>
          {step?.visual.return_value !== undefined && (
            <div className="viz-tutor-return">
              <span>return value</span>
              <code>{step.visual.return_value}</code>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function Visualizer() {
  const location = useLocation();
  const incomingState = location.state as VisualizerLocationState | null;
  const initialLanguage = normalizeIncomingLanguage(incomingState?.language);
  const initialCode = typeof incomingState?.code === 'string' && incomingState.code.trim()
    ? incomingState.code
    : EXAMPLES[initialLanguage];

  const [language, setLanguage] = useState<VisualizerLanguage>(initialLanguage);
  const [code, setCode] = useState(initialCode);
  const [timeline, setTimeline] = useState<VisualizationTimeline | null>(null);
  const [activeIndex, setActiveIndex] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [speed, setSpeed] = useState(900);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const activeStep = timeline?.steps[activeIndex];
  const activeLine = activeStep?.line;

  const codeLines = useMemo(() => code.split('\n'), [code]);

  useEffect(() => {
    if (!incomingState?.code || typeof incomingState.code !== 'string') return;
    const nextLanguage = normalizeIncomingLanguage(incomingState.language);
    setLanguage(nextLanguage);
    setCode(incomingState.code);
    setTimeline(null);
    setActiveIndex(0);
    setIsPlaying(false);
    setError('');
  }, [incomingState?.code, incomingState?.language]);

  useEffect(() => {
    if (!isPlaying || !timeline?.steps.length) return;
    intervalRef.current = setInterval(() => {
      setActiveIndex(current => {
        if (current >= timeline.steps.length - 1) {
          setIsPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, speed);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, speed, timeline]);

  const handleLanguageChange = (next: VisualizerLanguage) => {
    setLanguage(next);
    setCode(EXAMPLES[next]);
    setTimeline(null);
    setActiveIndex(0);
    setIsPlaying(false);
    setError('');
  };

  const handleGenerate = async () => {
    if (!code.trim()) {
      setError('Please enter code to visualize.');
      return;
    }
    const detectedLanguage = inferLanguageFromCode(code, language);
    if (detectedLanguage !== language) {
      setLanguage(detectedLanguage);
    }
    setLoading(true);
    setError('');
    setIsPlaying(false);
    try {
      const { data } = await visualizeCode({ language: detectedLanguage, code });
      setTimeline(data);
      setActiveIndex(0);
    } catch (err: unknown) {
      const axiosErr = err as { response?: { data?: { error?: string } } };
      setError(axiosErr.response?.data?.error || 'Could not generate visualization.');
    } finally {
      setLoading(false);
    }
  };

  const stepCount = timeline?.steps.length || 0;
  const progress = stepCount > 1 ? (activeIndex / (stepCount - 1)) * 100 : 0;
  const isExecutionTrace = timeline?.mode === 'execution_trace';

  return (
    <div className="viz-page">
      <div className="viz-hero">
        <div>
          <p className="viz-eyebrow">Interactive Code Visualizer</p>
          <h2>Watch your code come alive.</h2>
          <p>Generate a step-by-step animated story of variables, loops, branches, outputs, and beginner-friendly concepts.</p>
        </div>
        <button className="viz-generate" onClick={handleGenerate} disabled={loading || !code.trim()}>
          {loading ? 'Generating…' : 'Generate Animation'}
        </button>
      </div>

      <div className="viz-language-row">
        {LANGUAGES.map(lang => (
          <button
            key={lang}
            className={`sandbox-lang-pill${language === lang ? ' active' : ''}`}
            style={langStyle(lang)}
            onClick={() => handleLanguageChange(lang)}
          >
            <span className="sandbox-lang-dot" />
            {getLanguageMeta(lang).label}
          </button>
        ))}
      </div>

      {error && <p className="viz-error">{error}</p>}

      <div className="viz-grid">
        <section className="viz-card viz-editor-card">
          <div className="viz-card-header">
            <span>Code Input</span>
            <small>{getLanguageMeta(language).label}</small>
          </div>
          <CodeEditor
            value={code}
            onChange={value => {
              setCode(value ?? '');
              setTimeline(null);
              setActiveIndex(0);
              setIsPlaying(false);
              setError('');
            }}
            language={language}
            height="460px"
            theme="vs-dark"
          />
        </section>

        <section className="viz-card">
          <div className="viz-card-header">
            <span>{isExecutionTrace ? 'Tutor Trace' : 'Animation Canvas'}</span>
            <small>{timeline?.summary || 'Generate a timeline to begin'}</small>
          </div>
          {isExecutionTrace ? (
            <TutorTraceBoard
              step={activeStep}
              total={stepCount}
              index={activeIndex}
              codeLines={codeLines}
            />
          ) : (
            <VisualCanvas step={activeStep} total={stepCount} index={activeIndex} />
          )}

          <div className="viz-controls">
            <button onClick={() => setActiveIndex(0)} disabled={!stepCount}>Reset</button>
            <button onClick={() => setActiveIndex(i => Math.max(0, i - 1))} disabled={!stepCount || activeIndex === 0}>Prev</button>
            <button className="viz-play" onClick={() => setIsPlaying(p => !p)} disabled={!stepCount}>
              {isPlaying ? 'Pause' : 'Play'}
            </button>
            <button onClick={() => setActiveIndex(i => Math.min(stepCount - 1, i + 1))} disabled={!stepCount || activeIndex >= stepCount - 1}>Next</button>
            <select value={speed} onChange={e => setSpeed(Number(e.target.value))}>
              <option value={1300}>Slow</option>
              <option value={900}>Normal</option>
              <option value={550}>Fast</option>
            </select>
          </div>
          <div className="viz-progress"><span style={{ width: `${progress}%` }} /></div>
        </section>
      </div>

      {timeline && (
        <div className="viz-lower-grid">
          <section className="viz-card">
            <div className="viz-card-header">
              <span>Step Timeline</span>
              <small>{stepCount} steps</small>
            </div>
            <div className="viz-timeline">
              {timeline.steps.map((step, index) => {
                const meta = kindMeta(step.kind);
                return (
                  <button
                    key={step.id}
                    className={`viz-step${index === activeIndex ? ' active' : ''}`}
                    onClick={() => { setActiveIndex(index); setIsPlaying(false); }}
                    style={{ '--step-color': meta.color } as CSSProperties & { '--step-color': string }}
                  >
                    <span>{step.line}</span>
                    <div>
                      <strong>{step.title}</strong>
                      <small>{step.description}</small>
                      <code>{step.code}</code>
                    </div>
                  </button>
                );
              })}
            </div>
          </section>

          <section className="viz-card">
            <div className="viz-card-header">
              <span>Code Focus</span>
              <small>{activeLine ? `Line ${activeLine}` : 'No active line'}</small>
            </div>
            <pre className="viz-code-focus">
              {codeLines.map((line, index) => (
                <span key={`${index}-${line}`} className={activeLine === index + 1 ? 'active' : ''}>
                  <em>{index + 1}</em>{line || ' '}
                </span>
              ))}
            </pre>

            <div className="viz-concepts">
              <h3>Detected concepts</h3>
              <div>
                {timeline.concepts.map(concept => <span key={concept}>{concept}</span>)}
              </div>
            </div>

            <div className="viz-concepts">
              <h3>Recommended lessons</h3>
              <div>
                {timeline.recommendations.length
                  ? timeline.recommendations.map(item => <span key={item}>{item}</span>)
                  : <span>More patterns needed</span>}
              </div>
            </div>
          </section>
        </div>
      )}
    </div>
  );
}
