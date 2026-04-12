import apiClient from './client';
import type {
  JournalStats,
  SessionLog,
  SessionLogCreate,
  SessionLogListOut,
  SessionLogUpdate,
} from '../types/journal';

export interface SessionListParams {
  game_id?:  number;
  page?:     number;
  page_size?: number;
}

export const journalApi = {
  createSession: (payload: SessionLogCreate) =>
    apiClient.post<SessionLog>('/journal/sessions', payload).then((r) => r.data),

  listSessions: (params: SessionListParams = {}) =>
    apiClient
      .get<SessionLogListOut>('/journal/sessions', { params })
      .then((r) => r.data),

  updateSession: (sessionId: number, payload: SessionLogUpdate) =>
    apiClient
      .patch<SessionLog>(`/journal/sessions/${sessionId}`, payload)
      .then((r) => r.data),

  deleteSession: (sessionId: number) =>
    apiClient.delete(`/journal/sessions/${sessionId}`),

  getStats: () =>
    apiClient.get<JournalStats>('/journal/sessions/stats').then((r) => r.data),

  getFeed: (params: { page?: number; page_size?: number } = {}) =>
    apiClient
      .get<SessionLogListOut>('/journal/feed', { params })
      .then((r) => r.data),
};
