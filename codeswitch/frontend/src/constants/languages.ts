export const LANGUAGE_META = {
  python: { label: 'Python', color: '#3572A5', softBg: 'rgba(53, 114, 165, 0.16)' },
  c: { label: 'C', color: '#4f9ca6', softBg: 'rgba(79, 156, 166, 0.16)' },
  java: { label: 'Java', color: '#d96f32', softBg: 'rgba(217, 111, 50, 0.16)' },
  javascript: { label: 'JavaScript', color: '#f1e05a', softBg: 'rgba(241, 224, 90, 0.16)' },
  cpp: { label: 'C++', color: '#f34b7d', softBg: 'rgba(243, 75, 125, 0.16)' },
  other: { label: 'Other', color: '#8b8b8b', softBg: 'rgba(139, 139, 139, 0.16)' },
} as const;

export type KnownLanguage = keyof typeof LANGUAGE_META;

export function getLanguageMeta(language: string) {
  return LANGUAGE_META[language as KnownLanguage] ?? {
    label: language || 'Unknown',
    color: '#8b8b8b',
    softBg: 'rgba(139, 139, 139, 0.16)',
  };
}
