import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import type { CSSProperties } from 'react';

// ─── Demo sequences shown in the hero code window ─────────────────────────────
const DEMOS = [
  {
    from: { lang: 'Python', color: '#3b82f6' },
    fromCode: `def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(5))`,
    to: { lang: 'Java', color: '#f59e0b' },
    toCode: `public static int factorial(int n) {\n    if (n <= 1) return 1;\n    return n * factorial(n - 1);\n}\n\nSystem.out.println(factorial(5));`,
  },
  {
    from: { lang: 'Java', color: '#f59e0b' },
    fromCode: `for (int i = 0; i < 5; i++) {\n    System.out.println(\n        "Item " + i);\n}`,
    to: { lang: 'Python', color: '#3b82f6' },
    toCode: `for i in range(5):\n    print(f"Item {i}")`,
  },
  {
    from: { lang: 'C', color: '#10b981' },
    fromCode: `int sum(int arr[], int n) {\n    int total = 0;\n    for (int i = 0; i < n; i++)\n        total += arr[i];\n    return total;\n}`,
    to: { lang: 'Python', color: '#3b82f6' },
    toCode: `def sum_arr(arr):\n    total = 0\n    for x in arr:\n        total += x\n    return total`,
  },
];

// ─── Static feature card data ─────────────────────────────────────────────────
const FEATURES = [
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polyline points="16 18 22 12 16 6" />
        <polyline points="8 6 2 12 8 18" />
      </svg>
    ),
    title: 'AI-Powered Conversion',
    desc: 'Convert code between Python, Java, and C with AI accuracy. A rule-based fallback engine ensures conversions always work, even offline.',
    accent: '#7c6af7',
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    ),
    title: '13 Learning Modules',
    desc: 'Structured curriculum from Python basics to graph algorithms. Interactive examples, live sandbox, and per-lesson progress tracking.',
    accent: '#3b82f6',
  },
  {
    icon: (
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z" />
      </svg>
    ),
    title: 'Cloud File Manager',
    desc: 'Save and revisit your code from anywhere. Supports Python, Java, C, and JavaScript files with a built-in Monaco editor.',
    accent: '#10b981',
  },
];

// ─── Learning module list ──────────────────────────────────────────────────────
const MODULES = [
  { n: '01', name: 'Python Basics', tag: 'Beginner' },
  { n: '02', name: 'Strings & I/O', tag: 'Beginner' },
  { n: '03', name: 'Data Structures', tag: 'Intermediate' },
  { n: '04', name: 'OOP Concepts', tag: 'Intermediate' },
  { n: '05', name: 'Error Handling', tag: 'Advanced' },
  { n: '06', name: 'Algorithms', tag: 'Advanced' },
  { n: '07', name: 'Advanced Sorting', tag: 'Intermediate' },
  { n: '08', name: 'Dynamic Programming', tag: 'Advanced' },
  { n: '09', name: 'Graph Algorithms', tag: 'Advanced' },
  { n: '10', name: 'Pointers & Memory', tag: 'Intermediate' },
  { n: '11', name: 'Linked Lists', tag: 'Intermediate' },
  { n: '12', name: 'Stacks & Queues', tag: 'Intermediate' },
  { n: '13', name: 'Hash Tables & Dicts', tag: 'Intermediate' },
] as const;

type ModuleTag = (typeof MODULES)[number]['tag'];

const TAG_COLORS: Record<ModuleTag, { text: string; bg: string; border: string }> = {
  Beginner: { text: '#10b981', bg: '#10b98112', border: '#10b98140' },
  Intermediate: { text: '#f59e0b', bg: '#f59e0b12', border: '#f59e0b40' },
  Advanced: { text: '#f38ba8', bg: '#f38ba812', border: '#f38ba840' },
};

interface LandingProps {
  onGetStarted?: () => void;
}

const featureCardStyle = (accent: string, delay: number): CSSProperties & { '--accent': string } => ({
  '--accent': accent,
  animationDelay: `${delay}s`,
});

// ─── Animated code demo component ─────────────────────────────────────────────
function CodeDemo() {
  const [demoIdx, setDemoIdx] = useState(0);
  const [phase, setPhase] = useState('showing-input');
  // 'showing-input' → 'converting' → 'typing-output' → 'pausing' → 'transitioning'
  const [typedOutput, setTypedOutput] = useState('');
  const [visible, setVisible] = useState(true);

  const demo = DEMOS[demoIdx];

  // Phase state machine
  useEffect(() => {
    let t: ReturnType<typeof setTimeout> | undefined;
    if (phase === 'showing-input') {
      t = setTimeout(() => setPhase('converting'), 1800);
    } else if (phase === 'converting') {
      t = setTimeout(() => {
        setTypedOutput('');
        setPhase('typing-output');
      }, 1300);
    } else if (phase === 'pausing') {
      t = setTimeout(() => {
        setVisible(false);
        setPhase('transitioning');
      }, 2400);
    } else if (phase === 'transitioning') {
      t = setTimeout(() => {
        setDemoIdx(i => (i + 1) % DEMOS.length);
        setTypedOutput('');
        setVisible(true);
        setPhase('showing-input');
      }, 450);
    }
    return () => clearTimeout(t);
  }, [phase]);

  // Typewriter for output code
  useEffect(() => {
    if (phase !== 'typing-output') return;
    const text = demo.toCode;
    let i = 0;
    setTypedOutput('');
    const id = setInterval(() => {
      i++;
      setTypedOutput(text.slice(0, i));
      if (i >= text.length) {
        clearInterval(id);
        setTimeout(() => setPhase('pausing'), 350);
      }
    }, 18);
    return () => clearInterval(id);
  }, [phase, demo.toCode]);

  const isConverting = phase === 'converting';
  const showOutput = phase === 'typing-output' || phase === 'pausing' || phase === 'transitioning';

  return (
    <div className={`land-demo${visible ? '' : ' land-demo-hidden'}`}>

      {/* macOS-style title bar */}
      <div className="land-demo-bar">
        <div className="land-demo-dots-bar">
          <span className="demo-traffic-dot" style={{ background: '#f38ba8' }} />
          <span className="demo-traffic-dot" style={{ background: '#f9e2af' }} />
          <span className="demo-traffic-dot" style={{ background: '#a6e3a1' }} />
        </div>
        <span className="land-demo-title">CodeSwitch — Live Preview</span>
        <span />
      </div>

      {/* Editor panels */}
      <div className="land-demo-body">

        {/* Input panel */}
        <div className="land-demo-panel">
          <div className="land-demo-panel-hdr">
            <span className="land-demo-lang-chip" style={{ color: demo.from.color, borderColor: demo.from.color + '44', background: demo.from.color + '14' }}>
              {demo.from.lang}
            </span>
            <span className="land-demo-panel-label">Input</span>
          </div>
          <pre className="land-demo-code">{demo.fromCode}</pre>
        </div>

        {/* Center divider — arrow or spinner */}
        <div className="land-demo-mid">
          {isConverting ? (
            <div className="land-converting-wrap">
              <span className="land-demo-spinner" />
              <span className="land-converting-label">Converting</span>
            </div>
          ) : (
            <div className="land-arrow-wrap">
              <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </div>
          )}
        </div>

        {/* Output panel */}
        <div className="land-demo-panel">
          <div className="land-demo-panel-hdr">
            <span className="land-demo-lang-chip" style={{ color: demo.to.color, borderColor: demo.to.color + '44', background: demo.to.color + '14' }}>
              {demo.to.lang}
            </span>
            <span className="land-demo-panel-label">Output</span>
          </div>
          <pre className="land-demo-code land-demo-output-code">
            {showOutput
              ? typedOutput
              : <span className="land-demo-placeholder">Awaiting conversion...</span>
            }
            {phase === 'typing-output' && <span className="land-cursor-blink">▌</span>}
          </pre>
        </div>
      </div>

      {/* Cycle indicator dots */}
      <div className="land-demo-nav-dots">
        {DEMOS.map((_, i) => (
          <span key={i} className={`land-nav-dot${i === demoIdx ? ' active' : ''}`} />
        ))}
      </div>
    </div>
  );
}

// ─── Main Landing page ────────────────────────────────────────────────────────
export default function Landing({ onGetStarted }: LandingProps) {
  const navigate = useNavigate();
  const featuresRef = useRef(null);
  const modulesRef = useRef(null);
  const [featuresIn, setFeaturesIn] = useState(false);
  const [modulesIn, setModulesIn] = useState(false);

  useEffect(() => {
    document.title = 'CodeSwitch | Convert Code Between Python, Java & C';
  }, []);

  const goToPlayground = () => navigate('/playground');

  // Intersection observers for scroll-triggered animations
  useEffect(() => {
    const opts = { threshold: 0.12 };
    const obs = new IntersectionObserver((entries) => {
      entries.forEach(e => {
        if (e.isIntersecting) {
          if (e.target === featuresRef.current) setFeaturesIn(true);
          if (e.target === modulesRef.current) setModulesIn(true);
        }
      });
    }, opts);
    if (featuresRef.current) obs.observe(featuresRef.current);
    if (modulesRef.current) obs.observe(modulesRef.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div className="relative overflow-hidden min-h-screen">

      {/* ── Decorative background ── */}
      <div className="land-bg-grid" aria-hidden="true" />
      <div className="land-orb land-orb-1" aria-hidden="true" />
      <div className="land-orb land-orb-2" aria-hidden="true" />

      {/* ── Navbar ── */}
      <nav className="sticky top-0 z-50 flex items-center justify-between px-4 sm:px-8 py-4 border-b border-border bg-bg/80 backdrop-blur">
        <div className="flex items-center gap-2.5">
          <Logo size={30} id="nav" />
          <span className="font-bold text-base text-primary">CodeSwitch</span>
        </div>
        <div className="hidden sm:flex items-center gap-6">
          <a href="#features" className="land-nav-link">Features</a>
          <a href="#modules" className="land-nav-link">Modules</a>
        </div>
        <div className="flex items-center gap-2">
          <button
            className="hidden sm:inline-flex bg-transparent border border-border text-primary hover:bg-border rounded px-4 py-1.5 text-sm font-medium transition-colors"
            onClick={goToPlayground}
          >Try Playground</button>
          <button
            className="hidden sm:inline-flex bg-transparent border border-border text-primary hover:bg-border rounded px-4 py-1.5 text-sm font-medium transition-colors"
            onClick={() => onGetStarted?.()}
          >Sign In</button>
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-4 py-1.5 text-sm font-semibold transition-colors"
            onClick={() => onGetStarted?.()}
          >Get Started</button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="land-hero">
        <div className="land-hero-text land-fade-up">
          <div className="land-hero-badge">
            <span className="land-badge-pulse" />
            AI-Powered · Free to Use · Open Source
          </div>

          <h1 className="text-4xl font-bold leading-tight mt-0 mb-5">
            Translate Code<br />
            <span className="text-accent">Between Languages</span><br />
            Instantly
          </h1>

          <p className="text-muted text-base leading-relaxed mt-0 mb-8">
            CodeSwitch converts Python, Java, and C with AI accuracy.
            Learn programming with 13 structured modules, manage your
            files in the cloud, and track your progress — all in one place.
          </p>

          <div className="flex items-center gap-3 flex-wrap">
            <button
              className="bg-accent hover:bg-accent-h text-white border-none rounded px-6 py-3 text-sm font-semibold transition-colors inline-flex items-center gap-2"
              onClick={() => onGetStarted?.()}
            >
              Start for Free
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 12h14M12 5l7 7-7 7" />
              </svg>
            </button>
            <button
              className="bg-transparent border border-border text-primary hover:bg-border/50 rounded px-6 py-3 text-sm font-medium transition-colors inline-flex items-center gap-2"
              onClick={goToPlayground}
            >
              Try Playground
              <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M5 3l14 9-14 9V3z" />
              </svg>
            </button>
          </div>

          <div className="flex items-center flex-wrap gap-2 mt-1">
            {['Django', 'React 18', 'Monaco Editor', 'JWT Auth', 'Groq / OpenAI'].map(t => (
              <span key={t} className="text-xs text-muted border border-border rounded px-2.5 py-1 font-mono">{t}</span>
            ))}
          </div>
        </div>

        <div className="land-hero-demo land-fade-up land-delay-1">
          <CodeDemo />
        </div>
      </section>

      {/* ── Stats strip ── */}
      <div className="flex flex-wrap items-center justify-center gap-6 sm:gap-12 py-6 border-y border-border bg-surface/50 land-fade-up land-delay-2">
        {[
          { value: '5', label: 'Languages Supported' },
          { value: '13', label: 'Learning Modules' },
          { value: '50+', label: 'Reference Cards' },
          { value: 'AI', label: 'Powered Engine' },
        ].map(s => (
          <div key={s.label} className="flex flex-col items-center gap-1">
            <span className="text-2xl font-bold text-accent">{s.value}</span>
            <span className="text-xs text-muted">{s.label}</span>
          </div>
        ))}
      </div>

      {/* ── Features ── */}
      <section
        id="features"
        className={`land-features-section${featuresIn ? ' animate-in' : ''}`}
        ref={featuresRef}
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold m-0 mb-2">Everything you need to learn and convert code</h2>
          <p className="text-muted text-sm m-0">Three core tools built for CS students and developers.</p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5 px-4 sm:px-8 max-w-5xl mx-auto">
          {FEATURES.map((f, i) => (
            <div
              key={f.title}
              className="land-feat-card"
              style={featureCardStyle(f.accent, i * 0.13)}
            >
              <div
                className="w-11 h-11 rounded-lg flex items-center justify-center mb-4"
                style={{ color: f.accent, background: f.accent + '18' }}
              >
                {f.icon}
              </div>
              <h3 className="text-base font-semibold mb-2 m-0">{f.title}</h3>
              <p className="text-sm text-muted leading-relaxed m-0">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* ── Product Preview ── */}
      <section className="py-16 px-4 sm:px-8">
        <div className="text-center mb-10">
          <h2 className="text-2xl font-bold m-0 mb-2">See it in action</h2>
          <p className="text-muted text-sm m-0">AI-powered conversion inside a full Monaco editor — no downloads needed.</p>
        </div>

        <div className="land-browser-mock max-w-4xl mx-auto">
          {/* Browser chrome */}
          <div className="land-browser-bar">
            <div className="flex gap-1.5 flex-shrink-0">
              <span className="w-3 h-3 rounded-full" style={{ background: '#f38ba8' }} />
              <span className="w-3 h-3 rounded-full" style={{ background: '#f9e2af' }} />
              <span className="w-3 h-3 rounded-full" style={{ background: '#a6e3a1' }} />
            </div>
            <div className="flex-1 flex justify-center">
              <span className="text-xs text-muted bg-bg/60 rounded px-3 py-1 border border-border font-mono">
                🔒 code-switch-learntoconquer.vercel.app/converter
              </span>
            </div>
            <div className="w-16 flex-shrink-0" />
          </div>

          {/* App body */}
          <div className="flex overflow-hidden" style={{ height: '260px' }}>
            {/* Mock sidebar */}
            <div className="land-mock-sidebar">
              <div className="flex items-center gap-2 mb-4 px-1">
                <Logo size={18} id="mock-brand" />
                <span className="text-xs font-bold">CodeSwitch</span>
              </div>
              {['🏠 Dashboard', '💻 Converter', '📁 Files', '📚 Learn', '📖 Reference'].map((item, i) => (
                <div key={item} className={`land-mock-nav-item${i === 1 ? ' active' : ''}`}>{item}</div>
              ))}
            </div>

            {/* Converter panel */}
            <div className="flex-1 p-4 overflow-hidden flex flex-col gap-3" style={{ background: 'var(--bg)' }}>
              <div className="flex items-center gap-3 flex-wrap">
                <span className="text-xs text-muted">From</span>
                <span className="land-mock-pill" style={{ color: '#3b82f6', background: '#3b82f614', borderColor: '#3b82f640' }}>● Python</span>
                <span className="text-muted text-sm">→</span>
                <span className="bg-accent text-white text-xs font-semibold rounded px-3 py-1">Convert</span>
                <span className="text-muted text-sm">→</span>
                <span className="text-xs text-muted">To</span>
                <span className="land-mock-pill" style={{ color: '#f59e0b', background: '#f59e0b14', borderColor: '#f59e0b40' }}>● Java</span>
                <span className="ml-auto text-xs font-semibold rounded px-2 py-0.5" style={{ background: 'rgba(124,106,247,0.15)', color: 'var(--accent)', border: '1px solid var(--accent)' }}>✦ AI-powered</span>
              </div>

              <div className="grid grid-cols-2 gap-3 flex-1 min-h-0">
                <div className="land-mock-code-panel">
                  <div className="land-mock-panel-hdr" style={{ color: '#3b82f6' }}>Python · Input</div>
                  <pre className="land-mock-code">
                    <span style={{ color: '#c678dd' }}>def</span><span style={{ color: '#61afef' }}> factorial</span><span>(n):</span>{'\n'}
                    <span style={{ color: '#c678dd' }}>    if</span><span> n </span><span style={{ color: '#56b6c2' }}>{'<='}</span><span style={{ color: '#d19a66' }}> 1</span><span>: </span><span style={{ color: '#c678dd' }}>return</span><span style={{ color: '#d19a66' }}> 1</span>{'\n'}
                    <span style={{ color: '#c678dd' }}>    return</span><span> n </span><span style={{ color: '#56b6c2' }}>*</span><span style={{ color: '#61afef' }}> factorial</span><span>(n</span><span style={{ color: '#56b6c2' }}>-</span><span style={{ color: '#d19a66' }}>1</span><span>)</span>
                  </pre>
                </div>
                <div className="land-mock-code-panel">
                  <div className="land-mock-panel-hdr" style={{ color: '#f59e0b' }}>Java · Output</div>
                  <pre className="land-mock-code">
                    <span style={{ color: '#c678dd' }}>public static int</span><span style={{ color: '#61afef' }}> factorial</span><span>(</span><span style={{ color: '#c678dd' }}>int</span><span> n) {'{'}</span>{'\n'}
                    <span style={{ color: '#c678dd' }}>    if</span><span> (n </span><span style={{ color: '#56b6c2' }}>{'<='}</span><span style={{ color: '#d19a66' }}> 1</span><span>) </span><span style={{ color: '#c678dd' }}>return</span><span style={{ color: '#d19a66' }}> 1</span><span>;</span>{'\n'}
                    <span style={{ color: '#c678dd' }}>    return</span><span> n </span><span style={{ color: '#56b6c2' }}>*</span><span style={{ color: '#61afef' }}> factorial</span><span>(n</span><span style={{ color: '#56b6c2' }}>-</span><span style={{ color: '#d19a66' }}>1</span><span>);</span>{'\n'}
                    <span>{'}'}</span>
                  </pre>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── Modules ── */}
      <section
        id="modules"
        className={`land-modules-section${modulesIn ? ' animate-in' : ''}`}
        ref={modulesRef}
      >
        <div className="text-center mb-8">
          <h2 className="text-2xl font-bold m-0 mb-2">13 modules — from basics to algorithms</h2>
          <p className="text-muted text-sm m-0">Structured learning with interactive examples and progress tracking.</p>
        </div>

        <div className="grid gap-2 px-4 sm:px-8 max-w-3xl mx-auto">
          {MODULES.map((m, i) => {
            const tc = TAG_COLORS[m.tag];
            return (
              <div
                key={m.n}
                className="land-module-row"
                style={{ animationDelay: `${i * 0.055}s` }}
              >
                <span className="text-xs font-mono text-muted w-8 flex-shrink-0">{m.n}</span>
                <span className="text-sm font-medium flex-1">{m.name}</span>
                <span
                  className="text-[11px] font-semibold px-2.5 py-0.5 rounded border flex-shrink-0"
                  style={{ color: tc.text, background: tc.bg, borderColor: tc.border }}
                >
                  {m.tag}
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── CTA ── */}
      <section className="py-20 px-8 text-center">
        <div className="max-w-lg mx-auto flex flex-col items-center gap-4">
          <Logo size={52} id="cta" />
          <h2 className="text-2xl font-bold m-0">Ready to switch languages?</h2>
          <p className="text-muted text-sm m-0 leading-relaxed">
            Join students and developers already using CodeSwitch to learn,
            convert, and build.
          </p>
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-6 py-3 text-sm font-semibold transition-colors inline-flex items-center gap-2"
            onClick={() => onGetStarted?.()}
          >
            Create Free Account
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-8 px-8 border-t border-border text-center flex flex-col gap-2">
        <div className="flex items-center justify-center gap-2 mb-1">
          <Logo size={22} id="footer" />
          <span className="font-semibold text-sm">CodeSwitch</span>
        </div>
        <p className="text-xs text-muted m-0">
          Built with Django, React 18, and Monaco Editor. A full-stack project for code learning and translation.
        </p>
        <p className="text-xs text-muted m-0">
          &copy; {new Date().getFullYear()} CodeSwitch — Made for the open-source community.
        </p>
      </footer>

    </div>
  );
}
