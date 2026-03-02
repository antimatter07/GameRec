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
  Title,
} from '@mantine/core';
import { useQuery, useMutation } from '@tanstack/react-query';
import { adminApi } from '../../api/admin';

/**
 * Admin-only dashboard.
 * TODO: Wrap each section in its own component for readability
 * TODO: Add Mantine Charts (BarChart / LineChart) for user growth and recommendations served
 * TODO: Add real-time pipeline status polling (refetchInterval)
 * TODO: Add search input for user list
 * TODO: Add pagination for user list
 */
export default function AdminDashboardPage() {
  const { data: metrics, isLoading: metricsLoading } = useQuery({
    queryKey: ['admin-metrics'],
    queryFn: adminApi.getMetrics,
    refetchInterval: 30_000, // refresh every 30s
  });

  const { data: pipelineStatus } = useQuery({
    queryKey: ['pipeline-status'],
    queryFn: adminApi.getPipelineStatus,
    refetchInterval: 10_000,
  });

  const { data: premiumRequests } = useQuery({
    queryKey: ['premium-requests'],
    queryFn: adminApi.listPremiumRequests,
  });

  const { data: users, isLoading: usersLoading } = useQuery({
    queryKey: ['admin-users'],
    queryFn: () => adminApi.listUsers(),
  });

  const triggerPipeline = useMutation({ mutationFn: adminApi.triggerPipeline });

  return (
    <Stack gap="xl">
      <Title order={2}>Admin Dashboard</Title>

      {/* --- Metrics --- */}
      <Stack gap="xs">
        <Title order={4}>System Metrics</Title>
        {metricsLoading ? (
          <Loader size="sm" />
        ) : (
          <SimpleGrid cols={{ base: 2, sm: 4 }}>
            {/* TODO: Render actual metric values from `metrics` object */}
            {[
              { label: 'Total Users',           value: metrics?.total_users          ?? '–' },
              { label: 'Active Users (30d)',     value: metrics?.active_users         ?? '–' },
              { label: 'Premium Users',          value: metrics?.premium_count        ?? '–' },
              { label: 'Recommendations Served', value: metrics?.recommendations_served ?? '–' },
            ].map((m) => (
              <Paper key={m.label} p="md" withBorder radius="md">
                <Text size="xs" c="dimmed">{m.label}</Text>
                <Text fw={700} size="xl">{String(m.value)}</Text>
              </Paper>
            ))}
          </SimpleGrid>
        )}
      </Stack>

      {/* --- Data Pipeline --- */}
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
          {/* TODO: Render pipelineStatus.last_run, status, next_scheduled_run */}
          <Text size="sm" c="dimmed">Pipeline status will appear here once implemented.</Text>
        </Paper>
      </Stack>

      {/* --- Premium Requests --- */}
      {premiumRequests && premiumRequests.length > 0 && (
        <Stack gap="xs">
          <Title order={4}>Pending Premium Requests</Title>
          {/* TODO: Render request queue with Approve button per row */}
          <Text size="sm" c="dimmed">{premiumRequests.length} pending request(s)</Text>
        </Stack>
      )}

      {/* --- User Table --- */}
      <Stack gap="xs">
        <Title order={4}>Users</Title>
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
                    {/* TODO: Promote/demote buttons — call adminApi.updateUserRole() */}
                    <Text size="xs" c="dimmed">–</Text>
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
