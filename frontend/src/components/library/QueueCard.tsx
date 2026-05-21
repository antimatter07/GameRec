import type { CSSProperties, HTMLAttributes, ReactNode, Ref } from 'react';
import { Group, Rating, Text } from '@mantine/core';
import type { GameListItem } from '../../types/game';
import classes from './QueueCards.module.css';

interface QueueCardProps {
  game: GameListItem;
  rating: number | null;
  label: string;
  reason?: string | null;
  readOnly?: boolean;
  isDragging?: boolean;
  removeAction?: ReactNode;
  cardRef?: Ref<HTMLDivElement>;
  style?: CSSProperties;
  containerProps?: HTMLAttributes<HTMLDivElement>;
}

export function QueueCard({
  game,
  rating,
  label,
  reason,
  readOnly = false,
  isDragging = false,
  removeAction,
  cardRef,
  style,
  containerProps,
}: QueueCardProps) {
  const playtimeHours = game.hltb_main_hours ?? game.playtime ?? null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const primaryGenres = game.genres.slice(0, 2).map((genre) => genre.name).join(' / ');
  const className = [
    classes.card,
    readOnly ? classes.cardStatic : '',
    isDragging ? classes.cardDragging : '',
    containerProps?.className ?? '',
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <div
      ref={cardRef}
      {...containerProps}
      style={style}
      className={className}
    >
      <div className={classes.coverWrap}>
        <div className={classes.overlayLeft}>
          <div className={classes.queueBadge}>{label}</div>
        </div>

        {removeAction && (
          <div className={classes.overlayRight}>
            {removeAction}
          </div>
        )}

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

          {rating !== null && (
            <Group gap={4} wrap="nowrap">
              <Rating value={rating} fractions={2} readOnly size="xs" color="yellow" />
              <Text className={classes.ratingValue}>{rating.toFixed(1)}</Text>
            </Group>
          )}
        </div>

        {reason && (
          <div className={classes.reasonBlock}>
            <Text className={classes.reasonLabel}>AI reason</Text>
            <Text className={classes.reasonText}>{reason}</Text>
          </div>
        )}
      </div>
    </div>
  );
}
