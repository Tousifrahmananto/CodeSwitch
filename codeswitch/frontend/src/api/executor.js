/**
 * Code execution via the CodeSwitch backend proxy (/api/run/).
 * The backend picks a working Wandbox compiler and proxies the request,
 * so there are no CORS issues and no API keys required on the frontend.
 */

const SUPPORTED_LANGUAGES = new Set(['python', 'c', 'java', 'javascript', 'cpp']);

/**
 * Run code via the backend execution proxy.
 * @param {string} language - one of: python, c, java, javascript, cpp
 * @param {string} code     - source code to execute
 * @returns {{ stdout: string, stderr: string, code: number }}
 */
export async function runCode(language, code) {
  const resp = await fetch('/api/run/', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ language, code }),
  });

  const result = await resp.json().catch(() => ({}));

  if (!resp.ok) {
    throw new Error(result.error || `Execution service returned HTTP ${resp.status}`);
  }
  if (result.error) {
    throw new Error(result.error);
  }

  return {
    stdout: result.stdout || '',
    stderr: result.stderr || '',
    code: result.code,
  };
}

/** Returns true if the language is supported for execution. */
export function canRun(language) {
  return SUPPORTED_LANGUAGES.has(language);
}
