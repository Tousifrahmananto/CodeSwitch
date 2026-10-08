import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import Learning from './Learning';
import * as api from '../api/client';
import {runCode} from '../api/executor';
vi.mock('../api/executor',()=>({runCode:vi.fn(),canRun:()=>true}));

vi.mock('../api/client', () => ({ getModules: vi.fn(), getModule: vi.fn(), updateProgress: vi.fn(), getProgress: vi.fn(), convertCode: vi.fn(), getLessonQuiz: vi.fn(), submitQuiz: vi.fn() }));
vi.mock('../components/CodeEditor', () => ({ default: ({value,onChange,readOnly}:any) => <textarea aria-label="Editor" readOnly={readOnly} value={value} onChange={e=>onChange?.(e.target.value)}/> }));
const lessons = [1, 2, 3].map(id => ({ id, title: `Lesson ${id}`, content: 'content', example_code: '', order: id }));
const module = { id: 1, title: 'Basics', description: 'Basics', difficulty: 'beginner', language: 'python', lesson_count: 3, lessons };

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(api.getModules).mockResolvedValue({ data: [module] } as never);
  vi.mocked(api.getModule).mockResolvedValue({ data: module } as never);
  vi.mocked(api.getProgress).mockResolvedValue({ data: [] } as never);
});
async function open() {
  render(<MemoryRouter><Learning /></MemoryRouter>);
  fireEvent.click(await screen.findByRole('heading', { name: 'Basics' }));
  await screen.findByRole('heading', { name: 'Lesson 1' });
}

it('shows wrong-answer explanations from the submission response', async () => {
  vi.mocked(api.getLessonQuiz).mockResolvedValue({ data: { id: 1, title: 'Quiz', questions: [{ id: 7, order: 1, question_text: 'Question', options: [{ id: 9, option_text: 'Wrong' }, { id: 10, option_text: 'Right' }] }] } } as never);
  vi.mocked(api.submitQuiz).mockResolvedValue({ data: { score: 0, passed: false, correct_options: { 7: 10 }, explanations: { 7: { 9: 'Why this answer is wrong' } } } } as never);
  await open();
  fireEvent.click(screen.getByRole('button', { name: /Quiz/ }));
  fireEvent.click(await screen.findByRole('radio', { name: 'Wrong' }));
  fireEvent.click(screen.getByRole('button', { name: 'Submit Quiz' }));
  expect(await screen.findByText('Why this answer is wrong')).toBeInTheDocument();
});

it('keeps failed progress incomplete and lets the user retry', async () => {
  vi.mocked(api.updateProgress).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({ data: {} } as never);
  await open();
  fireEvent.click(screen.getByRole('button', { name: /Mark as Complete/ }));
  expect(await screen.findByText(/Could not save progress/)).toBeInTheDocument();
  expect(screen.getByText('0/3 complete')).toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /Mark as Complete/ }));
  expect(await screen.findByText('1/3 complete')).toBeInTheDocument();
});

it('prevents duplicate completion and does not advance another lesson', async () => {
  let finish!: (value: any) => void;
  vi.mocked(api.updateProgress).mockReturnValue(new Promise(r => { finish = r; }));
  await open();
  const complete = screen.getByRole('button', { name: /Mark as Complete/ });
  fireEvent.click(complete);
  fireEvent.click(complete);
  fireEvent.click(screen.getByText('Lesson 3'));
  vi.useFakeTimers();
  try {
    await act(async () => finish({ data: {} }));
    act(() => vi.advanceTimersByTime(1000));
    expect(screen.getByRole('heading', { name: 'Lesson 3' })).toBeInTheDocument();
    expect(api.updateProgress).toHaveBeenCalledTimes(1);
    expect(screen.getByText('1/3 complete')).toBeInTheDocument();
    fireEvent.click(screen.getByRole('button', { name: '← Modules' }));
    expect(screen.getByText('1/3')).toBeInTheDocument();
  } finally { vi.useRealTimers(); }
});

async function openSandbox() {
 vi.mocked(api.getModule).mockResolvedValue({data:{...module,lessons:[{...lessons[0],example_code:JSON.stringify({python:'print(1)',c:'int main() {}',java:'class Main {}'})}]}} as never);
 await open(); return within(document.querySelector('.try-it-sandbox')!);
}
it('discards C conversion when the sandbox target changes to Java',async()=>{
 let finish!:(v:any)=>void;vi.mocked(api.convertCode).mockReturnValue(new Promise(r=>finish=r));
 const sandbox=await openSandbox();fireEvent.click(sandbox.getByRole('button',{name:'Convert'}));
 fireEvent.click(sandbox.getAllByRole('button',{name:'Java'})[1]);
 await act(async()=>finish({data:{output:'int main() {}'}}));
 expect(sandbox.queryByText('JAVA Output')).not.toBeInTheDocument();expect(vi.mocked(api.convertCode).mock.calls[0][1]?.signal?.aborted).toBe(true);
});
it('reset discards a pending sandbox run',async()=>{
 let finish!:(v:any)=>void;vi.mocked(runCode).mockReturnValue(new Promise(r=>finish=r));
 const sandbox=await openSandbox();fireEvent.click(sandbox.getByRole('button',{name:'▶ Run'}));fireEvent.click(sandbox.getByRole('button',{name:'Reset'}));
 await act(async()=>finish({stdout:'obsolete sandbox output',stderr:'',code:0}));expect(screen.queryByText('obsolete sandbox output')).not.toBeInTheDocument();
});
