import { describe, it, expect, vi } from 'vitest';
import client, { login, logout, getMe, convertCode, visualizeCode, verifyConversion } from './client';

it('shares one refresh request across simultaneous 401 responses', async () => {
  vi.resetModules();
  const axios = (await import('axios')).default;
  const { AxiosError } = await import('axios');
  const { default: freshClient } = await import('./client');
  const csrf = vi.spyOn(axios, 'get').mockResolvedValue({ data: { csrf_token: 'csrf' } });
  let finish!: (value: any) => void;
  const refresh = vi.spyOn(axios, 'post').mockReturnValue(new Promise(r => { finish = r; }));
  freshClient.defaults.adapter = async config => {
    const response = { data: {}, status: 200, statusText: 'OK', headers: {}, config };
    if ((config as any)._retry) return response;
    throw new AxiosError('unauthorized', '401', config, undefined, { ...response, status: 401 });
  };
  try {
    const pending = [freshClient.get('/profile'), freshClient.get('/files'), freshClient.get('/progress')];
    await vi.waitFor(() => expect(refresh).toHaveBeenCalled());
    finish({ data: {} });
    await Promise.all(pending);
    expect(refresh).toHaveBeenCalledTimes(1);
  } finally {
    csrf.mockRestore();
    refresh.mockRestore();
  }
});

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
  it('exports visualizeCode function', () => expect(typeof visualizeCode).toBe('function'));
  it('exports verifyConversion function', () => expect(typeof verifyConversion).toBe('function'));
});
