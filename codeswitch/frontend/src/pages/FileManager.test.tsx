import { act, fireEvent, render, screen } from '@testing-library/react';
import { expect, it, vi } from 'vitest';
import FileManager from './FileManager';
import * as api from '../api/client';

vi.mock('../api/client', () => ({ getFiles: vi.fn(), createFile: vi.fn(), updateFile: vi.fn(), deleteFile: vi.fn() }));
vi.mock('../components/CodeEditor', () => ({ default: ({ value, onChange }: any) => <textarea aria-label="Code" value={value} onChange={e => onChange(e.target.value)} /> }));

it.each(['switch file', 'edit same file'])('preserves current edits after a delayed save: %s', async (action) => {
  vi.mocked(api.getFiles).mockResolvedValue({ data: [
    { id: 1, filename: 'A.py', language: 'python', code_content: 'A' },
    { id: 2, filename: 'B.py', language: 'python', code_content: 'B' },
  ] } as never);
  let resolve!: (value: any) => void;
  vi.mocked(api.updateFile).mockReturnValue(new Promise(r => { resolve = r; }));
  render(<FileManager />);
  fireEvent.click(await screen.findByText('A.py'));
  fireEvent.click(screen.getByRole('button', { name: /Save/ }));
  if (action === 'switch file') fireEvent.click(screen.getByText('B.py'));
  fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'new edits' } });
  await act(async () => resolve({ data: { id: 1, filename: 'A.py', language: 'python', code_content: 'A' } }));
  expect(screen.getByLabelText('Code')).toHaveValue('new edits');
  expect(screen.getByPlaceholderText('Filename (e.g. hello.py)')).toHaveValue(action === 'switch file' ? 'B.py' : 'A.py');
});
