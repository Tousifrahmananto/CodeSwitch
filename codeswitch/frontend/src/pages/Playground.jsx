import { useState } from 'react';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';
import Logo from '../components/Logo';
import { runCode } from '../api/executor';
import { createFile } from '../api/client';

const LANGUAGES = ['python', 'c', 'java', 'javascript', 'cpp'];

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
  const [stdin, setStdin] = useState('');
  const [runLoading, setRunLoading] = useState(false);
  const [runOutput, setRunOutput] = useState(null);
  const [runError, setRunError] = useState('');

  // Save to Files state
  const [showSaveModal, setShowSaveModal] = useState(false);
  const [saveFilename, setSaveFilename] = useState('');
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveToast, setSaveToast] = useState('');

  const isLoggedIn = !!localStorage.getItem('access_token');

  const handleLangChange = (newLang) => {
    setLang(newLang);
    setCode(STARTER_CODE[newLang]);
    setRunOutput(null);
    setRunError('');
    setStdin('');
  };

  const handleRun = async () => {
    if (!code.trim()) return;
    setRunLoading(true);
    setRunOutput(null);
    setRunError('');
    try {
      const result = await runCode(lang, code, stdin);
      setRunOutput(result);
    } catch (err) {
      setRunError(err.message || 'Could not reach execution server. Check your connection.');
    } finally {
      setRunLoading(false);
    }
  };

  const handleSaveOpen = () => {
    setSaveFilename('');
    setSaveToast('');
    setShowSaveModal(true);
  };

  const handleSaveConfirm = async () => {
    const filename = saveFilename.trim();
    if (!filename) return;
    setSaveLoading(true);
    try {
      await createFile({ filename, language: lang, code_content: code });
      setShowSaveModal(false);
      setSaveToast('Saved to Files!');
      setTimeout(() => setSaveToast(''), 3000);
    } catch {
      setSaveToast('Save failed. Please sign in first.');
      setTimeout(() => setSaveToast(''), 3000);
      setShowSaveModal(false);
    } finally {
      setSaveLoading(false);
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
          {code.trim() && (
            <button
              className="btn-save-playground"
              onClick={handleSaveOpen}
              title={isLoggedIn ? 'Save to your Files' : 'Sign in to save'}
            >
              💾 Save
            </button>
          )}
          {saveToast && <span className="share-toast">{saveToast}</span>}
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

        {/* ── Stdin input ── */}
        <div className="run-stdin-wrap">
          <label className="run-stdin-label">Program Input (stdin)</label>
          <textarea
            className="run-stdin"
            placeholder="Enter input for your program here (one value per line)..."
            value={stdin}
            onChange={e => setStdin(e.target.value)}
            rows={3}
            spellCheck={false}
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
              >×</button>
            </div>
            {runError && <pre className="run-stderr">{runError}</pre>}
            {runOutput && (
              <>
                {stdin.trim() && (
                  <>
                    <pre className="run-stdin-echo">{stdin.trim().split('\n').map(l => `> ${l}`).join('\n')}</pre>
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
        )}

      </div>

      {/* ── Save Modal ── */}
      {showSaveModal && (
        <div className="modal-overlay" onClick={() => setShowSaveModal(false)}>
          <div className="modal-box" onClick={e => e.stopPropagation()}>
            {isLoggedIn ? (
              <>
                <h3 className="modal-title">Save to Files</h3>
                <p className="modal-desc">Enter a filename for this {lang} snippet.</p>
                <input
                  className="modal-input"
                  type="text"
                  placeholder={`my_snippet.${lang === 'python' ? 'py' : lang === 'javascript' ? 'js' : lang === 'java' ? 'java' : lang === 'cpp' ? 'cpp' : 'c'}`}
                  value={saveFilename}
                  onChange={e => setSaveFilename(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSaveConfirm()}
                  autoFocus
                />
                <div className="modal-actions">
                  <button className="modal-btn-cancel" onClick={() => setShowSaveModal(false)}>Cancel</button>
                  <button
                    className="modal-btn-confirm"
                    onClick={handleSaveConfirm}
                    disabled={!saveFilename.trim() || saveLoading}
                  >
                    {saveLoading ? 'Saving…' : 'Save'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <h3 className="modal-title">Sign in to save</h3>
                <p className="modal-desc">Create a free account to save your code to your personal Files library.</p>
                <div className="modal-actions">
                  <button className="modal-btn-cancel" onClick={() => setShowSaveModal(false)}>Cancel</button>
                  <button className="modal-btn-confirm" onClick={onBack}>Sign In / Register</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
