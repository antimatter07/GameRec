import apiClient from './client';
import type {
  LibraryEntry,
  LibraryEntryCreate,
  LibraryQueryParams,
  LibraryEntryUpdate,
  LibraryStats,
  LibraryEntryUpdateOut,
} from '../types/library';
import type { GameListItem } from '../types/game';

export interface BacklogFiltersParams {
  mood_genre?: string;
  max_hours?: number;
  sort?: 'score' | 'playtime_asc' | 'playtime_desc' | 'added_at';
  page?: number;
  page_size?: number;
}

export interface PrioritizedBacklogItem {
  entry_id: number;
  game: GameListItem;
  playtime_hours: number | null;
  taste_score: number | null;
  priority_score: number;
  stale_months: number | null;
}

export interface PrioritizedBacklogOut {
  total: number;
  results: PrioritizedBacklogItem[];
}

export const libraryApi = {
  getAll: (params: LibraryQueryParams = {}) =>
    apiClient.get<LibraryEntry[]>('/library', { params }).then((r) => r.data),

  getStats: () =>
    apiClient.get<LibraryStats>('/library/stats').then((r) => r.data),

  add: (payload: LibraryEntryCreate) =>
    apiClient.post<LibraryEntry>('/library', payload).then((r) => r.data),

  update: (entryId: number, payload: LibraryEntryUpdate) =>
    apiClient.patch<LibraryEntryUpdateOut>(`/library/${entryId}`, payload).then((r) => r.data),

  remove: (entryId: number) =>
    apiClient.delete(`/library/${entryId}`),

  getPrioritizedBacklog: (filters: BacklogFiltersParams = {}) =>
    apiClient
      .get<PrioritizedBacklogOut>('/library/backlog/prioritized', { params: filters })
      .then((r) => r.data),
};
