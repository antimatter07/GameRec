import apiClient from './client';
import type { AIPicksState, FeedbackCreate, GameDNA, Recommendation } from '../types/recommendation';

export interface RecommendationFilters {
  genre?: string;
  platform?: string;
  release_year?: number;
}

export const recommendationsApi = {
  get: (filters: RecommendationFilters = {}) =>
    apiClient
      .get<Recommendation>('/recommendations', { params: filters })
      .then((r) => r.data),

  getHistory: (page = 1, pageSize = 10) =>
    apiClient
      .get<Recommendation[]>('/recommendations/history', {
        params: { page, page_size: pageSize },
      })
      .then((r) => r.data),

  getAIPicks: () =>
    apiClient.get<AIPicksState>('/recommendations/ai-picks').then((r) => r.data),

  refreshAIPicks: () =>
    apiClient.post<AIPicksState>('/recommendations/ai-picks/refresh').then((r) => r.data),

  /** Premium only */
  getGameDNA: () =>
    apiClient.get<GameDNA>('/recommendations/game-dna').then((r) => r.data),

  submitFeedback: (payload: FeedbackCreate) =>
    apiClient.post('/feedback', payload).then((r) => r.data),
};
