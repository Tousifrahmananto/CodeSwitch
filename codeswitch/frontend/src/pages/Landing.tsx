import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import Logo from '../components/Logo';
import type { CSSProperties, PointerEvent as ReactPointerEvent } from 'react';

// ─── Demo sequences shown in the hero code window ─────────────────────────────
const DEMOS = [
  {
    from: { lang: 'Python', color: '#4b8bbe' },
    fromCode: `def factorial(n):\n    if n <= 1:\n        return 1\n    return n * factorial(n - 1)\n\nprint(factorial(5))`,
    to: { lang: 'Java', color: '#f89820' },
    toCode: `public static int factorial(int n) {\n    if (n <= 1) return 1;\n    return n * factorial(n - 1);\n}\n\nSystem.out.println(factorial(5));`,
  },
  {
    from: { lang: 'Java', color: '#f89820' },
    fromCode: `for (int i = 0; i < 5; i++) {\n    System.out.println(\n        "Item " + i);\n}`,
    to: { lang: 'Python', color: '#4b8bbe' },
    toCode: `for i in range(5):\n    print(f"Item {i}")`,
  },
  {
    from: { lang: 'C', color: '#a8b9cc' },
    fromCode: `int sum(int arr[], int n) {\n    int total = 0;\n    for (int i = 0; i < n; i++)\n        total += arr[i];\n    return total;\n}`,
    to: { lang: 'Python', color: '#4b8bbe' },
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
    accent: '#e86c2f',
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
    accent: '#c9a84c',
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

const LANGUAGE_ACCENTS = [
  { name: 'Python', color: '#4b8bbe' },
  { name: 'C', color: '#a8b9cc' },
  { name: 'C++', color: '#659ad2' },
  { name: 'Java', color: '#f89820' },
  { name: 'JavaScript', color: '#f7df1e' },
] as const;

interface LandingProps {
  onGetStarted?: () => void;
}

const featureCardStyle = (accent: string, delay: number): CSSProperties & { '--accent': string } => ({
  '--accent': accent,
  animationDelay: `${delay}s`,
});

// ─── Animated code demo component ─────────────────────────────────────────────
function CodeDemo() {
  const [demoIdx, setDemoIdx] = useState(2);
  const [visible, setVisible] = useState(true);

  const demo = DEMOS[demoIdx];

  useEffect(() => {
    let transitionTimer: ReturnType<typeof setTimeout> | undefined;
    const cycleTimer = setInterval(() => {
      setVisible(false);
      transitionTimer = setTimeout(() => {
        setDemoIdx(i => (i + 1) % DEMOS.length);
        setVisible(true);
      }, 320);
    }, 6500);
    return () => {
      clearInterval(cycleTimer);
      clearTimeout(transitionTimer);
    };
  }, []);

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

        {/* Finished conversion state: one clear input-to-output flow */}
        <div className="land-demo-mid">
          <div className="land-arrow-wrap">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--accent)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </div>
        </div>

        {/* Output panel */}
        <div className="land-demo-panel">
          <div className="land-demo-panel-hdr">
            <span className="land-demo-lang-chip" style={{ color: demo.to.color, borderColor: demo.to.color + '44', background: demo.to.color + '14' }}>
              {demo.to.lang}
            </span>
            <span className="land-demo-panel-label">Output</span>
          </div>
          <pre className="land-demo-code land-demo-output-code">{demo.toCode}</pre>
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

function LanguageCube() {
  return (
    <div className="land-cube-wrap" aria-hidden="true">
      <div className="land-cube-glow" />
      <div className="land-code-cube">
        <span className="land-cube-face land-cube-front" style={{ '--face-color': '#4b8bbe' } as CSSProperties}>PY</span>
        <span className="land-cube-face land-cube-back" style={{ '--face-color': '#f7df1e' } as CSSProperties}>JS</span>
        <span className="land-cube-face land-cube-right" style={{ '--face-color': '#659ad2' } as CSSProperties}>C++</span>
        <span className="land-cube-face land-cube-left" style={{ '--face-color': '#a8b9cc' } as CSSProperties}>C</span>
        <span className="land-cube-face land-cube-top" style={{ '--face-color': '#c9a84c' } as CSSProperties}>AI</span>
        <span className="land-cube-face land-cube-bottom" style={{ '--face-color': '#f89820' } as CSSProperties}>JAVA</span>
      </div>
    </div>
  );
}

function HeroVisual() {
  const stageRef = useRef<HTMLDivElement>(null);

  const handlePointerMove = (event: ReactPointerEvent<HTMLDivElement>) => {
    const stage = stageRef.current;
    if (!stage) return;
    const rect = stage.getBoundingClientRect();
    const x = (event.clientX - rect.left) / rect.width - 0.5;
    const y = (event.clientY - rect.top) / rect.height - 0.5;
    stage.style.setProperty('--tilt-x', `${(-y * 7).toFixed(2)}deg`);
    stage.style.setProperty('--tilt-y', `${(x * 9).toFixed(2)}deg`);
    stage.style.setProperty('--light-x', `${((x + 0.5) * 100).toFixed(1)}%`);
    stage.style.setProperty('--light-y', `${((y + 0.5) * 100).toFixed(1)}%`);
  };

  const resetTilt = () => {
    const stage = stageRef.current;
    if (!stage) return;
    stage.style.setProperty('--tilt-x', '0deg');
    stage.style.setProperty('--tilt-y', '0deg');
    stage.style.setProperty('--light-x', '50%');
    stage.style.setProperty('--light-y', '35%');
  };

  return (
    <div
      ref={stageRef}
      className="land-visual-stage"
      onPointerMove={handlePointerMove}
      onPointerLeave={resetTilt}
    >
      <div className="land-orbit land-orbit-a" aria-hidden="true" />
      <div className="land-orbit land-orbit-b" aria-hidden="true" />
      <LanguageCube />
      <div className="land-demo-perspective">
        <div className="land-demo-depth" aria-hidden="true" />
        <CodeDemo />
      </div>
      <div className="land-visual-status">
        <span className="land-status-ping" />
        Conversion engine online
        <span className="land-status-latency">AI + rules fallback</span>
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
  const previewRef = useRef(null);
  const ctaRef = useRef(null);
  const [previewIn, setPreviewIn] = useState(false);
  const [ctaIn, setCtaIn] = useState(false);

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
          if (e.target === previewRef.current) setPreviewIn(true);
          if (e.target === ctaRef.current) setCtaIn(true);
        }
      });
    }, opts);
    if (featuresRef.current) obs.observe(featuresRef.current);
    if (modulesRef.current) obs.observe(modulesRef.current);
    if (previewRef.current) obs.observe(previewRef.current);
    if (ctaRef.current) obs.observe(ctaRef.current);
    return () => obs.disconnect();
  }, []);

  return (
    <div className="landing land-v2">

      {/* ── Decorative background ── */}
      <div className="land-bg-grid" aria-hidden="true" />
      <div className="land-orb land-orb-1" aria-hidden="true" />
      <div className="land-orb land-orb-2" aria-hidden="true" />

      {/* ── Navbar ── */}
      <nav className="land-v2-nav sticky top-0 z-50 flex items-center justify-between px-4 sm:px-8 py-4 border-b border-border bg-bg/80 backdrop-blur">
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
            className="land-nav-playground hidden sm:inline-flex bg-transparent border-none text-muted hover:text-primary rounded px-3 py-1.5 text-sm font-medium transition-colors"
            onClick={goToPlayground}
          >Try Playground</button>
          <button
            className="hidden sm:inline-flex bg-transparent border border-border text-primary hover:bg-border rounded px-4 py-1.5 text-sm font-medium transition-colors"
            onClick={() => onGetStarted?.()}
          >Sign In</button>
          <button
            className="land-nav-primary text-white border-none rounded px-4 py-1.5 text-sm font-semibold transition-colors"
            onClick={() => onGetStarted?.()}
          >Get Started</button>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="land-hero">
        <div className="land-hero-text land-fade-up">
          <div className="land-hero-badge">
            <span className="land-badge-pulse" />
            AI-powered · Run instantly · Learn as you go
          </div>

          <h1 className="land-v2-title mt-0 mb-5">
            Translate ideas,<br />
            <span>not syntax.</span>
          </h1>

          <p className="land-v2-sub text-muted text-base leading-relaxed mt-0 mb-8">
            Move real code between Python, C, C++, Java, and JavaScript.
            Then run it, understand the changes, and learn the concepts behind
            the translation in one focused workspace.
          </p>

          <div className="flex items-center gap-3 flex-wrap">
            <button
              className="land-primary-cta text-white border-none rounded px-6 py-3 text-sm font-semibold transition-colors inline-flex items-center gap-2"
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

          <div className="land-language-list flex items-center flex-wrap gap-2 mt-1">
            {LANGUAGE_ACCENTS.map(language => (
              <span
                key={language.name}
                className="land-language-pill text-xs rounded px-2.5 py-1 font-mono"
                style={{ '--lang-color': language.color } as CSSProperties}
              >
                <i aria-hidden="true" />
                {language.name}
              </span>
            ))}
          </div>
        </div>

        <div className="land-hero-demo land-fade-up land-delay-1">
          <HeroVisual />
        </div>
      </section>

      {/* ── Stats strip ── */}
      <div className="land-v2-stats flex flex-wrap items-center justify-center gap-6 sm:gap-12 py-6 border-y border-border bg-surface/50 land-fade-up land-delay-2">
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

      <section className="land-how-strip" aria-label="How CodeSwitch works">
        {[
          { n: '01', title: 'Paste your code', text: 'Drop in a real snippet or open a saved file.' },
          { n: '02', title: 'Choose a language', text: 'Switch between five supported languages.' },
          { n: '03', title: 'Run and learn', text: 'Test the result and understand what changed.' },
        ].map(step => (
          <div className="land-how-step" key={step.n}>
            <span>{step.n}</span>
            <div>
              <strong>{step.title}</strong>
              <p>{step.text}</p>
            </div>
          </div>
        ))}
      </section>

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
      <section
        ref={previewRef}
        className={`land-preview-section py-16 px-4 sm:px-8${previewIn ? ' animate-in' : ''}`}
      >
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
                <span className="land-mock-pill" style={{ color: '#3572A5', background: '#3572A514', borderColor: '#3572A540' }}>● Python</span>
                <span className="text-muted text-sm">→</span>
                <span className="bg-accent text-white text-xs font-semibold rounded px-3 py-1">Convert</span>
                <span className="text-muted text-sm">→</span>
                <span className="text-xs text-muted">To</span>
                <span className="land-mock-pill" style={{ color: '#f59e0b', background: '#f59e0b14', borderColor: '#f59e0b40' }}>● Java</span>
                <span className="ml-auto text-xs font-semibold rounded px-2 py-0.5" style={{ background: 'rgba(232,108,47,0.15)', color: 'var(--accent)', border: '1px solid var(--accent)' }}>✦ AI-powered</span>
              </div>

              <div className="grid grid-cols-2 gap-3 flex-1 min-h-0">
                <div className="land-mock-code-panel">
                  <div className="land-mock-panel-hdr" style={{ color: '#3572A5' }}>Python · Input</div>
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
      <section ref={ctaRef} className={`land-v2-cta py-20 px-8 text-center${ctaIn ? ' animate-in' : ''}`}>
        <div className="land-v2-cta-card max-w-2xl mx-auto flex flex-col items-center gap-4">
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
