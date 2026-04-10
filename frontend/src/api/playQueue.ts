import apiClient from './client';
import type { PlayQueue } from '../types/playQueue';

export const playQueueApi = {
  getQueue: () =>
    apiClient.get<PlayQueue>('/library/queue').then((r) => r.data),

  enqueue: (entryId: number) =>
    apiClient.post<PlayQueue>('/library/queue', { entry_id: entryId }).then((r) => r.data),

  dequeue: (entryId: number) =>
    apiClient.delete(`/library/queue/${entryId}`),

  reorder: (orderedEntryIds: number[]) =>
    apiClient
      .put<PlayQueue>('/library/queue/order', { ordered_entry_ids: orderedEntryIds })
      .then((r) => r.data),
};
