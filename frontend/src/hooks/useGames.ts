import { useQuery } from '@tanstack/react-query';
import { gamesApi } from '../api/games';
import type { GameFilters } from '../types/game';

export function useGamesList(page: number, pageSize: number, filters: GameFilters) {
  return useQuery({
    queryKey: ['games', page, pageSize, filters],
    queryFn: () => gamesApi.list(page, pageSize, filters),
    // TODO: Set staleTime to a reasonable value (e.g. 5 minutes) since game data
    //       changes infrequently
    staleTime: 5 * 60 * 1000,
  });
}

export function useGame(gameId: number) {
  return useQuery({
    queryKey: ['game', gameId],
    queryFn: () => gamesApi.getById(gameId),
    enabled: !!gameId,
  });
}
