import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { recommendationsApi, type RecommendationFilters } from '../api/recommendations';
import type { FeedbackCreate } from '../types/recommendation';

export function useRecommendations(filters: RecommendationFilters = {}) {
  return useQuery({
    queryKey: ['recommendations', filters],
    queryFn: () => recommendationsApi.get(filters),
    // TODO: Don't auto-refetch; recommendations should only refresh on user action
    refetchOnWindowFocus: false,
  });
}

export function useRecommendationHistory(page = 1) {
  return useQuery({
    queryKey: ['recommendation-history', page],
    queryFn: () => recommendationsApi.getHistory(page),
  });
}

export function useAIPicks() {
  return useQuery({
    queryKey: ['ai-picks'],
    queryFn: recommendationsApi.getAIPicks,
    refetchOnWindowFocus: false,
    refetchInterval: (query) => {
      const status = query.state.data?.recommendation?.status;
      return status === 'pending' ? 3000 : false;
    },
  });
}

export function useRefreshAIPicks() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: recommendationsApi.refreshAIPicks,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['ai-picks'] });
    },
  });
}

/** Premium only */
export function useGameDNA() {
  return useQuery({
    queryKey: ['game-dna'],
    queryFn: () => recommendationsApi.getGameDNA(),
    staleTime: 10 * 60 * 1000,
  });
}

export function useSubmitFeedback() {
  useQueryClient(); // available for future cache invalidation
  return useMutation({
    mutationFn: (payload: FeedbackCreate) => recommendationsApi.submitFeedback(payload),
    onSuccess: () => {
      // TODO: Optionally invalidate or optimistically update the recommendation cache
    },
  });
}
