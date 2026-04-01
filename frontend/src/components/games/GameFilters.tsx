import { ActionIcon, Button, Group, NumberInput, Select, TextInput } from '@mantine/core';
import { IconSearch } from '@tabler/icons-react';
import type { GameFilters } from '../../types/game';

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

/**
 * Filter bar for the game catalog.
 * TODO: Sync filter state with URL search params (useSearchParams)
 */
export function GameFiltersBar({ filters, onChange, onReset, searchInput, onSearchInputChange }: GameFiltersProps) {
  const update = (partial: Partial<GameFilters>) => onChange({ ...filters, ...partial });
  const commitSearch = () => update({ search: searchInput || undefined });

  return (
    <Group wrap="wrap" gap="sm">
      <TextInput
        placeholder="Search games..."
        value={searchInput}
        onChange={(e) => onSearchInputChange(e.currentTarget.value)}
        onKeyDown={(e) => e.key === 'Enter' && commitSearch()}
        rightSection={
          <ActionIcon variant="subtle" onClick={commitSearch} aria-label="Search">
            <IconSearch size={16} />
          </ActionIcon>
        }
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
