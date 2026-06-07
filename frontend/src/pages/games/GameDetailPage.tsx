import { useState } from 'react';
import {
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  Rating,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { IconClock, IconDeviceGamepad2, IconNotes, IconPlayerPlay } from '@tabler/icons-react';
import { useNavigate, useParams } from 'react-router';
import { LogSessionModal }         from '../../components/journal/LogSessionModal';
import { JournalFeedItem }         from '../../components/journal/JournalFeedItem';
import { MultiAxisRatingWidget }   from '../../components/journal/MultiAxisRatingWidget';
import { PlaythroughNoteModal }    from '../../components/journal/PlaythroughNoteModal';
import { ScratchpadPanel }         from '../../components/journal/ScratchpadPanel';
import { SaveToLibraryButton }     from '../../components/games/SaveToLibraryButton';
import { useGame }                 from '../../hooks/useGames';
import {
  useDeletePlaythroughNote,
  useJournalSessions,
  usePlaythroughNotes,
  useUpdatePlaythroughNote,
} from '../../hooks/useJournal';
import { useLibrary }              from '../../hooks/useLibrary';
import type { PlaythroughNote }    from '../../types/journal';
import classes from './GameDetailPage.module.css';

export default function GameDetailPage() {
  const { gameId } = useParams<{ gameId: string }>();
  const id = Number(gameId);

  const { data: game,           isLoading, isError } = useGame(id);
  const { data: recentSessions }                     = useJournalSessions({ game_id: id, per_page: 3 });
  const { data: notesData }                          = usePlaythroughNotes({ game_id: id, per_page: 100 });
  const { data: library }                            = useLibrary();
  const navigate = useNavigate();
  const [logOpened, { open: openLog, close: closeLog }] = useDisclosure(false);
  const [noteOpened, { open: openNote, close: closeNote }] = useDisclosure(false);
  const [editingNote, setEditingNote] = useState<PlaythroughNote | null>(null);
  const updateNote = useUpdatePlaythroughNote();
  const deleteNote = useDeletePlaythroughNote();

  if (isLoading) {
    return (
      <Center py={80}>
        <Stack align="center" gap="sm">
          <Loader color="ember" size="md" />
          <Text size="sm" c="dimmed">Loading game details…</Text>
        </Stack>
      </Center>
    );
  }

  if (isError || !game) {
    return (
      <Center py={80}>
        <Paper p="md" radius="xs" withBorder className={classes.emptyState}>
          <Stack align="center" gap="sm">
            <Text size="sm" fw={600}>Game not found</Text>
            <Text size="xs" c="dimmed">This title may have been removed or is not available yet.</Text>
            <Button size="xs" variant="light" onClick={() => navigate('/games')}>
              Back to catalog
            </Button>
          </Stack>
        </Paper>
      </Center>
    );
  }

  const libraryEntry = library?.find((e) => e.game.id === id) ?? null;
  const releaseYear = game.released ? new Date(game.released).getFullYear() : null;
  const cleanDescription = game.description?.replace(/<[^>]+>/g, '') ?? '';

  return (
    <Stack gap="lg" className={classes.page}>
      <section className={classes.hero}>
        {game.background_image ? (
          <div className={classes.heroImage}>
            <img src={game.background_image} alt="" />
          </div>
        ) : (
          <div className={classes.heroFallback}>
            <IconDeviceGamepad2 size={44} stroke={1.6} />
          </div>
        )}
        <div className={classes.heroScrim} />
        <div className={classes.heroContent}>
          <Title className={classes.title}>{game.name}</Title>

          <Group gap="xs">
            {game.genres.slice(0, 5).map((g) => (
              <Badge key={g.id} color="ember" variant="light">{g.name}</Badge>
            ))}
          </Group>

          <div className={classes.metaLine}>
            {releaseYear && <span>{releaseYear}</span>}
            {game.metacritic && <span>Metacritic {game.metacritic}</span>}
            {game.rating !== null && <span>RAWG {game.rating.toFixed(1)} from {game.ratings_count.toLocaleString()} ratings</span>}
          </div>

          {game.rating !== null && (
            <Group gap="xs" mt="sm">
              <Rating value={game.rating / 2} fractions={2} readOnly color="yellow" />
              <Text size="xs" c="gray.3">{game.rating.toFixed(1)} / 5</Text>
            </Group>
          )}

        <Group className={classes.actions}>
          <SaveToLibraryButton game={game} libraryEntry={libraryEntry} />
          <Button
            variant="light"
            color="ember"
            leftSection={<IconNotes size={16} />}
            onClick={() => {
              setEditingNote(null);
              openNote();
            }}
          >
            New note
          </Button>
          <Button variant="light" color="ember" leftSection={<IconPlayerPlay size={16} />} onClick={openLog}>
            Log session
          </Button>
        </Group>
        </div>
      </section>

      <LogSessionModal
        gameId={id}
        gameTitle={game.name}
        libraryEntryId={libraryEntry?.id}
        opened={logOpened}
        onClose={closeLog}
      />
      {noteOpened && (
        <PlaythroughNoteModal
          gameId={id}
          gameTitle={game.name}
          libraryEntryId={libraryEntry?.id}
          opened={noteOpened}
          onClose={() => {
            closeNote();
            setEditingNote(null);
          }}
          note={editingNote}
        />
      )}

      {/* ── Multi-axis ratings ────────────────────────────────────────────── */}
      <div className={classes.contentGrid}>
        <Stack gap="xs">
          {libraryEntry && (
            <Paper p="md" radius="xs" withBorder>
              <Text size="sm" fw={600} mb="sm">Your ratings</Text>
              <MultiAxisRatingWidget gameId={id} />
            </Paper>
          )}

          <Paper p="md" radius="xs" withBorder>
            <ScratchpadPanel
              title={`${game.name} scratchpad`}
              actionLabel="New note"
              notes={notesData?.items ?? []}
              emptyMessage="No notes for this game yet. Save a quest reminder, route, recipe, or clue."
              onCreate={() => {
                setEditingNote(null);
                openNote();
              }}
              onEdit={(note) => {
                setEditingNote(note);
                openNote();
              }}
              onToggleStatus={(note) => {
                updateNote.mutate({
                  noteId: note.id,
                  data: { status: note.status === 'done' ? 'open' : 'done' },
                });
              }}
              onTogglePinned={(note) => {
                updateNote.mutate({
                  noteId: note.id,
                  data: { pinned: !note.pinned },
                });
              }}
              onDelete={(note) => deleteNote.mutate(note.id)}
            />
          </Paper>

          {cleanDescription && (
            <Paper p="md" radius="xs" withBorder>
              <Text size="sm" fw={600} mb="xs">About</Text>
              <Text size="sm" className={classes.description}>{cleanDescription}</Text>
            </Paper>
          )}
        </Stack>

        <Stack gap="sm">
          {(game.hltb_main_hours != null ||
            game.hltb_main_extra_hours != null ||
            game.hltb_completionist_hours != null) && (
            <Paper p="md" radius="xs" withBorder>
              <Group gap="xs" mb="sm" className={classes.panelHeader}>
                <IconClock size={16} />
                <Text size="sm" fw={600}>How Long to Beat</Text>
              </Group>
              <div className={classes.timeGrid}>
                {game.hltb_main_hours != null && (
                  <div className={classes.timeCard}>
                    <Text size="xs" c="dimmed">Main story</Text>
                    <div className={classes.timeValue}>{game.hltb_main_hours.toFixed(1)}h</div>
                  </div>
                )}
                {game.hltb_main_extra_hours != null && (
                  <div className={classes.timeCard}>
                    <Text size="xs" c="dimmed">Main + Extras</Text>
                    <div className={classes.timeValue}>{game.hltb_main_extra_hours.toFixed(1)}h</div>
                  </div>
                )}
                {game.hltb_completionist_hours != null && (
                  <div className={classes.timeCard}>
                    <Text size="xs" c="dimmed">Completionist</Text>
                    <div className={classes.timeValue}>{game.hltb_completionist_hours.toFixed(1)}h</div>
                  </div>
                )}
              </div>
            </Paper>
          )}

          {recentSessions && recentSessions.items.length > 0 && (
            <Paper p="md" radius="xs" withBorder>
              <Text size="sm" fw={600} mb="sm">Recent sessions</Text>
              <Stack gap="xs">
                {recentSessions.items.map((s) => (
                  <JournalFeedItem key={s.id} session={s} />
                ))}
              </Stack>
            </Paper>
          )}
        </Stack>
      </div>

      {/* TODO: Screenshots carousel */}
      {/* TODO: Platform list */}
      {/* TODO: Tags */}
    </Stack>
  );
}
