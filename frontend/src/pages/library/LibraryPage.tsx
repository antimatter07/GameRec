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
  SegmentedControl,
  Select,
  Stack,
  Tabs,
  Text,
  TextInput,
  Tooltip,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import {
  IconArrowRight,
  IconBookmark,
  IconBooks,
  IconCheck,
  IconLayoutGrid,
  IconListDetails,
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
  useInfiniteLibrary,
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
  playing: 'ember',
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

const LIBRARY_PAGE_SIZE = 40;

function formatGenres(entry: LibraryEntry) {
  const genreNames = entry.game.genres.slice(0, 3).map((genre) => genre.name);
  return genreNames.length > 0 ? genreNames.join(' • ') : 'No genres yet';
}

function formatGameMeta(entry: LibraryEntry) {
  const releaseYear = entry.game.released ? new Date(entry.game.released).getFullYear() : null;
  const platform = entry.game.platforms[0]?.name;
  const genre = entry.game.genres[0]?.name;

  return [releaseYear ?? 'TBA', genre, platform].filter(Boolean).join(' / ');
}

function formatRuntime(entry: LibraryEntry) {
  const hours = entry.game.hltb_main_hours ?? entry.game.playtime;

  if (!hours) return null;

  return `${Math.round(hours)}h`;
}

function getGameInitials(name: string) {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0]?.toUpperCase())
    .join('');
}

export default function LibraryPage() {
  const [activeTab, setActiveTab] = useState<LibraryStatusFilter>('all');
  const [sort, setSort] = useState<LibrarySort>('added_at_desc');
  const [viewMode, setViewMode] = useState<'covers' | 'compact'>('covers');
  const [searchInput, setSearchInput] = useState('');
  const [appliedSearch, setAppliedSearch] = useState<string | undefined>(undefined);
  const [editingEntry, setEditingEntry] = useState<LibraryEntry | null>(null);
  const [editStatus, setEditStatus] = useState<LibraryStatus>('backlog');
  const [editRating, setEditRating] = useState<number>(0);
  const [removingEntryId, setRemovingEntryId] = useState<number | null>(null);
  const [updatingEntryId, setUpdatingEntryId] = useState<number | null>(null);
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
  const {
    data,
    fetchNextPage,
    hasNextPage,
    isError,
    isFetching,
    isFetchingNextPage,
    isLoading,
  } = useInfiniteLibrary(libraryQuery, LIBRARY_PAGE_SIZE);
  const { data: stats } = useLibraryStats();
  const removeEntry = useRemoveFromLibrary();
  const updateEntry = useUpdateLibraryEntry();

  const libraryEntries = useMemo(
    () => data?.pages.flatMap((page) => page.results) ?? [],
    [data],
  );
  const visibleTotal = data?.pages[0]?.total ?? 0;
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
  const avgRatingLabel = stats?.avg_rating !== null && stats?.avg_rating !== undefined
    ? stats.avg_rating.toFixed(1)
    : '—';
  const normalizedSearchInput = searchInput.trim() || undefined;
  const searchPending = normalizedSearchInput !== appliedSearch;
  const showSearchStatus = Boolean(searchPending || appliedSearch);

  const applySearch = (value: string) => {
    const normalizedSearch = value.trim() || undefined;
    setAppliedSearch((current) => (current === normalizedSearch ? current : normalizedSearch));
  };

  const clearSearch = () => {
    setSearchInput('');
    setAppliedSearch(undefined);
  };

  useEffect(() => {
    const timeoutId = window.setTimeout(() => {
      setAppliedSearch((current) => (current === normalizedSearchInput ? current : normalizedSearchInput));
    }, 3000);

    return () => window.clearTimeout(timeoutId);
  }, [normalizedSearchInput]);

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

  const handleInlineUpdate = async (entry: LibraryEntry, updates: { status?: LibraryStatus; rating?: number }) => {
    setUpdatingEntryId(entry.id);

    try {
      const result = await updateEntry.mutateAsync({
        id: entry.id,
        updates,
      });
      setNextCandidate(result.next_game_candidate);
    } catch {
      notifications.show({ color: 'red', message: `Failed to update ${entry.game.name}` });
    } finally {
      setUpdatingEntryId((current) => (current === entry.id ? null : current));
    }
  };

  if (isLoading && !data) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="ember" size="md" />
          <Text size="sm" c="dimmed">Loading your library…</Text>
        </Stack>
      </Center>
    );
  }

  if (isError && !data) {
    return (
      <Center py={80}>
        <Paper p="md" radius="xs" withBorder>
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
          color="ember"
          onClick={() => navigate('/library/backlog')}
        >
          Play next
        </Button>
      </div>

      <Paper className={classes.summaryBar} p="md" radius="xs" withBorder>
        <div className={classes.summaryItem}>
          <div className={classes.summaryIcon} style={{ background: 'var(--mantine-color-ember-light)' }}>
            <IconBooks size={16} color="var(--mantine-color-ember-5)" />
          </div>
          <div>
            <Text className={classes.summaryValue}>{statusCounts.all}</Text>
            <Text className={classes.summaryLabel}>saved games</Text>
          </div>
        </div>

        <div className={classes.summaryItem}>
          <div className={classes.summaryIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
            <IconPlayerPlay size={16} color="var(--mantine-color-blue-5)" />
          </div>
          <div>
            <Text className={classes.summaryValue}>{statusCounts.playing + statusCounts.replaying}</Text>
            <Text className={classes.summaryLabel}>playing now</Text>
          </div>
        </div>

        <div className={classes.summaryItem}>
          <div className={classes.summaryIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
            <IconTrophy size={16} color="var(--mantine-color-teal-5)" />
          </div>
          <div>
            <Text className={classes.summaryValue}>{completionRate}%</Text>
            <Text className={classes.summaryLabel}>completed</Text>
          </div>
        </div>

        <div className={classes.summaryItem}>
          <div className={classes.summaryIcon} style={{ background: 'var(--mantine-color-yellow-light)' }}>
            <IconStar size={16} color="var(--mantine-color-yellow-5)" />
          </div>
          <div>
            <Text className={classes.summaryValue}>{avgRatingLabel}</Text>
            <Text className={classes.summaryLabel}>
              {ratedEntries.length > 0 ? `${ratedEntries.length} rated` : 'rating'}
            </Text>
          </div>
        </div>
      </Paper>

      {nextCandidate && (
        <Paper p="md" radius="xs" withBorder>
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
                color="ember"
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

      <Tabs
        value={activeTab}
        onChange={(value) => {
          if (value) setActiveTab(value as LibraryStatusFilter);
        }}
        variant="pills"
        color="ember"
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
              <Paper p="md" radius="xs" withBorder>
                <Group justify="space-between" align="flex-start" gap="sm" mb="md" className={classes.panelHeader}>
                  <div>
                    <Text size="sm" fw={600}>
                      {tab.value === 'all' ? 'All library titles' : `${tab.label} games`}
                    </Text>
                    <Group gap="xs" align="center" wrap="nowrap">
                      <Text size="xs" c="dimmed">
                        {PANEL_COPY[tab.value]}
                      </Text>
                      {isActivePanel && isFetching && !isFetchingNextPage && (
                        <span className={classes.inlineLoading}>
                          <Loader size="xs" color="ember" />
                        </span>
                      )}
                    </Group>
                  </div>

                  {isActivePanel && (
                    <Group gap="sm" align="flex-end" className={classes.panelControls}>
                      <div className={classes.searchControl}>
                        <TextInput
                          className={classes.searchInput}
                          placeholder="Search saved games"
                          value={searchInput}
                          onChange={(event) => setSearchInput(event.currentTarget.value)}
                          onKeyDown={(event) => {
                            if (event.key === 'Enter') {
                              applySearch(searchInput);
                            }
                            if (event.key === 'Escape' && searchInput) {
                              clearSearch();
                            }
                          }}
                          leftSection={<IconSearch size={16} stroke={1.8} />}
                          rightSection={
                            searchInput ? (
                              <ActionIcon
                                variant="subtle"
                                color="gray"
                                onClick={clearSearch}
                                aria-label="Clear library search"
                              >
                                <IconX size={16} stroke={1.8} />
                              </ActionIcon>
                            ) : null
                          }
                          rightSectionPointerEvents="all"
                          size="sm"
                          radius="sm"
                        />
                        {showSearchStatus && (
                          <Text className={classes.searchStatus}>
                            {searchPending
                              ? 'Press Enter to search now, or pause typing for 3 seconds'
                              : `Showing matches for "${appliedSearch ?? ''}"`}
                          </Text>
                        )}
                      </div>

                      <Select
                        className={classes.sortSelect}
                        aria-label="Sort library entries"
                        value={sort}
                        onChange={(value) => value && setSort(value as LibrarySort)}
                        data={SORT_OPTIONS}
                        size="sm"
                        radius="sm"
                        allowDeselect={false}
                      />

                      <SegmentedControl
                        className={classes.viewSwitch}
                        aria-label="Library view"
                        value={viewMode}
                        onChange={(value) => setViewMode(value as 'covers' | 'compact')}
                        size="sm"
                        radius="sm"
                        color="ember"
                        data={[
                          {
                            value: 'covers',
                            label: (
                              <span className={classes.viewSwitchLabel}>
                                <IconLayoutGrid size={14} />
                                Covers
                              </span>
                            ),
                          },
                          {
                            value: 'compact',
                            label: (
                              <span className={classes.viewSwitchLabel}>
                                <IconListDetails size={14} />
                                Compact
                              </span>
                            ),
                          },
                        ]}
                      />

                      {tab.value === 'backlog' && panelEntries.length > 0 && (
                        <Button
                          size="xs"
                          variant="light"
                          color="ember"
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
                      {appliedSearch && (
                        <Button
                          size="xs"
                          variant="light"
                          color="ember"
                          mt="sm"
                          onClick={clearSearch}
                        >
                          Clear search
                        </Button>
                      )}
                    </div>
                  </div>
                ) : (
                  <>
                    {viewMode === 'covers' ? (
                      <Box className={classes.grid}>
                        {panelEntries.map((entry) => (
                          <Box key={entry.id} className={classes.libraryItem}>
                            <GameCard game={entry.game} />

                            <Paper p="sm" radius="xs" withBorder className={classes.entryMeta}>
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
                                  <Tooltip label={`Edit ${entry.game.name}`} withArrow>
                                    <ActionIcon
                                      size="sm"
                                      variant="subtle"
                                      color="gray"
                                      onClick={() => handleOpenEdit(entry)}
                                      aria-label={`Edit ${entry.game.name}`}
                                    >
                                      <IconPencil size={14} />
                                    </ActionIcon>
                                  </Tooltip>
                                  <Tooltip label={`Remove ${entry.game.name}`} withArrow>
                                    <ActionIcon
                                      size="sm"
                                      variant="subtle"
                                      color="red"
                                      onClick={() => handleRemove(entry.id, entry.game.name)}
                                      loading={removingEntryId === entry.id}
                                      aria-label={`Remove ${entry.game.name} from library`}
                                    >
                                      <IconTrash size={14} />
                                    </ActionIcon>
                                  </Tooltip>
                                </Group>
                              </Group>
                            </Paper>
                          </Box>
                        ))}
                      </Box>
                    ) : (
                      <div className={classes.compactList}>
                        {panelEntries.map((entry) => {
                          const rowUpdating = updatingEntryId === entry.id;
                          const runtime = formatRuntime(entry);

                          return (
                            <Paper key={entry.id} p="sm" radius="xs" withBorder className={classes.compactRow}>
                              <button
                                type="button"
                                className={classes.compactCover}
                                onClick={() => navigate(`/games/${entry.game.id}`)}
                                aria-label={`Open ${entry.game.name}`}
                              >
                                {entry.game.background_image ? (
                                  <img src={entry.game.background_image} alt="" />
                                ) : (
                                  <span>{getGameInitials(entry.game.name)}</span>
                                )}
                              </button>

                              <div className={classes.compactTitleBlock}>
                                <button
                                  type="button"
                                  className={classes.compactTitle}
                                  onClick={() => navigate(`/games/${entry.game.id}`)}
                                >
                                  {entry.game.name}
                                </button>
                                <Text className={classes.compactMeta}>{formatGameMeta(entry)}</Text>
                                <Group gap={6} wrap="wrap" className={classes.compactMobileBadges}>
                                  <Badge size="xs" color={STATUS_COLORS[entry.status]} variant="light">
                                    {STATUS_LABELS[entry.status]}
                                  </Badge>
                                  {runtime && <Badge size="xs" variant="default">{runtime}</Badge>}
                                </Group>
                              </div>

                              <div className={classes.compactStatus}>
                                <Select
                                  aria-label={`Change status for ${entry.game.name}`}
                                  value={entry.status}
                                  onChange={(value) => {
                                    if (value && value !== entry.status) {
                                      void handleInlineUpdate(entry, { status: value as LibraryStatus });
                                    }
                                  }}
                                  data={[
                                    { value: 'playing', label: 'Playing' },
                                    { value: 'replaying', label: 'Replaying' },
                                    { value: 'completed', label: 'Completed' },
                                    { value: 'backlog', label: 'Backlog' },
                                    { value: 'wishlist', label: 'Wishlist' },
                                    { value: 'dropped', label: 'Dropped' },
                                  ]}
                                  size="xs"
                                  radius="sm"
                                  disabled={rowUpdating}
                                  allowDeselect={false}
                                />
                              </div>

                              <div className={classes.compactRating}>
                                <Rating
                                  value={entry.rating ?? 0}
                                  fractions={2}
                                  size="xs"
                                  color="yellow"
                                  onChange={(value) => {
                                    if (value !== entry.rating && value > 0) {
                                      void handleInlineUpdate(entry, { rating: value });
                                    }
                                  }}
                                  aria-label={`Rate ${entry.game.name}`}
                                  readOnly={rowUpdating}
                                />
                                <Text size="xs" c="dimmed" className={classes.ratingText}>
                                  {entry.rating !== null ? entry.rating.toFixed(1) : 'Not rated'}
                                </Text>
                              </div>

                              <div className={classes.compactAdded}>
                                <Text className={classes.compactLabel}>Added</Text>
                                <Text className={classes.compactValue}>
                                  {dateFormatter.format(new Date(entry.added_at))}
                                </Text>
                              </div>

                              <div className={classes.compactRuntime}>
                                {runtime ? (
                                  <>
                                    <Text className={classes.compactLabel}>Runtime</Text>
                                    <Text className={classes.compactValue}>{runtime}</Text>
                                  </>
                                ) : (
                                  <Text className={classes.compactValue}>No runtime</Text>
                                )}
                              </div>

                              <Group gap={6} className={classes.compactActions} wrap="nowrap">
                                <Tooltip label={`Edit ${entry.game.name}`} withArrow>
                                  <ActionIcon
                                    size="sm"
                                    variant="subtle"
                                    color="gray"
                                    onClick={() => handleOpenEdit(entry)}
                                    aria-label={`Edit ${entry.game.name}`}
                                  >
                                    <IconPencil size={14} />
                                  </ActionIcon>
                                </Tooltip>
                                <Tooltip label={`Remove ${entry.game.name}`} withArrow>
                                  <ActionIcon
                                    size="sm"
                                    variant="subtle"
                                    color="red"
                                    onClick={() => handleRemove(entry.id, entry.game.name)}
                                    loading={removingEntryId === entry.id}
                                    aria-label={`Remove ${entry.game.name} from library`}
                                  >
                                    <IconTrash size={14} />
                                  </ActionIcon>
                                </Tooltip>
                              </Group>
                            </Paper>
                          );
                        })}
                      </div>
                    )}

                    <div className={classes.loadMoreFooter}>
                      <Text size="xs" c="dimmed">
                        Showing {panelEntries.length.toLocaleString()} of {visibleTotal.toLocaleString()}
                      </Text>
                      {hasNextPage && (
                        <Button
                          size="xs"
                          variant="light"
                          color="ember"
                          loading={isFetchingNextPage}
                          onClick={() => {
                            void fetchNextPage();
                          }}
                        >
                          Load more
                        </Button>
                      )}
                    </div>
                  </>
                )}
              </Paper>
            </Tabs.Panel>
          );
        })}
      </Tabs>

      <div className={classes.insightGrid}>
        <Paper p="md" radius="xs" withBorder className={classes.insightPanel}>
          <Group justify="space-between" mb="sm" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Library shape</Text>
              <Text size="xs" c="dimmed">A compact read after the shelf, not before it.</Text>
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

        <Paper p="md" radius="xs" withBorder className={classes.insightPanel}>
          <Group justify="space-between" mb="sm" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Taste signals</Text>
              <Text size="xs" c="dimmed">Genres showing up most often across saved titles.</Text>
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
                    color={index === 0 ? 'ember' : 'gray'}
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
            <Button color="ember" onClick={handleSaveEdit} loading={updateEntry.isPending}>Save</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
