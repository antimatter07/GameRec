import { Box, Center, Group, Loader, Pagination, Paper, Stack, Text, Title } from '@mantine/core';
import { useEffect, useState } from 'react';
import { GameFiltersBar } from '../../components/games/GameFilters';
import { GameCard } from '../../components/games/GameCard';
import { useGamesList } from '../../hooks/useGames';
import type { GameFilters } from '../../types/game';
import classes from './CatalogPage.module.css';

const DEFAULT_FILTERS: GameFilters = {};

/**
 * Paginated, filterable game catalog.
 * TODO: Sync page and filters with URL search params (useSearchParams)
 *       so users can share/bookmark filtered views
 * TODO: Add skeleton cards while loading (Mantine Skeleton)
 */
export default function CatalogPage() {
  const [page, setPage] = useState(1);
  const [filters, setFilters] = useState<GameFilters>(DEFAULT_FILTERS);
  const [searchInput, setSearchInput] = useState('');

  const { data, isLoading, isError } = useGamesList(page, 20, filters);

  const handleFiltersChange = (newFilters: GameFilters) => {
    setFilters(newFilters);
    setPage(1); // reset to page 1 on filter change
  };

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setFilters((current) => {
        const normalizedSearch = searchInput.trim() || undefined;
        if (current.search === normalizedSearch) {
          return current;
        }

        setPage(1);
        return { ...current, search: normalizedSearch };
      });
    }, 250);

    return () => window.clearTimeout(timeoutId);
  }, [searchInput]);

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Game <span className={classes.headerAccent}>Catalog</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Browse your collection-ready library feed with compact filters and consistent game cards.
          </Text>
        </div>
      </div>

      <Paper p="md" radius="md" withBorder className={classes.filterPanel}>
        <Group justify="space-between" align="flex-end" gap="sm" className={classes.panelHeader}>
          <div>
            <Text size="sm" fw={600} className={classes.panelTitle}>
              Browse games
            </Text>
            <Text size="xs" c="dimmed">
              Search by title, then narrow by genre, platform, or release year.
            </Text>
          </div>
          {data && (
            <Text size="xs" c="dimmed" className={classes.resultCount}>
              {data.total.toLocaleString()} games found
            </Text>
          )}
        </Group>

        <GameFiltersBar
          filters={filters}
          onChange={handleFiltersChange}
          onReset={() => {
            handleFiltersChange(DEFAULT_FILTERS);
            setSearchInput('');
          }}
          searchInput={searchInput}
          onSearchInputChange={setSearchInput}
        />
      </Paper>

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
          <Group justify="space-between" align="center" className={classes.sectionHeader}>
            <Title order={3} className={classes.sectionTitle}>
              Catalog results
            </Title>
            <Text size="xs" c="dimmed">
              Page {page} of {totalPages}
            </Text>
          </Group>

          <Box className={classes.grid}>
            {data.results.map((game) => (
              <GameCard key={game.id} game={game} showAdd />
            ))}
          </Box>

          <Center pt="sm">
            <Pagination color="violet" total={totalPages} value={page} onChange={setPage} radius="md" />
          </Center>
        </>
      )}
    </Stack>
  );
}
