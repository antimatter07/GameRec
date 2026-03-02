import { Badge, Center, Loader, Select, SimpleGrid, Stack, Tabs, Text, Title } from '@mantine/core';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { libraryApi } from '../../api/library';
import { GameCard } from '../../components/games/GameCard';
import type { LibraryStatus } from '../../types/library';

const STATUS_TABS: { value: LibraryStatus | 'all'; label: string }[] = [
  { value: 'all',       label: 'All'       },
  { value: 'playing',   label: 'Playing'   },
  { value: 'completed', label: 'Completed' },
  { value: 'backlog',   label: 'Backlog'   },
  { value: 'dropped',   label: 'Dropped'   },
];

/**
 * User's game library dashboard.
 * TODO: Add LibraryStats summary at the top (total games, avg rating, genre pie chart)
 * TODO: Add inline rating/status edit via a modal or popover
 * TODO: Add sort options (by added_at, rating, name)
 */
export default function LibraryPage() {
  const queryClient = useQueryClient();

  const { data: entries, isLoading } = useQuery({
    queryKey: ['library'],
    queryFn: libraryApi.getAll,
  });

  const removeMutation = useMutation({
    mutationFn: libraryApi.remove,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['library'] }),
  });

  // TODO: Implement active tab filtering — filter entries client-side or re-fetch with status param
  // TODO: Show LibraryStats from libraryApi.getStats()

  if (isLoading) return <Center h={400}><Loader /></Center>;

  return (
    <Stack gap="md">
      <Title order={2}>My Library</Title>

      {/* TODO: Insert LibraryStats component here */}

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

        {STATUS_TABS.map((tab) => (
          <Tabs.Panel key={tab.value} value={tab.value} pt="md">
            <SimpleGrid cols={{ base: 1, sm: 2, md: 3, lg: 4 }}>
              {(entries ?? [])
                .filter((e) => tab.value === 'all' || e.status === tab.value)
                .map((entry) => (
                  <GameCard key={entry.id} game={entry.game} />
                  // TODO: Wrap in a card that also shows status badge, star rating,
                  //       and a remove / edit button
                ))}
            </SimpleGrid>

            {entries?.length === 0 && (
              <Text c="dimmed" ta="center" mt="xl">
                Your library is empty. Browse the catalog to add games!
              </Text>
            )}
          </Tabs.Panel>
        ))}
      </Tabs>
    </Stack>
  );
}
