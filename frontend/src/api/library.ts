import apiClient from './client';
import type { LibraryEntry, LibraryEntryCreate, LibraryEntryUpdate, LibraryStats } from '../types/library';

export const libraryApi = {
  getAll: () =>
    apiClient.get<LibraryEntry[]>('/library').then((r) => r.data),

  getStats: () =>
    apiClient.get<LibraryStats>('/library/stats').then((r) => r.data),

  add: (payload: LibraryEntryCreate) =>
    apiClient.post<LibraryEntry>('/library', payload).then((r) => r.data),

  update: (entryId: number, payload: LibraryEntryUpdate) =>
    apiClient.patch<LibraryEntry>(`/library/${entryId}`, payload).then((r) => r.data),

  remove: (entryId: number) =>
    apiClient.delete(`/library/${entryId}`),
};
