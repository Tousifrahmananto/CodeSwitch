import { useState } from 'react';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';
import Logo from '../components/Logo';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'];

const PISTON_LANG = {
  python: 'python', c: 'c', java: 'java', javascript: 'javascript', cpp: 'c++',
};

const STARTER_CODE = {
  python:
    '# Python Playground\nprint("Hello, World!")\n\n# Try editing this code and click Run!\nfor i in range(1, 6):\n    print(f"Line {i}")',
  c:
    '// C Playground\n#include <stdio.h>\n\nint main() {\n    printf("Hello, World!\\n");\n\n    // Try editing this code and click Run!\n    for (int i = 1; i <= 5; i++) {\n        printf("Line %d\\n", i);\n    }\n    return 0;\n}',
  java:
    '// Java Playground\npublic class Main {\n    public static void main(String[] args) {\n        System.out.println("Hello, World!");\n\n        // Try editing this code and click Run!\n        for (int i = 1; i <= 5; i++) {\n            System.out.println("Line " + i);\n        }\n    }\n}',
  javascript:
    '// JavaScript Playground\nconsole.log("Hello, World!");\n\n// Try editing this code and click Run!\nfor (let i = 1; i <= 5; i++) {\n    console.log(`Line ${i}`);\n}',
  cpp:
    '// C++ Playground\n#include <iostream>\n\nint main() {\n    std::cout << "Hello, World!" << std::endl;\n\n    // Try editing this code and click Run!\n    for (int i = 1; i <= 5; i++) {\n        std::cout << "Line " << i << std::endl;\n    }\n    return 0;\n}',
};

export default function Playground({ onBack }) {
  const [lang, setLang] = useState('python');
  const [code, setCode] = useState(STARTER_CODE['python']);
  const [runLoading, setRunLoading] = useState(false);
  const [runOutput, setRunOutput] = useState(null);
  const [runError, setRunError] = useState('');

  const handleLangChange = (newLang) => {
    setLang(newLang);
    setCode(STARTER_CODE[newLang]);
    setRunOutput(null);
    setRunError('');
  };

  const handleRun = async () => {
    if (!code.trim()) return;
    setRunLoading(true);
    setRunOutput(null);
    setRunError('');
    try {
      const resp = await fetch('https://emkc.org/api/v2/piston/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          language: PISTON_LANG[lang],
          version: '*',
          files: [{ content: code }],
        }),
      });
      const result = await resp.json();
      const run = result.run || {};
      setRunOutput({ stdout: run.stdout || '', stderr: run.stderr || '', code: run.code });
    } catch {
      setRunError('Could not reach execution server. Check your connection.');
    } finally {
      setRunLoading(false);
    }
  };

  return (
    <div className="playground-page">

      {/* ── Header ── */}
      <header className="playground-header">
        <div className="playground-brand">
          <Logo size={26} id="playground" />
          <span className="playground-title">CodeSwitch <span className="playground-badge">Playground</span></span>
        </div>
        <div className="playground-header-actions">
          <span className="playground-desc">Write and run code — no sign-in required</span>
          <button className="land-btn-ghost" onClick={onBack}>Sign In</button>
          <button className="land-btn-primary" onClick={onBack}>Get Started</button>
        </div>
      </header>

      {/* ── Main area ── */}
      <div className="playground-body">

        {/* ── Toolbar ── */}
        <div className="playground-toolbar">
          <LanguageSelector
            label="Language:"
            value={lang}
            onChange={handleLangChange}
            languages={LANGUAGES}
          />
          <button
            className="btn-run playground-run-btn"
            onClick={handleRun}
            disabled={runLoading || !code.trim()}
          >
            {runLoading ? '⏳ Running...' : '▶ Run'}
          </button>
        </div>

        {/* ── Editor ── */}
        <div className="playground-editor-wrap">
          <CodeEditor
            value={code}
            onChange={setCode}
            language={lang}
            height="460px"
          />
        </div>

        {/* ── Terminal output ── */}
        {(runOutput !== null || runError) && (
          <div className="run-output">
            <div className="run-output-header">
              <span>Terminal</span>
              <button
                className="run-output-close"
                onClick={() => { setRunOutput(null); setRunError(''); }}
              >
                ×
              </button>
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
    </div>
  );
}
