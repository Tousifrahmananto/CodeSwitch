import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import { beforeEach, expect, it, vi } from 'vitest';
import Visualizer from './Visualizer';
import { visualizeCode } from '../api/client';

vi.mock('../api/client', () => ({ visualizeCode: vi.fn() }));
vi.mock('../components/CodeEditor', () => ({ default: ({value,onChange}:any) => <textarea aria-label="Editor" value={value} onChange={e=>onChange(e.target.value)}/> }));
beforeEach(()=>vi.clearAllMocks());

it.each(['concept_trace', 'execution_trace'])('labels Python visualization from the response mode: %s', async mode => {
  vi.mocked(visualizeCode).mockResolvedValue({ data: { language: 'python', mode, steps: [], trace: [], concepts: [], recommendations: [], summary: '' } } as never);
  const view = render(<MemoryRouter><Visualizer /></MemoryRouter>);
  const notice = within(view.container.querySelector('.viz-mode-notice') as HTMLElement);
  expect(notice.queryByText('Real execution trace')).not.toBeInTheDocument();
  fireEvent.click(screen.getByRole('button', { name: /Generate/ }));
  expect(await notice.findByText(mode === 'execution_trace' ? 'Real execution trace' : 'Concept trace')).toBeInTheDocument();
  if (mode === 'concept_trace') expect(notice.queryByText('Real execution trace')).not.toBeInTheDocument();
});

const oldTimeline = {language:'python',mode:'concept_trace',steps:[],trace:[],concepts:[],recommendations:[],summary:'old'};
it.each(['edit','language'])('discards a trace invalidated by %s',async change=>{
 let finish!:(v:any)=>void;vi.mocked(visualizeCode).mockReturnValue(new Promise(r=>finish=r));
 render(<MemoryRouter><Visualizer/></MemoryRouter>);
 fireEvent.click(screen.getByRole('button',{name:'Generate Trace'}));
 if(change==='edit') fireEvent.change(screen.getByRole('textbox',{name:'Editor'}),{target:{value:'print(99)'}});
 else fireEvent.click(screen.getByRole('button',{name:'Java'}));
 await act(async()=>finish({data:oldTimeline}));
 expect(screen.getByText('Visualization mode')).toBeInTheDocument();
 expect(vi.mocked(visualizeCode).mock.calls[0][1]?.signal?.aborted).toBe(true);
});
it('old cleanup cannot stop a newer trace request',async()=>{
 let finishOld!:(v:any)=>void,finishNew!:(v:any)=>void;
 vi.mocked(visualizeCode).mockReturnValueOnce(new Promise(r=>finishOld=r)).mockReturnValueOnce(new Promise(r=>finishNew=r));
 render(<MemoryRouter><Visualizer/></MemoryRouter>);fireEvent.click(screen.getByRole('button',{name:'Generate Trace'}));
 fireEvent.change(screen.getByRole('textbox',{name:'Editor'}),{target:{value:'print(99)'}});
 fireEvent.click(screen.getByRole('button',{name:'Generate Trace'}));
 await act(async()=>finishOld({data:oldTimeline}));expect(screen.getByRole('button',{name:'Generating…'})).toBeDisabled();
 await act(async()=>finishNew({data:oldTimeline}));expect(screen.getByRole('button',{name:'Generate Trace'})).toBeEnabled();
});
