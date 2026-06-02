import { Button, Group, Paper, SimpleGrid, Stack, Text } from '@mantine/core';
import { IconNote, IconNotes } from '@tabler/icons-react';
import type { PlaythroughNote } from '../../types/journal';
import { PlaythroughNoteCard } from './PlaythroughNoteCard';
import classes from './Journal.module.css';

interface ScratchpadPanelProps {
  notes: PlaythroughNote[];
  title?: string;
  emptyMessage: string;
  actionLabel?: string;
  onCreate?: () => void;
  onEdit: (note: PlaythroughNote) => void;
  onToggleStatus: (note: PlaythroughNote) => void;
  onTogglePinned: (note: PlaythroughNote) => void;
  onDelete: (note: PlaythroughNote) => void;
}

function byRecentUpdate(a: PlaythroughNote, b: PlaythroughNote) {
  return new Date(b.updated_at).getTime() - new Date(a.updated_at).getTime();
}

export function ScratchpadPanel({
  notes,
  title = 'Scratchpad',
  emptyMessage,
  actionLabel = 'New note',
  onCreate,
  onEdit,
  onToggleStatus,
  onTogglePinned,
  onDelete,
}: ScratchpadPanelProps) {
  const sorted = [...notes].sort(byRecentUpdate);
  const nextSessionNotes = sorted.filter((note) => note.status === 'open' && note.remind_next_session);
  const openNotes = sorted.filter((note) => note.status === 'open' && !note.remind_next_session);
  const completedNotes = sorted.filter((note) => note.status === 'done').slice(0, 6);
  const archivedNotes = sorted.filter((note) => note.status === 'archived').slice(0, 6);
  const hasVisibleSections = nextSessionNotes.length > 0 || openNotes.length > 0 || completedNotes.length > 0 || archivedNotes.length > 0;

  return (
    <Stack gap="md">
      <Group justify="space-between">
        <div>
          <Text size="sm" fw={600}>{title}</Text>
          <Text size="xs" c="dimmed">
            Keep quest reminders, recipes, clues, and tiny future-you nudges in one place.
          </Text>
        </div>
        {onCreate && (
          <Button className={classes.primaryAction} leftSection={<IconNote size={16} />} onClick={onCreate}>
            {actionLabel}
          </Button>
        )}
      </Group>

      {notes.length === 0 || !hasVisibleSections ? (
        <Paper withBorder radius="md" p="lg" className={classes.scratchpadEmpty}>
          <Stack align="center" gap="xs">
            <div className={classes.stateIcon}>
              <IconNotes size={18} stroke={1.8} />
            </div>
            <Text size="sm" c="dimmed" ta="center">{emptyMessage}</Text>
          </Stack>
        </Paper>
      ) : (
        <>
          {nextSessionNotes.length > 0 && (
            <div>
              <Text size="sm" fw={600} mb="xs">Next session</Text>
              <Stack gap="xs">
                {nextSessionNotes.map((note) => (
                  <PlaythroughNoteCard
                    key={note.id}
                    note={note}
                    onEdit={onEdit}
                    onToggleStatus={onToggleStatus}
                    onTogglePinned={onTogglePinned}
                    onDelete={onDelete}
                  />
                ))}
              </Stack>
            </div>
          )}

          {openNotes.length > 0 && (
            <div>
              <Text size="sm" fw={600} mb="xs">Open notes</Text>
              <Stack gap="xs">
                {openNotes.map((note) => (
                  <PlaythroughNoteCard
                    key={note.id}
                    note={note}
                    onEdit={onEdit}
                    onToggleStatus={onToggleStatus}
                    onTogglePinned={onTogglePinned}
                    onDelete={onDelete}
                  />
                ))}
              </Stack>
            </div>
          )}

          {completedNotes.length > 0 && (
            <div>
              <Text size="sm" fw={600} mb="xs">Done recently</Text>
              <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="xs">
                {completedNotes.map((note) => (
                  <PlaythroughNoteCard
                    key={note.id}
                    note={note}
                    onEdit={onEdit}
                    onToggleStatus={onToggleStatus}
                    onTogglePinned={onTogglePinned}
                    onDelete={onDelete}
                  />
                ))}
              </SimpleGrid>
            </div>
          )}

          {archivedNotes.length > 0 && (
            <div>
              <Text size="sm" fw={600} mb="xs">Archived</Text>
              <SimpleGrid cols={{ base: 1, lg: 2 }} spacing="xs">
                {archivedNotes.map((note) => (
                  <PlaythroughNoteCard
                    key={note.id}
                    note={note}
                    onEdit={onEdit}
                    onToggleStatus={onToggleStatus}
                    onTogglePinned={onTogglePinned}
                    onDelete={onDelete}
                  />
                ))}
              </SimpleGrid>
            </div>
          )}
        </>
      )}
    </Stack>
  );
}
