import axios from 'axios';

const API_BASE = process.env.REACT_APP_API_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token');
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-refresh token on 401
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config;
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      const refresh = localStorage.getItem('refresh_token');
      if (refresh) {
        try {
          const { data } = await axios.post(`${API_BASE}/token/refresh/`, { refresh });
          localStorage.setItem('access_token', data.access);
          original.headers.Authorization = `Bearer ${data.access}`;
          return client(original);
        } catch {
          localStorage.clear();
          window.location.reload();
        }
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────
export const register = (data) => client.post('/register', data);
export const login = (data) => client.post('/login', data);
export const logout = (data) => client.post('/logout', data);
export const getProfile = () => client.get('/profile');

// ── Converter ─────────────────────────────────
export const convertCode = (data) => client.post('/convert', data);
export const getConversionHistory = () => client.get('/convert/history');

// ── Files ─────────────────────────────────────
export const getFiles = () => client.get('/files');
export const createFile = (data) => client.post('/files', data);
export const getFile = (id) => client.get(`/files/${id}`);
export const updateFile = (id, data) => client.put(`/files/${id}`, data);
export const deleteFile = (id) => client.delete(`/files/${id}`);

// ── Learning ──────────────────────────────────
export const getModules = () => client.get('/modules');
export const getModule = (id) => client.get(`/modules/${id}`);
export const updateProgress = (lessonId) => client.post('/progress/update', { lesson_id: lessonId });
export const getProgress = () => client.get('/progress');

// ── Admin ──────────────────────────────────────
export const adminGetStats = () => client.get('/admin/stats');
export const adminGetUsers = () => client.get('/admin/users');
export const adminUpdateUser = (id, data) => client.patch(`/admin/users/${id}`, data);
export const adminDeleteUser = (id) => client.delete(`/admin/users/${id}`);
export const adminGetConversions = () => client.get('/admin/conversions');
export const adminGetModules = () => client.get('/admin/modules');
export const adminCreateModule = (data) => client.post('/admin/modules', data);
export const adminUpdateModule = (id, data) => client.put(`/admin/modules/${id}`, data);
export const adminDeleteModule = (id) => client.delete(`/admin/modules/${id}`);

export default client;
