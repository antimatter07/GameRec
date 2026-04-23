import { isAxiosError } from 'axios';
import apiClient from './client';
import type {
  SessionLogCreate,
  SessionLogUpdate,
  SessionLog,
  MultiAxisRatingUpsert,
  MultiAxisRating,
  JournalStats,
  EmotionStats,
  EmotionStatsPeriod,
  JournalFeedItem,
  PaginatedResponse,
} from '../types/journal';

// ─── Feed date-group helper ────────────────────────────────────────────────────

function toDateGroup(isoString: string): string {
  const date  = new Date(isoString);
  const today = new Date();
  const yesterday = new Date(today);
  yesterday.setDate(today.getDate() - 1);

  if (date.toDateString() === today.toDateString()) return 'Today';
  if (date.toDateString() === yesterday.toDateString()) return 'Yesterday';
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

function sessionsToFeedItems(sessions: SessionLog[]): JournalFeedItem[] {
  return sessions.map((s) => ({
    type: s.is_milestone ? 'milestone' : 'session',
    session: s,
    date_group: toDateGroup(s.started_at),
  }));
}

// ─── Journal API ──────────────────────────────────────────────────────────────

export const journalApi = {
  // ── Sessions ────────────────────────────────────────────────────────────────

  createSession: async (data: SessionLogCreate): Promise<SessionLog> => {
    const res = await apiClient.post<SessionLog>('/journal/sessions', data);
    return res.data;
  },

  getSessions: async (params?: {
    page?:      number;
    per_page?:  number;
    game_id?:   number;
    date_from?: string;
    date_to?:   string;
  }): Promise<PaginatedResponse<SessionLog>> => {
    const res = await apiClient.get<PaginatedResponse<SessionLog>>('/journal/sessions', { params });
    return res.data;
  },

  updateSession: async (sessionId: number, data: SessionLogUpdate): Promise<SessionLog> => {
    const res = await apiClient.patch<SessionLog>(`/journal/sessions/${sessionId}`, data);
    return res.data;
  },

  deleteSession: async (sessionId: number): Promise<void> => {
    await apiClient.delete(`/journal/sessions/${sessionId}`);
  },

  // ── Stats ────────────────────────────────────────────────────────────────────

  getStats: async (): Promise<JournalStats> => {
    const res = await apiClient.get<JournalStats>('/journal/sessions/stats');
    return res.data;
  },

  // ── Feed ─────────────────────────────────────────────────────────────────────

  getFeed: async (params?: {
    page?:     number;
    per_page?: number;
  }): Promise<PaginatedResponse<JournalFeedItem>> => {
    const res = await apiClient.get<PaginatedResponse<SessionLog>>('/journal/feed', { params });
    const { items, ...rest } = res.data;
    return { ...rest, items: sessionsToFeedItems(items) };
  },

  // ── Multi-Axis Ratings (no backend yet — degrade gracefully) ──────────────────

  upsertRating: async (gameId: number, data: MultiAxisRatingUpsert): Promise<MultiAxisRating> => {
    const res = await apiClient.put<MultiAxisRating>(`/journal/ratings/${gameId}`, data);
    return res.data;
  },

  getRating: async (gameId: number): Promise<MultiAxisRating | null> => {
    try {
      const res = await apiClient.get<MultiAxisRating>(`/journal/ratings/${gameId}`);
      return res.data;
    } catch (err: unknown) {
      if (isAxiosError(err) && (err.response?.status === 404 || err.response?.status === 422)) return null;
      throw err;
    }
  },

  getAllRatings: async (): Promise<MultiAxisRating[]> => {
    try {
      const res = await apiClient.get<MultiAxisRating[]>('/journal/ratings');
      return res.data;
    } catch (err: unknown) {
      if (isAxiosError(err) && (err.response?.status === 404 || err.response?.status === 422)) return [];
      throw err;
    }
  },

  // ── Emotion Stats (no backend yet — degrade gracefully) ──────────────────────

  getEmotionStats: async (params?: {
    period?:  EmotionStatsPeriod;
    game_id?: number;
    genre?:   string;
  }): Promise<EmotionStats | null> => {
    try {
      const res = await apiClient.get<EmotionStats>('/journal/emotions/stats', { params });
      return res.data;
    } catch (err: unknown) {
      if (isAxiosError(err) && (err.response?.status === 404 || err.response?.status === 422)) return null;
      throw err;
    }
  },
};
