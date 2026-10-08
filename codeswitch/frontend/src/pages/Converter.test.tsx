import { act, fireEvent, render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import Converter from './Converter';
import * as api from '../api/client';
import * as executor from '../api/executor';

vi.mock('../api/client', () => ({ convertCode: vi.fn(), createFile: vi.fn(), createSnippet: vi.fn(), explainCode: vi.fn(), verifyConversion: vi.fn() }));
vi.mock('../api/executor', () => ({ runCode: vi.fn(), canRun: () => true }));
vi.mock('../components/CodeEditor', () => ({ default: ({ value, onChange }: any) => <textarea aria-label="Code" value={value} onChange={e => onChange(e.target.value)} /> }));
vi.mock('../components/DiffView', () => ({ default: () => null }));

beforeEach(() => vi.clearAllMocks());
function mount() {
  render(<MemoryRouter><Converter /></MemoryRouter>);
  fireEvent.change(screen.getAllByLabelText('Code')[0], { target: { value: 'print(1)' } });
}

it('opens provider-specific recovery after a successful rules fallback', async () => {
  vi.mocked(api.convertCode).mockResolvedValue({ data: { output: 'converted', engine: 'rules', ai_error_code: 'ai_quota_exhausted', ai_provider: 'gemini' } } as never);
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Convert' }));
  expect(await screen.findByRole('link', { name: 'Gemini Studio' })).toHaveAttribute('href', 'https://aistudio.google.com/apikey');
  expect(screen.queryByRole('link', { name: 'Groq Console' })).not.toBeInTheDocument();
});

it.each(['ai_not_configured', 'ai_timeout', 'ai_invalid_response'])('shows key recovery only for configuration or quota failures: %s', async (code) => {
  vi.mocked(api.convertCode).mockRejectedValue({ response: { data: { error: 'AI unavailable', ai_error_code: code, ai_provider: 'groq' } } });
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Convert' }));
  await screen.findByText('AI unavailable');
  expect(Boolean(screen.queryByPlaceholderText('Paste your API key here'))).toBe(code === 'ai_not_configured');
});

it('discards a conversion after changing the target language', async () => {
  let resolve!: (value: any) => void;
  vi.mocked(api.convertCode).mockReturnValue(new Promise(r => { resolve = r; }));
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Convert' }));
  const signal = vi.mocked(api.convertCode).mock.calls[0][1]?.signal;
  fireEvent.click(screen.getAllByRole('button', { name: 'Java' })[1]);
  await act(async () => resolve({ data: { output: 'obsolete C', engine: 'ai' } }));
  expect(signal?.aborted).toBe(true);
  expect(screen.getAllByLabelText('Code')[1]).toHaveValue('');
  expect(screen.getByRole('button', { name: 'Convert' })).toBeEnabled();
});

it('does not let stale cleanup stop a newer conversion timer', async () => {
  vi.useFakeTimers();
  try {
    let finishFirst!: (value: any) => void;
    vi.mocked(api.convertCode)
      .mockReturnValueOnce(new Promise(r => { finishFirst = r; }))
      .mockReturnValueOnce(new Promise(() => {}));
    mount();
    fireEvent.click(screen.getByRole('button', { name: 'Convert' }));
    fireEvent.change(screen.getAllByLabelText('Code')[0], { target: { value: 'print(2)' } });
    fireEvent.click(screen.getByRole('button', { name: 'Convert' }));
    await act(async () => finishFirst({ data: { output: 'obsolete', engine: 'ai' } }));
    act(() => vi.advanceTimersByTime(5000));
    expect(screen.getByRole('button', { name: 'Converting… 5s' })).toBeDisabled();
    expect(screen.getAllByLabelText('Code')[1]).toHaveValue('');
  } finally {
    vi.useRealTimers();
  }
});

it.each(['verify', 'explain', 'run source', 'run target'])('discards stale %s results after editing', async (operation) => {
  vi.mocked(api.convertCode).mockResolvedValue({ data: { output: 'converted', engine: 'ai' } } as never);
  mount();
  fireEvent.click(screen.getByRole('button', { name: 'Convert' }));
  await screen.findByRole('button', { name: 'Verify behavior' });
  let resolve!: (value: any) => void;
  const pending = new Promise<any>(r => { resolve = r; });
  if (operation === 'verify') {
    vi.mocked(api.verifyConversion).mockReturnValue(pending);
    fireEvent.click(screen.getByRole('button', { name: 'Verify behavior' }));
  } else if (operation === 'explain') {
    vi.mocked(api.explainCode).mockReturnValue(pending);
    fireEvent.click(screen.getByRole('button', { name: 'Explain' }));
  } else {
    vi.mocked(executor.runCode).mockReturnValue(pending);
    fireEvent.click(screen.getByRole('button', { name: operation === 'run source' ? '▶ Run' : 'Run output' }));
  }
  fireEvent.change(screen.getAllByLabelText('Code')[0], { target: { value: 'print(2)' } });
  await act(async () => resolve(operation === 'verify'
    ? { data: { verified: true, summary: 'obsolete result', comparison: { stdout_match: true, exit_code_match: true }, source: { stdout: 'obsolete result', code: 0 }, target: { stdout: 'obsolete result', code: 0 } } }
    : operation === 'explain' ? { data: { explanation: 'obsolete result' } } : { stdout: 'obsolete result', stderr: '', code: 0 }));
  expect(screen.queryByText(/obsolete result/)).not.toBeInTheDocument();
});
