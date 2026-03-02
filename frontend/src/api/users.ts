import apiClient from './client';
import type { User, UserUpdate } from '../types/user';

export const usersApi = {
  getMe: () =>
    apiClient.get<User>('/users/me').then((r) => r.data),

  updateMe: (payload: UserUpdate) =>
    apiClient.patch<User>('/users/me', payload).then((r) => r.data),

  deleteMe: () =>
    apiClient.delete('/users/me'),

  requestPremium: () =>
    apiClient.post('/users/me/request-premium'),
};
