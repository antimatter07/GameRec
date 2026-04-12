import { Card, Group, Progress, SimpleGrid, Stack, Text, Title } from '@mantine/core';
import { IconFlame } from '@tabler/icons-react';
import type { JournalStats } from '../../types/journal';

interface Props {
  stats: JournalStats;
}

export function JournalStatsCard({ stats }: Props) {
  const maxHours = Math.max(...stats.top_genres_this_month.map((g) => g.hours), 1);

  return (
    <Stack gap="md">
      <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="md">
        <StatItem label="Hours this month" value={`${stats.total_hours_this_month}h`} />
        <StatItem label="Hours all time"   value={`${stats.total_hours_all_time}h`} />
        <StatItem label="Sessions this month" value={String(stats.sessions_this_month)} />
        <StatItem label="Games this month"    value={String(stats.games_played_this_month)} />
      </SimpleGrid>

      {stats.current_streak_days > 0 && (
        <Card withBorder padding="sm" radius="md">
          <Group gap="xs">
            <IconFlame size={18} color="orange" />
            <Text fw={600}>
              {stats.current_streak_days}-day streak
            </Text>
            {stats.longest_streak_days > stats.current_streak_days && (
              <Text size="sm" c="dimmed">
                (best: {stats.longest_streak_days} days)
              </Text>
            )}
          </Group>
        </Card>
      )}

      {stats.top_genres_this_month.length > 0 && (
        <Card withBorder padding="md" radius="md">
          <Title order={5} mb="sm">Top genres this month</Title>
          <Stack gap="xs">
            {stats.top_genres_this_month.map((g) => (
              <Stack key={g.genre} gap={2}>
                <Group justify="space-between">
                  <Text size="sm">{g.genre}</Text>
                  <Text size="xs" c="dimmed">{g.hours}h</Text>
                </Group>
                <Progress value={(g.hours / maxHours) * 100} size="xs" />
              </Stack>
            ))}
          </Stack>
        </Card>
      )}
    </Stack>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <Card withBorder padding="sm" radius="md">
      <Text size="xs" c="dimmed">{label}</Text>
      <Text fw={700} size="xl">{value}</Text>
    </Card>
  );
}
