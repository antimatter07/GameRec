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

/** Premium only */
export function useGameDNA() {
  return useQuery({
    queryKey: ['game-dna'],
    queryFn: () => recommendationsApi.getGameDNA(),
    staleTime: 10 * 60 * 1000,
  });
}

export function useSubmitFeedback() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: FeedbackCreate) => recommendationsApi.submitFeedback(payload),
    onSuccess: () => {
      // TODO: Optionally invalidate or optimistically update the recommendation cache
    },
  });
}
