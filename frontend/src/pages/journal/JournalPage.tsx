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
  Pagination,
  Skeleton,
} from '@mantine/core';
import {
  IconBookmark,
  IconChartBar,
  IconCheck,
  IconDeviceGamepad2,
  IconFilter,
  IconMoodSmile,
  IconNote,
  IconNotes,
  IconPlus,
  IconTimeline,
} from '@tabler/icons-react';
import {
  useJournalStats,
  useJournalFeed,
  useAllRatings,
  useEmotionStats,
  useDeletePlaythroughNote,
  usePlaythroughNotes,
  useUpdatePlaythroughNote,
} from '../../hooks/useJournal';
import {
  GenreHoursChart,
  WeeklyActivityCard,
  EmotionSummaryCard,
  BacklogProgressCard,
  JournalFeedItem,
  LogSessionModal,
  MultiAxisRatingBars,
  PlaythroughNoteModal,
  ScratchpadPanel,
} from '../../components/journal';
import classes from '../../components/journal/Journal.module.css';
import { EMOTION_CONFIG } from '../../types/journal';
import type { JournalFeedItem as JournalFeedItemType, JournalStats, PlaythroughNote } from '../../types/journal';

const RATING_COLORS = [
  '#d4674d',
  'var(--mantine-color-teal-5)',
  '#e0b957',
  '#5b8def',
  'var(--mantine-color-pink-5)',
  'var(--mantine-color-orange-5)',
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

type FeedFilter = 'all' | 'notes' | 'milestones' | 'month';

function formatDateGroup(isoString: string): string {
  const date = new Date(isoString);
  const now = new Date();
  const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return 'Earlier this week';

  return date.toLocaleDateString([], { month: 'long', year: 'numeric' });
}

function isThisMonth(isoString: string): boolean {
  const date = new Date(isoString);
  const now = new Date();
  return date.getMonth() === now.getMonth() && date.getFullYear() === now.getFullYear();
}

function filterFeedItems(items: JournalFeedItemType[], filter: FeedFilter) {
  if (filter === 'notes') {
    return items.filter((item) => item.session.notes && item.session.notes.trim().length > 0);
  }
  if (filter === 'milestones') {
    return items.filter((item) => item.session.is_milestone);
  }
  if (filter === 'month') {
    return items.filter((item) => isThisMonth(item.session.started_at));
  }
  return items;
}

function groupFeedItems(items: JournalFeedItemType[]) {
  return items.reduce<Array<{ label: string; items: JournalFeedItemType[] }>>((groups, item) => {
    const label = item.date_group || formatDateGroup(item.session.started_at);
    const existing = groups.find((group) => group.label === label);
    if (existing) {
      existing.items.push(item);
    } else {
      groups.push({ label, items: [item] });
    }
    return groups;
  }, []);
}

function getWeeklyInsight(stats: JournalStats | undefined) {
  if (!stats) return null;
  const topGenre = stats.top_genres_this_month[0];
  const dominantMood = stats.dominant_emotion_this_month ? EMOTION_CONFIG[stats.dominant_emotion_this_month]?.label : null;

  if (topGenre && stats.total_hours_this_month > 0) {
    return `${topGenre.genre} is carrying this month at ${Math.round((topGenre.hours / stats.total_hours_this_month) * 100)}% of logged playtime.`;
  }
  if (dominantMood) {
    return `${dominantMood} is your clearest mood signal this month.`;
  }
  return 'Log a few sessions with notes and emotions to reveal useful patterns.';
}

export default function JournalPage() {
  const [activeTab,    setActiveTab]    = useState<string | null>('journal');
  const [logModalOpen, setLogModalOpen] = useState(false);
  const [noteModalOpen, setNoteModalOpen] = useState(false);
  const [editingNote, setEditingNote] = useState<PlaythroughNote | null>(null);
  const [feedPage,     setFeedPage]     = useState(1);
  const [feedFilter,   setFeedFilter]   = useState<FeedFilter>('all');

  const { data: stats,        isLoading: statsLoading    } = useJournalStats();
  const { data: feedData,     isLoading: feedLoading     } = useJournalFeed(feedPage);
  const { data: ratings,      isLoading: ratingsLoading  } = useAllRatings();
  const { data: emotionStats, isLoading: emotionsLoading } = useEmotionStats({ period: '30d' });
  const { data: notesData,    isLoading: notesLoading    } = usePlaythroughNotes({ per_page: 100 });
  const updateNote = useUpdatePlaythroughNote();
  const deleteNote = useDeletePlaythroughNote();

  const isLoading = statsLoading || feedLoading || ratingsLoading || emotionsLoading || notesLoading;
  const feedItems = feedData?.items ?? [];
  const filteredFeedItems = filterFeedItems(feedItems, feedFilter);
  const groupedFeedItems = groupFeedItems(filteredFeedItems);
  const nextSessionNotes = (notesData?.items ?? [])
    .filter((note) => note.status === 'open' && note.remind_next_session)
    .sort((a, b) => Number(b.pinned) - Number(a.pinned) || new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime())
    .slice(0, 3);
  const weeklyInsight = getWeeklyInsight(stats);

  if (isLoading && !stats) {
    return (
      <Center py={80} className={classes.journalPage}>
        <Stack className={classes.loadingState} p="lg" align="center" gap="sm">
          <Loader color="orange" size="md" />
          <Text size="sm" c="dimmed">Loading your journal...</Text>
          <Group gap="xs" aria-hidden="true">
            <Skeleton height={8} width={72} radius="xl" />
            <Skeleton height={8} width={44} radius="xl" />
          </Group>
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
            Journal
          </Text>
          <Text size="xs" c="dimmed">
            A timeline of what you played, felt, and want to remember.
          </Text>
        </div>
        <Group gap="xs">
          <Button
            variant="light"
            className={classes.secondaryAction}
            leftSection={<IconNotes size={16} />}
            onClick={() => {
              setEditingNote(null);
              setNoteModalOpen(true);
            }}
          >
            New note
          </Button>
          <Button className={classes.primaryAction} leftSection={<IconPlus size={16} />} onClick={() => setLogModalOpen(true)}>
            Log session
          </Button>
        </Group>
      </div>

      {/* ─── Tabs ────────────────────────────────────────────────────────────── */}
      <Tabs value={activeTab} onChange={setActiveTab} variant="pills" mb="lg" className={classes.journalTabs}>
        <Tabs.List>
          <Tabs.Tab value="journal" leftSection={<IconTimeline size={14} />}>Journal</Tabs.Tab>
          <Tabs.Tab value="notes" leftSection={<IconNote size={14} />}>Notes</Tabs.Tab>
          <Tabs.Tab value="mood"     leftSection={<IconMoodSmile size={14} />}>Mood profile</Tabs.Tab>
          <Tabs.Tab value="ratings" leftSection={<IconChartBar size={14} />}>Ratings</Tabs.Tab>
        </Tabs.List>

        {/* ════ JOURNAL ═════════════════════════════════════════════════════ */}
        <Tabs.Panel value="journal" pt="lg">
          <div className={classes.journalWorkspace}>
            <Stack gap="md" className={classes.timelineColumn}>
              <Paper p="md" radius="xs" withBorder className={classes.timelinePanel}>
                <Group justify="space-between" align="flex-start" mb="md">
                  <div>
                    <Text size="sm" fw={600}>Timeline</Text>
                    <Text size="xs" c="dimmed">
                      Sessions grouped by when they happened.
                    </Text>
                  </div>
                  <Group gap={6} wrap="wrap" className={classes.feedFilters}>
                    {[
                      { value: 'all', label: 'All' },
                      { value: 'notes', label: 'With notes' },
                      { value: 'milestones', label: 'Milestones' },
                      { value: 'month', label: 'This month' },
                    ].map((filter) => (
                      <Button
                        key={filter.value}
                        size="xs"
                        variant={feedFilter === filter.value ? 'filled' : 'subtle'}
                        className={feedFilter === filter.value ? classes.primaryAction : classes.filterAction}
                        leftSection={filter.value === 'all' ? <IconFilter size={13} /> : undefined}
                        onClick={() => setFeedFilter(filter.value as FeedFilter)}
                      >
                        {filter.label}
                      </Button>
                    ))}
                  </Group>
                </Group>

                <Stack gap="lg">
                  {groupedFeedItems.map((group) => (
                    <div key={group.label} className={classes.timelineGroup}>
                      <div className={classes.timelineGroupLabel}>{group.label}</div>
                      <Stack gap="xs">
                        {group.items.map((item) => (
                          <JournalFeedItem key={item.session.id} session={item.session} variant="timeline" />
                        ))}
                      </Stack>
                    </div>
                  ))}
                  {feedItems.length === 0 && (
                    <div className={classes.emptyJournalState}>
                      <div className={classes.stateIcon}>
                        <IconTimeline size={18} stroke={1.8} />
                      </div>
                      <Text size="sm" fw={600}>No sessions yet</Text>
                      <Text size="sm" c="dimmed" ta="center">
                        Log a session after playing to build your timeline, mood profile, and recommendations.
                      </Text>
                      <Button className={classes.primaryAction} leftSection={<IconPlus size={16} />} onClick={() => setLogModalOpen(true)}>
                        Log session
                      </Button>
                    </div>
                  )}
                  {feedItems.length > 0 && filteredFeedItems.length === 0 && (
                    <Text size="sm" c="dimmed" ta="center" py="xl">
                      No sessions match this filter.
                    </Text>
                  )}
                </Stack>
              </Paper>

              {feedData && feedData.total > feedData.per_page && (
                <Group justify="center">
                  <Pagination
                    radius="sm"
                    className={classes.journalPagination}
                    total={Math.ceil(feedData.total / feedData.per_page)}
                    value={feedPage}
                    onChange={setFeedPage}
                  />
                </Group>
              )}

              <div className={classes.patternGrid}>
                <Paper p="md" radius="xs" withBorder>
                  <Group justify="space-between" mb="sm">
                    <Text size="sm" fw={600}>Hours per genre: {currentMonth}</Text>
                  </Group>
                  {stats && <GenreHoursChart genres={stats.top_genres_this_month} />}
                </Paper>

                <Paper p="md" radius="xs" withBorder>
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
            </Stack>

            <aside className={classes.journalSidebar}>
              {stats && (
                <Paper p="md" radius="xs" withBorder className={classes.weekSummaryPanel}>
                  <Text size="sm" fw={600} mb="sm">This week</Text>
                  <div className={classes.weekSummaryGrid}>
                    <div>
                      <div className={classes.weekSummaryValue}>{stats.total_hours_this_week.toFixed(1)}</div>
                      <div className={classes.weekSummaryLabel}>hours</div>
                    </div>
                    <div>
                      <div className={classes.weekSummaryValue}>{stats.sessions_this_month}</div>
                      <div className={classes.weekSummaryLabel}>sessions this month</div>
                    </div>
                    <div>
                      <div className={classes.weekSummaryValue}>{stats.current_streak_days}</div>
                      <div className={classes.weekSummaryLabel}>day streak</div>
                    </div>
                  </div>
                  {weeklyInsight && <div className={classes.insightBox}>{weeklyInsight}</div>}
                </Paper>
              )}

              <Paper p="md" radius="xs" withBorder>
                <Group justify="space-between" mb="sm">
                  <Text size="sm" fw={600}>Next session notes</Text>
                  <Anchor size="xs" c="#e97d61" onClick={() => setActiveTab('notes')}>
                    View notes
                  </Anchor>
                </Group>
                <Stack gap="xs">
                  {nextSessionNotes.map((note) => (
                    <div key={note.id} className={classes.sidebarNote}>
                      <div className={classes.sidebarNoteIcon}>
                        {note.pinned ? <IconBookmark size={14} /> : <IconNote size={14} />}
                      </div>
                      <div className={classes.sidebarNoteBody}>
                        <Text size="xs" fw={600} lineClamp={2}>{note.title}</Text>
                        <Text size="xs" c="dimmed" truncate>{note.game_title ?? `Game #${note.game_id}`}</Text>
                      </div>
                    </div>
                  ))}
                  {nextSessionNotes.length === 0 && (
                    <Text size="sm" c="dimmed">
                      Mark a note for next session and it will appear here.
                    </Text>
                  )}
                </Stack>
              </Paper>

              <Paper p="md" radius="xs" withBorder>
                <Text size="sm" fw={600} mb="sm">Mood signal</Text>
                <EmotionSummaryCard
                  emotionStats={emotionStats ?? null}
                  dominantEmotion={stats?.dominant_emotion_this_month ?? null}
                  coveragePct={stats?.emotion_coverage_pct ?? null}
                  totalSessions={stats?.sessions_this_month ?? 0}
                />
              </Paper>

              {stats && (
                <Paper p="md" radius="xs" withBorder>
                  <Text size="sm" fw={600} mb="sm">Backlog progress</Text>
                  <BacklogProgressCard
                    completed={stats.games_completed}
                    playing={stats.games_playing}
                    backlog={stats.games_in_backlog}
                  />
                </Paper>
              )}
            </aside>
          </div>
        </Tabs.Panel>

        <Tabs.Panel value="notes" pt="lg">
          <ScratchpadPanel
            notes={notesData?.items ?? []}
            emptyMessage="No scratchpad notes yet. Save a quest reminder, recipe, or clue for future-you."
            onCreate={() => {
              setEditingNote(null);
              setNoteModalOpen(true);
            }}
            onEdit={(note) => {
              setEditingNote(note);
              setNoteModalOpen(true);
            }}
            onToggleStatus={(note) => {
              updateNote.mutate({
                noteId: note.id,
                data: { status: note.status === 'done' ? 'open' : 'done' },
              });
            }}
            onTogglePinned={(note) => {
              updateNote.mutate({
                noteId: note.id,
                data: { pinned: !note.pinned },
              });
            }}
            onDelete={(note) => deleteNote.mutate(note.id)}
          />
        </Tabs.Panel>

        <Tabs.Panel value="ratings" pt="lg">
          {ratings && ratings.length > 0 ? (
            <Paper p="md" radius="xs" withBorder>
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
          ) : (
            <Paper p="lg" radius="xs" withBorder className={classes.statePanel}>
              <Stack align="center" gap="xs">
                <div className={classes.stateIcon}>
                  <IconCheck size={18} stroke={1.8} />
                </div>
                <Text size="sm" c="dimmed" ta="center">
                  Rate a completed game to compare story, gameplay, visuals, soundtrack, and overall feel.
                </Text>
              </Stack>
            </Paper>
          )}
        </Tabs.Panel>

        {/* ════ MOOD PROFILE ════════════════════════════════════════════════ */}
        <Tabs.Panel value="mood" pt="lg">
          <Paper p="md" radius="xs" withBorder mb="md">
            <Text size="sm" fw={600} mb="md">Emotion breakdown: last 30 days</Text>
            <EmotionSummaryCard
              emotionStats={emotionStats ?? null}
              dominantEmotion={stats?.dominant_emotion_this_month ?? null}
              coveragePct={stats?.emotion_coverage_pct ?? null}
              totalSessions={stats?.sessions_this_month ?? 0}
            />
          </Paper>

          {emotionStats && emotionStats.per_game.length > 0 && (
            <Paper p="md" radius="xs" withBorder mb="md">
              <Text size="sm" fw={600} mb="sm">Emotions by game</Text>
              <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="sm">
                {emotionStats.per_game.map((g) => {
                  const config = EMOTION_CONFIG[g.dominant_emotion];
                  return (
                    <Group key={g.game_id} gap="sm" wrap="nowrap">
                      <div className={classes.moodGameMedia}>
                        {g.cover_url
                          ? <img src={g.cover_url} alt={g.game_title} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
                          : <IconDeviceGamepad2 size={18} />}
                      </div>
                      <div style={{ flex: 1, minWidth: 0 }}>
                        <Text size="xs" fw={600} truncate>{g.game_title}</Text>
                        <Text size="xs" c="dimmed">
                          {config?.label ?? g.dominant_emotion} · {g.session_count} sessions
                        </Text>
                      </div>
                      <div
                        className={classes.moodDot}
                        style={{ background: EMOTION_CSS_COLORS[g.dominant_emotion] ?? 'var(--mantine-color-gray-5)' }}
                      />
                    </Group>
                  );
                })}
              </SimpleGrid>
            </Paper>
          )}

          {emotionStats && emotionStats.per_genre.length > 0 && (
            <Paper p="md" radius="xs" withBorder>
              <Text size="sm" fw={600} mb="sm">Emotions by genre</Text>
              <Stack gap="xs">
                {emotionStats.per_genre.map((g) => (
                  <Group key={g.genre} justify="space-between" wrap="nowrap">
                    <Text size="xs" style={{ minWidth: 64, flex: '0 0 auto' }} truncate>{g.genre}</Text>
                    <div className={classes.genreEmotionStack}>
                      {g.emotion_breakdown.slice(0, 5).map((e) => (
                        <div
                          key={e.emotion}
                          className={classes.genreEmotionSegment}
                          style={{
                            flex: e.percentage,
                            background: EMOTION_CSS_COLORS[e.emotion] ?? 'var(--mantine-color-gray-5)',
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
      {noteModalOpen && (
        <PlaythroughNoteModal
          opened={noteModalOpen}
          onClose={() => {
            setNoteModalOpen(false);
            setEditingNote(null);
          }}
          note={editingNote}
        />
      )}
    </div>
  );
}
