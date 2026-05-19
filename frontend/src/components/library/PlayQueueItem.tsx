import { ActionIcon, Group, Rating, Text } from '@mantine/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { IconX } from '@tabler/icons-react';
import type { PlayQueueEntry } from '../../types/playQueue';
import { useDequeueGame } from '../../hooks/usePlayQueue';
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

  const playtimeHours = game.hltb_main_hours ?? game.playtime ?? null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const primaryGenres = game.genres.slice(0, 2).map((genre) => genre.name).join(' / ');

  return (
    <div
      ref={setNodeRef}
      style={{
        transform: CSS.Transform.toString(transform),
        transition,
      }}
      className={`${classes.card} ${isDragging ? classes.cardDragging : ''}`}
      {...attributes}
      {...listeners}
    >
      <div className={classes.coverWrap}>
        <div className={classes.overlayLeft}>
          <div className={classes.queueBadge}>#{item.position}</div>
        </div>

        <div className={classes.overlayRight}>
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
        </div>

        {game.background_image ? (
          <img src={game.background_image} alt={game.name} className={classes.coverImage} />
        ) : (
          <div className={classes.coverFallback}>
            <Text size="lg">🎮</Text>
          </div>
        )}
      </div>

      <div className={classes.body}>
        <Text className={classes.title} lineClamp={2}>
          {game.name}
        </Text>

        <div className={classes.meta}>
          {releaseYear && <span>{releaseYear}</span>}
          {primaryGenres && <span>{primaryGenres}</span>}
        </div>

        <div className={classes.footer}>
          <div className={classes.footerLeft}>
            {playtimeHours != null && (
              <Text className={classes.footnote}>~{Number(playtimeHours).toFixed(0)}h</Text>
            )}
          </div>

          {item.entry.rating !== null && (
            <Group gap={4} wrap="nowrap">
              <Rating value={item.entry.rating} fractions={2} readOnly size="xs" color="yellow" />
              <Text className={classes.ratingValue}>{item.entry.rating.toFixed(1)}</Text>
            </Group>
          )}
        </div>
      </div>
    </div>
  );
}
