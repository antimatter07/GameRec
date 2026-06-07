import { Button, Group, Select, TextInput } from '@mantine/core';
import { IconRefresh, IconSearch } from '@tabler/icons-react';
import type { GameFilters } from '../../types/game';
import classes from './GameFilters.module.css';

interface GameFiltersProps {
  filters: GameFilters;
  onChange: (filters: GameFilters) => void;
  onReset: () => void;
  searchInput: string;
  onSearchInputChange: (value: string) => void;
  onSearchCommit: () => void;
}

// TODO: Fetch these dynamically from RAWG /genres and /platforms endpoints
//       (or from your own DB after syncing) and populate the selects
const GENRE_OPTIONS = [
  { value: 'action', label: 'Action' },
  { value: 'rpg', label: 'RPG' },
  { value: 'strategy', label: 'Strategy' },
  { value: 'shooter', label: 'Shooter' },
  { value: 'adventure', label: 'Adventure' },
  { value: 'puzzle', label: 'Puzzle' },
  { value: 'sports', label: 'Sports' },
];

const PLATFORM_OPTIONS = [
  { value: 'pc', label: 'PC' },
  { value: 'playstation5', label: 'PlayStation 5' },
  { value: 'xbox-series-x', label: 'Xbox Series X' },
  { value: 'nintendo-switch', label: 'Nintendo Switch' },
];

const YEAR_OPTIONS = Array.from({ length: new Date().getFullYear() - 1979 }, (_, index) => {
  const year = String(new Date().getFullYear() - index);
  return { value: year, label: year };
});

const RATING_OPTIONS = [
  { value: '4', label: '4.0+' },
  { value: '3.5', label: '3.5+' },
  { value: '3', label: '3.0+' },
];

const LENGTH_OPTIONS = [
  { value: '10', label: 'Under 10h' },
  { value: '25', label: 'Under 25h' },
  { value: '50', label: 'Under 50h' },
];

const LIBRARY_OPTIONS = [
  { value: 'all', label: 'All games' },
  { value: 'not_saved', label: 'Not saved' },
  { value: 'saved', label: 'Saved' },
];

const SORT_OPTIONS = [
  { value: 'rating_desc', label: 'Top rated' },
  { value: 'released_desc', label: 'Newest' },
  { value: 'playtime_asc', label: 'Shortest' },
  { value: 'name_asc', label: 'A-Z' },
];

/**
 * Filter bar for the game catalog.
 * TODO: Sync filter state with URL search params (useSearchParams)
 */
export function GameFiltersBar({
  filters,
  onChange,
  onReset,
  searchInput,
  onSearchInputChange,
  onSearchCommit,
}: GameFiltersProps) {
  const update = (partial: Partial<GameFilters>) => onChange({ ...filters, ...partial });

  return (
    <Group className={classes.filtersRow} wrap="wrap" gap="sm" align="center">
      <TextInput
        className={classes.searchInput}
        aria-label="Search games"
        placeholder="Search games…"
        value={searchInput}
        onChange={(e) => onSearchInputChange(e.currentTarget.value)}
        onKeyDown={(e) => e.key === 'Enter' && onSearchCommit()}
        leftSection={<IconSearch size={18} stroke={1.7} />}
        size="md"
        radius="sm"
      />

      <Select
        className={classes.filterSelect}
        aria-label="Filter by genre"
        placeholder="Genre"
        clearable
        data={GENRE_OPTIONS}
        value={filters.genre ?? null}
        onChange={(v) => update({ genre: v ?? undefined })}
        size="md"
        radius="sm"
      />

      <Select
        className={classes.filterSelect}
        aria-label="Filter by platform"
        placeholder="Platform"
        clearable
        data={PLATFORM_OPTIONS}
        value={filters.platform ?? null}
        onChange={(v) => update({ platform: v ?? undefined })}
        size="md"
        radius="sm"
      />

      <Select
        className={classes.yearSelect}
        aria-label="Filter by release year"
        placeholder="Year"
        clearable
        data={YEAR_OPTIONS}
        value={filters.year ? String(filters.year) : null}
        onChange={(v) => update({ year: v ? Number(v) : undefined })}
        size="md"
        radius="sm"
      />

      <Select
        className={classes.compactSelect}
        aria-label="Filter by minimum rating"
        placeholder="Rating"
        clearable
        data={RATING_OPTIONS}
        value={filters.min_rating ? String(filters.min_rating) : null}
        onChange={(v) => update({ min_rating: v ? Number(v) : undefined })}
        size="md"
        radius="sm"
      />

      <Select
        className={classes.compactSelect}
        aria-label="Filter by playtime length"
        placeholder="Length"
        clearable
        data={LENGTH_OPTIONS}
        value={filters.max_hours ? String(filters.max_hours) : null}
        onChange={(v) => update({ max_hours: v ? Number(v) : undefined })}
        size="md"
        radius="sm"
      />

      <Select
        className={classes.filterSelect}
        aria-label="Filter by library state"
        data={LIBRARY_OPTIONS}
        value={filters.library_state ?? 'all'}
        onChange={(v) => update({ library_state: (v as GameFilters['library_state']) ?? 'all' })}
        size="md"
        radius="sm"
        allowDeselect={false}
      />

      <Select
        className={classes.filterSelect}
        aria-label="Sort catalog"
        data={SORT_OPTIONS}
        value={filters.sort ?? 'rating_desc'}
        onChange={(v) => update({ sort: (v as GameFilters['sort']) ?? 'rating_desc' })}
        size="md"
        radius="sm"
        allowDeselect={false}
      />

      <Button
        className={classes.resetButton}
        variant="subtle"
        leftSection={<IconRefresh size={16} stroke={1.8} />}
        onClick={onReset}
      >
        Reset
      </Button>
    </Group>
  );
}
