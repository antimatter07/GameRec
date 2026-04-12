import { useMemo } from 'react';
import {
  Anchor,
  Center,
  Loader,
  Pagination,
  Stack,
  Tabs,
  Text,
  Title,
} from '@mantine/core';
import { useState } from 'react';
import { Link } from 'react-router';
import { JournalFeedItem } from '../../components/journal/JournalFeedItem';
import { JournalStatsCard } from '../../components/journal/JournalStatsCard';
import { useJournalFeed, useJournalStats, useSessionsList } from '../../hooks/useJournal';
import type { SessionLog } from '../../types/journal';

const PAGE_SIZE = 20;

export default function JournalPage() {
  const [feedPage, setFeedPage] = useState(1);
  const [byGamePage, setByGamePage] = useState(1);

  const { data: feed,  isLoading: feedLoading  } = useJournalFeed(feedPage, PAGE_SIZE);
  const { data: stats, isLoading: statsLoading } = useJournalStats();
  // Fetch all sessions (large page) to group by game for the By Game tab
  const { data: allSessions } = useSessionsList(undefined, 1, 500);

  const gameGroups = useMemo(() => {
    if (!allSessions) return [];
    const map = new Map<number, { game: SessionLog['game']; totalMinutes: number; count: number }>();
    for (const s of allSessions.results) {
      const existing = map.get(s.game_id);
      if (existing) {
        existing.totalMinutes += s.duration_minutes ?? 0;
        existing.count += 1;
      } else {
        map.set(s.game_id, { game: s.game, totalMinutes: s.duration_minutes ?? 0, count: 1 });
      }
    }
    return Array.from(map.values()).sort((a, b) => b.totalMinutes - a.totalMinutes);
  }, [allSessions]);

  const byGameTotal = gameGroups.length;
  const byGameSlice = gameGroups.slice((byGamePage - 1) * PAGE_SIZE, byGamePage * PAGE_SIZE);

  // Group feed items by calendar date for section headers
  const feedGrouped = useMemo(() => {
    if (!feed) return [];
    const groups: Array<{ label: string; sessions: SessionLog[] }> = [];
    const today     = new Date().toDateString();
    const yesterday = new Date(Date.now() - 86_400_000).toDateString();

    for (const s of feed.results) {
      const d    = new Date(s.started_at);
      const key  = d.toDateString();
      const label =
        key === today     ? 'Today' :
        key === yesterday ? 'Yesterday' :
        d.toLocaleDateString(undefined, { month: 'long', day: 'numeric', year: 'numeric' });

      const last = groups[groups.length - 1];
      if (last && last.label === label) {
        last.sessions.push(s);
      } else {
        groups.push({ label, sessions: [s] });
      }
    }
    return groups;
  }, [feed]);

  return (
    <Stack gap="lg">
      <Title order={2}>Gaming Journal</Title>

      <Tabs defaultValue="feed">
        <Tabs.List>
          <Tabs.Tab value="feed">Feed</Tabs.Tab>
          <Tabs.Tab value="stats">Stats</Tabs.Tab>
          <Tabs.Tab value="by-game">By Game</Tabs.Tab>
        </Tabs.List>

        {/* ── Feed ── */}
        <Tabs.Panel value="feed" pt="md">
          {feedLoading ? (
            <Center h={200}><Loader /></Center>
          ) : !feed || feed.total === 0 ? (
            <Text c="dimmed">No sessions logged yet. Head to a game page and log your first session!</Text>
          ) : (
            <Stack gap="lg">
              {feedGrouped.map((group) => (
                <Stack key={group.label} gap="xs">
                  <Text fw={600} size="sm" c="dimmed">{group.label}</Text>
                  {group.sessions.map((s) => (
                    <JournalFeedItem key={s.id} session={s} />
                  ))}
                </Stack>
              ))}
              {feed.total > PAGE_SIZE && (
                <Center>
                  <Pagination
                    value={feedPage}
                    onChange={setFeedPage}
                    total={Math.ceil(feed.total / PAGE_SIZE)}
                  />
                </Center>
              )}
            </Stack>
          )}
        </Tabs.Panel>

        {/* ── Stats ── */}
        <Tabs.Panel value="stats" pt="md">
          {statsLoading ? (
            <Center h={200}><Loader /></Center>
          ) : !stats ? (
            <Text c="dimmed">No data yet.</Text>
          ) : (
            <JournalStatsCard stats={stats} />
          )}
        </Tabs.Panel>

        {/* ── By Game ── */}
        <Tabs.Panel value="by-game" pt="md">
          {!allSessions ? (
            <Center h={200}><Loader /></Center>
          ) : byGameTotal === 0 ? (
            <Text c="dimmed">No sessions logged yet.</Text>
          ) : (
            <Stack gap="xs">
              {byGameSlice.map(({ game, totalMinutes, count }) => (
                <Anchor key={game.id} component={Link} to={`/games/${game.id}`} underline="never">
                  <Stack gap={2} style={{ padding: '8px 0', borderBottom: '1px solid var(--mantine-color-default-border)' }}>
                    <Text fw={600}>{game.name}</Text>
                    <Text size="sm" c="dimmed">
                      {count} session{count !== 1 ? 's' : ''} ·{' '}
                      {totalMinutes >= 60
                        ? `${(totalMinutes / 60).toFixed(1)}h`
                        : `${totalMinutes}m`}{' '}
                      logged
                    </Text>
                  </Stack>
                </Anchor>
              ))}
              {byGameTotal > PAGE_SIZE && (
                <Center mt="sm">
                  <Pagination
                    value={byGamePage}
                    onChange={setByGamePage}
                    total={Math.ceil(byGameTotal / PAGE_SIZE)}
                  />
                </Center>
              )}
            </Stack>
          )}
        </Tabs.Panel>
      </Tabs>
    </Stack>
  );
}
