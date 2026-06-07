import { useEffect, useState } from 'react';
import {
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  Stack,
  Table,
  Text,
  TextInput,
} from '@mantine/core';
import { IconRefresh, IconSearch } from '@tabler/icons-react';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import { useAuthStore } from '../../store/authStore';
import type { UserRole } from '../../types/user';
import classes from './AdminDashboardPage.module.css';

const PIPELINE_STATUS_COLORS: Record<string, string> = {
  never_run: 'gray',
  triggered: 'yellow',
  success:   'green',
  failure:   'red',
};

function formatRelativeTime(iso: string | null): string {
  if (!iso) return 'Never';
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60_000);
  if (mins < 1)  return 'Just now';
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24)  return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function AdminDashboardPage() {
  const currentUser = useAuthStore((s) => s.user);
  const queryClient = useQueryClient();
  const [searchInput, setSearchInput] = useState('');
  const [appliedSearch, setAppliedSearch] = useState<string | undefined>(undefined);

  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: adminApi.getMetrics,
    refetchInterval: 30_000,
  });

  const { data: pipelineStatus } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: adminApi.getPipelineStatus,
    refetchInterval: 10_000,
  });

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users', appliedSearch],
    queryFn: () => adminApi.listUsers(1, 50, appliedSearch),
  });

  const applySearch = (value: string) => {
    const normalizedSearch = value.trim() || undefined;
    setAppliedSearch((current) => (current === normalizedSearch ? current : normalizedSearch));
  };

  useEffect(() => {
    const normalizedSearch = searchInput.trim() || undefined;
    if (normalizedSearch === appliedSearch) return undefined;

    const timeoutId = window.setTimeout(() => {
      setAppliedSearch((current) => (current === normalizedSearch ? current : normalizedSearch));
    }, 3000);

    return () => window.clearTimeout(timeoutId);
  }, [appliedSearch, searchInput]);

  const triggerPipeline = useMutation({
    mutationFn: adminApi.triggerPipeline,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pipeline-status'] });
      notifications.show({ color: 'teal', message: 'Pipeline sync triggered' });
    },
  });

  const updateRole = useMutation({
    mutationFn: ({ userId, role }: { userId: number; role: UserRole }) =>
      adminApi.updateUserRole(userId, role),
    onSuccess: (_, { role }) => {
      queryClient.invalidateQueries({ queryKey: ['admin-users'] });
      notifications.show({
        color: 'green',
        message: `User role updated to ${role}`,
      });
    },
    onError: () => {
      notifications.show({ color: 'red', message: 'Failed to update role' });
    },
  });

  return (
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Admin <span className={classes.headerAccent}>Dashboard</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Monitor user access, recommendation activity, and RAWG sync health from one operational surface.
          </Text>
        </div>

        <Button
          leftSection={<IconRefresh size={16} />}
          loading={triggerPipeline.isPending}
          onClick={() => triggerPipeline.mutate()}
        >
          Trigger sync
        </Button>
      </div>

      <Stack gap="xs">
        <Group justify="space-between" className={classes.panelHeader}>
          <div>
            <Text size="sm" fw={600}>System metrics</Text>
            <Text size="xs" c="dimmed">Snapshot refreshed automatically while the page is open.</Text>
          </div>
        </Group>
        {metricsLoading ? (
          <Center py="xl"><Loader size="sm" /></Center>
        ) : (
          <div className={classes.metricsGrid}>
            {[
              { label: 'Total Users',            value: metrics?.total_users            ?? '–' },
              { label: 'Active Users (30d)',      value: metrics?.active_users           ?? '–' },
              { label: 'Premium Users',           value: metrics?.premium_count          ?? '–' },
              { label: 'Recommendations Served',  value: metrics?.recommendations_served ?? '–' },
            ].map((m) => (
              <Paper key={m.label} p="md" withBorder radius="md" className={classes.metricCard}>
                <div className={classes.metricLabel}>{m.label}</div>
                <div className={classes.metricValue}>{String(m.value)}</div>
              </Paper>
            ))}
          </div>
        )}
        {metrics?.feedback_helpful_pct !== undefined && metrics.feedback_helpful_pct !== null && (
          <Text size="sm" c="dimmed">
            Feedback helpful: <strong>{metrics.feedback_helpful_pct}%</strong>
          </Text>
        )}
      </Stack>

      <Stack gap="xs">
        <Group justify="space-between" className={classes.panelHeader}>
          <div>
            <Text size="sm" fw={600}>Data pipeline</Text>
            <Text size="xs" c="dimmed">RAWG catalog sync status and current worker task.</Text>
          </div>
        </Group>
        <Paper p="md" withBorder radius="md">
          <Group gap="md">
            <Badge color={PIPELINE_STATUS_COLORS[pipelineStatus?.status ?? 'never_run'] ?? 'gray'}>
              {pipelineStatus?.status ?? 'never_run'}
            </Badge>
            <Text size="sm">
              Last run: <strong>{formatRelativeTime(pipelineStatus?.last_run ?? null)}</strong>
            </Text>
            {pipelineStatus?.task_id && (
              <Text size="xs" c="dimmed">Task: {pipelineStatus.task_id}</Text>
            )}
          </Group>
        </Paper>
      </Stack>

      <Stack gap="xs">
        <Group justify="space-between" className={classes.panelHeader}>
          <div>
            <Text size="sm" fw={600}>Users</Text>
            <Text size="xs" c="dimmed">Promote or demote accounts without changing your own role.</Text>
          </div>
        </Group>
        <TextInput
          className={classes.searchInput}
          leftSection={<IconSearch size={16} />}
          placeholder="Search by email or name…"
          value={searchInput}
          onChange={(e) => setSearchInput(e.currentTarget.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') {
              applySearch(searchInput);
            }
          }}
        />
        {usersLoading ? (
          <Center><Loader /></Center>
        ) : (
          <Paper withBorder radius="md" className={classes.tableWrap}>
            <Table striped highlightOnHover className={classes.userTable}>
              <Table.Thead>
                <Table.Tr>
                  <Table.Th>ID</Table.Th>
                  <Table.Th>Email</Table.Th>
                  <Table.Th>Display name</Table.Th>
                  <Table.Th>Role</Table.Th>
                  <Table.Th>Active</Table.Th>
                  <Table.Th>Actions</Table.Th>
                </Table.Tr>
              </Table.Thead>
              <Table.Tbody>
                {(users ?? []).map((u) => (
                  <Table.Tr key={u.id}>
                    <Table.Td>{u.id}</Table.Td>
                    <Table.Td>{u.email}</Table.Td>
                    <Table.Td>{u.display_name ?? '–'}</Table.Td>
                    <Table.Td>
                      <Badge color={u.role === 'admin' ? 'red' : u.role === 'premium' ? 'ember' : 'gray'} variant="light">
                        {u.role}
                      </Badge>
                    </Table.Td>
                    <Table.Td>
                      <span className={u.is_active ? classes.activeState : classes.inactiveState}>
                        {u.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </Table.Td>
                    <Table.Td>
                      {u.role === 'basic' && u.id !== currentUser?.id && (
                        <Button
                          size="xs"
                          color="ember"
                          loading={updateRole.isPending}
                          onClick={() => updateRole.mutate({ userId: u.id, role: 'premium' })}
                        >
                          Promote
                        </Button>
                      )}
                      {u.role === 'premium' && u.id !== currentUser?.id && (
                        <Button
                          size="xs"
                          variant="outline"
                          color="gray"
                          loading={updateRole.isPending}
                          onClick={() => updateRole.mutate({ userId: u.id, role: 'basic' })}
                        >
                          Demote
                        </Button>
                      )}
                    </Table.Td>
                  </Table.Tr>
                ))}
              </Table.Tbody>
            </Table>
          </Paper>
        )}
      </Stack>
    </Stack>
  );
}
