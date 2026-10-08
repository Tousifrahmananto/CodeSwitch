import {act,fireEvent,render,screen} from '@testing-library/react';
import {beforeEach,it,expect,vi} from 'vitest';
import App from './App';
import {getMe,logout} from './api/client';
vi.mock('./api/client',()=>({getMe:vi.fn(),logout:vi.fn()}));
vi.mock('./pages/Dashboard',()=>({default:()=> <p>Dashboard</p>}));
vi.mock('./pages/Login',()=>({default:()=> <p>Login</p>}));
vi.mock('./pages/Landing',()=>({default:()=>null}));
vi.mock('./pages/Reference',()=>({default:()=>null}));
vi.mock('./pages/AdminPanel',()=>({default:()=>null}));
vi.mock('./pages/ShareView',()=>({default:()=>null}));
vi.mock('./pages/ProfilePage',()=>({default:()=>null}));
vi.mock('./pages/Playground',()=>({default:()=>null}));
const user={id:1,username:'Alice',email:'alice@example.com',is_staff:false};
beforeEach(()=>{vi.clearAllMocks();localStorage.setItem('user',JSON.stringify(user));window.history.replaceState({},'', '/dashboard');});
it('ignores a session response after logout and waits for cookie cleanup',async()=>{
 let finishMe!:(v:any)=>void,finishLogout!:(v:any)=>void;
 vi.mocked(getMe).mockReturnValue(new Promise(r=>finishMe=r));vi.mocked(logout).mockReturnValue(new Promise(r=>finishLogout=r));
 render(<App/>);fireEvent.click(screen.getByRole('button',{name:'🚪 Logout'}));
 expect(screen.queryByText('Login')).not.toBeInTheDocument();
 await act(async()=>finishLogout({data:{}}));expect(await screen.findByText('Login')).toBeInTheDocument();
 await act(async()=>finishMe({data:user}));expect(screen.queryByRole('button',{name:'🚪 Logout'})).not.toBeInTheDocument();expect(localStorage.getItem('user')).toBeNull();
});
it('keeps the session visible with a retryable error when logout fails',async()=>{
 vi.mocked(getMe).mockReturnValue(new Promise(()=>{}));vi.mocked(logout).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce({data:{}} as never);
 render(<App/>);fireEvent.click(screen.getByRole('button',{name:'🚪 Logout'}));
 expect(await screen.findByRole('alert')).toHaveTextContent('Could not log out');expect(localStorage.getItem('user')).not.toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'🚪 Logout'}));expect(await screen.findByText('Login')).toBeInTheDocument();
});
