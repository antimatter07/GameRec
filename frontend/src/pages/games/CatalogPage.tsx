import { Box, Center, Group, Pagination, Paper, Skeleton, Stack, Text, Title } from '@mantine/core';
import { IconAlertCircle, IconSearchOff } from '@tabler/icons-react';
import { useMemo } from 'react';
import { useSearchParams } from 'react-router';
import { GameFiltersBar } from '../../components/games/GameFilters';
import { GameCard } from '../../components/games/GameCard';
import { useGamesList } from '../../hooks/useGames';
import type { GameFilters } from '../../types/game';
import classes from './CatalogPage.module.css';

const DEFAULT_FILTERS: GameFilters = {
  library_state: 'all',
  sort: 'rating_desc',
};

function parseCatalogParams(searchParams: URLSearchParams) {
  const pageParam = Number(searchParams.get('page') ?? '1');
  const yearParam = Number(searchParams.get('year'));
  const minRatingParam = Number(searchParams.get('min_rating'));
  const maxHoursParam = Number(searchParams.get('max_hours'));

  const filters: GameFilters = {
    ...DEFAULT_FILTERS,
    search: searchParams.get('search') || undefined,
    genre: searchParams.get('genre') || undefined,
    platform: searchParams.get('platform') || undefined,
    year: Number.isFinite(yearParam) && yearParam > 0 ? yearParam : undefined,
    min_rating: Number.isFinite(minRatingParam) && minRatingParam > 0 ? minRatingParam : undefined,
    max_hours: Number.isFinite(maxHoursParam) && maxHoursParam > 0 ? maxHoursParam : undefined,
    library_state: (searchParams.get('library_state') as GameFilters['library_state']) || 'all',
    sort: (searchParams.get('sort') as GameFilters['sort']) || 'rating_desc',
  };

  return {
    page: Number.isFinite(pageParam) && pageParam > 0 ? pageParam : 1,
    filters,
  };
}

function writeCatalogParams(filters: GameFilters, page: number) {
  const params = new URLSearchParams();

  if (page > 1) params.set('page', String(page));
  if (filters.search) params.set('search', filters.search);
  if (filters.genre) params.set('genre', filters.genre);
  if (filters.platform) params.set('platform', filters.platform);
  if (filters.year) params.set('year', String(filters.year));
  if (filters.min_rating) params.set('min_rating', String(filters.min_rating));
  if (filters.max_hours) params.set('max_hours', String(filters.max_hours));
  if (filters.library_state && filters.library_state !== 'all') params.set('library_state', filters.library_state);
  if (filters.sort && filters.sort !== 'rating_desc') params.set('sort', filters.sort);

  return params;
}

/**
 * Paginated, filterable game catalog.
 * TODO: Sync page and filters with URL search params (useSearchParams)
 *       so users can share/bookmark filtered views
 */
export default function CatalogPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const { page, filters } = useMemo(() => parseCatalogParams(searchParams), [searchParams]);

  const { data, isLoading, isError } = useGamesList(page, 20, filters);

  const handleFiltersChange = (newFilters: GameFilters) => {
    setSearchParams(writeCatalogParams(newFilters, 1));
  };

  const totalPages = data ? Math.ceil(data.total / data.page_size) : 1;
  const activeFilterCount = Object.entries(filters).filter(([key, value]) => {
    if (value === undefined || value === '') return false;
    if (key === 'library_state' && value === 'all') return false;
    if (key === 'sort' && value === 'rating_desc') return false;
    return true;
  }).length;

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Game <span className={classes.headerAccent}>Catalog</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Browse a cinematic shelf of games with compact signals for quality, length, and save-worthy picks.
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
              Search by title, then narrow by platform, rating, runtime, release year, or library state.
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
          }}
          searchInput={filters.search ?? ''}
          onSearchInputChange={(value) => {
            handleFiltersChange({ ...filters, search: value.trim() || undefined });
          }}
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
                <button
                  type="button"
                  className={classes.clearButton}
                  onClick={() => {
                    handleFiltersChange(DEFAULT_FILTERS);
                  }}
                >
                  Clear filters
                </button>
              </Center>
            </Paper>
          )}

          {totalPages > 1 && (
            <Center pt="sm">
              <Pagination
                total={totalPages}
                value={page}
                onChange={(nextPage) => setSearchParams(writeCatalogParams(filters, nextPage))}
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
