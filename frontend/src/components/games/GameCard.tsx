import type { KeyboardEvent } from 'react';
import { Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
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
      </Card.Section>

      <Stack gap={10} mt="sm" className={classes.body}>
        <Text fw={600} lineClamp={2} className={classes.title}>
          {game.name}
        </Text>

        <Text size="sm" c="dimmed" className={classes.meta}>
          {releaseYear ?? 'TBA'}
        </Text>

        <Group gap={8} align="center" className={classes.ratingRow}>
          <Rating value={(game.rating ?? 0) / 2} fractions={2} readOnly size="sm" color="orange" />
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
