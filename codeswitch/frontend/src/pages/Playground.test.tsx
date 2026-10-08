import {act,fireEvent,render,screen} from '@testing-library/react';
import {it,expect,vi,beforeEach} from 'vitest';
import Playground from './Playground';
import {runCode} from '../api/executor';
vi.mock('../api/executor',()=>({runCode:vi.fn()}));
vi.mock('../api/client',()=>({createFile:vi.fn()}));
vi.mock('../components/CodeEditor',()=>({default:({value,onChange}:any)=><textarea aria-label="Editor" value={value} onChange={e=>onChange(e.target.value)}/>}));
beforeEach(()=>vi.clearAllMocks());
it.each(['edit','language','stdin'])('discards a playground run after %s changes',async change=>{
 let finish!:(v:any)=>void;vi.mocked(runCode).mockReturnValue(new Promise(r=>finish=r));render(<Playground/>);
 fireEvent.click(screen.getByRole('button',{name:'▶ Run'}));
 if(change==='edit') fireEvent.change(screen.getByRole('textbox',{name:'Editor'}),{target:{value:'print(99)'}});
 else if(change==='language') fireEvent.change(screen.getByRole('combobox'),{target:{value:'java'}});
 else fireEvent.change(screen.getByPlaceholderText('Enter input for your program here (one value per line)...'),{target:{value:'new stdin'}});
 await act(async()=>finish({stdout:'obsolete playground output',stderr:'',code:0}));
 expect(screen.queryByText('obsolete playground output')).not.toBeInTheDocument();
 expect(vi.mocked(runCode).mock.calls[0][3]?.signal?.aborted).toBe(true);
});
