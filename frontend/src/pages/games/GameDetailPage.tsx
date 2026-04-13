import {
  Badge,
  Button,
  Center,
  Divider,
  Group,
  Image,
  Loader,
  Paper,
  Rating,
  SimpleGrid,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconClock } from '@tabler/icons-react';
import { useParams } from 'react-router';
import { LogSessionModal }         from '../../components/journal/LogSessionModal';
import { JournalFeedItem }         from '../../components/journal/JournalFeedItem';
import { MultiAxisRatingWidget }   from '../../components/journal/MultiAxisRatingWidget';
import { useGame }                 from '../../hooks/useGames';
import { useJournalSessions }      from '../../hooks/useJournal';
import { useLibrary }              from '../../hooks/useLibrary';

export default function GameDetailPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const id = Number(gameId);

  const { data: game,           isLoading, isError } = useGame(id);
  const { data: recentSessions }                     = useJournalSessions({ game_id: id, per_page: 3 });
  const { data: library }                            = useLibrary();
  const [logOpened, { open: openLog, close: closeLog }] = useDisclosure(false);

  if (isLoading) return <Center h={400}><Loader /></Center>;
  if (isError || !game) return <Text c="red">Game not found.</Text>;

  const libraryEntry = library?.find((e) => e.game.id === id) ?? null;

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
          <Button variant="light" color="violet" onClick={openLog}>
            Log Session
          </Button>
        </Group>
      </Group>

      <LogSessionModal
        gameId={id}
        gameTitle={game.name}
        libraryEntryId={libraryEntry?.id}
        opened={logOpened}
        onClose={closeLog}
      />

      {/* ── Multi-axis ratings ────────────────────────────────────────────── */}
      {libraryEntry && (
        <Paper p="md" radius="md" withBorder>
          <Text size="sm" fw={600} mb="sm">Your ratings</Text>
          <MultiAxisRatingWidget gameId={id} />
        </Paper>
      )}

      {/* ── How Long to Beat ─────────────────────────────────────────────── */}
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

      {/* ── About ─────────────────────────────────────────────────────────── */}
      {game.description && (
        <Stack gap="xs">
          <Title order={4}>About</Title>
          {/* TODO: Sanitize HTML — RAWG returns HTML */}
          <Text size="sm">{game.description.replace(/<[^>]+>/g, '')}</Text>
        </Stack>
      )}

      {/* ── Recent sessions ───────────────────────────────────────────────── */}
      {recentSessions && recentSessions.items.length > 0 && (
        <Stack gap="xs">
          <Divider />
          <Title order={4}>Your Recent Sessions</Title>
          {recentSessions.items.map((s) => (
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
