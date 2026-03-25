import { Badge, Card, Group, Image, Rating, Stack, Text } from '@mantine/core';
import { Link } from 'react-router';
import type { GameListItem } from '../../types/game';

interface GameCardProps {
  game: GameListItem;
  /** Show an "Add to Library" button — omit on the library page */
  showAdd?: boolean;
}

/**
 * Reusable game card for catalog and recommendation lists.
 * TODO: Add "Add to Library" button that calls libraryApi.add()
 * TODO: Show a badge if the game is already in the user's library
 * TODO: Add skeleton loading state (Mantine Skeleton)
 */
export function GameCard({ game, showAdd = false }: GameCardProps) {
  return (
    <Card shadow="sm" padding="sm" radius="md" withBorder component={Link} to={`/games/${game.id}`}>
      <Card.Section>
        <Image
          src={game.background_image ?? undefined}
          height={500}
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
        </Group>

        {game.rating !== null && (
          <Group gap="xs">
            <Rating value={game.rating / 2} fractions={2} readOnly size="xs" />
            <Text size="xs" c="dimmed">
              {game.rating.toFixed(1)}
            </Text>
          </Group>
        )}

        {/* TODO: Render showAdd button here */}
      </Stack>
    </Card>
  );
}
