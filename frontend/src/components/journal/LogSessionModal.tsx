import { useState } from 'react';
import {
  Modal,
  TextInput,
  NumberInput,
  Textarea,
  Switch,
  Chip,
  Group,
  Button,
  Stack,
  Text,
  SimpleGrid,
  Autocomplete,
} from '@mantine/core';
import {
  IconClock,
  IconNote,
  IconTrophy,
  IconMoodSmile,
  IconMoodSad,
  IconMoodConfuzed,
  IconFlame,
  IconLeaf,
  IconZzz,
  IconGhost,
  IconMoodEmpty,
  IconSearch,
  IconBookmark,
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useCreateSession } from '../../hooks/useJournal';
import { useLibrary } from '../../hooks/useLibrary';
import { EmotionType, EMOTION_CONFIG } from '../../types/journal';
import type { SessionLogCreate } from '../../types/journal';
import classes from './Journal.module.css';

const EMOTION_ICONS: Record<string, React.ElementType> = {
  IconMoodConfuzed,
  IconMoodSmile,
  IconMoodSad,
  IconFlame,
  IconLeaf,
  IconZzz,
  IconTrophy,
  IconGhost,
  IconMoodEmpty,
};

interface LogSessionModalProps {
  opened:          boolean;
  onClose:         () => void;
  /** Pass the game's id. Use 0 when no game is pre-selected (journal page). */
  gameId:          number;
  /** Display name for the pre-selected game. Ignored when gameId === 0. */
  gameTitle?:      string;
  libraryEntryId?: number | null;
}

export function LogSessionModal({
  opened,
  onClose,
  gameId,
  gameTitle = '',
  libraryEntryId,
}: LogSessionModalProps) {
  const pickerMode = gameId === 0;

  // Game picker state (only used when pickerMode is true)
  const [gameSearch,            setGameSearch]            = useState('');
  const [selectedGameId,        setSelectedGameId]        = useState<number | null>(null);
  const [selectedGameTitle,     setSelectedGameTitle]     = useState('');
  const [selectedLibraryEntryId, setSelectedLibraryEntryId] = useState<number | null>(null);

  // Session form state
  const [durationMinutes, setDurationMinutes] = useState<number | ''>('');
  const [notes,           setNotes]           = useState('');
  const [isMilestone,     setIsMilestone]     = useState(false);
  const [milestoneLabel,  setMilestoneLabel]  = useState('');
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>([]);
  const [followUpNoteTitle, setFollowUpNoteTitle] = useState('');

  const createSession = useCreateSession();

  // Always called (hook rules); results only used in picker mode
  const { data: libraryData } = useLibrary();

  const effectiveGameId    = pickerMode ? (selectedGameId ?? 0) : gameId;
  const effectiveGameTitle = pickerMode ? selectedGameTitle : gameTitle;
  const effectiveLibraryEntryId = pickerMode ? selectedLibraryEntryId : (libraryEntryId ?? null);

  const resetForm = () => {
    setGameSearch('');
    setSelectedGameId(null);
    setSelectedGameTitle('');
    setSelectedLibraryEntryId(null);
    setDurationMinutes('');
    setNotes('');
    setIsMilestone(false);
    setMilestoneLabel('');
    setSelectedEmotions([]);
    setFollowUpNoteTitle('');
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = () => {
    if (effectiveGameId === 0) {
      notifications.show({ color: 'yellow', message: 'Please select a game first.' });
      return;
    }

    const data: SessionLogCreate = {
      game_id:          effectiveGameId,
      library_entry_id: effectiveLibraryEntryId,
      duration_minutes: typeof durationMinutes === 'number' ? durationMinutes : null,
      notes:            notes.trim() || null,
      is_milestone:     isMilestone,
      milestone_label:  isMilestone ? milestoneLabel.trim() || null : null,
      emotions:         selectedEmotions.length > 0 ? (selectedEmotions as EmotionType[]) : null,
      follow_up_note_title: followUpNoteTitle.trim() || null,
    };

    createSession.mutate(data, {
      onSuccess: () => {
        const priorStatus = libraryData?.find((entry) => entry.id === effectiveLibraryEntryId)?.status;
        if (priorStatus === 'completed') {
          notifications.show({ color: 'teal', message: 'Session logged. Moved to Replaying.' });
        } else if (priorStatus === 'wishlist' || priorStatus === 'backlog') {
          notifications.show({ color: 'teal', message: 'Session logged. Moved to Playing.' });
        } else {
          notifications.show({ color: 'green', message: 'Session logged!' });
        }
        handleClose();
      },
      onError: () => {
        notifications.show({ color: 'red', message: 'Failed to log session.' });
      },
    });
  };

  const handleEmotionChange = (values: string[]) => {
    if (values.length <= 5) setSelectedEmotions(values);
  };

  const libraryOptions = (libraryData ?? [])
    .filter((e) => e.game.name.toLowerCase().includes(gameSearch.toLowerCase()))
    .map((e) => e.game.name);

  const modalTitle = pickerMode
    ? 'Log session'
    : `Log session: ${effectiveGameTitle}`;

  return (
    <Modal
      opened={opened}
      onClose={handleClose}
      title={modalTitle}
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
        {/* ── Game picker (only in picker mode) ─────────────────────────── */}
        {pickerMode && (
          <Autocomplete
            label="Game"
            placeholder="Search your library..."
            leftSection={<IconSearch size={16} />}
            value={gameSearch}
            onChange={(val) => {
              setGameSearch(val);
              if (!val) {
                setSelectedGameId(null);
                setSelectedGameTitle('');
                setSelectedLibraryEntryId(null);
              }
            }}
            onOptionSubmit={(val) => {
              const entry = libraryData?.find((e) => e.game.name === val);
              if (entry) {
                setSelectedGameId(entry.game.id);
                setSelectedGameTitle(entry.game.name);
                setSelectedLibraryEntryId(entry.id);
                setGameSearch(entry.game.name);
              }
            }}
            data={libraryOptions}
          />
        )}

        <NumberInput
          label="Duration (minutes)"
          value={durationMinutes}
          onChange={(val) => setDurationMinutes(typeof val === 'number' ? val : '')}
          min={1}
          max={1440}
          leftSection={<IconClock size={16} />}
          placeholder="e.g. 90"
        />

        <Textarea
          label="Session notes"
          placeholder="What happened? What did you think?"
          value={notes}
          onChange={(e) => setNotes(e.currentTarget.value)}
          leftSection={<IconNote size={16} />}
          minRows={3}
          autosize
          maxRows={6}
        />

        <TextInput
          label="Reminder for next time"
          placeholder="First do the side quest in Mallenia and find Blaidd"
          value={followUpNoteTitle}
          onChange={(e) => setFollowUpNoteTitle(e.currentTarget.value)}
          leftSection={<IconBookmark size={16} />}
        />

        <Group>
          <Switch
            label="Milestone"
            checked={isMilestone}
            onChange={(e) => setIsMilestone(e.currentTarget.checked)}
          />
          {isMilestone && (
            <TextInput
              placeholder='e.g. "Completed", "Beat Act 2"'
              value={milestoneLabel}
              onChange={(e) => setMilestoneLabel(e.currentTarget.value)}
              leftSection={<IconTrophy size={16} />}
              style={{ flex: 1 }}
            />
          )}
        </Group>

        {/* ── Emotion picker ─────────────────────────────────────────────── */}
        <div>
          <Text size="sm" c="dimmed" mb="xs">
            How did this session feel? Optional, pick up to 5.
          </Text>
          <Chip.Group multiple value={selectedEmotions} onChange={handleEmotionChange}>
            <SimpleGrid cols={{ base: 2, sm: 3 }} spacing="xs">
              {Object.values(EmotionType).map((emotion) => {
                const config        = EMOTION_CONFIG[emotion];
                const IconComponent = EMOTION_ICONS[config.icon];
                return (
                  <Chip
                    key={emotion}
                    value={emotion}
                    color={config.color}
                    variant="outline"
                    icon={IconComponent ? <IconComponent size={14} /> : undefined}
                  >
                    {config.label}
                  </Chip>
                );
              })}
            </SimpleGrid>
          </Chip.Group>
        </div>

        <Group justify="flex-end" mt="sm">
          <Button variant="subtle" className={classes.secondaryAction} onClick={handleClose}>
            Cancel
          </Button>
          <Button
            className={classes.primaryAction}
            onClick={handleSubmit}
            loading={createSession.isPending}
            disabled={pickerMode && !selectedGameId}
          >
            Save session
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
