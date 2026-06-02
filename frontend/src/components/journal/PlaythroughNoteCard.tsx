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
  IconDeviceGamepad2,
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
          <IconDeviceGamepad2 size={18} />
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
              <ActionIcon
                className={classes.noteAction}
                variant="subtle"
                color={isDone ? 'yellow' : 'teal'}
                aria-label={isDone ? 'Mark note open again' : 'Mark note done'}
                onClick={() => onToggleStatus(note)}
              >
                {isDone ? <IconRestore size={15} /> : <IconCheck size={15} />}
              </ActionIcon>
            </Tooltip>
            <Tooltip label={note.pinned ? 'Unpin' : 'Pin'} withArrow>
              <ActionIcon
                className={classes.noteAction}
                variant="subtle"
                color={note.pinned ? 'yellow' : 'gray'}
                aria-label={note.pinned ? 'Unpin note' : 'Pin note'}
                onClick={() => onTogglePinned(note)}
              >
                {note.pinned ? <IconPinnedOff size={15} /> : <IconPinned size={15} />}
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Edit" withArrow>
              <ActionIcon className={classes.noteAction} variant="subtle" color="blue" aria-label="Edit note" onClick={() => onEdit(note)}>
                <IconEdit size={15} />
              </ActionIcon>
            </Tooltip>
            <Tooltip label="Delete" withArrow>
              <ActionIcon className={classes.noteAction} variant="subtle" color="red" aria-label="Delete note" onClick={() => onDelete(note)}>
                <IconTrash size={15} />
              </ActionIcon>
            </Tooltip>
          </Group>
        </Group>

        <Group gap={6} mt={8}>
          <Badge size="xs" variant="light" color={isDone ? 'teal' : 'orange'}>
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
