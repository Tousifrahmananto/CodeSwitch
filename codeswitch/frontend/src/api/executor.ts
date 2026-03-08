/**
 * Code execution via the CodeSwitch backend proxy (POST /api/run/).
 * Uses the shared axios client so the correct API base URL is always used.
 */
import client from './client';
import type { RunResult } from '../types';

/**
 * Run code via the backend execution proxy.
 */
export async function runCode(language: string, code: string, stdin = ''): Promise<RunResult> {
  try {
    const { data } = await client.post<RunResult>('/run/', { language, code, stdin });
    return {
      stdout: data.stdout || '',
      stderr: data.stderr || '',
      code: data.code,
    };
  } catch (err: unknown) {
    const axiosErr = err as { response?: { data?: { error?: string } }; message?: string };
    const msg = axiosErr.response?.data?.error || axiosErr.message || 'Could not reach execution server.';
    throw new Error(msg);
  }
}

/** Returns true if the language is supported for execution. */
export function canRun(language: string): boolean {
  return ['python', 'c', 'java', 'javascript', 'cpp'].includes(language);
}
