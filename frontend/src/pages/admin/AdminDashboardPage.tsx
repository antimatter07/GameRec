import { useState } from 'react';
import {
  Badge,
  Button,
  Center,
  Group,
  Loader,
  Paper,
  SimpleGrid,
  Stack,
  Table,
  Text,
  TextInput,
  Title,
} from '@mantine/core';
import { notifications } from '@mantine/notifications';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';
import { useAuthStore } from '../../store/authStore';
import type { UserRole } from '../../types/user';

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
  const [search, setSearch] = useState('');

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
    queryKey: ['admin-users', search],
    queryFn: () => adminApi.listUsers(1, 50, search || undefined),
  });

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
    <Stack gap="xl">
      <Title order={2}>Admin Dashboard</Title>

      {/* Metrics */}
      <Stack gap="xs">
        <Title order={4}>System Metrics</Title>
        {metricsLoading ? (
          <Loader size="sm" />
        ) : (
          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            {[
              { label: 'Total Users',            value: metrics?.total_users            ?? '–' },
              { label: 'Active Users (30d)',      value: metrics?.active_users           ?? '–' },
              { label: 'Premium Users',           value: metrics?.premium_count          ?? '–' },
              { label: 'Recommendations Served',  value: metrics?.recommendations_served ?? '–' },
            ].map((m) => (
              <Paper key={m.label} p="md" withBorder radius="md">
                <Text size="xs" c="dimmed">{m.label}</Text>
                <Text fw={700} size="xl">{String(m.value)}</Text>
              </Paper>
            ))}
          </SimpleGrid>
        )}
        {metrics?.feedback_helpful_pct !== undefined && metrics.feedback_helpful_pct !== null && (
          <Text size="sm" c="dimmed">
            Feedback helpful: <strong>{metrics.feedback_helpful_pct}%</strong>
          </Text>
        )}
      </Stack>

      {/* Data Pipeline */}
      <Stack gap="xs">
        <Group justify="space-between">
          <Title order={4}>Data Pipeline (RAWG Sync)</Title>
          <Button
            size="xs"
            loading={triggerPipeline.isPending}
            onClick={() => triggerPipeline.mutate()}
          >
            Trigger Manual Sync
          </Button>
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

      {/* User Table */}
      <Stack gap="xs">
        <Title order={4}>Users</Title>
        <TextInput
          placeholder="Search by email or name…"
          value={search}
          onChange={(e) => setSearch(e.currentTarget.value)}
          maw={320}
        />
        {usersLoading ? (
          <Center><Loader /></Center>
        ) : (
          <Table striped highlightOnHover>
            <Table.Thead>
              <Table.Tr>
                <Table.Th>ID</Table.Th>
                <Table.Th>Email</Table.Th>
                <Table.Th>Display Name</Table.Th>
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
                    <Badge color={u.role === 'admin' ? 'red' : u.role === 'premium' ? 'violet' : 'gray'}>
                      {u.role}
                    </Badge>
                  </Table.Td>
                  <Table.Td>{u.is_active ? '✅' : '❌'}</Table.Td>
                  <Table.Td>
                    {u.role === 'basic' && u.id !== currentUser?.id && (
                      <Button
                        size="xs"
                        color="violet"
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
        )}
      </Stack>
    </Stack>
  );
}
