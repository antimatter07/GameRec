import { useState } from 'react';
import {
  Autocomplete,
  Button,
  Group,
  Modal,
  Select,
  Stack,
  Switch,
  Textarea,
  TextInput,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { IconBookmark, IconChecklist, IconDeviceGamepad2, IconNotes, IconSearch } from '@tabler/icons-react';
import {
  useCreatePlaythroughNote,
  useUpdatePlaythroughNote,
} from '../../hooks/useJournal';
import { useLibrary } from '../../hooks/useLibrary';
import {
  PlaythroughNoteKind,
  PlaythroughNoteStatus,
} from '../../types/journal';
import type {
  PlaythroughNote,
  PlaythroughNoteCreate,
  PlaythroughNoteKind as PlaythroughNoteKindValue,
  PlaythroughNoteStatus as PlaythroughNoteStatusValue,
  PlaythroughNoteUpdate,
} from '../../types/journal';
import classes from './Journal.module.css';

interface PlaythroughNoteModalProps {
  opened: boolean;
  onClose: () => void;
  gameId?: number;
  gameTitle?: string;
  libraryEntryId?: number | null;
  note?: PlaythroughNote | null;
}

const kindOptions = [
  { value: PlaythroughNoteKind.GOAL, label: 'Goal' },
  { value: PlaythroughNoteKind.QUEST, label: 'Quest' },
  { value: PlaythroughNoteKind.NOTE, label: 'Note' },
  { value: PlaythroughNoteKind.RECIPE, label: 'Recipe' },
  { value: PlaythroughNoteKind.LOCATION, label: 'Location' },
  { value: PlaythroughNoteKind.BUILD, label: 'Build' },
];

const statusOptions = [
  { value: PlaythroughNoteStatus.OPEN, label: 'Open' },
  { value: PlaythroughNoteStatus.DONE, label: 'Done' },
  { value: PlaythroughNoteStatus.ARCHIVED, label: 'Archived' },
];

export function PlaythroughNoteModal({
  opened,
  onClose,
  gameId = 0,
  gameTitle = '',
  libraryEntryId = null,
  note = null,
}: PlaythroughNoteModalProps) {
  const pickerMode = gameId === 0;
  const isEditing = Boolean(note);

  const [gameSearch, setGameSearch] = useState(note?.game_title ?? gameTitle);
  const [selectedGameId, setSelectedGameId] = useState<number | null>(note?.game_id ?? (gameId > 0 ? gameId : null));
  const [selectedLibraryEntryId, setSelectedLibraryEntryId] = useState<number | null>(note?.library_entry_id ?? libraryEntryId);
  const [kind, setKind] = useState<PlaythroughNoteKindValue>(note?.kind ?? PlaythroughNoteKind.NOTE);
  const [title, setTitle] = useState(note?.title ?? '');
  const [body, setBody] = useState(note?.body ?? '');
  const [statusValue, setStatusValue] = useState<PlaythroughNoteStatusValue>(note?.status ?? PlaythroughNoteStatus.OPEN);
  const [pinned, setPinned] = useState(note?.pinned ?? false);
  const [remindNextSession, setRemindNextSession] = useState(note?.remind_next_session ?? false);

  const createNote = useCreatePlaythroughNote();
  const updateNote = useUpdatePlaythroughNote();
  const { data: libraryData } = useLibrary();

  const effectiveGameId = pickerMode ? (selectedGameId ?? 0) : gameId;
  const effectiveLibraryEntryId = pickerMode ? selectedLibraryEntryId : libraryEntryId;

  const libraryOptions = (libraryData ?? [])
    .filter((entry) => entry.game.name.toLowerCase().includes(gameSearch.toLowerCase()))
    .map((entry) => entry.game.name);

  const handleClose = () => {
    if (createNote.isPending || updateNote.isPending) return;
    onClose();
  };

  const handleSubmit = () => {
    if (!title.trim()) {
      notifications.show({ color: 'yellow', message: 'Add a title so future-you knows what this note is.' });
      return;
    }

    if (effectiveGameId === 0) {
      notifications.show({ color: 'yellow', message: 'Pick a game for this scratchpad note first.' });
      return;
    }

    if (isEditing && note) {
      const payload: PlaythroughNoteUpdate = {
        kind,
        title: title.trim(),
        body: body.trim() || null,
        status: statusValue,
        pinned,
        remind_next_session: remindNextSession,
      };
      updateNote.mutate(
        { noteId: note.id, data: payload },
        {
          onSuccess: () => {
            notifications.show({ color: 'green', message: 'Scratchpad note updated.' });
            onClose();
          },
          onError: () => {
            notifications.show({ color: 'red', message: 'Could not update that note.' });
          },
        },
      );
      return;
    }

    const payload: PlaythroughNoteCreate = {
      game_id: effectiveGameId,
      library_entry_id: effectiveLibraryEntryId,
      kind,
      title: title.trim(),
      body: body.trim() || null,
      status: statusValue,
      pinned,
      remind_next_session: remindNextSession,
    };
    createNote.mutate(payload, {
      onSuccess: () => {
        notifications.show({ color: 'green', message: 'Scratchpad note saved.' });
        onClose();
      },
      onError: () => {
        notifications.show({ color: 'red', message: 'Could not save that note.' });
      },
    });
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={isEditing ? 'Edit scratchpad note' : 'New scratchpad note'}
      size="lg"
      centered
      classNames={{
        content: classes.modalContent,
        header: classes.modalHeader,
        title: classes.modalTitle,
        body: classes.modalBody,
      }}
    >
      <Stack gap="md" className={classes.journalForm}>
        {pickerMode && (
          <Autocomplete
            label="Game"
            placeholder="Search your library..."
            leftSection={<IconSearch size={16} />}
            value={gameSearch}
            onChange={(value) => {
              setGameSearch(value);
              if (!value) {
                setSelectedGameId(null);
                setSelectedLibraryEntryId(null);
              }
            }}
            onOptionSubmit={(value) => {
              const entry = libraryData?.find((candidate) => candidate.game.name === value);
              if (!entry) return;
              setSelectedGameId(entry.game.id);
              setSelectedLibraryEntryId(entry.id);
              setGameSearch(entry.game.name);
            }}
            data={libraryOptions}
          />
        )}

        <Group grow>
          <Select
            label="Type"
            leftSection={<IconDeviceGamepad2 size={16} />}
            data={kindOptions}
            value={kind}
            onChange={(value) => setKind((value as typeof kind) ?? PlaythroughNoteKind.NOTE)}
            allowDeselect={false}
          />
          <Select
            label="Status"
            leftSection={<IconChecklist size={16} />}
            data={statusOptions}
            value={statusValue}
            onChange={(value) => setStatusValue((value as typeof statusValue) ?? PlaythroughNoteStatus.OPEN)}
            allowDeselect={false}
          />
        </Group>

        <TextInput
          label="Title"
          placeholder="Find Blaidd before heading north"
          leftSection={<IconBookmark size={16} />}
          value={title}
          onChange={(event) => setTitle(event.currentTarget.value)}
        />

        <Textarea
          label="Details"
          placeholder="Anything you want to remember later..."
          leftSection={<IconNotes size={16} />}
          value={body}
          onChange={(event) => setBody(event.currentTarget.value)}
          minRows={3}
          autosize
          maxRows={8}
        />

        <Group grow>
          <Switch
            checked={pinned}
            onChange={(event) => setPinned(event.currentTarget.checked)}
            label="Pin this note"
          />
          <Switch
            checked={remindNextSession}
            onChange={(event) => setRemindNextSession(event.currentTarget.checked)}
            label="Show for next session"
          />
        </Group>

        <Group justify="flex-end">
          <Button variant="subtle" className={classes.secondaryAction} onClick={handleClose}>Cancel</Button>
          <Button className={classes.primaryAction} onClick={handleSubmit} loading={createNote.isPending || updateNote.isPending}>
            {isEditing ? 'Save changes' : 'Save note'}
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
