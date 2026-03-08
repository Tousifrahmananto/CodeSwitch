import axios, { AxiosResponse, InternalAxiosRequestConfig } from 'axios';
import type { User, ConversionRecord, CodeFile, LearningModule, Lesson, UserProgress, Quiz, SharedSnippet, PublicProfile, AdminStats, AdminUser, AdminConversion, AdminLesson } from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

const client = axios.create({
  baseURL: API_BASE,
  withCredentials: true,           // Send httpOnly cookies automatically
  xsrfCookieName: 'csrftoken',    // Django CSRF cookie name
  xsrfHeaderName: 'X-CSRFToken',  // Django CSRF header name
  headers: { 'Content-Type': 'application/json' },
});

// NOTE: No request interceptor attaching Bearer tokens.
// Authentication is handled entirely via httpOnly cookies set by the server.

// Auto-refresh token on 401 — calls /api/token/refresh/ (cookie-based, no body needed)
client.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true;
      try {
        // The refresh_token cookie is automatically included via withCredentials
        await axios.post(`${API_BASE}/token/refresh/`, {}, { withCredentials: true });
        // Retry the original request — the new access_token cookie will be included
        return client(original);
      } catch {
        // Refresh failed — user has no valid session. Clear stale local state
        // and reject so the caller (App.tsx) can set user=null and show login.
        // Do NOT reload here — that would create an infinite loop when no user
        // is logged in (every /me/ 401 would trigger reload → /me/ → 401 ...).
        localStorage.removeItem('user');
        return Promise.reject(error);
      }
    }
    return Promise.reject(error);
  }
);

// ── Auth ──────────────────────────────────────
export const register = (data: Record<string, string>): Promise<AxiosResponse> =>
  client.post('/register', data);

export const login = (data: { username: string; password: string }): Promise<AxiosResponse<{ user: User }>> =>
  client.post('/login', data);

export const logout = (): Promise<AxiosResponse> =>
  client.post('/logout', {});

export const getMe = (): Promise<AxiosResponse<User>> =>
  client.get('/me/');

export const getProfile = (): Promise<AxiosResponse<User>> =>
  client.get('/profile');

export const updateProfile = (formData: FormData): Promise<AxiosResponse<User>> =>
  client.patch('/profile', formData, { headers: { 'Content-Type': 'multipart/form-data' } });

// ── Converter ─────────────────────────────────
export const convertCode = (data: {
  source_language: string;
  target_language: string;
  code: string;
}): Promise<AxiosResponse<{ output: string; engine: string }>> =>
  client.post('/convert', data);

export const getConversionHistory = (): Promise<AxiosResponse<ConversionRecord[]>> =>
  client.get('/convert/history');

export const explainCode = (data: {
  input_code: string;
  output_code: string;
  source_language: string;
  target_language: string;
}): Promise<AxiosResponse<{ explanation: string }>> =>
  client.post('/explain/', data);

// ── Snippets ──────────────────────────────────
export const createSnippet = (data: {
  source_language: string;
  target_language: string;
  input_code: string;
  output_code: string;
  engine: string;
}): Promise<AxiosResponse<{ slug: string }>> =>
  client.post('/snippets/', data);

export const getSnippet = (slug: string): Promise<AxiosResponse<SharedSnippet>> =>
  client.get(`/snippets/${slug}/`);

// ── Files ─────────────────────────────────────
export const getFiles = (): Promise<AxiosResponse<CodeFile[]>> =>
  client.get('/files');

export const createFile = (data: Omit<CodeFile, 'id' | 'created_at' | 'updated_at'>): Promise<AxiosResponse<CodeFile>> =>
  client.post('/files', data);

export const getFile = (id: number): Promise<AxiosResponse<CodeFile>> =>
  client.get(`/files/${id}`);

export const updateFile = (id: number, data: Partial<CodeFile>): Promise<AxiosResponse<CodeFile>> =>
  client.put(`/files/${id}`, data);

export const deleteFile = (id: number): Promise<AxiosResponse> =>
  client.delete(`/files/${id}`);

// ── Learning ──────────────────────────────────
export const getModules = (): Promise<AxiosResponse<LearningModule[]>> =>
  client.get('/modules');

export const getModule = (id: number): Promise<AxiosResponse<LearningModule>> =>
  client.get(`/modules/${id}`);

export const updateProgress = (lessonId: number): Promise<AxiosResponse> =>
  client.post('/progress/update', { lesson_id: lessonId });

export const getProgress = (): Promise<AxiosResponse<UserProgress[]>> =>
  client.get('/progress');

export const getLessonQuiz = (lessonId: number): Promise<AxiosResponse<Quiz>> =>
  client.get(`/lessons/${lessonId}/quiz/`);

export const submitQuiz = (
  quizId: number,
  answers: Record<string, number>
): Promise<AxiosResponse<{ score: number; passed: boolean; correct_options: Record<string, number> }>> =>
  client.post(`/quizzes/${quizId}/submit/`, { answers });

// ── Public Profile ─────────────────────────────
export const getPublicProfile = (username: string): Promise<AxiosResponse<PublicProfile>> =>
  client.get(`/profile/${username}/`);

// ── Admin ──────────────────────────────────────
export const adminGetStats = (): Promise<AxiosResponse<AdminStats>> =>
  client.get('/admin/stats');

export const adminGetUsers = (): Promise<AxiosResponse<AdminUser[]>> =>
  client.get('/admin/users');

export const adminUpdateUser = (id: number, data: Partial<AdminUser>): Promise<AxiosResponse<AdminUser>> =>
  client.patch(`/admin/users/${id}`, data);

export const adminDeleteUser = (id: number): Promise<AxiosResponse> =>
  client.delete(`/admin/users/${id}`);

export const adminGetConversions = (): Promise<AxiosResponse<AdminConversion[]>> =>
  client.get('/admin/conversions');

export const adminGetModules = (): Promise<AxiosResponse<LearningModule[]>> =>
  client.get('/admin/modules');

export const adminCreateModule = (data: Omit<LearningModule, 'id' | 'lesson_count'>): Promise<AxiosResponse<LearningModule>> =>
  client.post('/admin/modules', data);

export const adminUpdateModule = (id: number, data: Partial<LearningModule>): Promise<AxiosResponse<LearningModule>> =>
  client.put(`/admin/modules/${id}`, data);

export const adminDeleteModule = (id: number): Promise<AxiosResponse> =>
  client.delete(`/admin/modules/${id}`);

export const adminGetModuleLessons = (moduleId: number): Promise<AxiosResponse<AdminLesson[]>> =>
  client.get(`/admin/modules/${moduleId}/lessons`);

export const adminGetLesson = (id: number): Promise<AxiosResponse<AdminLesson>> =>
  client.get(`/admin/lessons/${id}`);

export const adminCreateLesson = (moduleId: number, data: Partial<Lesson>): Promise<AxiosResponse<Lesson>> =>
  client.post(`/admin/modules/${moduleId}/lessons`, data);

export const adminUpdateLesson = (id: number, data: Partial<Lesson>): Promise<AxiosResponse<Lesson>> =>
  client.put(`/admin/lessons/${id}`, data);

export const adminDeleteLesson = (id: number): Promise<AxiosResponse> =>
  client.delete(`/admin/lessons/${id}`);

export default client;
