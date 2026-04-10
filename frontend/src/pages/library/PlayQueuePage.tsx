import { Box, Button, Center, Group, Loader, Stack, Text, Title } from '@mantine/core';
import {
  DndContext,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  type DragEndEvent,
} from '@dnd-kit/core';
import { SortableContext, rectSortingStrategy } from '@dnd-kit/sortable';
import { IconArrowLeft } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { PlayQueueItem } from '../../components/library/PlayQueueItem';
import { usePlayQueue, useReorderQueue } from '../../hooks/usePlayQueue';

export default function PlayQueuePage() {
  const navigate = useNavigate();
  const { data: queue, isLoading } = usePlayQueue();
  const reorder = useReorderQueue();

  const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 5 } }));

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id || !queue) return;

    const oldIds = queue.entries.map((e) => e.entry_id);
    const fromIdx = oldIds.indexOf(active.id as number);
    const toIdx = oldIds.indexOf(over.id as number);
    if (fromIdx === -1 || toIdx === -1) return;

    const reordered = [...oldIds];
    reordered.splice(fromIdx, 1);
    reordered.splice(toIdx, 0, active.id as number);

    reorder.mutate(reordered);
  };

  if (isLoading) return <Center h={400}><Loader /></Center>;

  return (
    <Stack gap="md">
      <Group justify="space-between" align="center">
        <Group gap="xs">
          <Button
            variant="subtle"
            size="xs"
            leftSection={<IconArrowLeft size={14} />}
            onClick={() => navigate('/library')}
          >
            Library
          </Button>
          <Title order={2}>My Play Queue</Title>
        </Group>
        {queue && queue.total > 0 && (
          <Text size="sm" c="dimmed">{queue.total} {queue.total === 1 ? 'game' : 'games'}</Text>
        )}
      </Group>

      {!queue || queue.total === 0 ? (
        <Center h={300}>
          <Stack align="center" gap="sm">
            <Text c="dimmed" ta="center">No games queued yet.</Text>
            <Text c="dimmed" size="sm" ta="center">
              Head to Play Next to find candidates, then add them here to set your own order.
            </Text>
            <Button variant="light" size="sm" onClick={() => navigate('/library/backlog')}>
              Go to Play Next
            </Button>
          </Stack>
        </Center>
      ) : (
        <DndContext sensors={sensors} collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
          <SortableContext items={queue.entries.map((e) => e.entry_id)} strategy={rectSortingStrategy}>
            <Box
              style={{
                display: 'flex',
                flexWrap: 'wrap',
                gap: 12,
              }}
            >
              {queue.entries.map((item) => (
                <PlayQueueItem key={item.entry_id} item={item} />
              ))}
            </Box>
          </SortableContext>
        </DndContext>
      )}
    </Stack>
  );
}
