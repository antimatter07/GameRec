import apiClient from './client';
import type { UserAdminView, UserRole } from '../types/user';

export const adminApi = {
  listUsers: (page = 1, pageSize = 50, search?: string) =>
    apiClient
      .get<UserAdminView[]>('/admin/users', { params: { page, page_size: pageSize, search } })
      .then((r) => r.data),

  updateUserRole: (userId: number, role: UserRole) =>
    apiClient.patch(`/admin/users/${userId}/role`, null, { params: { role } }),

  listPremiumRequests: () =>
    apiClient.get('/admin/premium-requests').then((r) => r.data),

  approvePremiumRequest: (requestId: number) =>
    apiClient.post(`/admin/premium-requests/${requestId}/approve`),

  getMetrics: () =>
    apiClient.get('/admin/metrics').then((r) => r.data),

  getPipelineStatus: () =>
    apiClient.get('/admin/pipeline/status').then((r) => r.data),

  triggerPipeline: () =>
    apiClient.post('/admin/pipeline/trigger').then((r) => r.data),
};
