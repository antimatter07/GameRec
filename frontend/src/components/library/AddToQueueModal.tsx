import { Badge, Button, Group, Image, Modal, Rating, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import type { LibraryEntry, LibraryStatus } from '../../types/library';
import { useEnqueueGame } from '../../hooks/usePlayQueue';

interface AddToQueueModalProps {
  entry: LibraryEntry | null;
  opened: boolean;
  onClose: () => void;
}

const STATUS_COLORS: Record<LibraryStatus, string> = {
  playing:   'violet',
  completed: 'blue',
  backlog:   'teal',
  dropped:   'grape',
};

export function AddToQueueModal({ entry, opened, onClose }: AddToQueueModalProps) {
  const enqueue = useEnqueueGame();

  const handleAdd = () => {
    if (!entry) return;
    enqueue.mutate(entry.id, {
      onSuccess: (data) => {
        const pos = data.entries.find((e) => e.entry_id === entry.id)?.position;
        notifications.show({
          message: `Added "${entry.game.name}" to queue${pos != null ? ` at position ${pos}` : ''}`,
          color: 'grape',
        });
        onClose();
      },
      onError: () => {
        notifications.show({ color: 'red', message: 'Failed to add to queue' });
      },
    });
  };

  return (
    <Modal opened={opened} onClose={onClose} title="Add to Queue" centered size="sm">
      {entry && (
        <Stack gap="md">
          <Image
            src={entry.game.background_image ?? undefined}
            h={140}
            radius="sm"
            fallbackSrc="https://placehold.co/400x140?text=?"
            style={{ objectFit: 'cover' }}
          />

          <Stack gap={6}>
            <Text fw={600} size="md">{entry.game.name}</Text>

            <Group gap={4} wrap="wrap">
              <Badge size="xs" color={STATUS_COLORS[entry.status]} variant="light">
                {entry.status}
              </Badge>
              {entry.game.genres.slice(0, 3).map((g) => (
                <Badge key={g.id} size="xs" variant="light">{g.name}</Badge>
              ))}
            </Group>

            {entry.rating !== null && (
              <Group gap={6}>
                <Rating value={entry.rating} fractions={2} readOnly size="xs" />
                <Text size="xs" c="dimmed">{entry.rating.toFixed(1)} / 5</Text>
              </Group>
            )}
          </Stack>

          <Group justify="flex-end" gap="xs">
            <Button variant="default" onClick={onClose}>Cancel</Button>
            <Button color="violet" onClick={handleAdd} loading={enqueue.isPending}>
              Add to Queue
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}
