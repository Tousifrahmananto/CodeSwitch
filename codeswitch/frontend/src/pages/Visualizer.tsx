import { useEffect, useMemo, useRef, useState } from 'react';
import { useLocation } from 'react-router-dom';
import { visualizeCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import { getLanguageMeta } from '../constants/languages';
import type { CSSProperties } from 'react';
import type {
  VisualizationHeapObject,
  VisualizationStep,
  VisualizationTimeline,
  VisualizationTraceStep,
  VisualizationValue,
} from '../types';

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

function isRef(value: VisualizationValue | unknown): value is { $ref: string } {
  return !!value && typeof value === 'object' && '$ref' in value && typeof (value as { $ref?: unknown }).$ref === 'string';
}

function formatTraceValue(value: VisualizationValue | unknown): string {
  if (isRef(value)) return '● ref';
  if (value === null || value === undefined) return 'None';
  if (typeof value === 'string') return `"${value}"`;
  if (typeof value === 'boolean') return value ? 'True' : 'False';
  return String(value);
}

function renderHeapItems(object: VisualizationHeapObject) {
  if (Array.isArray(object.items)) {
    return object.items.map((value, index) => (
      <p key={index} className="viz-heap-item">
        <span>{index}</span>
        <code className={isRef(value) ? 'ref' : ''} data-ref-target={isRef(value) ? value.$ref : undefined}>
          {formatTraceValue(value)}
        </code>
      </p>
    ));
  }
  if (object.items && typeof object.items === 'object') {
    return Object.entries(object.items as Record<string, unknown>).map(([key, value]) => (
      <p key={key} className="viz-heap-item">
        <span>{key}</span>
        <code className={isRef(value) ? 'ref' : ''} data-ref-target={isRef(value) ? value.$ref : undefined}>
          {formatTraceValue(value)}
        </code>
      </p>
    ));
  }
  return <p className="viz-heap-empty">empty</p>;
}

function MemoryTraceBoard({
  step,
  total,
  index,
  codeLines,
}: {
  step?: VisualizationTraceStep;
  total: number;
  index: number;
  codeLines: string[];
}) {
  const memoryRef = useRef<HTMLDivElement | null>(null);
  const [paths, setPaths] = useState<string[]>([]);
  const activeLine = step?.line;

  useEffect(() => {
    const draw = () => {
      const root = memoryRef.current;
      if (!root) return;
      const rootRect = root.getBoundingClientRect();
      const nextPaths: string[] = [];
      root.querySelectorAll<HTMLElement>('[data-ref-target]').forEach(ref => {
        const targetId = ref.dataset.refTarget;
        if (!targetId) return;
        const heapBox = root.querySelector<HTMLElement>(`[data-heap-id="${targetId}"]`);
        if (!heapBox) return;
        const from = ref.getBoundingClientRect();
        const to = heapBox.getBoundingClientRect();
        const x1 = from.right - rootRect.left;
        const y1 = from.top + from.height / 2 - rootRect.top;
        const x2 = to.left - rootRect.left + 6;
        const y2 = to.top + 18 - rootRect.top;
        const mid = Math.max(x1 + 32, x2 - 44);
        nextPaths.push(`M ${x1} ${y1} C ${mid} ${y1}, ${mid} ${y2}, ${x2} ${y2}`);
      });
      setPaths(nextPaths);
    };

    const frame = requestAnimationFrame(draw);
    window.addEventListener('resize', draw);
    const root = memoryRef.current;
    root?.addEventListener('scroll', draw, true);
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener('resize', draw);
      root?.removeEventListener('scroll', draw, true);
    };
  }, [step]);

  return (
    <div className="viz-memory-board">
      <div className="viz-memory-code">
        <div className="viz-tutor-section-title">
          <span>Code</span>
          <small>{activeLine ? `Executing line ${activeLine}` : 'Generate a trace to begin'}</small>
        </div>
        <pre>
          {codeLines.map((line, lineIndex) => {
            const lineNumber = lineIndex + 1;
            return (
              <span key={`${lineNumber}-${line}`} className={activeLine === lineNumber ? 'active' : ''}>
                <b>{activeLine === lineNumber ? '➜' : ' '}</b>
                <em>{lineNumber}</em>
                <code>{line || ' '}</code>
              </span>
            );
          })}
        </pre>
      </div>

      <div className="viz-memory-side">
        <div className="viz-memory-status">
          <span className={step?.event === 'exception' ? 'error' : ''}>
            {step?.event === 'exception' ? 'Exception' : 'Real trace'}
          </span>
          <strong>Step {Math.min(index + 1, total || 1)} / {total || 1}</strong>
          <p>{step?.error?.message || 'Trace generated by executing Python once, then replaying snapshots.'}</p>
        </div>

        <div className="viz-memory-diagram" ref={memoryRef}>
          <svg className="viz-memory-arrows">
            <defs>
              <marker id="vizArrowHead" markerWidth="8" markerHeight="8" refX="7" refY="3" orient="auto">
                <path d="M0,0 L7,3 L0,6 Z" fill="#a78bfa" />
              </marker>
            </defs>
            {paths.map((path, pathIndex) => <path key={pathIndex} d={path} />)}
          </svg>

          <section className="viz-memory-column viz-frame-column">
            <div className="viz-memory-label">Frames</div>
            {step?.frames.length ? step.frames.map(frame => (
              <div key={frame.id} className={`viz-memory-frame${frame.name === '<module>' ? ' global' : ''}`}>
                <strong>{frame.name === '<module>' ? 'Global frame' : frame.name}</strong>
                {Object.keys(frame.variables).length ? Object.entries(frame.variables).map(([name, value]) => (
                  <p key={`${frame.id}-${name}`}>
                    <span>{name}</span>
                    <code className={isRef(value) ? 'ref' : ''} data-ref-target={isRef(value) ? value.$ref : undefined}>
                      {formatTraceValue(value)}
                    </code>
                  </p>
                )) : <p><span>empty</span><code>{'{}'}</code></p>}
              </div>
            )) : <div className="viz-tutor-empty">No frames captured yet.</div>}
          </section>

          <section className="viz-memory-column viz-heap-column">
            <div className="viz-memory-label">Objects / heap</div>
            {step && Object.keys(step.heap).length ? Object.entries(step.heap).map(([id, object]) => (
              <div key={id} className="viz-heap-box" data-heap-id={id}>
                <strong><span>{object.type}</span><small>{id}</small></strong>
                {renderHeapItems(object)}
                {object.repr && <p className="viz-heap-repr">{object.repr}</p>}
              </div>
            )) : <div className="viz-tutor-empty">Lists, dicts, sets, tuples, and objects appear here.</div>}
          </section>
        </div>

        <div className="viz-memory-output">
          <div className="viz-tutor-section-title">
            <span>Output</span>
            <small>stdout so far</small>
          </div>
          <pre>{step?.stdout || '(nothing printed yet)'}</pre>
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

  const traceSteps = timeline?.trace || [];
  const isRealTrace = timeline?.mode === 'execution_trace' && traceSteps.length > 0;
  const activeTraceStep = isRealTrace ? traceSteps[activeIndex] : undefined;
  const activeStep = timeline?.steps[activeIndex];
  const activeLine = activeTraceStep?.line || activeStep?.line;

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
    const totalSteps = isRealTrace ? traceSteps.length : timeline?.steps.length || 0;
    if (!isPlaying || !totalSteps) return;
    intervalRef.current = setInterval(() => {
      setActiveIndex(current => {
        if (current >= totalSteps - 1) {
          setIsPlaying(false);
          return current;
        }
        return current + 1;
      });
    }, speed);
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isPlaying, speed, timeline, isRealTrace, traceSteps.length]);

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

  const stepCount = isRealTrace ? traceSteps.length : timeline?.steps.length || 0;
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
            <span>{isRealTrace ? 'Python Tutor Trace' : 'Animation Canvas'}</span>
            <small>
              {timeline
                ? isRealTrace ? 'Real trace' : 'Concept trace: this explains structure, not runtime memory.'
                : 'Generate a timeline to begin'}
            </small>
          </div>
          {isRealTrace ? (
            <MemoryTraceBoard
              step={activeTraceStep}
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

      {timeline && !isRealTrace && (
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
