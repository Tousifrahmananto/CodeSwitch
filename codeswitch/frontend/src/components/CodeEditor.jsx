import Editor from '@monaco-editor/react';

const LANG_MAP = {
  python: 'python',
  c: 'c',
  java: 'java',
  javascript: 'javascript',
  other: 'plaintext',
};

const CUSTOM_THEMES = {
  monokai: {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '75715E', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'F92672' },
      { token: 'string', foreground: 'E6DB74' },
      { token: 'number', foreground: 'AE81FF' },
      { token: 'type', foreground: '66D9EF' },
      { token: 'function', foreground: 'A6E22E' },
    ],
    colors: {
      'editor.background': '#272822',
      'editor.foreground': '#F8F8F2',
      'editorLineNumber.foreground': '#75715E',
      'editor.selectionBackground': '#49483E',
      'editor.lineHighlightBackground': '#3E3D32',
    },
  },
  dracula: {
    base: 'vs-dark',
    inherit: true,
    rules: [
      { token: 'comment', foreground: '6272A4', fontStyle: 'italic' },
      { token: 'keyword', foreground: 'FF79C6' },
      { token: 'string', foreground: 'F1FA8C' },
      { token: 'number', foreground: 'BD93F9' },
      { token: 'type', foreground: '8BE9FD' },
      { token: 'function', foreground: '50FA7B' },
    ],
    colors: {
      'editor.background': '#282A36',
      'editor.foreground': '#F8F8F2',
      'editorLineNumber.foreground': '#6272A4',
      'editor.selectionBackground': '#44475A',
      'editor.lineHighlightBackground': '#44475A',
    },
  },
};

function registerThemes(monaco) {
  Object.entries(CUSTOM_THEMES).forEach(([id, def]) => monaco.editor.defineTheme(id, def));
}

export default function CodeEditor({ value, onChange, language = 'python', readOnly = false, height = '400px', theme }) {
  const activeTheme = theme || localStorage.getItem('editor_theme') || 'vs-dark';
  return (
    <div className="monaco-wrapper" style={{ height }}>
      <Editor
        height={height}
        language={LANG_MAP[language] || 'plaintext'}
        value={value}
        onChange={readOnly ? undefined : onChange}
        theme={activeTheme}
        beforeMount={registerThemes}
        options={{
          readOnly,
          fontSize: 13,
          fontFamily: "'Ubuntu Mono', 'Cascadia Code', 'Fira Code', Consolas, monospace",
          minimap: { enabled: false },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          lineNumbers: 'on',
          tabSize: 4,
          automaticLayout: true,
        }}
      />
    </div>
  );
}
