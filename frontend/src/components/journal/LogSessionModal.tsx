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
import { DateTimePicker } from '@mantine/dates';
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
} from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useCreateSession } from '../../hooks/useJournal';
import { useGamesList } from '../../hooks/useGames';
import { EmotionType, EMOTION_CONFIG } from '../../types/journal';
import type { SessionLogCreate } from '../../types/journal';

// Map icon names to actual components
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
  const [gameSearch,       setGameSearch]       = useState('');
  const [selectedGameId,   setSelectedGameId]   = useState<number | null>(null);
  const [selectedGameTitle, setSelectedGameTitle] = useState('');

  // Session form state
  const [startedAt,       setStartedAt]       = useState<Date | null>(new Date());
  const [durationMinutes, setDurationMinutes] = useState<number | ''>('');
  const [notes,           setNotes]           = useState('');
  const [isMilestone,     setIsMilestone]     = useState(false);
  const [milestoneLabel,  setMilestoneLabel]  = useState('');
  const [selectedEmotions, setSelectedEmotions] = useState<string[]>([]);

  const createSession = useCreateSession();

  // Game search — always called (hook rules); results only used when in pickerMode
  const search = pickerMode && gameSearch.length >= 2 ? gameSearch : '';
  const { data: searchResults } = useGamesList(1, 8, { search });

  const effectiveGameId    = pickerMode ? (selectedGameId ?? 0) : gameId;
  const effectiveGameTitle = pickerMode ? selectedGameTitle : gameTitle;

  const resetForm = () => {
    setGameSearch('');
    setSelectedGameId(null);
    setSelectedGameTitle('');
    setStartedAt(new Date());
    setDurationMinutes('');
    setNotes('');
    setIsMilestone(false);
    setMilestoneLabel('');
    setSelectedEmotions([]);
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const handleSubmit = () => {
    if (!startedAt) return;
    if (effectiveGameId === 0) {
      notifications.show({ color: 'yellow', message: 'Please select a game first.' });
      return;
    }

    const data: SessionLogCreate = {
      game_id:          effectiveGameId,
      library_entry_id: libraryEntryId ?? null,
      started_at:       startedAt.toISOString(),
      duration_minutes: typeof durationMinutes === 'number' ? durationMinutes : null,
      notes:            notes.trim() || null,
      is_milestone:     isMilestone,
      milestone_label:  isMilestone ? milestoneLabel.trim() || null : null,
      emotions:         selectedEmotions.length > 0 ? (selectedEmotions as EmotionType[]) : null,
    };

    createSession.mutate(data, {
      onSuccess: () => {
        notifications.show({ color: 'green', message: 'Session logged!' });
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

  const gameOptions = searchResults?.results?.map((g: any) => g.name) ?? [];

  const modalTitle = pickerMode
    ? 'Log session'
    : `Log session — ${effectiveGameTitle}`;

  return (
    <Modal opened={opened} onClose={handleClose} title={modalTitle} size="lg" centered>
      <Stack gap="md">
        {/* ── Game picker (only in picker mode) ─────────────────────────── */}
        {pickerMode && (
          <Autocomplete
            label="Game"
            placeholder="Type to search for a game…"
            leftSection={<IconSearch size={16} />}
            value={gameSearch}
            onChange={(val) => {
              setGameSearch(val);
              // If the user clears text, clear selection too
              if (!val) {
                setSelectedGameId(null);
                setSelectedGameTitle('');
              }
            }}
            onOptionSubmit={(val) => {
              const game = searchResults?.results?.find((g: any) => g.name === val);
              if (game) {
                setSelectedGameId(game.id);
                setSelectedGameTitle(game.name);
                setGameSearch(game.name);
              }
            }}
            data={gameOptions}
          />
        )}

        <DateTimePicker
          label="Start time"
          value={startedAt}
          onChange={(val: any) => setStartedAt(val)}
          leftSection={<IconClock size={16} />}
        />

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
            How did this session feel? (optional — pick up to 5)
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
          <Button variant="subtle" onClick={handleClose}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            loading={createSession.isPending}
            disabled={!startedAt || (pickerMode && !selectedGameId)}
          >
            Save session
          </Button>
        </Group>
      </Stack>
    </Modal>
  );
}
