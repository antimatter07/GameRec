import { Group, NumberInput, Select, SegmentedControl, Text } from '@mantine/core';
import type { BacklogFiltersParams } from '../../api/library';
import classes from './BacklogTools.module.css';

interface BacklogFiltersProps {
  filters: BacklogFiltersParams;
  onChange: (filters: BacklogFiltersParams) => void;
}

const SORT_OPTIONS = [
  { label: 'Best match', value: 'score' },
  { label: 'Shortest first', value: 'playtime_asc' },
  { label: 'Longest first', value: 'playtime_desc' },
  { label: 'Date added', value: 'added_at' },
];

const GENRE_OPTIONS = [
  'Action', 'RPG', 'Strategy', 'Puzzle', 'Adventure', 'Shooter',
  'Simulation', 'Sports', 'Horror', 'Platformer', 'Fighting', 'Racing',
];

export function BacklogFilters({ filters, onChange }: BacklogFiltersProps) {
  return (
    <Group className={classes.filters} wrap="wrap">
      <Select
        className={classes.control}
        label="Mood / Genre"
        placeholder="Any genre"
        clearable
        data={GENRE_OPTIONS}
        value={filters.mood_genre ?? null}
        onChange={(v) => onChange({ ...filters, mood_genre: v ?? undefined, page: 1 })}
      />

      <NumberInput
        className={classes.control}
        label="Max hours to beat"
        placeholder="Any length"
        min={1}
        max={999}
        value={filters.max_hours ?? ''}
        onChange={(v) =>
          onChange({ ...filters, max_hours: v === '' ? undefined : Number(v), page: 1 })
        }
      />

      <Group gap={6} align="flex-start" className={classes.sortGroup}>
        <Text className={classes.sortLabel}>Sort</Text>
        <SegmentedControl
          size="sm"
          color="ember"
          data={SORT_OPTIONS}
          value={filters.sort ?? 'score'}
          onChange={(v) =>
            onChange({ ...filters, sort: v as BacklogFiltersParams['sort'], page: 1 })
          }
        />
      </Group>
    </Group>
  );
}
