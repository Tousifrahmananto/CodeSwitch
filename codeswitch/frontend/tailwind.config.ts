import type { Config } from 'tailwindcss';

export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  darkMode: ['attribute', 'data-theme'],
  theme: {
    extend: {
      // Map Tailwind tokens directly to CSS variables so the existing
      // dark/light toggle (data-theme attribute) keeps working automatically.
      colors: {
        bg: 'var(--bg)',
        surface: 'var(--surface)',
        border: 'var(--border)',
        accent: 'var(--accent)',
        'accent-h': 'var(--accent-hover)',
        primary: 'var(--text)',
        muted: 'var(--text-muted)',
        success: 'var(--success)',
        danger: 'var(--danger)',
        warning: 'var(--warning)',
      },
      fontFamily: {
        sans: ['var(--font)', 'system-ui', 'sans-serif'],
        mono: ['var(--mono)', 'monospace'],
      },
      borderRadius: {
        DEFAULT: 'var(--radius)',
        lg: 'calc(var(--radius) * 1.5)',
      },
      width: {
        sidebar: 'var(--sidebar-w)',
      },
    },
  },
  plugins: [],
} satisfies Config;
