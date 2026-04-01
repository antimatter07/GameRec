import { Badge, Button, Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBookmark, IconBookmarkFilled } from '@tabler/icons-react';
import { Link } from 'react-router';
import { useAddToLibrary, useLibrary, useRemoveFromLibrary } from '../../hooks/useLibrary';
import type { GameListItem } from '../../types/game';

interface GameCardProps {
  game: GameListItem;
  /** Show an "Add to Library" button — omit on the library page */
  showAdd?: boolean;
}

export function GameCard({ game, showAdd = false }: GameCardProps) {
  const { data: library } = useLibrary();
  const addToLibrary = useAddToLibrary();
  const removeFromLibrary = useRemoveFromLibrary();

  const libraryEntry = library?.find((entry) => entry.game.id === game.id) ?? null;
  const inLibrary = libraryEntry !== null;

  const handleAdd = async (e: React.MouseEvent) => {
    e.preventDefault();
    try {
      await addToLibrary.mutateAsync({ game_id: game.id });
      notifications.show({ color: 'green', message: `${game.name} added to library` });
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      if (err?.response?.status === 409) {
        notifications.show({ color: 'yellow', message: 'Already in your library' });
      } else {
        notifications.show({ color: 'red', message: detail ?? 'Failed to add to library' });
      }
    }
  };

  const handleRemove = async (e: React.MouseEvent) => {
    e.preventDefault();
    if (!libraryEntry) return;
    try {
      await removeFromLibrary.mutateAsync(libraryEntry.id);
      notifications.show({ color: 'blue', message: `${game.name} removed from library` });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to remove from library' });
    }
  };

  return (
    <Card shadow="sm" padding="sm" radius="md" withBorder component={Link} to={`/games/${game.id}`}>
      <Card.Section>
        <Image
          src={game.background_image ?? undefined}
          height={200}
          alt={game.name}
          fallbackSrc="https://placehold.co/400x200?text=No+Image"
        />
      </Card.Section>

      <Stack gap="xs" mt="sm">
        <Text fw={600} lineClamp={2}>
          {game.name}
        </Text>

        <Group gap="xs">
          {game.genres.slice(0, 2).map((g) => (
            <Badge key={g.id} size="xs" variant="light">
              {g.name}
            </Badge>
          ))}
          {inLibrary && (
            <Badge size="xs" color="green" variant="filled">
              In Library
            </Badge>
          )}
        </Group>

        {game.rating !== null && (
          <Group gap="xs">
            <Rating value={game.rating / 2} fractions={2} readOnly size="xs" />
            <Text size="xs" c="dimmed">
              {game.rating.toFixed(1)}
            </Text>
          </Group>
        )}

        {showAdd && (
          <Group gap="xs" mt="xs">
            {!inLibrary ? (
              <Button
                size="xs"
                variant="filled"
                leftSection={<IconBookmark size={14} />}
                onClick={handleAdd}
                loading={addToLibrary.isPending}
                style={{ flex: 1 }}
              >
                Add to Library
              </Button>
            ) : (
              <Button
                size="xs"
                variant="light"
                color="red"
                leftSection={<IconBookmarkFilled size={14} />}
                onClick={handleRemove}
                loading={removeFromLibrary.isPending}
                style={{ flex: 1 }}
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
