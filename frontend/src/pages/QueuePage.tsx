import { useMemo, useState } from 'react';
import {
  Box,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  Stack,
  Text,
} from '@mantine/core';
import {
  DndContext,
  closestCenter,
  pointerWithin,
  PointerSensor,
  useDroppable,
  useSensor,
  useSensors,
  type DragEndEvent,
  type CollisionDetection,
} from '@dnd-kit/core';
import { SortableContext, rectSortingStrategy } from '@dnd-kit/sortable';
import {
  IconArrowRight,
  IconBooks,
  IconClock,
  IconLayoutGrid,
  IconPlayerPlay,
} from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { PlayQueueItem } from '../components/library/PlayQueueItem';
import { QueuePoolCard } from '../components/library/QueuePoolCard';
import { AddToQueueModal } from '../components/library/AddToQueueModal';
import {
  useDequeueGame,
  useEnqueueGame,
  usePlayQueue,
  useReorderQueue,
} from '../hooks/usePlayQueue';
import { useLibrary } from '../hooks/useLibrary';
import type { LibraryEntry } from '../types/library';
import type { PlayQueueEntry } from '../types/playQueue';
import classes from './QueuePage.module.css';

const POOL_STATUSES = new Set(['backlog', 'completed', 'dropped']);

// Prefer pointer-within detection so empty containers are valid drop targets,
// fall back to closestCenter for precise reordering within a populated container.
const collisionDetection: CollisionDetection = (args) => {
  const pointerCollisions = pointerWithin(args);
  if (pointerCollisions.length > 0) return pointerCollisions;
  return closestCenter(args);
};

function DroppableZone({
  id,
  children,
}: {
  id: string;
  children: React.ReactNode;
}) {
  const { isOver, setNodeRef } = useDroppable({ id });

  return (
    <div
      ref={setNodeRef}
      className={`${classes.droppableZone} ${isOver ? classes.droppableZoneActive : ''}`}
    >
      {children}
    </div>
  );
}

function sumQueueHours(entries: PlayQueueEntry[]) {
  return entries.reduce((total, item) => {
    const hours = item.entry.game.hltb_main_hours ?? item.entry.game.playtime ?? 0;
    return total + hours;
  }, 0);
}

export default function QueuePage() {
  const { data: queue, isLoading: queueLoading } = usePlayQueue();
  const { data: entries, isLoading: libraryLoading } = useLibrary();
  const enqueue = useEnqueueGame();
  const dequeue = useDequeueGame();
  const reorder = useReorderQueue();
  const navigate = useNavigate();

  const [modalEntry, setModalEntry] = useState<LibraryEntry | null>(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const queuedEntryIds = new Set(queue?.entries.map((entry) => entry.entry_id) ?? []);
  const poolEntries = (entries ?? [])
    .filter((entry) => !queuedEntryIds.has(entry.id) && POOL_STATUSES.has(entry.status))
    .sort((a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime());

  const queueItems = queue?.entries ?? [];
  const queueSortableIds = queueItems.map((entry) => entry.entry_id);
  const poolSortableIds = poolEntries.map((entry) => `pool-${entry.id}`);

  const queueHours = useMemo(() => sumQueueHours(queueItems), [queueItems]);
  const availableBacklogCount = poolEntries.filter((entry) => entry.status === 'backlog').length;
  const nextUp = queueItems[0] ?? null;
  const topQueuedGenres = useMemo(() => {
    const counts = new Map<string, number>();

    queueItems.forEach((item) => {
      item.entry.game.genres.forEach((genre) => {
        counts.set(genre.name, (counts.get(genre.name) ?? 0) + 1);
      });
    });

    return [...counts.entries()]
      .sort((a, b) => b[1] - a[1] || a[0].localeCompare(b[0]))
      .slice(0, 5)
      .map(([name, count]) => ({ name, count }));
  }, [queueItems]);

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const activeIsPool = activeId.startsWith('pool-');
    const overIsPool = overId.startsWith('pool-') || overId === 'pool-container';
    const overIsQueue = !overIsPool;

    // Case A: pool -> queue (enqueue)
    if (activeIsPool && overIsQueue) {
      const entryId = Number(activeId.replace('pool-', ''));
      enqueue.mutate(entryId);
      return;
    }

    // Case B: queue -> pool (dequeue)
    if (!activeIsPool && overIsPool) {
      dequeue.mutate(Number(activeId));
      return;
    }

    // Case C: within queue (reorder)
    if (!activeIsPool && !overIsPool && active.id !== over.id && queue) {
      const oldIds = queue.entries.map((entry) => entry.entry_id);
      const fromIdx = oldIds.indexOf(Number(activeId));
      const toIdx = oldIds.indexOf(Number(overId));
      if (fromIdx === -1 || toIdx === -1) return;

      const reordered = [...oldIds];
      reordered.splice(fromIdx, 1);
      reordered.splice(toIdx, 0, Number(activeId));

      reorder.mutate(reordered);
    }

    // Case D: within pool — no persisted order, ignore
  };

  if (queueLoading || libraryLoading) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="violet" size="md" />
          <Text size="sm" c="dimmed">Loading your queue…</Text>
        </Stack>
      </Center>
    );
  }

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Play <span className={classes.headerAccent}>Queue</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Keep your next games lined up, reorder them by drag and drop, and pull fresh candidates in from your library.
          </Text>
        </div>

        <Button
          leftSection={<IconArrowRight size={16} />}
          color="violet"
          variant="light"
          onClick={() => navigate('/library/backlog')}
        >
          Backlog tools
        </Button>
      </div>

      <div className={classes.metricsGrid}>
        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-violet-light)' }}>
            <IconLayoutGrid size={18} color="var(--mantine-color-violet-5)" />
          </div>
          <div className={classes.metricLabel}>Queued now</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-violet-4)' }}>
            {queueItems.length}
          </div>
          <div className={classes.metricSub}>Drag cards to reorder the lineup</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
            <IconBooks size={18} color="var(--mantine-color-blue-5)" />
          </div>
          <div className={classes.metricLabel}>Available pool</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-blue-4)' }}>
            {poolEntries.length}
          </div>
          <div className={classes.metricSub}>Eligible library games ready to drag in</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
            <IconClock size={18} color="var(--mantine-color-teal-5)" />
          </div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-teal-4)' }}>
            {queueHours > 0 ? `${Math.round(queueHours)}h` : '—'}
          </div>
          <div className={classes.metricLabel}>Est. queue time</div>
          <div className={classes.metricSub}>Based on main-story hours when available</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-yellow-light)' }}>
            <IconPlayerPlay size={18} color="var(--mantine-color-yellow-5)" />
          </div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-yellow-4)' }}>
            {availableBacklogCount}
          </div>
          <div className={classes.metricLabel}>Backlog ready</div>
          <div className={classes.metricSub}>Unqueued backlog titles waiting for a slot</div>
        </Paper>
      </div>

      <div className={classes.overviewGrid}>
        <Paper p="md" radius="md" withBorder>
          <Group justify="space-between" mb="sm" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Next up</Text>
              <Text size="xs" c="dimmed">The current front of the queue, plus a quick reminder of how the board behaves.</Text>
            </div>
          </Group>

          {nextUp ? (
            <div className={classes.nextUpCard}>
              <div className={classes.nextUpCover}>
                {nextUp.entry.game.background_image ? (
                  <img src={nextUp.entry.game.background_image} alt={nextUp.entry.game.name} />
                ) : (
                  <Text size="lg">🎮</Text>
                )}
              </div>
              <div className={classes.nextUpInfo}>
                <div className={classes.nextUpTitle}>{nextUp.entry.game.name}</div>
                <div className={classes.nextUpMeta}>
                  <span>Position {nextUp.position}</span>
                  {(nextUp.entry.game.hltb_main_hours ?? nextUp.entry.game.playtime) !== null && (
                    <>
                      <span>·</span>
                      <span>~{Math.round(nextUp.entry.game.hltb_main_hours ?? nextUp.entry.game.playtime ?? 0)}h</span>
                    </>
                  )}
                  {nextUp.entry.game.genres[0] && (
                    <>
                      <span>·</span>
                      <span>{nextUp.entry.game.genres[0].name}</span>
                    </>
                  )}
                </div>
                <Text size="xs" c="dimmed" className={classes.nextUpNote}>
                  Drag within the top board to reorder. Drag a queued card down into the library pool to remove it.
                </Text>
              </div>
            </div>
          ) : (
            <div className={classes.emptyMiniState}>
              <Text size="sm" fw={600}>Queue is empty</Text>
              <Text size="xs" c="dimmed">
                Pull titles up from the library pool below to start building the lineup.
              </Text>
            </div>
          )}
        </Paper>

        <Paper p="md" radius="md" withBorder>
          <Group justify="space-between" mb="sm" className={classes.panelHeader}>
            <div>
              <Text size="sm" fw={600}>Queued genres</Text>
              <Text size="xs" c="dimmed">A quick read on the mix of what you have lined up.</Text>
            </div>
          </Group>

          {topQueuedGenres.length > 0 ? (
            <Stack gap="sm">
              <div className={classes.genreCloud}>
                {topQueuedGenres.map((genre, index) => (
                  <div key={genre.name} className={classes.genreRow}>
                    <div className={classes.genreMeta}>
                      <Text className={classes.genreLabel}>{genre.name}</Text>
                      <Text className={classes.genreValue}>{genre.count}</Text>
                    </div>
                    <div className={classes.genreTrack}>
                      <div
                        className={classes.genreFill}
                        style={{
                          width: `${Math.max((genre.count / queueItems.length) * 100, 10)}%`,
                          background: index === 0
                            ? 'var(--mantine-color-violet-5)'
                            : 'var(--mantine-color-blue-5)',
                        }}
                      />
                    </div>
                  </div>
                ))}
              </div>
              <Text size="xs" c="dimmed">
                {topQueuedGenres[0].name} is currently the strongest thread running through the queue.
              </Text>
            </Stack>
          ) : (
            <div className={classes.emptyMiniState}>
              <Text size="sm" fw={600}>No queued genre mix yet</Text>
              <Text size="xs" c="dimmed">
                Once you add a few games, the queue’s genre balance will show up here.
              </Text>
            </div>
          )}
        </Paper>
      </div>

      <DndContext sensors={sensors} collisionDetection={collisionDetection} onDragEnd={handleDragEnd}>
        <Paper withBorder radius="md" p="md">
          <Stack gap="sm">
            <Group justify="space-between" align="flex-start" gap="sm" className={classes.panelHeader}>
              <div>
                <Text size="sm" fw={600}>My queue</Text>
                <Text size="xs" c="dimmed">Compact drag cards with position, runtime, and quick removal.</Text>
              </div>
              <Text size="xs" c="dimmed" className={classes.panelMeta}>
                Drag to reorder
              </Text>
            </Group>

            <DroppableZone id="queue-container">
              <SortableContext items={queueSortableIds} strategy={rectSortingStrategy}>
                {queueItems.length === 0 ? (
                  <div className={classes.emptyState}>
                    <div>
                      <Text size="sm" fw={600}>Nothing queued yet</Text>
                      <Text size="xs" c="dimmed" mt={4}>
                        Drag a game up from your library pool, or use the add button on any eligible card below.
                      </Text>
                    </div>
                  </div>
                ) : (
                  <Box className={classes.cardGrid}>
                    {queueItems.map((item) => (
                      <PlayQueueItem key={item.entry_id} item={item} />
                    ))}
                  </Box>
                )}
              </SortableContext>
            </DroppableZone>
          </Stack>
        </Paper>

        <Paper withBorder radius="md" p="md">
          <Stack gap="sm">
            <Group justify="space-between" align="flex-start" gap="sm" className={classes.panelHeader}>
              <div>
                <Text size="sm" fw={600}>Library pool</Text>
                <Text size="xs" c="dimmed">Drag from here into the queue, or tap the plus button to place a title directly.</Text>
              </div>
              <Text size="xs" c="dimmed" className={classes.panelMeta}>
                {poolEntries.length} available
              </Text>
            </Group>

            <DroppableZone id="pool-container">
              <SortableContext items={poolSortableIds} strategy={rectSortingStrategy}>
                {poolEntries.length === 0 ? (
                  <div className={classes.emptyState}>
                    <div>
                      <Text size="sm" fw={600}>Pool is clear</Text>
                      <Text size="xs" c="dimmed" mt={4}>
                        {entries && entries.length === 0
                          ? 'Your library is empty. Add games from the catalog to queue them.'
                          : 'Every eligible library game is already queued.'}
                      </Text>
                    </div>
                  </div>
                ) : (
                  <Box className={classes.cardGrid}>
                    {poolEntries.map((entry) => (
                      <QueuePoolCard
                        key={entry.id}
                        entry={entry}
                        onPlusClick={() => setModalEntry(entry)}
                      />
                    ))}
                  </Box>
                )}
              </SortableContext>
            </DroppableZone>
          </Stack>
        </Paper>
      </DndContext>

      <AddToQueueModal
        entry={modalEntry}
        opened={modalEntry !== null}
        onClose={() => setModalEntry(null)}
      />
    </Stack>
  );
}
