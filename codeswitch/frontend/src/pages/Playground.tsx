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
    <div className="flex flex-col min-h-screen bg-bg">

      {/* ── Header ── */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-border bg-surface flex-shrink-0">
        <div className="flex items-center gap-2">
          <Logo size={26} id="playground" />
          <span className="font-semibold text-sm text-primary">
            CodeSwitch <span className="text-[10px] bg-accent/15 text-accent px-1.5 py-0.5 rounded font-semibold uppercase tracking-wide ml-1">Playground</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-xs text-muted">Write and run code — no sign-in required</span>
          <button
            className="bg-transparent border border-border text-primary hover:bg-border rounded px-4 py-1.5 text-sm font-medium transition-colors"
            onClick={onBack}
          >Sign In</button>
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-4 py-1.5 text-sm font-semibold transition-colors"
            onClick={onBack}
          >Get Started</button>
        </div>
      </header>

      {/* ── Main area ── */}
      <div className="flex flex-col gap-3 p-4 flex-1">

        {/* ── Toolbar ── */}
        <div className="flex items-center gap-3 flex-wrap">
          <LanguageSelector
            label="Language:"
            value={lang}
            onChange={handleLangChange}
            languages={LANGUAGES}
          />
          <button
            className="bg-accent hover:bg-accent-h text-white border-none rounded px-4 py-2 text-sm font-semibold transition-colors disabled:opacity-50"
            onClick={handleRun}
            disabled={runLoading || !code.trim()}
          >
            {runLoading ? '⏳ Running...' : '▶ Run'}
          </button>
          {code.trim() && (
            <button
              className="bg-transparent border border-border text-primary hover:bg-border rounded px-4 py-2 text-sm font-medium transition-colors"
              onClick={handleSaveOpen}
              title={isLoggedIn ? 'Save to your Files' : 'Sign in to save'}
            >
              💾 Save
            </button>
          )}
          {saveToast && <span className="text-xs text-success">{saveToast}</span>}
        </div>

        {/* ── Editor ── */}
        <div>
          <CodeEditor
            value={code}
            onChange={setCode}
            language={lang}
            height="460px"
          />
        </div>

        {/* ── Stdin input ── */}
        <div className="flex flex-col gap-1.5">
          <label className="text-xs text-muted font-medium">Program Input (stdin)</label>
          <textarea
            className="w-full bg-bg border border-border rounded px-3 py-2 text-sm font-mono text-primary resize-y focus:outline-none focus:border-accent"
            placeholder="Enter input for your program here (one value per line)..."
            value={stdin}
            onChange={e => setStdin(e.target.value)}
            rows={3}
            spellCheck={false}
          />
        </div>

        {/* ── Terminal output ── */}
        {(runOutput !== null || runError) && (
          <div className="bg-[#0d1117] border border-border rounded overflow-hidden">
            <div className="flex items-center justify-between px-4 py-2 border-b border-border bg-surface text-xs text-muted">
              <span>Terminal</span>
              <button
                className="text-muted hover:text-primary cursor-pointer text-base leading-none bg-transparent border-none p-0"
                onClick={() => { setRunOutput(null); setRunError(''); }}
              >×</button>
            </div>
            {runError && <pre className="block p-3 text-xs font-mono text-danger whitespace-pre-wrap">{runError}</pre>}
            {runOutput && (
              <>
                {stdin.trim() && (
                  <>
                    <pre className="block p-3 pb-0 text-xs font-mono text-muted whitespace-pre">{stdin.trim().split('\n').map(l => `> ${l}`).join('\n')}</pre>
                    <hr className="border-none border-t border-border my-2" />
                  </>
                )}
                {runOutput.stdout && <pre className="block p-3 text-xs font-mono text-primary whitespace-pre-wrap">{runOutput.stdout}</pre>}
                {runOutput.stderr && <pre className="block p-3 text-xs font-mono text-danger whitespace-pre-wrap">{runOutput.stderr}</pre>}
                {!runOutput.stdout && !runOutput.stderr && (
                  <pre className="block p-3 text-xs font-mono text-muted italic whitespace-pre-wrap">(no output)</pre>
                )}
                <span className={`block px-3 pb-2 text-xs font-mono ${runOutput.code === 0 ? 'text-success' : 'text-danger'}`}>
                  {runOutput.code === 0 ? '✓' : '✗'} exit {runOutput.code}
                </span>
              </>
            )}
          </div>
        )}

      </div>

      {/* ── Save Modal ── */}
      {showSaveModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowSaveModal(false)}>
          <div className="bg-surface border border-border rounded-lg p-6 w-80 flex flex-col gap-3" onClick={e => e.stopPropagation()}>
            {isLoggedIn ? (
              <>
                <h3 className="text-base font-semibold m-0">Save to Files</h3>
                <p className="text-sm text-muted m-0">Enter a filename for this {lang} snippet.</p>
                <input
                  className="w-full bg-bg border border-border rounded px-3 py-2 text-sm text-primary focus:outline-none focus:border-accent"
                  type="text"
                  placeholder={`my_snippet.${lang === 'python' ? 'py' : lang === 'javascript' ? 'js' : lang === 'java' ? 'java' : lang === 'cpp' ? 'cpp' : 'c'}`}
                  value={saveFilename}
                  onChange={e => setSaveFilename(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSaveConfirm()}
                  autoFocus
                />
                <div className="flex gap-2 justify-end">
                  <button
                    className="px-4 py-2 text-sm border border-border rounded text-muted hover:text-primary bg-transparent transition-colors"
                    onClick={() => setShowSaveModal(false)}
                  >Cancel</button>
                  <button
                    className="px-4 py-2 text-sm bg-accent hover:bg-accent-h text-white rounded border-none transition-colors disabled:opacity-50"
                    onClick={handleSaveConfirm}
                    disabled={!saveFilename.trim() || saveLoading}
                  >
                    {saveLoading ? 'Saving…' : 'Save'}
                  </button>
                </div>
              </>
            ) : (
              <>
                <h3 className="text-base font-semibold m-0">Sign in to save</h3>
                <p className="text-sm text-muted m-0">Create a free account to save your code to your personal Files library.</p>
                <div className="flex gap-2 justify-end">
                  <button
                    className="px-4 py-2 text-sm border border-border rounded text-muted hover:text-primary bg-transparent transition-colors"
                    onClick={() => setShowSaveModal(false)}
                  >Cancel</button>
                  <button
                    className="px-4 py-2 text-sm bg-accent hover:bg-accent-h text-white rounded border-none transition-colors"
                    onClick={onBack}
                  >Sign In / Register</button>
                </div>
              </>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
