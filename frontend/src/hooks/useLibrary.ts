import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '../api/library';
import type { BacklogFiltersParams } from '../api/library';
import type { LibraryEntryCreate, LibraryEntryUpdate } from '../types/library';

export function useLibrary() {
  return useQuery({
    queryKey: ['library'],
    queryFn: libraryApi.getAll,
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
