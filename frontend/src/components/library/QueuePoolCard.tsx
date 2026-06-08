import { ActionIcon, Badge, Group, Rating, Text, Tooltip } from '@mantine/core';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { IconDeviceGamepad2, IconGripVertical, IconPlus } from '@tabler/icons-react';
import type { LibraryEntry, LibraryStatus } from '../../types/library';
import classes from './QueueCards.module.css';

interface QueuePoolCardProps {
  entry: LibraryEntry;
  onPlusClick: () => void;
}

const STATUS_COLORS: Record<LibraryStatus, string> = {
  playing:   'ember',
  completed: 'blue',
  backlog:   'teal',
  dropped:   'grape',
  wishlist:  'pink',
  replaying: 'orange',
};

export function QueuePoolCard({ entry, onPlusClick }: QueuePoolCardProps) {
  const { game } = entry;

  const { attributes, listeners, setNodeRef, transform, transition, isDragging } = useSortable({
    id: `pool-${entry.id}`,
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
          <Badge size="xs" color={STATUS_COLORS[entry.status]} variant="filled">
            {entry.status}
          </Badge>
        </div>

        <div className={classes.overlayRight}>
          <ActionIcon
            size="sm"
            radius="sm"
            variant="filled"
            color="ember"
            className={classes.actionButton}
            onClick={(event) => {
              event.stopPropagation();
              onPlusClick();
            }}
            onPointerDown={(event) => event.stopPropagation()}
            aria-label={`Add ${game.name} to queue`}
          >
            <IconPlus size={12} />
          </ActionIcon>
        </div>

        {game.background_image ? (
          <img src={game.background_image} alt={game.name} className={classes.coverImage} />
        ) : (
          <div className={classes.coverFallback}>
            <IconDeviceGamepad2 size={24} stroke={1.6} />
          </div>
        )}
      </div>

      <div className={classes.body}>
        <div className={classes.titleRow}>
          <Text className={classes.title} lineClamp={2}>
            {game.name}
          </Text>

          <Tooltip label="Drag card" withArrow openDelay={150}>
            <span className={classes.dragHandle} aria-hidden="true">
              <IconGripVertical size={15} stroke={1.8} />
            </span>
          </Tooltip>
        </div>

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

          {entry.rating !== null && (
            <Group gap={4} wrap="nowrap">
              <Rating value={entry.rating} fractions={2} readOnly size="xs" color="yellow" />
              <Text className={classes.ratingValue}>{entry.rating.toFixed(1)}</Text>
            </Group>
          )}
        </div>
      </div>
    </div>
  );
}
