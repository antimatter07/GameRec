import apiClient from './client';
import type { User } from '../types/user';

export interface LoginCredentials {
  username: string; // OAuth2PasswordRequestForm uses "username"
  password: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name?: string;
}

export const authApi = {
  ensureCsrf: () =>
    apiClient.get('/auth/csrf'),

  register: (payload: RegisterPayload) =>
    apiClient.post<User>('/auth/register', payload).then((r) => r.data),

  login: (credentials: LoginCredentials) => {
    // FastAPI OAuth2 expects form data, not JSON
    const form = new URLSearchParams();
    form.append('username', credentials.username);
    form.append('password', credentials.password);
    return apiClient
      .post<User>('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .then((r) => r.data);
  },

  logout: () =>
    apiClient.post('/auth/logout'),

  googleLogin: (accessToken: string) =>
    apiClient.post<User>('/auth/google', { google_token: accessToken }).then((r) => r.data),
};
