// src/components/LanguageSelector.tsx
// Dropdown for selecting a programming language.

interface LanguageSelectorProps {
  value: string;
  onChange: (lang: string) => void;
  languages: string[];
  label?: string;
}

const LANGUAGE_LABELS: Record<string, string> = {
  python: 'Python',
  c: 'C',
  java: 'Java',
  javascript: 'JavaScript',
  cpp: 'C++',
  other: 'Other',
};

export default function LanguageSelector({ value, onChange, languages, label }: LanguageSelectorProps) {
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
