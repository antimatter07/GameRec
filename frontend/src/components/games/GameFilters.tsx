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

/**
 * Filter bar for the game catalog.
 * TODO: Sync filter state with URL search params (useSearchParams)
 */
export function GameFiltersBar({ filters, onChange, onReset, searchInput, onSearchInputChange }: GameFiltersProps) {
  const update = (partial: Partial<GameFilters>) => onChange({ ...filters, ...partial });
  const commitSearch = () => update({ search: searchInput.trim() || undefined });

  return (
    <Group className={classes.filtersRow} wrap="wrap" gap="md" align="center">
      <TextInput
        className={classes.searchInput}
        placeholder="Search games..."
        value={searchInput}
        onChange={(e) => onSearchInputChange(e.currentTarget.value)}
        onKeyDown={(e) => e.key === 'Enter' && commitSearch()}
        onBlur={commitSearch}
        leftSection={<IconSearch size={18} stroke={1.7} />}
        size="md"
        radius="md"
      />

      <Select
        className={classes.filterSelect}
        placeholder="Genre"
        clearable
        data={GENRE_OPTIONS}
        value={filters.genre ?? null}
        onChange={(v) => update({ genre: v ?? undefined })}
        size="md"
        radius="md"
      />

      <Select
        className={classes.filterSelect}
        placeholder="Platform"
        clearable
        data={PLATFORM_OPTIONS}
        value={filters.platform ?? null}
        onChange={(v) => update({ platform: v ?? undefined })}
        size="md"
        radius="md"
      />

      <Select
        className={classes.yearSelect}
        placeholder="Year"
        clearable
        data={YEAR_OPTIONS}
        value={filters.year ? String(filters.year) : null}
        onChange={(v) => update({ year: v ? Number(v) : undefined })}
        size="md"
        radius="md"
      />

      <Button
        className={classes.resetButton}
        variant="subtle"
        color="violet"
        leftSection={<IconRefresh size={16} stroke={1.8} />}
        onClick={onReset}
      >
        Reset
      </Button>
    </Group>
  );
}
