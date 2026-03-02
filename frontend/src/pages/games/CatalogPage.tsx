import { Center, Loader, Pagination, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import { useState } from 'react';
import { GameFiltersBar } from '../../components/games/GameFilters';
import { GameCard } from '../../components/games/GameCard';
import { useGamesList } from '../../hooks/useGames';
import type { GameFilters } from '../../types/game';

const DEFAULT_FILTERS: GameFilters = {};

/**
 * Paginated, filterable game catalog.
 * TODO: Sync page and filters with URL search params (useSearchParams)
 *       so users can share/bookmark filtered views
 * TODO: Add skeleton cards while loading (Mantine Skeleton)
 */
export default function CatalogPage() {
  const [page, setPage]       = useState(1);
  const [filters, setFilters] = useState<GameFilters>(DEFAULT_FILTERS);

  const { data, isLoading, isError } = useGamesList(page, 20, filters);

  const handleFiltersChange = (newFilters: GameFilters) => {
    setFilters(newFilters);
    setPage(1); // reset to page 1 on filter change
  };

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  return (
    <Stack gap="md">
      <Title order={2}>Game Catalog</Title>

      <GameFiltersBar
        filters={filters}
        onChange={handleFiltersChange}
        onReset={() => handleFiltersChange(DEFAULT_FILTERS)}
      />

      {isLoading && (
        <Center h={300}>
          <Loader />
        </Center>
      )}

      {isError && (
        <Text c="red">Failed to load games. Please try again.</Text>
      )}

      {data && (
        <>
          <Text size="sm" c="dimmed">
            {data.total.toLocaleString()} games found
          </Text>

          <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }}>
            {data.results.map((game) => (
              <GameCard key={game.id} game={game} showAdd />
            ))}
          </SimpleGrid>

          <Center>
            <Pagination total={totalPages} value={page} onChange={setPage} />
          </Center>
        </>
      )}
    </Stack>
  );
}
