import { ActionIcon } from '@mantine/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { IconX } from '@tabler/icons-react';
import type { PlayQueueEntry } from '../../types/playQueue';
import { useDequeueGame } from '../../hooks/usePlayQueue';
import { QueueCard } from './QueueCard';
import classes from './QueueCards.module.css';

interface PlayQueueItemProps {
  item: PlayQueueEntry;
}

export function PlayQueueItem({ item }: PlayQueueItemProps) {
  const { game } = item.entry;
  const dequeue = useDequeueGame();

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: item.entry_id,
  });

  return (
    <QueueCard
      cardRef={setNodeRef}
      game={game}
      rating={item.entry.rating}
      label={`#${item.position}`}
      isDragging={isDragging}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
      containerProps={{ ...attributes, ...listeners }}
      removeAction={(
        <ActionIcon
          size="sm"
          radius="sm"
          variant="filled"
          color="dark"
          className={classes.actionButton}
          onClick={(event) => {
            event.stopPropagation();
            dequeue.mutate(item.entry_id);
          }}
          onPointerDown={(event) => event.stopPropagation()}
          loading={dequeue.isPending}
          aria-label={`Remove ${game.name} from queue`}
        >
          <IconX size={12} />
        </ActionIcon>
      )}
    />
  );
}
