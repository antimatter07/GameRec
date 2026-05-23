import { Box, Center, Group, Pagination, Paper, Skeleton, Stack, Text, Title } from '@mantine/core';
import { IconAlertCircle, IconSearchOff } from '@tabler/icons-react';
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
  const activeFilterCount = Object.values(filters).filter((value) => value !== undefined && value !== '').length;

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
              {activeFilterCount > 0 ? `, ${activeFilterCount} active filter${activeFilterCount === 1 ? '' : 's'}` : ''}
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
        <Box className={classes.grid} aria-label="Loading games">
          {Array.from({ length: 8 }, (_, index) => (
            <Paper key={index} withBorder radius="md" className={classes.skeletonCard}>
              <Skeleton height={220} radius={0} />
              <Stack gap="xs" p="sm">
                <Skeleton height={18} width="82%" />
                <Skeleton height={12} width="34%" />
                <Skeleton height={16} width="54%" />
                <Skeleton height={42} mt="auto" />
              </Stack>
            </Paper>
          ))}
        </Box>
      )}

      {isError && (
        <Paper withBorder radius="md" p="md" className={classes.statePanel}>
          <Group gap="sm" align="flex-start">
            <div className={classes.stateIcon}>
              <IconAlertCircle size={18} stroke={1.8} />
            </div>
            <div>
              <Text size="sm" fw={600}>
                Catalog could not load
              </Text>
              <Text size="xs" c="dimmed">
                Check the API connection, then refresh the page.
              </Text>
            </div>
          </Group>
        </Paper>
      )}

      {data && !isLoading && !isError && (
        <>
          <Group justify="space-between" align="center" className={classes.sectionHeader}>
            <Title order={3} className={classes.sectionTitle}>
              Catalog results
            </Title>
            <Text size="xs" c="dimmed">
              Page {page} of {totalPages}
            </Text>
          </Group>

          {data.results.length > 0 ? (
            <Box className={classes.grid}>
              {data.results.map((game) => (
                <GameCard key={game.id} game={game} showAdd />
              ))}
            </Box>
          ) : (
            <Paper withBorder radius="md" p="lg" className={classes.statePanel}>
              <Center className={classes.emptyState}>
                <div className={classes.stateIcon}>
                  <IconSearchOff size={18} stroke={1.8} />
                </div>
                <Text size="sm" fw={600}>
                  No games match these filters
                </Text>
                <Text size="xs" c="dimmed" ta="center">
                  Try a broader title search, a different genre, or clear the year filter.
                </Text>
              </Center>
            </Paper>
          )}

          {totalPages > 1 && (
            <Center pt="sm">
              <Pagination
                total={totalPages}
                value={page}
                onChange={setPage}
                radius="md"
                className={classes.pagination}
              />
            </Center>
          )}
        </>
      )}
    </Stack>
  );
}
