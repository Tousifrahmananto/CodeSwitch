const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

function shouldUpgradeToHttps(url: URL): boolean {
  if (typeof window === 'undefined') return false;
  if (window.location.protocol !== 'https:') return false;
  if (url.protocol !== 'http:') return false;
  return !['localhost', '127.0.0.1', '::1'].includes(url.hostname);
}

function normalizeMediaUrl(url: URL): string {
  if (shouldUpgradeToHttps(url)) {
    url.protocol = 'https:';
  }
  return url.toString();
}

/** Resolve absolute DRF image URLs and relative /media/ paths safely. */
export function resolveMediaUrl(value?: string | null): string | null {
  if (!value) return null;
  try {
    if (/^https?:\/\//i.test(value)) return normalizeMediaUrl(new URL(value));
    const apiUrl = new URL(API_BASE, window.location.origin);
    return normalizeMediaUrl(new URL(value, apiUrl.origin + '/'));
  } catch {
    return value;
  }
}
