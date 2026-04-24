import { useState } from 'react';
import { Box, Center, Group, Loader, Paper, Stack, Text, Title } from '@mantine/core';
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

const POOL_STATUSES = new Set(['backlog', 'completed', 'dropped']);

// Prefer pointer-within detection so empty containers are valid drop targets,
// fall back to closestCenter for precise reordering within a populated container.
const collisionDetection: CollisionDetection = (args) => {
  const pointerCollisions = pointerWithin(args);
  if (pointerCollisions.length > 0) return pointerCollisions;
  return closestCenter(args);
};

function DroppableZone({ id, children }: { id: string; children: React.ReactNode }) {
  const { setNodeRef } = useDroppable({ id });
  // minHeight ensures the droppable rect is always large enough to detect,
  // even when the container has no sortable children.
  return <div ref={setNodeRef} style={{ minHeight: 80 }}>{children}</div>;
}

export default function QueuePage() {
  const { data: queue, isLoading: queueLoading } = usePlayQueue();
  const { data: entries, isLoading: libraryLoading } = useLibrary();
  const enqueue = useEnqueueGame();
  const dequeue = useDequeueGame();
  const reorder = useReorderQueue();

  const [modalEntry, setModalEntry] = useState<LibraryEntry | null>(null);

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const queuedEntryIds = new Set(queue?.entries.map((e) => e.entry_id) ?? []);
  const poolEntries = (entries ?? [])
    .filter((e) => !queuedEntryIds.has(e.id) && POOL_STATUSES.has(e.status))
    .sort((a, b) => new Date(b.added_at).getTime() - new Date(a.added_at).getTime());

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over) return;

    const activeId = String(active.id);
    const overId = String(over.id);

    const activeIsPool = activeId.startsWith('pool-');
    const overIsPool = overId.startsWith('pool-') || overId === 'pool-container';
    const overIsQueue = !overIsPool;

    // Case A: pool → queue (enqueue)
    if (activeIsPool && overIsQueue) {
      const entryId = Number(activeId.replace('pool-', ''));
      enqueue.mutate(entryId);
      return;
    }

    // Case B: queue → pool (dequeue)
    if (!activeIsPool && overIsPool) {
      dequeue.mutate(Number(activeId));
      return;
    }

    // Case C: within queue (reorder)
    if (!activeIsPool && !overIsPool && active.id !== over.id && queue) {
      const oldIds = queue.entries.map((e) => e.entry_id);
      const fromIdx = oldIds.indexOf(Number(activeId));
      const toIdx = oldIds.indexOf(Number(overId));
      if (fromIdx === -1 || toIdx === -1) return;

      const reordered = [...oldIds];
      reordered.splice(fromIdx, 1);
      reordered.splice(toIdx, 0, Number(activeId));

      reorder.mutate(reordered);
      return;
    }

    // Case D: within pool — no persisted order, ignore
  };

  if (queueLoading || libraryLoading) {
    return <Center h={400}><Loader /></Center>;
  }

  const queueItems = queue?.entries ?? [];
  const queueSortableIds = queueItems.map((e) => e.entry_id);
  const poolSortableIds = poolEntries.map((e) => `pool-${e.id}`);

  return (
    <Stack gap="md">
      <Group justify="space-between" align="center">
        <Title order={2}>Queue</Title>
        <Text size="sm" c="dimmed">
          {queueItems.length} queued · {poolEntries.length} available
        </Text>
      </Group>

      <DndContext sensors={sensors} collisionDetection={collisionDetection} onDragEnd={handleDragEnd}>
        {/* Top: the queue */}
        <Paper withBorder radius="md" p="md">
          <Stack gap="xs">
            <Group justify="space-between" align="center">
              <Text fw={600} size="sm">My Queue</Text>
              <Text size="xs" c="dimmed">
                Drag to reorder · drag to the list below to remove
              </Text>
            </Group>

            <DroppableZone id="queue-container">
              <SortableContext items={queueSortableIds} strategy={rectSortingStrategy}>
                {queueItems.length === 0 ? (
                  <Center py="xl">
                    <Text c="dimmed" size="sm" ta="center">
                      No games queued yet. Drag a game from your library below, or click its
                      <Text span fw={600}> + </Text>
                      icon to add it.
                    </Text>
                  </Center>
                ) : (
                  <Box style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
                    {queueItems.map((item) => (
                      <PlayQueueItem key={item.entry_id} item={item} />
                    ))}
                  </Box>
                )}
              </SortableContext>
            </DroppableZone>
          </Stack>
        </Paper>

        {/* Bottom: library pool */}
        <Paper withBorder radius="md" p="md">
          <Stack gap="xs">
            <Group justify="space-between" align="center">
              <Text fw={600} size="sm">Library</Text>
              <Text size="xs" c="dimmed">
                Drag into the queue or click + to add
              </Text>
            </Group>

            <DroppableZone id="pool-container">
              <SortableContext items={poolSortableIds} strategy={rectSortingStrategy}>
                {poolEntries.length === 0 ? (
                  <Center py="xl">
                    <Text c="dimmed" size="sm" ta="center">
                      {entries && entries.length === 0
                        ? 'Your library is empty. Add games from the catalog to queue them.'
                        : 'Every eligible library game is already queued.'}
                    </Text>
                  </Center>
                ) : (
                  <Box style={{ display: 'flex', flexWrap: 'wrap', gap: 12 }}>
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
