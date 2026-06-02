import { useState } from 'react';
import {
  Button,
  Center,
  Loader,
  Pagination,
  Paper,
  Stack,
  Text,
} from '@mantine/core';
import { IconArrowLeft } from '@tabler/icons-react';
import { useNavigate } from 'react-router';
import { BacklogFilters } from '../../components/library/BacklogFilters';
import { BacklogPriorityCard } from '../../components/library/BacklogPriorityCard';
import { usePrioritizedBacklog } from '../../hooks/useLibrary';
import type { BacklogFiltersParams } from '../../api/library';
import classes from './BacklogPage.module.css';

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
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Button
            variant="subtle"
            size="xs"
            leftSection={<IconArrowLeft size={14} />}
            onClick={() => navigate('/library')}
          >
            Library
          </Button>
          <Text className={classes.headerTitle}>
            Play <span className={classes.headerAccent}>Next</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Prioritize backlog titles by fit, time commitment, and how long they have been waiting.
          </Text>
        </div>
        {data && (
          <Text size="sm" c="dimmed">{data.total} game{data.total !== 1 ? 's' : ''} in backlog</Text>
        )}
      </div>

      <Paper p="md" radius="md" withBorder>
        <BacklogFilters filters={filters} onChange={setFilters} />
      </Paper>

      {isLoading && <Center h={300}><Loader color="ember" /></Center>}

      {isError && (
        <Paper p="md" radius="md" withBorder>
          <Text c="red.4" ta="center" size="sm">Failed to load backlog. Try again.</Text>
        </Paper>
      )}

      {data && data.results.length === 0 && (
        <div className={classes.emptyState}>
          <div>
            <Text size="sm" fw={600}>No matching backlog games</Text>
            <Text size="xs" c="dimmed" mt={4}>Adjust the filters or add more saved games to your backlog.</Text>
          </div>
        </div>
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
