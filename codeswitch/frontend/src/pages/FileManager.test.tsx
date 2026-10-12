import { act, fireEvent, render, screen } from '@testing-library/react';
import { beforeEach, expect, it, vi } from 'vitest';
import FileManager from './FileManager';
import * as api from '../api/client';

vi.mock('../api/client', () => ({ getFiles: vi.fn(), getFile: vi.fn(), createFile: vi.fn(), updateFile: vi.fn(), deleteFile: vi.fn() }));
vi.mock('../components/CodeEditor', () => ({ default: ({ value, onChange }: any) => <textarea aria-label="Code" value={value} onChange={e => onChange(e.target.value)} /> }));

beforeEach(() => vi.resetAllMocks());

it.each(['switch file', 'edit same file'])('preserves current edits after a delayed save: %s', async (action) => {
  const files = [
    { id: 1, filename: 'A.py', language: 'python', code_content: 'A' },
    { id: 2, filename: 'B.py', language: 'python', code_content: 'B' },
  ];
  vi.mocked(api.getFiles).mockResolvedValue({ data: { results: files, count: 2, next: null } } as never);
  vi.mocked(api.getFile).mockImplementation(async id => ({ data: files.find(file => file.id === id) }) as never);
  let resolve!: (value: any) => void;
  vi.mocked(api.updateFile).mockReturnValue(new Promise(r => { resolve = r; }));
  render(<FileManager />);
  fireEvent.click(await screen.findByText('A.py'));
  await screen.findByDisplayValue('A');
  fireEvent.click(screen.getByRole('button', { name: /Save/ }));
  if (action === 'switch file') fireEvent.click(screen.getByText('B.py'));
  fireEvent.change(screen.getByLabelText('Code'), { target: { value: 'new edits' } });
  await act(async () => resolve({ data: { id: 1, filename: 'A.py', language: 'python', code_content: 'A' } }));
  expect(screen.getByLabelText('Code')).toHaveValue('new edits');
  expect(screen.getByPlaceholderText('Filename (e.g. hello.py)')).toHaveValue(action === 'switch file' ? 'B.py' : 'A.py');
});

it('fetches source on open and discards an older file response', async () => {
  const files = [{ id: 1, filename: 'A.py', language: 'python' }, { id: 2, filename: 'B.py', language: 'python' }];
  vi.mocked(api.getFiles).mockResolvedValue({ data: { results: files, count: 2, next: null } } as never);
  let resolveA!: (value: any) => void;
  vi.mocked(api.getFile).mockImplementation(id => id === 1
    ? new Promise(resolve => { resolveA = resolve; })
    : Promise.resolve({ data: { ...files[1], code_content: 'B source' } }) as never);
  render(<FileManager />);
  await screen.findByText('A.py');
  expect(api.getFile).not.toHaveBeenCalled();
  fireEvent.click(screen.getByText('A.py'));
  expect(screen.getByRole('button', { name: /Save/ })).toBeDisabled();
  fireEvent.click(screen.getByText('B.py'));
  await screen.findByDisplayValue('B source');
  await act(async () => resolveA({ data: { ...files[0], code_content: 'A source' } }));
  expect(screen.getByLabelText('Code')).toHaveValue('B source');
});

it('keeps save disabled after a failed file open until a successful retry', async () => {
  const file = { id: 1, filename: 'A.py', language: 'python' };
  vi.mocked(api.getFiles).mockResolvedValue({ data: { results: [file], count: 1, next: null } } as never);
  vi.mocked(api.getFile).mockRejectedValueOnce(new Error('offline'))
    .mockResolvedValue({ data: { ...file, code_content: 'preserved source' } } as never);
  render(<FileManager />);
  fireEvent.click(await screen.findByText('A.py'));
  await screen.findByText(/Failed to open file/);
  expect(screen.getByRole('button', { name: /Save/ })).toBeDisabled();
  fireEvent.click(screen.getByText('A.py'));
  await screen.findByDisplayValue('preserved source');
  expect(screen.getByRole('button', { name: /Save/ })).toBeEnabled();
});

it('loads later metadata pages without fetching their source code', async () => {
  vi.mocked(api.getFiles).mockResolvedValueOnce({ data: {
    results: [{ id: 1, filename: 'A.py', language: 'python' }], count: 2, next: '/files?page=2',
  } } as never).mockResolvedValueOnce({ data: {
    results: [{ id: 2, filename: 'B.py', language: 'python' }], count: 2, next: null,
  } } as never);
  render(<FileManager />);
  fireEvent.click(await screen.findByRole('button', { name: 'Load more files' }));
  await screen.findByText('B.py');
  expect(screen.getByText('A.py')).toBeInTheDocument();
  expect(api.getFiles).toHaveBeenLastCalledWith(2);
  expect(api.getFile).not.toHaveBeenCalled();
});
