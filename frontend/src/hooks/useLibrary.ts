import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { notifications } from '@mantine/notifications';
import { libraryApi } from '../api/library';
import type { BacklogFiltersParams } from '../api/library';
import type { LibraryEntryCreate, LibraryEntryUpdate, LibraryQueryParams } from '../types/library';

export function useLibrary(params: LibraryQueryParams = {}) {
  return useQuery({
    queryKey: ['library', params],
    queryFn: () => libraryApi.getAll(params),
    placeholderData: keepPreviousData,
    staleTime: 2 * 60 * 1000,
  });
}

export function useAddToLibrary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (payload: LibraryEntryCreate) => libraryApi.add(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });
}

export function useRemoveFromLibrary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (entryId: number) => libraryApi.remove(entryId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library'] });
    },
  });
}

export function useUpdateLibraryEntry() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ id, updates }: { id: number; updates: LibraryEntryUpdate }) =>
      libraryApi.update(id, updates),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ['library'] });
      queryClient.invalidateQueries({ queryKey: ['library-stats'] });
      queryClient.invalidateQueries({ queryKey: ['play-queue'] });
      if (data.queue_removed && data.next_game_candidate) {
        notifications.show({
          title: 'Removed from queue',
          message: `${data.next_game_candidate.game.name} is ready when you want to start it.`,
          color: 'teal',
        });
      }
    },
  });
}

export function useImportSteamLibrary() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (steamProfile: string) => libraryApi.importSteam(steamProfile),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['library'] });
      queryClient.invalidateQueries({ queryKey: ['library-stats'] });
    },
  });
}

export function useLibraryStats() {
  return useQuery({
    queryKey: ['library-stats'],
    queryFn: libraryApi.getStats,
  });
}

export function usePrioritizedBacklog(filters: BacklogFiltersParams = {}) {
  return useQuery({
    queryKey: ['library', 'backlog', 'prioritized', filters],
    queryFn: () => libraryApi.getPrioritizedBacklog(filters),
  });
}
