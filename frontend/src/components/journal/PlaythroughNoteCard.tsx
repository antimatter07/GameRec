import {
  ActionIcon,
  Badge,
  Group,
  Image,
  Paper,
  Text,
  Tooltip,
} from '@mantine/core';
import {
  IconCheck,
  IconEdit,
  IconPinned,
  IconPinnedOff,
  IconRestore,
  IconTrash,
} from '@tabler/icons-react';
import type { PlaythroughNote } from '../../types/journal';
import classes from './Journal.module.css';

interface PlaythroughNoteCardProps {
  note: PlaythroughNote;
  onEdit: (note: PlaythroughNote) => void;
  onToggleStatus: (note: PlaythroughNote) => void;
  onTogglePinned: (note: PlaythroughNote) => void;
  onDelete: (note: PlaythroughNote) => void;
}

export function PlaythroughNoteCard({
  note,
  onEdit,
  onToggleStatus,
  onTogglePinned,
  onDelete,
}: PlaythroughNoteCardProps) {
  const isDone = note.status === 'done';

  return (
    <Paper withBorder radius="md" p="sm" className={classes.noteCard}>
      <div className={classes.noteCardMedia}>
        {note.game_cover_url ? (
          <Image src={note.game_cover_url} alt={note.game_title ?? 'Game'} w={44} h={58} fit="cover" />
        ) : (
          <Text size="lg">🎮</Text>
        )}
      </div>

      <div className={classes.noteCardBody}>
        <Group justify="space-between" align="flex-start" gap="xs">
          <div className={classes.noteTitleBlock}>
            <Text fw={600} size="sm" lineClamp={2}>{note.title}</Text>
            <Text size="xs" c="dimmed">
              {note.game_title ?? `Game #${note.game_id}`}
            </Text>
          </div>

          <Group gap={6} wrap="nowrap">
            <Tooltip label={isDone ? 'Mark open again' : 'Mark done'} withArrow>
              <ActionIcon variant="subtle" color={isDone ? 'yellow' : 'teal'} onClick={() => onToggleStatus(note)}>
                {isDone ? <IconRestore size={15} /> : <IconCheck size={15} />}
              </ActionIcon>
            </Tooltip>
            <Tooltip label={note.pinned ? 'Unpin' : 'Pin'} withArrow>
              <ActionIcon variant="subtle" color={note.pinned ? 'yellow' : 'gray'} onClick={() => onTogglePinned(note)}>
                {note.pinned ? <IconPinned size={15} /> : <IconPinnedOff size={15} />}
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Edit" withArrow>
              <ActionIcon variant="subtle" color="blue" onClick={() => onEdit(note)}>
                <IconEdit size={15} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Delete" withArrow>
              <ActionIcon variant="subtle" color="red" onClick={() => onDelete(note)}>
                <IconTrash size={15} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>

        <Group gap={6} mt={8}>
          <Badge size="xs" variant="light" color={isDone ? 'teal' : 'violet'}>
            {note.kind}
          </Badge>
          {note.remind_next_session && (
            <Badge size="xs" variant="light" color="orange">Next session</Badge>
          )}
          {note.status === 'archived' && (
            <Badge size="xs" variant="light" color="gray">Archived</Badge>
          )}
        </Group>

        {note.body && (
          <Text size="sm" c="dimmed" mt={8} lineClamp={3}>
            {note.body}
          </Text>
        )}
      </div>
    </Paper>
  );
}
