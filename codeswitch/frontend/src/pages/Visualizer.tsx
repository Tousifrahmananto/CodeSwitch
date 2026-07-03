import { useEffect, useMemo, useRef, useState } from 'react';
import { visualizeCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import { getLanguageMeta } from '../constants/languages';
import type { CSSProperties } from 'react';
import type { VisualizationStep, VisualizationTimeline } from '../types';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'] as const;
type VisualizerLanguage = (typeof LANGUAGES)[number];

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
  return: { icon: '↩', label: 'Return', color: '#fb7185' },
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

function VisualCanvas({ step, total, index }: { step?: VisualizationStep; total: number; index: number }) {
  const meta = kindMeta(step?.kind || 'statement');
  const variables = step?.visual.variables || [];
  const nodes = variables.length ? variables : [{ name: 'code', value: step ? step.kind : 'ready' }];

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
    </div>
  );
}

export default function Visualizer() {
  const [language, setLanguage] = useState<VisualizerLanguage>('python');
  const [code, setCode] = useState(EXAMPLES.python);
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
    setLoading(true);
    setError('');
    setIsPlaying(false);
    try {
      const { data } = await visualizeCode({ language, code });
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
            onChange={value => setCode(value ?? '')}
            language={language}
            height="460px"
            theme="vs-dark"
          />
        </section>

        <section className="viz-card">
          <div className="viz-card-header">
            <span>Animation Canvas</span>
            <small>{timeline?.summary || 'Generate a timeline to begin'}</small>
          </div>
          <VisualCanvas step={activeStep} total={stepCount} index={activeIndex} />

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
