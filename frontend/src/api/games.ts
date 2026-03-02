import apiClient from './client';
import type { Game, GameFilters, PaginatedGames } from '../types/game';

export const gamesApi = {
  list: (page = 1, pageSize = 20, filters: GameFilters = {}) =>
    apiClient
      .get<PaginatedGames>('/games', {
        params: { page, page_size: pageSize, ...filters },
      })
      .then((r) => r.data),

  getById: (gameId: number) =>
    apiClient.get<Game>(`/games/${gameId}`).then((r) => r.data),
};
