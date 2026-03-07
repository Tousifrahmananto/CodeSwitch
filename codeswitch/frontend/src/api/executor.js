/**
 * Code execution via the CodeSwitch backend proxy (POST /api/run/).
 * Uses the shared axios client so the correct API base URL is always used.
 */
import client from './client';

/**
 * Run code via the backend execution proxy.
 * @param {string} language - one of: python, c, java, javascript, cpp
 * @param {string} code     - source code to execute
 * @returns {{ stdout: string, stderr: string, code: number }}
 */
export async function runCode(language, code) {
  try {
    const { data } = await client.post('/run/', { language, code });
    return {
      stdout: data.stdout || '',
      stderr: data.stderr || '',
      code: data.code,
    };
  } catch (err) {
    const msg = err.response?.data?.error || err.message || 'Could not reach execution server.';
    throw new Error(msg);
  }
}

/** Returns true if the language is supported for execution. */
export function canRun(language) {
  return ['python', 'c', 'java', 'javascript', 'cpp'].includes(language);
}
