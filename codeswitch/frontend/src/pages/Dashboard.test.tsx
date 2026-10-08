import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import Dashboard from './Dashboard';
import * as api from '../api/client';

vi.mock('../api/client', () => ({
  getProfile: vi.fn(), getConversionHistory: vi.fn(), getProgress: vi.fn(),
  getFiles: vi.fn(), getModules: vi.fn(), getPublicProfile: vi.fn(),
}));
vi.mock('../components/charts/sankey', () => ({
  SankeyChart: () => null, SankeyLink: () => null,
  SankeyNode: () => null, SankeyTooltip: () => null,
}));

it('loads fresh private data when another account opens the dashboard', async () => {
  vi.mocked(api.getProfile).mockResolvedValue({ data: { username: 'Alice', email: 'alice@example.com' } } as never);
  vi.mocked(api.getConversionHistory).mockResolvedValue({ data: [] } as never);
  vi.mocked(api.getProgress).mockResolvedValue({ data: [] } as never);
  vi.mocked(api.getModules).mockResolvedValue({ data: [] } as never);
  vi.mocked(api.getPublicProfile).mockResolvedValue({ data: {} } as never);
  vi.mocked(api.getFiles).mockResolvedValue({ data: [{ id: 1, name: 'Alice private file', language: 'python', updated_at: '2026-10-08' }] } as never);
  const first = render(<MemoryRouter><Dashboard /></MemoryRouter>);
  await screen.findByText('alice@example.com');
  first.unmount();
  vi.mocked(api.getProfile).mockResolvedValue({ data: { username: 'Bob', email: 'bob@example.com' } } as never);
  vi.mocked(api.getFiles).mockResolvedValue({ data: [] } as never);
  render(<MemoryRouter><Dashboard /></MemoryRouter>);
  expect(screen.queryByText('alice@example.com')).not.toBeInTheDocument();
  expect(screen.queryByText('Alice private file')).not.toBeInTheDocument();
  await screen.findByText('bob@example.com');
  await waitFor(() => expect(api.getFiles).toHaveBeenCalledTimes(2));
});
