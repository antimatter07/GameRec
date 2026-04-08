import { useState } from 'react';
import {
  ActionIcon,
  Badge,
  Box,
  Center,
  Group,
  Loader,
  Modal,
  Paper,
  Rating,
  Select,
  SimpleGrid,
  Stack,
  Text,
  Button,
  Title,
  Tabs,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { IconPencil, IconTrash } from '@tabler/icons-react';
import { GameCard } from '../../components/games/GameCard';
import {
  useLibrary,
  useLibraryStats,
  useRemoveFromLibrary,
  useUpdateLibraryEntry,
} from '../../hooks/useLibrary';
import type { LibraryEntry, LibraryStatus } from '../../types/library';

const STATUS_TABS: { value: LibraryStatus | 'all'; label: string }[] = [
  { value: 'all',       label: 'All'       },
  { value: 'playing',   label: 'Playing'   },
  { value: 'completed', label: 'Completed' },
  { value: 'backlog',   label: 'Backlog'   },
  { value: 'dropped',   label: 'Dropped'   },
];

const STATUS_COLORS: Record<LibraryStatus, string> = {
  playing:   'teal',
  completed: 'blue',
  backlog:   'gray',
  dropped:   'red',
};

export default function LibraryPage() {
  const { data: entries, isLoading } = useLibrary();
  const { data: stats } = useLibraryStats();
  const removeEntry = useRemoveFromLibrary();
  const updateEntry = useUpdateLibraryEntry();

  const [editingEntry, setEditingEntry] = useState<LibraryEntry | null>(null);
  const [editStatus, setEditStatus] = useState<LibraryStatus>('backlog');
  const [editRating, setEditRating] = useState<number>(0);
  const [editOpened, { open: openEdit, close: closeEdit }] = useDisclosure(false);

  const handleOpenEdit = (entry: LibraryEntry) => {
    setEditingEntry(entry);
    setEditStatus(entry.status);
    setEditRating(entry.rating ?? 0);
    openEdit();
  };

  const handleSaveEdit = async () => {
    if (!editingEntry) return;
    try {
      await updateEntry.mutateAsync({
        id: editingEntry.id,
        updates: {
          status: editStatus,
          rating: editRating > 0 ? editRating : undefined,
        },
      });
      closeEdit();
      notifications.show({ color: 'green', message: 'Entry updated' });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to update entry' });
    }
  };

  const handleRemove = async (entryId: number, gameName: string) => {
    try {
      await removeEntry.mutateAsync(entryId);
      notifications.show({ color: 'blue', message: `${gameName} removed from library` });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to remove entry' });
    }
  };

  if (isLoading) return <Center h={400}><Loader /></Center>;

  return (
    <Stack gap="md">
      <Title order={2}>My Library</Title>

      {/* Stats bar */}
      {stats && (
        <Paper p="sm" withBorder radius="md">
          <Group gap="lg" wrap="wrap">
            <Text size="sm" fw={600}>
              {stats.total_games} {stats.total_games === 1 ? 'game' : 'games'}
            </Text>
            {stats.avg_rating !== null && (
              <Group gap={4}>
                <Rating value={stats.avg_rating / 2} fractions={2} readOnly size="xs" />
                <Text size="xs" c="dimmed">avg {stats.avg_rating.toFixed(1)}</Text>
              </Group>
            )}
            <Group gap="xs">
              {stats.top_genres.slice(0, 3).map((g) => (
                <Badge key={g.genre} size="xs" variant="light">{g.genre}</Badge>
              ))}
            </Group>
          </Group>
        </Paper>
      )}

      <Tabs defaultValue="all">
        <Tabs.List>
          {STATUS_TABS.map((tab) => (
            <Tabs.Tab key={tab.value} value={tab.value}>
              {tab.label}
              {entries && tab.value !== 'all' && (
                <Badge size="xs" ml="xs" variant="light">
                  {entries.filter((e) => e.status === tab.value).length}
                </Badge>
              )}
            </Tabs.Tab>
          ))}
        </Tabs.List>

        {STATUS_TABS.map((tab) => {
          const filtered = (entries ?? []).filter(
            (e) => tab.value === 'all' || e.status === tab.value
          );
          return (
            <Tabs.Panel key={tab.value} value={tab.value} pt="md">
              {filtered.length === 0 ? (
                <Text c="dimmed" ta="center" mt="xl">
                  {entries?.length === 0
                    ? 'Your library is empty. Browse the catalog to add games!'
                    : `No ${tab.value} games.`}
                </Text>
              ) : (
                <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }}>
                  {filtered.map((entry) => (
                    <Box key={entry.id}>
                      <GameCard game={entry.game} />
                      <Paper px="xs" py={6} withBorder style={{ borderTop: 0, borderRadius: '0 0 8px 8px' }}>
                        <Group justify="space-between" align="center">
                          <Group gap="xs">
                            <Badge size="xs" color={STATUS_COLORS[entry.status]} variant="light">
                              {entry.status}
                            </Badge>
                            {entry.rating !== null && (
                              <Rating value={entry.rating / 2} fractions={2} readOnly size="xs" />
                            )}
                          </Group>
                          <Group gap={4}>
                            <ActionIcon
                              size="xs"
                              variant="subtle"
                              onClick={() => handleOpenEdit(entry)}
                              aria-label="Edit entry"
                            >
                              <IconPencil size={14} />
                            </ActionIcon>
                            <ActionIcon
                              size="xs"
                              variant="subtle"
                              color="red"
                              onClick={() => handleRemove(entry.id, entry.game.name)}
                              loading={removeEntry.isPending}
                              aria-label="Remove from library"
                            >
                              <IconTrash size={14} />
                            </ActionIcon>
                          </Group>
                        </Group>
                      </Paper>
                    </Box>
                  ))}
                </SimpleGrid>
              )}
            </Tabs.Panel>
          );
        })}
      </Tabs>

      {/* Edit modal — single shared instance */}
      <Modal opened={editOpened} onClose={closeEdit} title="Edit library entry" centered size="sm">
        <Stack gap="md">
          <Select
            label="Status"
            value={editStatus}
            onChange={(v) => v && setEditStatus(v as LibraryStatus)}
            data={[
              { value: 'playing',   label: 'Playing'   },
              { value: 'completed', label: 'Completed' },
              { value: 'backlog',   label: 'Backlog'   },
              { value: 'dropped',   label: 'Dropped'   },
            ]}
          />
          <Stack gap={4}>
            <Text size="sm" fw={500}>Rating</Text>
            <Rating
              value={editRating / 2}
              fractions={2}
              onChange={(v) => setEditRating(v * 2)}
            />
            {editRating > 0 && (
              <Text size="xs" c="dimmed">{editRating.toFixed(1)} / 5</Text>
            )}
          </Stack>
          <Group justify="flex-end">
            <Button variant="default" onClick={closeEdit}>Cancel</Button>
            <Button onClick={handleSaveEdit} loading={updateEntry.isPending}>Save</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
