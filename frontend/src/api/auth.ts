import apiClient from './client';
import type { User } from '../types/user';

export interface LoginCredentials {
  username: string; // OAuth2PasswordRequestForm uses "username"
  password: string;
}

export interface AuthTokens {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

export interface RegisterPayload {
  email: string;
  password: string;
  display_name?: string;
}

export const authApi = {
  register: (payload: RegisterPayload) =>
    apiClient.post<User>('/auth/register', payload).then((r) => r.data),

  login: (credentials: LoginCredentials) => {
    // FastAPI OAuth2 expects form data, not JSON
    const form = new URLSearchParams();
    form.append('username', credentials.username);
    form.append('password', credentials.password);
    return apiClient
      .post<AuthTokens>('/auth/login', form, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      })
      .then((r) => r.data);
  },

  refresh: (refreshToken: string) =>
    apiClient
      .post<AuthTokens>('/auth/refresh', null, { params: { refresh_token: refreshToken } })
      .then((r) => r.data),

  logout: (refreshToken: string) =>
    apiClient.post('/auth/logout', null, { params: { refresh_token: refreshToken } }),

  googleLogin: (idToken: string) =>
    apiClient.post<AuthTokens>('/auth/google', { id_token: idToken }).then((r) => r.data),
};
