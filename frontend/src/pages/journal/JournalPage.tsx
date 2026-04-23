import { useState } from 'react';
import {
  Paper,
  Text,
  Group,
  Button,
  Tabs,
  Stack,
  Loader,
  Center,
  Anchor,
  SimpleGrid,
} from '@mantine/core';
import { IconPlus, IconTimeline, IconChartBar, IconMoodSmile } from '@tabler/icons-react';
import {
  useJournalStats,
  useJournalFeed,
  useAllRatings,
  useEmotionStats,
} from '../../hooks/useJournal';
import {
  MetricCards,
  GenreHoursChart,
  WeeklyActivityCard,
  EmotionSummaryCard,
  BacklogProgressCard,
  JournalFeedItem,
  LogSessionModal,
  MultiAxisRatingBars,
} from '../../components/journal';
import classes from '../../components/journal/Journal.module.css';
import { EMOTION_CONFIG } from '../../types/journal';

const RATING_COLORS = [
  'var(--mantine-color-violet-5)',
  'var(--mantine-color-teal-5)',
  'var(--mantine-color-pink-5)',
  'var(--mantine-color-blue-5)',
  'var(--mantine-color-orange-5)',
  'var(--mantine-color-grape-5)',
];

const EMOTION_CSS_COLORS: Record<string, string> = {
  frustrated:   'var(--mantine-color-orange-6)',
  happy:        'var(--mantine-color-yellow-5)',
  sad:          'var(--mantine-color-blue-4)',
  angry:        'var(--mantine-color-red-6)',
  relaxed:      'var(--mantine-color-teal-5)',
  bored:        'var(--mantine-color-gray-5)',
  proud:        'var(--mantine-color-yellow-7)',
  creeped_out:  'var(--mantine-color-grape-6)',
  disappointed: 'var(--mantine-color-gray-6)',
};

export default function JournalPage() {
  const [activeTab,    setActiveTab]    = useState<string | null>('overview');
  const [logModalOpen, setLogModalOpen] = useState(false);

  const { data: stats,        isLoading: statsLoading    } = useJournalStats();
  const { data: feedData,     isLoading: feedLoading     } = useJournalFeed();
  const { data: ratings,      isLoading: ratingsLoading  } = useAllRatings();
  const { data: emotionStats, isLoading: emotionsLoading } = useEmotionStats({ period: '30d' });

  const isLoading = statsLoading || feedLoading || ratingsLoading || emotionsLoading;

  if (isLoading && !stats) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="violet" size="md" />
          <Text size="sm" c="dimmed">Loading your journal…</Text>
        </Stack>
      </Center>
    );
  }

  const currentMonth = new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' });

  return (
    <div className={classes.journalPage}>
      {/* ─── Header ─────────────────────────────────────────────────────────── */}
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Gaming <span className={classes.headerAccent}>Journal</span>
          </Text>
          <Text size="xs" c="dimmed">
            Your play sessions, moods, and progress — all in one place
          </Text>
        </div>
        <Button leftSection={<IconPlus size={16} />} color="violet" onClick={() => setLogModalOpen(true)}>
          Log session
        </Button>
      </div>

      {/* ─── Tabs ────────────────────────────────────────────────────────────── */}
      <Tabs value={activeTab} onChange={setActiveTab} variant="pills" color="violet" mb="lg">
        <Tabs.List>
          <Tabs.Tab value="overview" leftSection={<IconChartBar size={14} />}>Overview</Tabs.Tab>
          <Tabs.Tab value="feed"     leftSection={<IconTimeline size={14} />}>Feed</Tabs.Tab>
          <Tabs.Tab value="mood"     leftSection={<IconMoodSmile size={14} />}>Mood profile</Tabs.Tab>
        </Tabs.List>

        {/* ════ OVERVIEW ════════════════════════════════════════════════════ */}
        <Tabs.Panel value="overview" pt="lg">
          {stats && <MetricCards stats={stats} />}

          <div className={classes.twoColMain}>
            <Paper p="md" radius="md" withBorder>
              <Group justify="space-between" mb="sm">
                <Text size="sm" fw={600}>Hours per genre — {currentMonth}</Text>
              </Group>
              {stats && <GenreHoursChart genres={stats.top_genres_this_month} />}
              {stats && stats.top_genres_this_month.length > 0 && (
                <div className={classes.insightBox}>
                  You spent{' '}
                  <Text span fw={600} c="var(--mantine-color-text)">
                    {stats.total_hours_this_month.toFixed(0)} hours
                  </Text>{' '}
                  gaming this month.
                  {stats.top_genres_this_month[0] && (
                    <>
                      {' '}{stats.top_genres_this_month[0].genre} dominated at{' '}
                      <Text span fw={600} c="var(--mantine-color-text)">
                        {Math.round((stats.top_genres_this_month[0].hours / stats.total_hours_this_month) * 100)}%
                      </Text>{' '}
                      of total playtime.
                    </>
                  )}
                </div>
              )}
            </Paper>

            <Paper p="md" radius="md" withBorder>
              <Text size="sm" fw={600} mb="sm">Weekly activity</Text>
              {stats && (
                <WeeklyActivityCard
                  dailyHours={stats.daily_hours_this_week}
                  currentStreak={stats.current_streak_days}
                  longestStreak={stats.longest_streak_days}
                />
              )}
            </Paper>
          </div>

          <div className={classes.twoColEqual}>
            <Paper p="md" radius="md" withBorder>
              <Text size="sm" fw={600} mb="sm">How gaming makes you feel</Text>
              <EmotionSummaryCard
                emotionStats={emotionStats ?? null}
                dominantEmotion={stats?.dominant_emotion_this_month ?? null}
                coveragePct={stats?.emotion_coverage_pct ?? null}
                totalSessions={stats?.sessions_this_month ?? 0}
              />
            </Paper>

            <Paper p="md" radius="md" withBorder>
              <Text size="sm" fw={600} mb="sm">Backlog progress</Text>
              {stats && (
                <BacklogProgressCard
                  completed={stats.games_completed}
                  playing={stats.games_playing}
                  backlog={stats.games_in_backlog}
                />
              )}
            </Paper>
          </div>

          {/* Recent sessions */}
          <Paper p="md" radius="md" withBorder mb="md">
            <Group justify="space-between" mb="sm">
              <Text size="sm" fw={600}>Recent sessions</Text>
              <Anchor size="xs" c="violet.4" onClick={() => setActiveTab('feed')}>
                View all →
              </Anchor>
            </Group>
            <Stack gap="xs">
              {feedData?.items.slice(0, 5).map((item) => (
                <JournalFeedItem key={item.session.id} session={item.session} />
              ))}
              {(!feedData || feedData.items.length === 0) && (
                <Text size="sm" c="dimmed" ta="center" py="lg">
                  No sessions logged yet. Click "Log session" to get started!
                </Text>
              )}
            </Stack>
          </Paper>

          {/* Multi-axis ratings */}
          {ratings && ratings.length > 0 && (
            <Paper p="md" radius="md" withBorder>
              <Text size="sm" fw={600} mb="sm">Multi-axis ratings</Text>
              <div className={classes.ratingWidgetGrid}>
                {ratings.map((r, i) => (
                  <div key={r.id} className={classes.ratingGameCard}>
                    <div className={classes.ratingGameTitle}>{r.game_title ?? `Game #${r.game_id}`}</div>
                    <MultiAxisRatingBars rating={r} color={RATING_COLORS[i % RATING_COLORS.length]} />
                  </div>
                ))}
              </div>
            </Paper>
          )}
        </Tabs.Panel>

        {/* ════ FEED ════════════════════════════════════════════════════════ */}
        <Tabs.Panel value="feed" pt="lg">
          <Stack gap="xs">
            {feedData?.items.map((item) => (
              <JournalFeedItem key={item.session.id} session={item.session} />
            ))}
            {(!feedData || feedData.items.length === 0) && (
              <Text size="sm" c="dimmed" ta="center" py="xl">
                Your journal is empty. Log your first session to see it here.
              </Text>
            )}
          </Stack>
        </Tabs.Panel>

        {/* ════ MOOD PROFILE ════════════════════════════════════════════════ */}
        <Tabs.Panel value="mood" pt="lg">
          <Paper p="md" radius="md" withBorder mb="md">
            <Text size="sm" fw={600} mb="md">Emotion breakdown — last 30 days</Text>
            <EmotionSummaryCard
              emotionStats={emotionStats ?? null}
              dominantEmotion={stats?.dominant_emotion_this_month ?? null}
              coveragePct={stats?.emotion_coverage_pct ?? null}
              totalSessions={stats?.sessions_this_month ?? 0}
            />
          </Paper>

          {emotionStats && emotionStats.per_game.length > 0 && (
            <Paper p="md" radius="md" withBorder mb="md">
              <Text size="sm" fw={600} mb="sm">Emotions by game</Text>
              <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
                {emotionStats.per_game.map((g) => {
                  const config = EMOTION_CONFIG[g.dominant_emotion];
                  return (
                    <Group key={g.game_id} gap="sm" wrap="nowrap">
                      <div style={{ width: 40, height: 40, borderRadius: 8, background: 'var(--mantine-color-dark-6)', overflow: 'hidden', flexShrink: 0, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                        {g.cover_url
                          ? <img src={g.cover_url} alt={g.game_title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          : <Text size="md">🎮</Text>}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Text size="xs" fw={600} truncate>{g.game_title}</Text>
                        <Text size="xs" c="dimmed">
                          {config?.label ?? g.dominant_emotion} · {g.session_count} sessions
                        </Text>
                      </div>
                      <div style={{ width: 10, height: 10, borderRadius: '50%', background: EMOTION_CSS_COLORS[g.dominant_emotion] ?? 'var(--mantine-color-gray-5)', flexShrink: 0 }} />
                    </Group>
                  );
                })}
              </SimpleGrid>
            </Paper>
          )}

          {emotionStats && emotionStats.per_genre.length > 0 && (
            <Paper p="md" radius="md" withBorder>
              <Text size="sm" fw={600} mb="sm">Emotions by genre</Text>
              <Stack gap="xs">
                {emotionStats.per_genre.map((g) => (
                  <Group key={g.genre} justify="space-between" wrap="nowrap">
                    <Text size="xs" style={{ minWidth: 64, flex: '0 0 auto' }} truncate>{g.genre}</Text>
                    <div style={{ display: 'flex', flex: 1, gap: 2, marginInline: 8 }}>
                      {g.emotion_breakdown.slice(0, 5).map((e) => (
                        <div
                          key={e.emotion}
                          style={{
                            flex: e.percentage,
                            height: 16,
                            borderRadius: 3,
                            background: EMOTION_CSS_COLORS[e.emotion] ?? 'var(--mantine-color-gray-5)',
                            opacity: 0.8,
                            minWidth: 4,
                          }}
                          title={`${EMOTION_CONFIG[e.emotion]?.label}: ${Math.round(e.percentage)}%`}
                        />
                      ))}
                    </div>
                    <Text size="xs" c="dimmed" style={{ minWidth: 52, flex: '0 0 auto', textAlign: 'right' }}>{g.session_count} sessions</Text>
                  </Group>
                ))}
              </Stack>
            </Paper>
          )}
        </Tabs.Panel>
      </Tabs>

      {/* ─── Log Session Modal ───────────────────────────────────────────────── */}
      <LogSessionModal
        opened={logModalOpen}
        onClose={() => setLogModalOpen(false)}
        gameId={0}
      />
    </div>
  );
}
