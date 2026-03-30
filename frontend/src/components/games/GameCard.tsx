import { Badge, Button, Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBookmark, IconBookmarkFilled } from '@tabler/icons-react';
import { Link } from 'react-router';
import { useAddToLibrary, useLibrary } from '../../hooks/useLibrary';
import type { GameListItem } from '../../types/game';

interface GameCardProps {
  game: GameListItem;
  /** Show an "Add to Library" button — omit on the library page */
  showAdd?: boolean;
}

export function GameCard({ game, showAdd = false }: GameCardProps) {
  const { data: library } = useLibrary();
  const addToLibrary = useAddToLibrary();

  const inLibrary = library?.some((entry) => entry.game.id === game.id) ?? false;

  const handleAdd = async (e: React.MouseEvent) => {
    e.preventDefault(); // prevent navigating to game detail
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
          <Button
            size="xs"
            variant={inLibrary ? 'light' : 'filled'}
            color={inLibrary ? 'green' : 'blue'}
            leftSection={inLibrary ? <IconBookmarkFilled size={14} /> : <IconBookmark size={14} />}
            onClick={handleAdd}
            disabled={inLibrary || addToLibrary.isPending}
            loading={addToLibrary.isPending}
            mt="xs"
          >
            {inLibrary ? 'In Library' : 'Add to Library'}
          </Button>
        )}
      </Stack>
    </Card>
  );
}
