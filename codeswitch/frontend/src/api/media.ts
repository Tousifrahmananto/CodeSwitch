const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

/** Resolve absolute DRF image URLs and relative /media/ paths safely. */
export function resolveMediaUrl(value?: string | null): string | null {
  if (!value) return null;
  try {
    if (/^https?:\/\//i.test(value)) return value;
    const apiUrl = new URL(API_BASE, window.location.origin);
    return new URL(value, apiUrl.origin + '/').toString();
  } catch {
    return value;
  }
}
