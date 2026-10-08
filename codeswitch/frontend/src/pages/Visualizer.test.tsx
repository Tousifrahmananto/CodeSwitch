import { fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { expect, it, vi } from 'vitest';
import Visualizer from './Visualizer';
import { visualizeCode } from '../api/client';

vi.mock('../api/client', () => ({ visualizeCode: vi.fn() }));
vi.mock('../components/CodeEditor', () => ({ default: () => null }));

it.each(['concept_trace', 'execution_trace'])('labels Python visualization from the response mode: %s', async mode => {
  vi.mocked(visualizeCode).mockResolvedValue({ data: { language: 'python', mode, steps: [], trace: [], concepts: [], recommendations: [], summary: '' } } as never);
  const view = render(<MemoryRouter><Visualizer /></MemoryRouter>);
  const notice = within(view.container.querySelector('.viz-mode-notice') as HTMLElement);
  expect(notice.queryByText('Real execution trace')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /Generate/ }));
  expect(await notice.findByText(mode === 'execution_trace' ? 'Real execution trace' : 'Concept trace')).toBeInTheDocument();
  if (mode === 'concept_trace') expect(notice.queryByText('Real execution trace')).not.toBeInTheDocument();
});
