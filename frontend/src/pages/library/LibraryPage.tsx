import type { ReactNode } from 'react';
import { useEffect, useMemo, useState } from 'react';
import {
  ActionIcon,
  Badge,
  Box,
  Button,
  Center,
  Group,
  Loader,
  Modal,
  Paper,
  Rating,
  Select,
  Stack,
  Tabs,
  Text,
  TextInput,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import {
  IconArrowRight,
  IconBookmark,
  IconBooks,
  IconCheck,
  IconLayoutGrid,
  IconPencil,
  IconPlayerPlay,
  IconStar,
  IconTrash,
  IconTrophy,
  IconX,
  IconHeart,
  IconRepeat,
  IconSearch,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { GameCard } from '../../components/games/GameCard';
import {
  useLibrary,
  useLibraryStats,
  useRemoveFromLibrary,
  useUpdateLibraryEntry,
} from '../../hooks/useLibrary';
import type { LibraryEntry, LibrarySort, LibraryStatus, LibraryStatusFilter } from '../../types/library';
import classes from './LibraryPage.module.css';

const dateFormatter = new Intl.DateTimeFormat('en-US', {
  month: 'short',
  day: 'numeric',
  year: 'numeric',
});

const STATUS_TABS: { value: LibraryStatus | 'all'; label: string; icon: ReactNode }[] = [
  { value: 'all',       label: 'All',       icon: <IconLayoutGrid size={14} /> },
  { value: 'playing',   label: 'Playing',   icon: <IconPlayerPlay size={14} /> },
  { value: 'replaying', label: 'Replaying', icon: <IconRepeat size={14} /> },
  { value: 'completed', label: 'Completed', icon: <IconCheck size={14} /> },
  { value: 'backlog',   label: 'Backlog',   icon: <IconBookmark size={14} /> },
  { value: 'wishlist',  label: 'Wishlist',  icon: <IconHeart size={14} /> },
  { value: 'dropped',   label: 'Dropped',   icon: <IconX size={14} /> },
];

const STATUS_LABELS: Record<LibraryStatus, string> = {
  playing: 'Playing',
  completed: 'Completed',
  backlog: 'Backlog',
  dropped: 'Dropped',
  wishlist: 'Wishlist',
  replaying: 'Replaying',
};

const STATUS_COLORS: Record<LibraryStatus, string> = {
  playing: 'violet',
  completed: 'teal',
  backlog: 'blue',
  dropped: 'grape',
  wishlist: 'pink',
  replaying: 'orange',
};

const PANEL_COPY: Record<LibraryStatus | 'all', string> = {
  all: 'Every title you have saved, with quick editing and status tracking.',
  playing: 'Your active games, ready to pick back up without digging.',
  replaying: 'Games you finished before and are actively revisiting.',
  completed: 'Finished runs, neatly archived with ratings close at hand.',
  backlog: 'Games waiting for their turn, with a shortcut into Play Next.',
  wishlist: 'Games you are curious about before committing them to the backlog.',
  dropped: 'Titles you set aside, kept visible without cluttering the rest.',
};

const EMPTY_COPY: Record<LibraryStatus | 'all', string> = {
  all: 'Your library is empty. Browse the catalog to start saving games.',
  playing: 'Nothing is marked as playing right now.',
  replaying: 'No replays in motion right now.',
  completed: 'No completed games yet.',
  backlog: 'Your backlog is clear right now.',
  wishlist: 'No wishlist games yet.',
  dropped: 'No dropped games here.',
};

const SORT_OPTIONS: Array<{ value: LibrarySort; label: string }> = [
  { value: 'added_at_desc', label: 'Recently added' },
  { value: 'added_at_asc', label: 'Oldest added' },
  { value: 'status', label: 'Status' },
];

function formatGenres(entry: LibraryEntry) {
  const genreNames = entry.game.genres.slice(0, 3).map((genre) => genre.name);
  return genreNames.length > 0 ? genreNames.join(' • ') : 'No genres yet';
}

export default function LibraryPage() {
  const [activeTab, setActiveTab] = useState<LibraryStatusFilter>('all');
  const [sort, setSort] = useState<LibrarySort>('added_at_desc');
  const [searchInput, setSearchInput] = useState('');
  const [appliedSearch, setAppliedSearch] = useState<string | undefined>(undefined);
  const [editingEntry, setEditingEntry] = useState<LibraryEntry | null>(null);
  const [editStatus, setEditStatus] = useState<LibraryStatus>('backlog');
  const [editRating, setEditRating] = useState<number>(0);
  const [removingEntryId, setRemovingEntryId] = useState<number | null>(null);
  const [nextCandidate, setNextCandidate] = useState<LibraryEntry | null>(null);
  const [editOpened, { open: openEdit, close: closeEdit }] = useDisclosure(false);
  const navigate = useNavigate();

  const libraryQuery = useMemo(
    () => ({
      status: activeTab,
      sort,
      search: appliedSearch,
    }),
    [activeTab, appliedSearch, sort],
  );
  const { data: entries, isLoading, isError, isFetching } = useLibrary(libraryQuery);
  const { data: stats } = useLibraryStats();
  const removeEntry = useRemoveFromLibrary();
  const updateEntry = useUpdateLibraryEntry();

  const libraryEntries = useMemo(() => entries ?? [], [entries]);
  const ratedEntries = useMemo(
    () => libraryEntries.filter((entry) => entry.rating !== null),
    [libraryEntries],
  );

  const statusCounts = useMemo(() => {
    if (stats) {
      return {
        all: stats.total_games,
        playing: stats.by_status.playing ?? 0,
        replaying: stats.by_status.replaying ?? 0,
        completed: stats.by_status.completed,
        backlog: stats.by_status.backlog,
        wishlist: stats.by_status.wishlist ?? 0,
        dropped: stats.by_status.dropped,
      };
    }

    return libraryEntries.reduce(
      (acc, entry) => {
        acc.all += 1;
        acc[entry.status] += 1;
        return acc;
      },
      { all: 0, playing: 0, replaying: 0, completed: 0, backlog: 0, wishlist: 0, dropped: 0 },
    );
  }, [libraryEntries, stats]);

  const topGenre = stats?.top_genres[0] ?? null;
  const completionRate = statusCounts.all > 0
    ? Math.round((statusCounts.completed / statusCounts.all) * 100)
    : 0;

  const applySearch = (value: string) => {
    const normalizedSearch = value.trim() || undefined;
    setAppliedSearch((current) => (current === normalizedSearch ? current : normalizedSearch));
  };

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      applySearch(searchInput);
    }, 3000);

    return () => window.clearTimeout(timeoutId);
  }, [searchInput]);

  const handleOpenEdit = (entry: LibraryEntry) => {
    setEditingEntry(entry);
    setEditStatus(entry.status);
    setEditRating(entry.rating ?? 0);
    openEdit();
  };

  const handleSaveEdit = async () => {
    if (!editingEntry) return;

    try {
      const result = await updateEntry.mutateAsync({
        id: editingEntry.id,
        updates: {
          status: editStatus,
          rating: editRating > 0 ? editRating : undefined,
        },
      });
      setNextCandidate(result.next_game_candidate);
      closeEdit();
      notifications.show({ color: 'green', message: 'Library entry updated' });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to update entry' });
    }
  };

  const handleRemove = async (entryId: number, gameName: string) => {
    setRemovingEntryId(entryId);

    try {
      await removeEntry.mutateAsync(entryId);
      notifications.show({ color: 'blue', message: `${gameName} removed from library` });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to remove entry' });
    } finally {
      setRemovingEntryId((current) => (current === entryId ? null : current));
    }
  };

  if (isLoading && !entries) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="violet" size="md" />
          <Text size="sm" c="dimmed">Loading your library…</Text>
        </Stack>
      </Center>
    );
  }

  if (isError && !entries) {
    return (
      <Center py={80}>
        <Paper p="md" radius="md" withBorder>
          <Text size="sm" c="red.4">Failed to load your library. Please try again.</Text>
        </Paper>
      </Center>
    );
  }

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            My <span className={classes.headerAccent}>Library</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Track what you are playing, what you have finished, and what deserves the next slot in rotation.
          </Text>
        </div>

        <Button
          leftSection={<IconArrowRight size={16} />}
          color="violet"
          onClick={() => navigate('/library/backlog')}
        >
          Play next
        </Button>
      </div>

      <div className={classes.metricsGrid}>
        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-violet-light)' }}>
            <IconBooks size={18} color="var(--mantine-color-violet-5)" />
          </div>
          <div className={classes.metricLabel}>Total games</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-violet-4)' }}>
            {statusCounts.all}
          </div>
          <div className={classes.metricSub}>
            {topGenre
              ? `${topGenre.genre} leads with ${topGenre.count} title${topGenre.count === 1 ? '' : 's'}`
              : 'Start building your collection'}
          </div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
            <IconPlayerPlay size={18} color="var(--mantine-color-blue-5)" />
          </div>
          <div className={classes.metricLabel}>Playing now</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-blue-4)' }}>
            {statusCounts.playing + statusCounts.replaying}
          </div>
          <div className={classes.metricSub}>
            {statusCounts.backlog > 0
              ? `${statusCounts.backlog} waiting in backlog`
              : 'Nothing waiting in backlog'}
          </div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
            <IconTrophy size={18} color="var(--mantine-color-teal-5)" />
          </div>
          <div className={classes.metricLabel}>Completed</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-teal-4)' }}>
            {statusCounts.completed}
          </div>
          <div className={classes.metricSub}>
            {statusCounts.all > 0 ? `${completionRate}% of your library finished` : 'No finished runs yet'}
          </div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-yellow-light)' }}>
            <IconStar size={18} color="var(--mantine-color-yellow-5)" />
          </div>
          <div className={classes.metricLabel}>Average rating</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-yellow-4)' }}>
            {stats?.avg_rating !== null && stats?.avg_rating !== undefined
              ? stats.avg_rating.toFixed(1)
              : '—'}
          </div>
          <div className={classes.metricSub}>
            {ratedEntries.length > 0 ? `${ratedEntries.length} rated entr${ratedEntries.length === 1 ? 'y' : 'ies'}` : 'Add ratings as you go'}
          </div>
        </Paper>
      </div>

      {nextCandidate && (
        <Paper p="md" radius="md" withBorder>
          <Group justify="space-between" align="center" gap="sm">
            <div>
              <Text size="sm" fw={600}>Ready to start next?</Text>
              <Text size="xs" c="dimmed">
                {nextCandidate.game.name} is now at the front of your queue.
              </Text>
            </div>
            <Group gap="xs">
              <Button variant="default" size="xs" onClick={() => setNextCandidate(null)}>
                Not now
              </Button>
              <Button
                color="violet"
                size="xs"
                loading={updateEntry.isPending}
                onClick={async () => {
                  await updateEntry.mutateAsync({
                    id: nextCandidate.id,
                    updates: { status: 'playing' },
                  });
                  notifications.show({ color: 'teal', message: `Now playing: ${nextCandidate.game.name}` });
                  setNextCandidate(null);
                }}
              >
                Start next
              </Button>
            </Group>
          </Group>
        </Paper>
      )}

      <div className={classes.overviewGrid}>
        <Paper p="md" radius="md" withBorder>
          <Group justify="space-between" mb="sm" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Status overview</Text>
              <Text size="xs" c="dimmed">A quick read on how your collection is distributed.</Text>
            </div>
          </Group>

          <Stack gap="sm">
            {(Object.keys(STATUS_LABELS) as LibraryStatus[]).map((status) => {
              const count = statusCounts[status];
              const width = statusCounts.all > 0 ? Math.max((count / statusCounts.all) * 100, count > 0 ? 8 : 0) : 0;

              return (
                <div key={status} className={classes.statusRow}>
                  <div className={classes.statusMeta}>
                    <Text className={classes.statusLabel}>{STATUS_LABELS[status]}</Text>
                    <Text className={classes.statusValue}>{count}</Text>
                  </div>
                  <div className={classes.statusTrack}>
                    <div
                      className={classes.statusFill}
                      style={{
                        width: `${width}%`,
                        background: `var(--mantine-color-${STATUS_COLORS[status]}-5)`,
                      }}
                    />
                  </div>
                </div>
              );
            })}
          </Stack>
        </Paper>

        <Paper p="md" radius="md" withBorder>
          <Group justify="space-between" mb="sm" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Top genres</Text>
              <Text size="xs" c="dimmed">The genres showing up most often across your saved titles.</Text>
            </div>
            <Text size="xs" c="dimmed" className={classes.panelMeta}>
              {statusCounts.all} tracked
            </Text>
          </Group>

          {stats && stats.top_genres.length > 0 ? (
            <Stack gap="sm">
              <div className={classes.genreCloud}>
                {stats.top_genres.slice(0, 6).map((genre, index) => (
                  <Badge
                    key={genre.genre}
                    size="sm"
                    variant={index === 0 ? 'light' : 'default'}
                    color={index === 0 ? 'violet' : 'gray'}
                  >
                    {genre.genre} {genre.count}
                  </Badge>
                ))}
              </div>
              <Text size="xs" c="dimmed" className={classes.genreInsight}>
                {topGenre
                  ? `${topGenre.genre} is setting the tone for your library right now.`
                  : 'Genre trends will show up here as your library grows.'}
              </Text>
            </Stack>
          ) : (
            <Text size="sm" c="dimmed" py="lg">
              Add a few more games to surface genre trends here.
            </Text>
          )}
        </Paper>
      </div>

      <Tabs
        value={activeTab}
        onChange={(value) => {
          if (value) setActiveTab(value as LibraryStatusFilter);
        }}
        variant="pills"
        color="violet"
      >
        <Tabs.List className={classes.tabsList}>
          {STATUS_TABS.map((tab) => (
            <Tabs.Tab key={tab.value} value={tab.value} leftSection={tab.icon}>
              <span className={classes.tabLabel}>
                <span>{tab.label}</span>
                <span className={classes.tabCount}>{statusCounts[tab.value]}</span>
              </span>
            </Tabs.Tab>
          ))}
        </Tabs.List>

        {STATUS_TABS.map((tab) => {
          const isActivePanel = activeTab === tab.value;
          const panelEntries = isActivePanel ? libraryEntries : [];

          return (
            <Tabs.Panel key={tab.value} value={tab.value} pt="lg">
              <Paper p="md" radius="md" withBorder>
                <Group justify="space-between" align="flex-start" gap="sm" mb="md" className={classes.panelHeader}>
                  <div>
                    <Text size="sm" fw={600}>
                      {tab.value === 'all' ? 'All library titles' : `${tab.label} games`}
                    </Text>
                    <Group gap="xs" align="center" wrap="nowrap">
                      <Text size="xs" c="dimmed">
                        {PANEL_COPY[tab.value]}
                      </Text>
                      {isActivePanel && isFetching && (
                        <span className={classes.inlineLoading}>
                          <Loader size="xs" color="violet" />
                        </span>
                      )}
                    </Group>
                  </div>

                  {isActivePanel && (
                    <Group gap="sm" align="flex-end" className={classes.panelControls}>
                      <TextInput
                        className={classes.searchInput}
                        placeholder="Search library titles..."
                        value={searchInput}
                        onChange={(event) => setSearchInput(event.currentTarget.value)}
                        onKeyDown={(event) => {
                          if (event.key === 'Enter') {
                            applySearch(searchInput);
                          }
                        }}
                        rightSection={
                          <ActionIcon
                            variant="subtle"
                            color="gray"
                            onClick={() => applySearch(searchInput)}
                            aria-label="Search library"
                          >
                            <IconSearch size={16} stroke={1.8} />
                          </ActionIcon>
                        }
                        rightSectionPointerEvents="all"
                        size="sm"
                        radius="md"
                      />

                      <Select
                        className={classes.sortSelect}
                        aria-label="Sort library entries"
                        value={sort}
                        onChange={(value) => value && setSort(value as LibrarySort)}
                        data={SORT_OPTIONS}
                        size="sm"
                        radius="md"
                        allowDeselect={false}
                      />

                      {tab.value === 'backlog' && panelEntries.length > 0 && (
                        <Button
                          size="xs"
                          variant="light"
                          color="violet"
                          rightSection={<IconArrowRight size={14} />}
                          onClick={() => navigate('/library/backlog')}
                        >
                          Open Play Next
                        </Button>
                      )}
                    </Group>
                  )}
                </Group>

                {panelEntries.length === 0 ? (
                  <div className={classes.emptyState}>
                    <div>
                      <Text size="sm" fw={600}>Nothing here yet</Text>
                      <Text size="xs" c="dimmed" mt={4}>
                        {appliedSearch
                          ? `No ${tab.value === 'all' ? 'library titles' : tab.label.toLowerCase()} matched "${appliedSearch}".`
                          : EMPTY_COPY[tab.value]}
                      </Text>
                    </div>
                  </div>
                ) : (
                  <Box className={classes.grid}>
                    {panelEntries.map((entry) => (
                      <Box key={entry.id} className={classes.libraryItem}>
                        <GameCard game={entry.game} />

                        <Paper p="sm" radius="md" withBorder className={classes.entryMeta}>
                          <Group justify="space-between" align="flex-start" gap="sm" wrap="nowrap">
                            <div className={classes.entryInfo}>
                              <Group gap={6} wrap="wrap" mb={6}>
                                <Badge size="xs" color={STATUS_COLORS[entry.status]} variant="light">
                                  {STATUS_LABELS[entry.status]}
                                </Badge>
                                {entry.rating !== null && (
                                  <Group gap={6} wrap="nowrap">
                                    <Rating value={entry.rating} fractions={2} readOnly size="xs" color="yellow" />
                                    <Text size="xs" c="dimmed" className={classes.ratingText}>
                                      {entry.rating.toFixed(1)}
                                    </Text>
                                  </Group>
                                )}
                              </Group>

                              <Text className={classes.entryMetaLine}>
                                Added {dateFormatter.format(new Date(entry.added_at))}
                              </Text>
                              <Text className={`${classes.entryMetaLine} ${classes.entryGenres}`}>
                                {formatGenres(entry)}
                              </Text>
                            </div>

                            <Group gap={6} className={classes.entryActions} wrap="nowrap">
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                color="gray"
                                onClick={() => handleOpenEdit(entry)}
                                aria-label="Edit entry"
                              >
                                <IconPencil size={14} />
                              </ActionIcon>
                              <ActionIcon
                                size="sm"
                                variant="subtle"
                                color="red"
                                onClick={() => handleRemove(entry.id, entry.game.name)}
                                loading={removingEntryId === entry.id}
                                aria-label="Remove from library"
                              >
                                <IconTrash size={14} />
                              </ActionIcon>
                            </Group>
                          </Group>
                        </Paper>
                      </Box>
                    ))}
                  </Box>
                )}
              </Paper>
            </Tabs.Panel>
          );
        })}
      </Tabs>

      <Modal opened={editOpened} onClose={closeEdit} title="Edit library entry" centered size="sm">
        <Stack gap="md">
          <Select
            label="Status"
            value={editStatus}
            onChange={(value) => value && setEditStatus(value as LibraryStatus)}
            data={[
              { value: 'playing', label: 'Playing' },
              { value: 'replaying', label: 'Replaying' },
              { value: 'completed', label: 'Completed' },
              { value: 'backlog', label: 'Backlog' },
              { value: 'wishlist', label: 'Wishlist' },
              { value: 'dropped', label: 'Dropped' },
            ]}
          />

          <Stack gap={4}>
            <Text size="sm" fw={500}>Rating</Text>
            <Rating value={editRating} fractions={2} onChange={setEditRating} color="yellow" />
            {editRating > 0 && (
              <Text size="xs" c="dimmed">{editRating.toFixed(1)} / 5</Text>
            )}
          </Stack>

          <Group justify="flex-end">
            <Button variant="default" onClick={closeEdit}>Cancel</Button>
            <Button color="violet" onClick={handleSaveEdit} loading={updateEntry.isPending}>Save</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
