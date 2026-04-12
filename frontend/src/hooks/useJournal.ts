import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { journalApi } from '../api/journal';
import type { SessionLogCreate, SessionLogUpdate } from '../types/journal';

const JOURNAL_KEYS = {
  sessions: (gameId?: number, page?: number) => ['journal-sessions', gameId, page] as const,
  stats:    ()                                => ['journal-stats'] as const,
  feed:     (page?: number)                  => ['journal-feed', page] as const,
};

function invalidateAll(queryClient: ReturnType<typeof useQueryClient>) {
  queryClient.invalidateQueries({ queryKey: ['journal-sessions'] });
  queryClient.invalidateQueries({ queryKey: ['journal-stats'] });
  queryClient.invalidateQueries({ queryKey: ['journal-feed'] });
}

export function useSessionsList(gameId?: number, page = 1, pageSize = 20) {
  return useQuery({
    queryKey: JOURNAL_KEYS.sessions(gameId, page),
    queryFn:  () => journalApi.listSessions({ game_id: gameId, page, page_size: pageSize }),
    staleTime: 2 * 60 * 1000,
  });
}

export function useJournalStats() {
  return useQuery({
    queryKey: JOURNAL_KEYS.stats(),
    queryFn:  journalApi.getStats,
    staleTime: 5 * 60 * 1000,
  });
}

export function useJournalFeed(page = 1, pageSize = 20) {
  return useQuery({
    queryKey: JOURNAL_KEYS.feed(page),
    queryFn:  () => journalApi.getFeed({ page, page_size: pageSize }),
    staleTime: 2 * 60 * 1000,
  });
}

export function useCreateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: SessionLogCreate) => journalApi.createSession(payload),
    onSuccess: () => invalidateAll(queryClient),
  });
}

export function useUpdateSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: SessionLogUpdate }) =>
      journalApi.updateSession(id, updates),
    onSuccess: () => invalidateAll(queryClient),
  });
}

export function useDeleteSession() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: number) => journalApi.deleteSession(sessionId),
    onSuccess: () => invalidateAll(queryClient),
  });
}
