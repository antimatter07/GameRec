import { Badge, Button, Group, Modal, Rating, Stack, Text } from '@mantine/core';
import { IconDeviceGamepad2 } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import type { LibraryEntry, LibraryStatus } from '../../types/library';
import { useEnqueueGame } from '../../hooks/usePlayQueue';
import classes from './QueueCards.module.css';

interface AddToQueueModalProps {
  entry: LibraryEntry | null;
  opened: boolean;
  onClose: () => void;
}

const STATUS_COLORS: Record<LibraryStatus, string> = {
  playing:   'ember',
  completed: 'blue',
  backlog:   'teal',
  dropped:   'grape',
  wishlist:  'pink',
  replaying: 'orange',
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
          color: 'ember',
        });
        onClose();
      },
      onError: () => {
        notifications.show({ color: 'red', message: 'Failed to add to queue' });
      },
    });
  };

  return (
    <Modal opened={opened} onClose={onClose} title="Add to queue" centered size="sm">
      {entry && (
        <Stack gap="md">
          <div className={classes.modalCover}>
            {entry.game.background_image ? (
              <img src={entry.game.background_image} alt="" />
            ) : (
              <div className={classes.modalCoverFallback}>
                <IconDeviceGamepad2 size={30} stroke={1.6} />
              </div>
            )}
            <div className={classes.modalCoverShade} />
          </div>

          <Stack gap={6}>
            <Text className={classes.modalTitle}>{entry.game.name}</Text>

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
            <Button color="ember" onClick={handleAdd} loading={enqueue.isPending}>
              Add to queue
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}
