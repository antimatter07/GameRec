import { useState } from 'react';
import {
  Button,
  Center,
  Group,
  Loader,
  Pagination,
  Stack,
  Text,
  Title,
} from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { BacklogFilters } from '../../components/library/BacklogFilters';
import { BacklogPriorityCard } from '../../components/library/BacklogPriorityCard';
import { usePrioritizedBacklog } from '../../hooks/useLibrary';
import type { BacklogFiltersParams } from '../../api/library';

const PAGE_SIZE = 20;

export default function BacklogPage() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<BacklogFiltersParams>({
    sort: 'score',
    page: 1,
    page_size: PAGE_SIZE,
  });

  const { data, isLoading, isError } = usePrioritizedBacklog(filters);

  const totalPages = data ? Math.ceil(data.total / PAGE_SIZE) : 1;

  return (
    <Stack gap="md">
      <Group justify="space-between" align="center">
        <Group gap="xs">
          <Button
            variant="subtle"
            size="xs"
            leftSection={<IconArrowLeft size={14} />}
            onClick={() => navigate('/library')}
          >
            Library
          </Button>
          <Title order={2}>Play Next</Title>
        </Group>
        {data && (
          <Text size="sm" c="dimmed">{data.total} game{data.total !== 1 ? 's' : ''} in backlog</Text>
        )}
      </Group>

      <BacklogFilters filters={filters} onChange={setFilters} />

      {isLoading && <Center h={300}><Loader /></Center>}

      {isError && (
        <Text c="red" ta="center">Failed to load backlog. Try again.</Text>
      )}

      {data && data.results.length === 0 && (
        <Text c="dimmed" ta="center" mt="xl">
          No backlog games match your filters.
        </Text>
      )}

      {data && data.results.length > 0 && (
        <Stack gap="xs">
          {data.results.map((item) => (
            <BacklogPriorityCard key={item.entry_id} item={item} />
          ))}
        </Stack>
      )}

      {totalPages > 1 && (
        <Center>
          <Pagination
            total={totalPages}
            value={filters.page ?? 1}
            onChange={(p) => setFilters((f) => ({ ...f, page: p }))}
          />
        </Center>
      )}
    </Stack>
  );
}
