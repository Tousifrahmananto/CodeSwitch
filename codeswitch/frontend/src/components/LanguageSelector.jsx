// src/components/LanguageSelector.jsx
// Dropdown for selecting a programming language.

const LANGUAGE_LABELS = {
  python: 'Python',
  c: 'C',
  java: 'Java',
  javascript: 'JavaScript',
  cpp: 'C++',
  other: 'Other',
};

export default function LanguageSelector({ value, onChange, languages, label }) {
  return (
    <label style={{ display: 'flex', alignItems: 'center', gap: 8, color: 'var(--text-muted)' }}>
      {label && <span>{label}</span>}
      <select value={value} onChange={(e) => onChange(e.target.value)}>
        {languages.map((lang) => (
          <option key={lang} value={lang}>
            {LANGUAGE_LABELS[lang] || lang}
          </option>
        ))}
      </select>
    </label>
  );
}
