import { useState } from 'react';
import {
  Button,
  Group,
  Modal,
  NumberInput,
  Stack,
  Switch,
  Text,
  Textarea,
  TextInput,
} from '@mantine/core';
import { DateTimePicker } from '@mantine/dates';
import { notifications } from '@mantine/notifications';
import { useCreateSession } from '../../hooks/useJournal';
import { useUpdateLibraryEntry } from '../../hooks/useLibrary';
import type { LibraryStatus } from '../../types/library';

interface Props {
  gameId:          number;
  libraryEntryId?: number;
  libraryStatus?:  LibraryStatus;
  opened:          boolean;
  onClose:         () => void;
}

export function LogSessionModal({
  gameId,
  libraryEntryId,
  libraryStatus,
  opened,
  onClose,
}: Props) {
  const createSession       = useCreateSession();
  const updateLibraryEntry  = useUpdateLibraryEntry();

  const [startedAt,       setStartedAt]       = useState<Date | null>(new Date());
  const [durationMinutes, setDurationMinutes] = useState<number | string>('');
  const [notes,           setNotes]           = useState('');
  const [isMilestone,     setIsMilestone]     = useState(false);
  const [milestoneLabel,  setMilestoneLabel]  = useState('');
  const [showPromotion,   setShowPromotion]   = useState(false);

  const resetForm = () => {
    setStartedAt(new Date());
    setDurationMinutes('');
    setNotes('');
    setIsMilestone(false);
    setMilestoneLabel('');
    setShowPromotion(false);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSave = async () => {
    if (!startedAt) return;

    try {
      await createSession.mutateAsync({
        game_id:          gameId,
        started_at:       startedAt.toISOString(),
        duration_minutes: durationMinutes !== '' ? Number(durationMinutes) : undefined,
        notes:            notes.trim() || undefined,
        is_milestone:     isMilestone,
        milestone_label:  isMilestone && milestoneLabel.trim() ? milestoneLabel.trim() : undefined,
        library_entry_id: libraryEntryId,
      });

      notifications.show({ color: 'green', message: 'Session logged!' });

      if (libraryStatus === 'backlog') {
        setShowPromotion(true);
      } else {
        handleClose();
      }
    } catch {
      notifications.show({ color: 'red', message: 'Failed to log session.' });
    }
  };

  const handlePromoteToPlaying = async () => {
    if (!libraryEntryId) {
      handleClose();
      return;
    }
    try {
      await updateLibraryEntry.mutateAsync({ id: libraryEntryId, updates: { status: 'playing' } });
      notifications.show({ color: 'teal', message: 'Moved to Playing!' });
    } catch {
      // Non-fatal — session was already saved
    }
    handleClose();
  };

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={showPromotion ? 'Move to Playing?' : 'Log a Session'}
      centered
    >
      {showPromotion ? (
        <Stack>
          <Text size="sm">
            This game is in your backlog. Do you want to move it to <strong>Playing</strong>?
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={handleClose}>
              No, keep in Backlog
            </Button>
            <Button color="teal" onClick={handlePromoteToPlaying} loading={updateLibraryEntry.isPending}>
              Yes, move to Playing
            </Button>
          </Group>
        </Stack>
      ) : (
        <Stack>
          <DateTimePicker
            label="Started at"
            value={startedAt}
            onChange={setStartedAt}
            required
          />

          <NumberInput
            label="Duration (minutes)"
            placeholder="e.g. 90"
            min={1}
            value={durationMinutes}
            onChange={setDurationMinutes}
          />

          <Textarea
            label="Notes"
            placeholder="How did it go?"
            autosize
            minRows={2}
            maxRows={5}
            value={notes}
            onChange={(e) => setNotes(e.currentTarget.value)}
          />

          <Switch
            label="Milestone"
            description="Check this if you hit a significant moment (e.g. beat the final boss)"
            checked={isMilestone}
            onChange={(e) => setIsMilestone(e.currentTarget.checked)}
          />

          {isMilestone && (
            <TextInput
              label="Milestone label"
              placeholder="e.g. Completed the game"
              value={milestoneLabel}
              onChange={(e) => setMilestoneLabel(e.currentTarget.value)}
            />
          )}

          <Group justify="flex-end" mt="xs">
            <Button variant="default" onClick={handleClose}>
              Cancel
            </Button>
            <Button
              onClick={handleSave}
              loading={createSession.isPending}
              disabled={!startedAt}
            >
              Save Session
            </Button>
          </Group>
        </Stack>
      )}
    </Modal>
  );
}
