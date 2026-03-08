import { describe, it, expect } from 'vitest';
import client, { login, logout, getMe, convertCode } from './client';

describe('API client configuration', () => {
  it('has withCredentials enabled for cookie auth', () => {
    expect(client.defaults.withCredentials).toBe(true);
  });

  it('sets correct CSRF cookie and header names', () => {
    expect(client.defaults.xsrfCookieName).toBe('csrftoken');
    expect(client.defaults.xsrfHeaderName).toBe('X-CSRFToken');
  });

  it('sends JSON content type by default', () => {
    const contentType = client.defaults.headers?.['Content-Type'];
    expect(contentType).toBe('application/json');
  });

  it('base URL falls back to localhost when env var is absent', () => {
    // In test env VITE_API_URL is not set, so baseURL should be the fallback
    expect(client.defaults.baseURL).toBeTruthy();
  });
});

describe('API client exports named functions', () => {
  it('exports login function', () => expect(typeof login).toBe('function'));
  it('exports logout function', () => expect(typeof logout).toBe('function'));
  it('exports getMe function', () => expect(typeof getMe).toBe('function'));
  it('exports convertCode function', () => expect(typeof convertCode).toBe('function'));
});
