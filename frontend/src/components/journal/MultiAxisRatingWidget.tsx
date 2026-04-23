import { useState } from 'react';
import { Stack, Group, Text, Rating, Button, Paper } from '@mantine/core';
import { IconDeviceFloppy } from '@tabler/icons-react';
import { useGameRating, useUpsertRating } from '../../hooks/useJournal';
import type { MultiAxisRating } from '../../types/journal';

const AXES = [
  { key: 'story',     label: 'Story'     },
  { key: 'gameplay',  label: 'Gameplay'  },
  { key: 'visuals',   label: 'Visuals'   },
  { key: 'soundtrack', label: 'Soundtrack' },
  { key: 'overall',   label: 'Overall'   },
] as const;

type AxisKey = (typeof AXES)[number]['key'];

interface MultiAxisRatingWidgetProps {
  gameId:    number;
  readOnly?: boolean;
  compact?:  boolean;
}

export function MultiAxisRatingWidget({
  gameId,
  readOnly = false,
  compact  = false,
}: MultiAxisRatingWidgetProps) {
  const { data: existing, isLoading } = useGameRating(gameId);
  const upsertRating = useUpsertRating();

  const [localEdits, setLocalEdits] = useState<Partial<Record<AxisKey, number>>>({});

  const ratings: Record<AxisKey, number | null> = {
    story:      localEdits.story      ?? existing?.story      ?? null,
    gameplay:   localEdits.gameplay   ?? existing?.gameplay   ?? null,
    visuals:    localEdits.visuals    ?? existing?.visuals    ?? null,
    soundtrack: localEdits.soundtrack ?? existing?.soundtrack ?? null,
    overall:    localEdits.overall    ?? existing?.overall    ?? null,
  };
  const dirty = Object.keys(localEdits).length > 0;

  const handleChange = (axis: AxisKey, value: number) => {
    setLocalEdits((prev) => ({ ...prev, [axis]: value }));
  };

  const handleSave = () => {
    upsertRating.mutate(
      { gameId, data: ratings },
      { onSuccess: () => setLocalEdits({}) },
    );
  };

  if (isLoading) {
    return (
      <Paper p="sm" radius="sm" bg="var(--mantine-color-dark-6)">
        <Text size="xs" c="dimmed">Loading ratings…</Text>
      </Paper>
    );
  }

  return (
    <Stack gap={compact ? 4 : 'xs'}>
      {AXES.map(({ key, label }) => (
        <Group key={key} gap="xs" wrap="nowrap">
          <Text size={compact ? 'xs' : 'sm'} c="dimmed" w={compact ? 68 : 80} ta="right">
            {label}
          </Text>
          <Rating
            value={ratings[key] ?? 0}
            onChange={(v) => handleChange(key, v)}
            fractions={2}
            readOnly={readOnly}
            size={compact ? 'xs' : 'sm'}
            color="violet"
          />
          {ratings[key] !== null && (
            <Text
              size="xs"
              fw={600}
              c="dimmed"
              w={28}
              ta="right"
              style={{ fontVariantNumeric: 'tabular-nums' }}
            >
              {ratings[key]!.toFixed(1)}
            </Text>
          )}
        </Group>
      ))}
      {!readOnly && dirty && (
        <Group justify="flex-end" mt={4}>
          <Button
            size="xs"
            variant="light"
            color="violet"
            leftSection={<IconDeviceFloppy size={14} />}
            onClick={handleSave}
            loading={upsertRating.isPending}
          >
            Save ratings
          </Button>
        </Group>
      )}
    </Stack>
  );
}

// ─── Read-only bar version for dashboard cards ────────────────────────────────

interface RatingBarsProps {
  rating: MultiAxisRating;
  color?: string;
}

export function MultiAxisRatingBars({
  rating,
  color = 'var(--mantine-color-violet-5)',
}: RatingBarsProps) {
  return (
    <Stack gap={4}>
      {AXES.map(({ key, label }) => {
        const val = rating[key];
        if (val === null || val === undefined) return null;
        const pct = (val / 5) * 100;
        return (
          <div key={key} style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Text size="xs" c="dimmed" w={68} ta="right" style={{ flexShrink: 0 }}>
              {label}
            </Text>
            <div style={{ flex: 1, height: 6, background: 'var(--mantine-color-dark-8)', borderRadius: 3, overflow: 'hidden' }}>
              <div style={{ width: `${pct}%`, height: '100%', background: color, borderRadius: 3, transition: 'width 500ms ease' }} />
            </div>
            <Text size="xs" fw={600} c="dimmed" w={28} ta="right" style={{ fontVariantNumeric: 'tabular-nums', flexShrink: 0 }}>
              {val.toFixed(1)}
            </Text>
          </div>
        );
      })}
    </Stack>
  );
}
