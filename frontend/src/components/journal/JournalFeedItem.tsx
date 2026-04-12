import { Badge, Card, Group, Image, Stack, Text } from '@mantine/core';
import { IconClock, IconFlag } from '@tabler/icons-react';
import type { SessionLog } from '../../types/journal';

interface Props {
  session: SessionLog;
}

export function JournalFeedItem({ session }: Props) {
  const date = new Date(session.started_at).toLocaleDateString(undefined, {
    month: 'short',
    day:   'numeric',
    year:  'numeric',
  });

  return (
    <Card withBorder padding="sm" radius="md">
      <Group align="flex-start" wrap="nowrap">
        <Image
          src={session.game.background_image ?? undefined}
          width={72}
          height={48}
          radius="sm"
          alt={session.game.name}
          fallbackSrc="https://placehold.co/72x48?text=?"
        />

        <Stack gap={4} style={{ flex: 1, minWidth: 0 }}>
          <Group justify="space-between" wrap="nowrap">
            <Text fw={600} size="sm" truncate>
              {session.game.name}
            </Text>
            <Text size="xs" c="dimmed" style={{ whiteSpace: 'nowrap' }}>
              {date}
            </Text>
          </Group>

          <Group gap="xs">
            {session.duration_minutes != null && (
              <Badge size="xs" variant="light" leftSection={<IconClock size={10} />}>
                {session.duration_minutes >= 60
                  ? `${(session.duration_minutes / 60).toFixed(1)}h`
                  : `${session.duration_minutes}m`}
              </Badge>
            )}
            {session.is_milestone && (
              <Badge size="xs" color="yellow" variant="light" leftSection={<IconFlag size={10} />}>
                {session.milestone_label ?? 'Milestone'}
              </Badge>
            )}
          </Group>

          {session.notes && (
            <Text size="xs" c="dimmed" lineClamp={2}>
              {session.notes}
            </Text>
          )}
        </Stack>
      </Group>
    </Card>
  );
}
