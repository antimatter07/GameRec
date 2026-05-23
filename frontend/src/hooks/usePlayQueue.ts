import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { playQueueApi } from '../api/playQueue';
import type { PlayQueue, QueueSuggestionState } from '../types/playQueue';

export function usePlayQueue() {
  return useQuery({
    queryKey: ['play-queue'],
    queryFn: playQueueApi.getQueue,
    staleTime: 2 * 60 * 1000,
  });
}

export function useQueueSuggestion() {
  return useQuery({
    queryKey: ['queue-suggestion'],
    queryFn: playQueueApi.getSuggestion,
    refetchOnWindowFocus: false,
    refetchInterval: (query) => {
      const state = query.state.data;
      return state?.is_generating || state?.suggestion?.status === 'pending' ? 3000 : false;
    },
  });
}

export function useEnsureQueueSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (triggerSource: string) => playQueueApi.ensureSuggestion(triggerSource),
    onSuccess: (data: QueueSuggestionState) => {
      queryClient.setQueryData(['queue-suggestion'], data);
      queryClient.invalidateQueries({ queryKey: ['queue-suggestion'] });
    },
  });
}

export function useAdoptQueueSuggestion() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: playQueueApi.adoptSuggestion,
    onSuccess: (data) => {
      queryClient.setQueryData(['play-queue'], data);
      queryClient.invalidateQueries({ queryKey: ['queue-suggestion'] });
    },
  });
}

export function useEnqueueGame() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entryId: number) => playQueueApi.enqueue(entryId),
    onSuccess: (data) => {
      queryClient.setQueryData(['play-queue'], data);
      queryClient.invalidateQueries({ queryKey: ['queue-suggestion'] });
    },
  });
}

export function useDequeueGame() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entryId: number) => playQueueApi.dequeue(entryId),
    onMutate: async (entryId) => {
      await queryClient.cancelQueries({ queryKey: ['play-queue'] });
      const snapshot = queryClient.getQueryData<PlayQueue>(['play-queue']);
      if (snapshot) {
        const filtered = snapshot.entries.filter((e) => e.entry_id !== entryId);
        // Re-number positions after optimistic remove
        const reindexed = filtered.map((e, i) => ({ ...e, position: i + 1 }));
        queryClient.setQueryData(['play-queue'], { total: reindexed.length, entries: reindexed });
      }
      return { snapshot };
    },
    onError: (_err, _entryId, context) => {
      if (context?.snapshot) {
        queryClient.setQueryData(['play-queue'], context.snapshot);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['play-queue'] });
      queryClient.invalidateQueries({ queryKey: ['queue-suggestion'] });
    },
  });
}

export function useReorderQueue() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (orderedEntryIds: number[]) => playQueueApi.reorder(orderedEntryIds),
    onMutate: async (orderedEntryIds) => {
      await queryClient.cancelQueries({ queryKey: ['play-queue'] });
      const snapshot = queryClient.getQueryData<PlayQueue>(['play-queue']);
      if (snapshot) {
        const entryMap = new Map(snapshot.entries.map((e) => [e.entry_id, e]));
        const reordered = orderedEntryIds
          .map((id, i) => {
            const e = entryMap.get(id);
            return e ? { ...e, position: i + 1 } : null;
          })
          .filter(Boolean) as PlayQueue['entries'];
        queryClient.setQueryData(['play-queue'], { total: reordered.length, entries: reordered });
      }
      return { snapshot };
    },
    onError: (_err, _ids, context) => {
      if (context?.snapshot) {
        queryClient.setQueryData(['play-queue'], context.snapshot);
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: ['play-queue'] });
      queryClient.invalidateQueries({ queryKey: ['queue-suggestion'] });
    },
  });
}
