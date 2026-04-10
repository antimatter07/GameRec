import { Badge, Button, Group, Image, Paper, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconClock, IconStar } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import type { PrioritizedBacklogItem } from '../../api/library';
import { useUpdateLibraryEntry } from '../../hooks/useLibrary';
import { useEnqueueGame, usePlayQueue } from '../../hooks/usePlayQueue';

interface BacklogPriorityCardProps {
  item: PrioritizedBacklogItem;
}

export function BacklogPriorityCard({ item }: BacklogPriorityCardProps) {
  const { game, playtime_hours, taste_score, stale_months } = item;
  const updateEntry = useUpdateLibraryEntry();
  const enqueue = useEnqueueGame();
  const { data: queue } = usePlayQueue();
  const navigate = useNavigate();

  const isQueued = queue?.entries.some((e) => e.entry_id === item.entry_id) ?? false;

  const handleStartPlaying = () => {
    updateEntry.mutate({ id: item.entry_id, updates: { status: 'playing' } });
  };

  const handleEnqueue = () => {
    enqueue.mutate(item.entry_id, {
      onSuccess: (data) => {
        const pos = data.entries.find((e) => e.entry_id === item.entry_id)?.position;
        notifications.show({
          message: `Added to queue${pos != null ? ` at position ${pos}` : ''}`,
          color: 'grape',
        });
      },
    });
  };

  return (
    <Paper withBorder radius="md" p="sm">
      <Group gap="sm" align="flex-start" wrap="nowrap">
        <Image
          src={game.background_image ?? undefined}
          w={80}
          h={60}
          radius="sm"
          fallbackSrc="https://placehold.co/80x60?text=?"
          style={{ flexShrink: 0, objectFit: 'cover' }}
        />

        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Text
            fw={600}
            size="sm"
            lineClamp={1}
            style={{ cursor: 'pointer' }}
            onClick={() => navigate(`/games/${game.id}`)}
          >
            {game.name}
          </Text>

          <Group gap={4} wrap="wrap">
            {game.genres.slice(0, 2).map((g) => (
              <Badge key={g.id} size="xs" variant="light">{g.name}</Badge>
            ))}
          </Group>

          <Group gap="xs">
            {playtime_hours != null && (
              <Group gap={4}>
                <IconClock size={12} />
                <Text size="xs" c="dimmed">~{playtime_hours.toFixed(0)}h to beat</Text>
              </Group>
            )}

            {taste_score != null && (
              <Group gap={4}>
                <IconStar size={12} />
                <Text size="xs" c="dimmed">{Math.round(taste_score * 100)}% match</Text>
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
            onClick={handleStartPlaying}
            loading={updateEntry.isPending}
          >
            Play
          </Button>
          <Button
            size="xs"
            variant={isQueued ? 'outline' : 'light'}
            color="grape"
            disabled={isQueued}
            onClick={handleEnqueue}
            loading={enqueue.isPending}
          >
            {isQueued ? 'In Queue' : '+ Queue'}
          </Button>
        </Stack>
      </Group>
    </Paper>
  );
}
