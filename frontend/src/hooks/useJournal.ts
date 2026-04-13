import {
  useQuery,
  useMutation,
  useQueryClient,
} from '@tanstack/react-query';
import { journalApi } from '../api/journal';
import type {
  SessionLogCreate,
  SessionLogUpdate,
  EmotionStatsPeriod,
} from '../types/journal';

// ─── Query Keys ───────────────────────────────────────────────────────────────

export const journalKeys = {
  all:          ['journal'] as const,
  sessions:     () => [...journalKeys.all, 'sessions'] as const,
  sessionList:  (filters?: Record<string, unknown>) =>
    [...journalKeys.sessions(), 'list', filters] as const,
  stats:        () => [...journalKeys.all, 'stats'] as const,
  ratings:      () => [...journalKeys.all, 'ratings'] as const,
  ratingDetail: (gameId: number) => [...journalKeys.ratings(), gameId] as const,
  allRatings:   () => [...journalKeys.ratings(), 'all'] as const,
  feed:         (page?: number) => [...journalKeys.all, 'feed', page] as const,
  emotionStats: (params?: Record<string, unknown>) =>
    [...journalKeys.all, 'emotionStats', params] as const,
};

// ─── Session Queries ──────────────────────────────────────────────────────────

export function useJournalSessions(params?: {
  page?:      number;
  per_page?:  number;
  game_id?:   number;
  date_from?: string;
  date_to?:   string;
}) {
  return useQuery({
    queryKey: journalKeys.sessionList(params),
    queryFn:  () => journalApi.getSessions(params),
  });
}

export function useJournalStats() {
  return useQuery({
    queryKey: journalKeys.stats(),
    queryFn:  journalApi.getStats,
    staleTime: 1000 * 60 * 5, // 5 min
  });
}

export function useJournalFeed(page = 1) {
  return useQuery({
    queryKey: journalKeys.feed(page),
    queryFn:  () => journalApi.getFeed({ page, per_page: 20 }),
  });
}

// ─── Rating Queries ───────────────────────────────────────────────────────────

export function useGameRating(gameId: number) {
  return useQuery({
    queryKey: journalKeys.ratingDetail(gameId),
    queryFn:  () => journalApi.getRating(gameId),
    enabled:  gameId > 0,
  });
}

export function useAllRatings() {
  return useQuery({
    queryKey: journalKeys.allRatings(),
    queryFn:  journalApi.getAllRatings,
  });
}

// ─── Emotion Stats ────────────────────────────────────────────────────────────

export function useEmotionStats(params?: {
  period?:  EmotionStatsPeriod;
  game_id?: number;
  genre?:   string;
}) {
  return useQuery({
    queryKey: journalKeys.emotionStats(params),
    queryFn:  () => journalApi.getEmotionStats(params),
    staleTime: 1000 * 60 * 5,
  });
}

// ─── Mutations ────────────────────────────────────────────────────────────────

export function useCreateSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SessionLogCreate) => journalApi.createSession(data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: journalKeys.sessions() });
      qc.invalidateQueries({ queryKey: journalKeys.stats() });
      qc.invalidateQueries({ queryKey: journalKeys.feed() });
      qc.invalidateQueries({ queryKey: journalKeys.emotionStats() });
    },
  });
}

export function useUpdateSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ sessionId, data }: { sessionId: number; data: SessionLogUpdate }) =>
      journalApi.updateSession(sessionId, data),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: journalKeys.sessions() });
      qc.invalidateQueries({ queryKey: journalKeys.stats() });
      qc.invalidateQueries({ queryKey: journalKeys.feed() });
      qc.invalidateQueries({ queryKey: journalKeys.emotionStats() });
    },
  });
}

export function useDeleteSession() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (sessionId: number) => journalApi.deleteSession(sessionId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: journalKeys.sessions() });
      qc.invalidateQueries({ queryKey: journalKeys.stats() });
      qc.invalidateQueries({ queryKey: journalKeys.feed() });
      qc.invalidateQueries({ queryKey: journalKeys.emotionStats() });
    },
  });
}

export function useUpsertRating() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({
      gameId,
      data,
    }: {
      gameId: number;
      data: {
        story?:     number | null;
        gameplay?:  number | null;
        visuals?:   number | null;
        soundtrack?: number | null;
        overall?:   number | null;
      };
    }) => journalApi.upsertRating(gameId, data),
    onSuccess: (_data, variables) => {
      qc.invalidateQueries({ queryKey: journalKeys.ratingDetail(variables.gameId) });
      qc.invalidateQueries({ queryKey: journalKeys.allRatings() });
    },
  });
}

// ─── Legacy aliases (keep GameDetailPage from breaking during transition) ──────

/** @deprecated use useJournalSessions */
export function useSessionsList(gameId?: number, page = 1, pageSize = 20) {
  return useJournalSessions({ game_id: gameId, page, per_page: pageSize });
}
