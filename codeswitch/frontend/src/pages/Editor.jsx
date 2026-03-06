import { useState } from 'react';
import { convertCode } from '../api/client';
import CodeEditor from '../components/CodeEditor';
import LanguageSelector from '../components/LanguageSelector';

const LANGUAGES = ['python', 'c', 'java'];

const THEMES = [
  { id: 'vs-dark', label: 'Dark' },
  { id: 'vs', label: 'Light' },
  { id: 'hc-black', label: 'High Contrast' },
  { id: 'monokai', label: 'Monokai' },
  { id: 'dracula', label: 'Dracula' },
];

export default function Editor() {
  const [sourceLang, setSourceLang] = useState('python');
  const [targetLang, setTargetLang] = useState('c');
  const [inputCode, setInputCode] = useState('');
  const [outputCode, setOutputCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [engine, setEngine] = useState('');
  const [theme, setTheme] = useState(() => localStorage.getItem('editor_theme') || 'vs-dark');

  const handleConvert = async () => {
    if (!inputCode.trim()) return setError('Please enter some code.');
    if (sourceLang === targetLang) return setError('Source and target languages must differ.');
    setLoading(true);
    setError('');
    setEngine('');
    try {
      const { data } = await convertCode({
        source_language: sourceLang,
        target_language: targetLang,
        code: inputCode,
      });
      setOutputCode(data.output);
      setEngine(data.engine || 'rules');
    } catch (err) {
      setError(err.response?.data?.error || 'Conversion failed.');
    } finally {
      setLoading(false);
    }
  };

  const handleThemeChange = (t) => {
    setTheme(t);
    localStorage.setItem('editor_theme', t);
  };

  return (
    <div className="editor-page">
      <h2>Code Converter</h2>

      <div className="lang-selectors">
        <LanguageSelector label="From:" value={sourceLang} onChange={setSourceLang} languages={LANGUAGES} />

        <button className="btn-convert" onClick={handleConvert} disabled={loading}>
          {loading ? 'Converting...' : '⇒ Convert'}
        </button>

        <LanguageSelector label="To:" value={targetLang} onChange={setTargetLang} languages={LANGUAGES} />

        <div className="theme-selector">
          <label>Theme</label>
          <select value={theme} onChange={e => handleThemeChange(e.target.value)}>
            {THEMES.map(t => <option key={t.id} value={t.id}>{t.label}</option>)}
          </select>
        </div>
      </div>

      {error && <p className="error">{error}</p>}

      {engine && (
        <p className={`engine-badge ${engine === 'ai' ? 'badge-ai' : 'badge-rules'}`}>
          {engine === 'ai' ? '✦ AI-powered conversion' : '⚙ Rule-based conversion (set AI_API_KEY in .env to enable AI)'}
        </p>
      )}

      <div className="editor-panels">
        <div className="panel">
          <h4>{sourceLang} (Input)</h4>
          <CodeEditor
            value={inputCode}
            onChange={setInputCode}
            language={sourceLang}
            height="420px"
            theme={theme}
          />
        </div>

        <div className="panel">
          <h4>{targetLang} (Output)</h4>
          <CodeEditor
            value={outputCode}
            language={targetLang}
            readOnly
            height="420px"
            theme={theme}
          />
        </div>
      </div>
    </div>
  );
}
