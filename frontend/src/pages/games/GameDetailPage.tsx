import {
  Badge,
  Button,
  Center,
  Group,
  Image,
  Loader,
  Rating,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useParams } from 'react-router';
import { useGame } from '../../hooks/useGames';

/**
 * Full game detail page.
 * TODO: Render game.screenshots in a Carousel (Mantine Carousel)
 * TODO: Add "Add to Library" button with status selector (Select + Button)
 * TODO: If game is in library, show current status + rating + edit option
 * TODO: Strip HTML tags from game.description (RAWG returns HTML)
 *       — use a lightweight lib like dompurify + dangerouslySetInnerHTML,
 *         or parse with a regex for the basic cases
 */
export default function GameDetailPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const { data: game, isLoading, isError } = useGame(Number(gameId));

  if (isLoading) return <Center h={400}><Loader /></Center>;
  if (isError || !game) return <Text c="red">Game not found.</Text>;

  return (
    <Stack gap="lg">
      <Image
        src={game.background_image ?? undefined}
        height={300}
        radius="md"
        alt={game.name}
        fallbackSrc="https://placehold.co/1200x300?text=No+Image"
      />

      <Group justify="space-between" align="flex-start">
        <Stack gap="xs">
          <Title>{game.name}</Title>

          <Group gap="xs">
            {game.genres.map((g) => (
              <Badge key={g.id}>{g.name}</Badge>
            ))}
          </Group>

          {game.rating !== null && (
            <Group gap="xs">
              <Rating value={game.rating / 2} fractions={2} readOnly />
              <Text size="sm" c="dimmed">
                {game.rating.toFixed(1)} ({game.ratings_count.toLocaleString()} ratings)
              </Text>
            </Group>
          )}

          {game.metacritic && (
            <Text size="sm">
              Metacritic: <strong>{game.metacritic}</strong>
            </Text>
          )}

          {game.released && (
            <Text size="sm" c="dimmed">
              Released: {new Date(game.released).toLocaleDateString()}
            </Text>
          )}
        </Stack>

        {/* TODO: Replace with AddToLibraryButton component */}
        <Button>Add to Library</Button>
      </Group>

      {game.description && (
        <Stack gap="xs">
          <Title order={4}>About</Title>
          {/* TODO: Sanitize HTML — see component-level TODO above */}
          <Text size="sm">{game.description.replace(/<[^>]+>/g, '')}</Text>
        </Stack>
      )}

      {/* TODO: Screenshots carousel */}
      {/* TODO: Platform list */}
      {/* TODO: Tags */}
    </Stack>
  );
}
