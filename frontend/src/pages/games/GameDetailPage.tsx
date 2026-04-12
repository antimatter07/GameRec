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
import { useDisclosure } from '@mantine/hooks';
import { IconClock } from '@tabler/icons-react';
import { useParams } from 'react-router';
import { LogSessionModal } from '../../components/journal/LogSessionModal';
import { JournalFeedItem } from '../../components/journal/JournalFeedItem';
import { useGame } from '../../hooks/useGames';
import { useSessionsList } from '../../hooks/useJournal';

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
  const { data: recentSessions } = useSessionsList(Number(gameId), 1, 3);
  const [logOpened, { open: openLog, close: closeLog }] = useDisclosure(false);

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
        <Group>
          <Button>Add to Library</Button>
          <Button variant="light" onClick={openLog}>Log Session</Button>
        </Group>
      </Group>

      <LogSessionModal
        gameId={Number(gameId)}
        opened={logOpened}
        onClose={closeLog}
      />

      {(game.hltb_main_hours != null ||
        game.hltb_main_extra_hours != null ||
        game.hltb_completionist_hours != null) && (
        <Stack gap="xs">
          <Group gap="xs">
            <IconClock size={16} />
            <Title order={4}>How Long to Beat</Title>
          </Group>
          <SimpleGrid cols={3} spacing="md">
            {game.hltb_main_hours != null && (
              <Stack gap={2} align="center">
                <Text size="xs" c="dimmed">Main Story</Text>
                <Text fw={600}>{game.hltb_main_hours.toFixed(1)}h</Text>
              </Stack>
            )}
            {game.hltb_main_extra_hours != null && (
              <Stack gap={2} align="center">
                <Text size="xs" c="dimmed">Main + Extras</Text>
                <Text fw={600}>{game.hltb_main_extra_hours.toFixed(1)}h</Text>
              </Stack>
            )}
            {game.hltb_completionist_hours != null && (
              <Stack gap={2} align="center">
                <Text size="xs" c="dimmed">Completionist</Text>
                <Text fw={600}>{game.hltb_completionist_hours.toFixed(1)}h</Text>
              </Stack>
            )}
          </SimpleGrid>
        </Stack>
      )}

      {game.description && (
        <Stack gap="xs">
          <Title order={4}>About</Title>
          {/* TODO: Sanitize HTML — see component-level TODO above */}
          <Text size="sm">{game.description.replace(/<[^>]+>/g, '')}</Text>
        </Stack>
      )}

      {recentSessions && recentSessions.total > 0 && (
        <Stack gap="xs">
          <Title order={4}>Your Recent Sessions</Title>
          {recentSessions.results.map((s) => (
            <JournalFeedItem key={s.id} session={s} />
          ))}
        </Stack>
      )}

      {/* TODO: Screenshots carousel */}
      {/* TODO: Platform list */}
      {/* TODO: Tags */}
    </Stack>
  );
}
