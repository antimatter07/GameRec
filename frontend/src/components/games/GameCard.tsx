import type { KeyboardEvent } from 'react';
import { Badge, Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
import { useNavigate } from 'react-router';
import { useLibrary } from '../../hooks/useLibrary';
import type { GameListItem } from '../../types/game';
import { SaveToLibraryButton } from './SaveToLibraryButton';
import classes from './GameCard.module.css';

interface GameCardProps {
  game: GameListItem;
  /** Show an "Add to Library" button — omit on the library page */
  showAdd?: boolean;
}

export function GameCard({ game, showAdd = false }: GameCardProps) {
  const { data: library } = useLibrary();
  const navigate = useNavigate();

  const libraryEntry = library?.find((entry) => entry.game.id === game.id) ?? null;
  const inLibrary = libraryEntry !== null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const primaryGenre = game.genres[0]?.name;
  const primaryPlatform = game.platforms[0]?.name;
  const metaItems = [releaseYear ?? 'TBA', primaryGenre, primaryPlatform].filter(Boolean).join(' / ');
  const playtimeLabel = game.hltb_main_hours
    ? `${Math.round(game.hltb_main_hours)}h main`
    : game.playtime
      ? `${game.playtime}h avg`
      : null;

  const openGame = () => navigate(`/games/${game.id}`);

  return (
    <Card
      className={classes.card}
      padding="sm"
      radius="md"
      withBorder
      role="link"
      tabIndex={0}
      onClick={openGame}
      onKeyDown={(event: KeyboardEvent) => {
        if (event.key === 'Enter' || event.key === ' ') {
          event.preventDefault();
          openGame();
        }
      }}
      aria-label={`Open ${game.name}`}
    >
      <Card.Section className={classes.imageSection}>
        <Image
          src={game.background_image ?? undefined}
          alt={game.name}
          className={classes.image}
          fallbackSrc="https://placehold.co/400x200?text=No+Image"
        />
        <div className={classes.imageShade} />
        {playtimeLabel && (
          <Badge className={classes.playtimeBadge} variant="filled" size="sm">
            {playtimeLabel}
          </Badge>
        )}
      </Card.Section>

      <Stack gap={10} mt="sm" className={classes.body}>
        <Text fw={600} lineClamp={2} className={classes.title}>
          {game.name}
        </Text>

        <Text size="sm" c="dimmed" className={classes.meta}>
          {metaItems}
        </Text>

        <Group gap={8} align="center" className={classes.ratingRow}>
          <Rating value={(game.rating ?? 0) / 2} fractions={2} readOnly size="sm" color="yellow" />
          <Text size="sm" c="dimmed" className={classes.ratingValue}>
            {game.rating !== null ? game.rating.toFixed(1) : 'NR'}
          </Text>
        </Group>

        {showAdd && (
          <Group gap="xs" mt="auto">
            <SaveToLibraryButton
              game={game}
              libraryEntry={libraryEntry}
              className={`${classes.actionButton} ${inLibrary ? classes.removeButton : ''}`}
              fullWidth
            />
          </Group>
        )}
      </Stack>
    </Card>
  );
}
