import type { KeyboardEvent, MouseEvent } from 'react';
import { isAxiosError } from 'axios';
import { Button, Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBookmark, IconTrash } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { useAddToLibrary, useLibrary, useRemoveFromLibrary } from '../../hooks/useLibrary';
import type { GameListItem } from '../../types/game';
import classes from './GameCard.module.css';

interface GameCardProps {
  game: GameListItem;
  /** Show an "Add to Library" button — omit on the library page */
  showAdd?: boolean;
}

export function GameCard({ game, showAdd = false }: GameCardProps) {
  const { data: library } = useLibrary();
  const addToLibrary = useAddToLibrary();
  const removeFromLibrary = useRemoveFromLibrary();
  const navigate = useNavigate();

  const libraryEntry = library?.find((entry) => entry.game.id === game.id) ?? null;
  const inLibrary = libraryEntry !== null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;

  const openGame = () => navigate(`/games/${game.id}`);

  const handleAdd = async (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    try {
      await addToLibrary.mutateAsync({ game_id: game.id });
      notifications.show({ color: 'green', message: `${game.name} added to library` });
    } catch (err: unknown) {
      if (isAxiosError(err)) {
        const detail = err.response?.data?.detail as string | undefined;
        if (err.response?.status === 409) {
          notifications.show({ color: 'yellow', message: 'Already in your library' });
        } else {
          notifications.show({ color: 'red', message: detail ?? 'Failed to add to library' });
        }
      } else {
        notifications.show({ color: 'red', message: 'Failed to add to library' });
      }
    }
  };

  const handleRemove = async (e: MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!libraryEntry) return;

    try {
      await removeFromLibrary.mutateAsync(libraryEntry.id);
      notifications.show({ color: 'red', message: `${game.name} removed from library` });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to remove from library' });
    }
  };

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
            {!inLibrary ? (
              <Button
                className={classes.actionButton}
                size="md"
                variant="filled"
                color="violet"
                leftSection={<IconBookmark size={15} />}
                onClick={handleAdd}
                loading={addToLibrary.isPending}
                fullWidth
              >
                Add to Library
              </Button>
            ) : (
              <Button
                className={`${classes.actionButton} ${classes.removeButton}`}
                size="md"
                variant="filled"
                leftSection={<IconTrash size={15} />}
                onClick={handleRemove}
                loading={removeFromLibrary.isPending}
                fullWidth
              >
                Remove
              </Button>
            )}
          </Group>
        )}
      </Stack>
    </Card>
  );
}
