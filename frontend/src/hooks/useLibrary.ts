import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '../api/library';
import type { LibraryEntryCreate } from '../types/library';

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
