import { describe, expect, it } from 'vitest';
import { resolveMediaUrl } from './media';

describe('resolveMediaUrl', () => {
  it('keeps absolute backend URLs unchanged', () => {
    const url = 'https://api.example.com/media/avatars/user.png';
    expect(resolveMediaUrl(url)).toBe(url);
  });

  it('resolves relative media paths against the API origin', () => {
    expect(resolveMediaUrl('/media/avatars/user.png'))
      .toBe('http://localhost:8000/media/avatars/user.png');
  });

  it('handles missing avatars', () => {
    expect(resolveMediaUrl(null)).toBeNull();
  });
});
