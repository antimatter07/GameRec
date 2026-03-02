import { Button, Group, NumberInput, Select, TextInput } from '@mantine/core';
import type { GameFilters } from '../../types/game';

interface GameFiltersProps {
  filters: GameFilters;
  onChange: (filters: GameFilters) => void;
  onReset: () => void;
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

/**
 * Filter bar for the game catalog.
 * TODO: Debounce the search input (useDebouncedValue from @mantine/hooks)
 * TODO: Sync filter state with URL search params (useSearchParams)
 */
export function GameFiltersBar({ filters, onChange, onReset }: GameFiltersProps) {
  const update = (partial: Partial<GameFilters>) => onChange({ ...filters, ...partial });

  return (
    <Group wrap="wrap" gap="sm">
      <TextInput
        placeholder="Search games..."
        value={filters.search ?? ''}
        onChange={(e) => update({ search: e.currentTarget.value })}
        style={{ flex: 1, minWidth: 200 }}
      />

      <Select
        placeholder="Genre"
        clearable
        data={GENRE_OPTIONS}
        value={filters.genre ?? null}
        onChange={(v) => update({ genre: v ?? undefined })}
      />

      <Select
        placeholder="Platform"
        clearable
        data={PLATFORM_OPTIONS}
        value={filters.platform ?? null}
        onChange={(v) => update({ platform: v ?? undefined })}
      />

      <NumberInput
        placeholder="Year"
        min={1970}
        max={new Date().getFullYear()}
        value={filters.year ?? ''}
        onChange={(v) => update({ year: typeof v === 'number' ? v : undefined })}
        style={{ width: 100 }}
      />

      <Button variant="subtle" onClick={onReset}>
        Reset
      </Button>
    </Group>
  );
}
