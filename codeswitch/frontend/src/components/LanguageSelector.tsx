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
    <label className="flex items-center gap-2 text-muted text-sm">
      {label && <span>{label}</span>}
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="bg-surface border border-border text-primary rounded px-2 py-1.5 text-sm focus:outline-none focus:border-accent cursor-pointer"
      >
        {languages.map((lang) => (
          <option key={lang} value={lang}>
            {LANGUAGE_LABELS[lang] || lang}
          </option>
        ))}
      </select>
    </label>
  );
}
