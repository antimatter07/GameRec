import { Badge, Button, Group, Paper, Stack, Text } from '@mantine/core';
import { IconClock, IconDeviceGamepad2, IconPlayerPlay, IconStar } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import type { PrioritizedBacklogItem } from '../../api/library';
import { useUpdateLibraryEntry } from '../../hooks/useLibrary';
import classes from './BacklogTools.module.css';

interface BacklogPriorityCardProps {
  item: PrioritizedBacklogItem;
}

export function BacklogPriorityCard({ item }: BacklogPriorityCardProps) {
  const { game, playtime_hours, taste_score, stale_months } = item;
  const updateEntry = useUpdateLibraryEntry();
  const navigate = useNavigate();

  const handleStartPlaying = () => {
    updateEntry.mutate({ id: item.entry_id, updates: { status: 'playing' } });
  };

  return (
    <Paper withBorder radius="md" p="sm" className={classes.priorityCard}>
      <Group gap="sm" align="flex-start" wrap="nowrap">
        <div className={classes.cover}>
          {game.background_image ? (
            <img src={game.background_image} alt="" />
          ) : (
            <div className={classes.coverFallback}>
              <IconDeviceGamepad2 size={24} stroke={1.6} />
            </div>
          )}
        </div>

        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <button
            type="button"
            className={classes.titleButton}
            onClick={() => navigate(`/games/${game.id}`)}
          >
            {game.name}
          </button>

          <Group gap={4} wrap="wrap">
            {game.genres.slice(0, 2).map((g) => (
              <Badge key={g.id} size="xs" variant="light">{g.name}</Badge>
            ))}
          </Group>

          <Group gap="xs">
            {playtime_hours != null && (
              <Group gap={4}>
                <IconClock size={12} />
                <Text className={classes.metaText}>~{playtime_hours.toFixed(0)}h to beat</Text>
              </Group>
            )}

            {taste_score != null && (
              <Group gap={4}>
                <IconStar size={12} />
                <Text className={classes.metaText}>{Math.round(taste_score * 100)}% match</Text>
              </Group>
            )}
          </Group>

          {stale_months != null && stale_months >= 6 && (
            <Text size="xs" c="orange">Added {stale_months} months ago</Text>
          )}
        </Stack>

        <Stack gap={4} style={{ flexShrink: 0 }}>
          <Button
            size="xs"
            variant="light"
            color="ember"
            leftSection={<IconPlayerPlay size={14} />}
            onClick={handleStartPlaying}
            loading={updateEntry.isPending}
          >
            Play
          </Button>
        </Stack>
      </Group>
    </Paper>
  );
}
