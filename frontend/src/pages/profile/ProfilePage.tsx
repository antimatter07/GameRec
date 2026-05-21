import {
  Accordion,
  Alert,
  Avatar,
  Badge,
  Button,
  Divider,
  Group,
  Modal,
  Stack,
  Text,
  TextInput,
  Textarea,
  Title,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useForm } from '@mantine/form';
import { useState } from 'react';
import { isAxiosError } from 'axios';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';
import { usersApi } from '../../api/users';
import { useImportSteamLibrary } from '../../hooks/useLibrary';
import type { SteamImportGameResult, SteamImportResponse } from '../../types/library';

function SteamResultList({ items }: { items: SteamImportGameResult[] }) {
  if (items.length === 0) {
    return <Text size="sm" c="dimmed">No titles in this group.</Text>;
  }

  return (
    <Stack gap={6}>
      {items.slice(0, 20).map((item) => (
        <Group key={`${item.steam_app_id}-${item.steam_name}`} justify="space-between" align="flex-start" gap="sm">
          <Stack gap={0}>
            <Text size="sm" fw={500}>{item.steam_name}</Text>
            {item.game && (
              <Text size="xs" c="dimmed">
                Matched to {item.game.name}
                {item.match_confidence !== null ? ` (${Math.round(item.match_confidence)}%)` : ''}
              </Text>
            )}
            {!item.game && item.reason && <Text size="xs" c="dimmed">{item.reason}</Text>}
          </Stack>
          <Text size="xs" c="dimmed">#{item.steam_app_id}</Text>
        </Group>
      ))}
      {items.length > 20 && (
        <Text size="xs" c="dimmed">{items.length - 20} more not shown</Text>
      )}
    </Stack>
  );
}

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const { updateProfile, logout } = useAuth();
  const [deleteOpened, { open: openDelete, close: closeDelete }] = useDisclosure(false);
  const [steamProfile, setSteamProfile] = useState('');
  const [steamResult, setSteamResult] = useState<SteamImportResponse | null>(null);
  const importSteam = useImportSteamLibrary();

  const form = useForm({
    initialValues: {
      display_name: user?.display_name ?? '',
      bio:          user?.bio          ?? '',
      avatar_url:   user?.avatar_url   ?? '',
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    try {
      await updateProfile(values);
      notifications.show({ color: 'green', message: 'Profile updated' });
    } catch {
      notifications.show({ color: 'red', message: 'Failed to update profile' });
    }
  });

  const handleDeleteAccount = async () => {
    try {
      await usersApi.deleteMe();
      closeDelete();
      logout();
    } catch {
      notifications.show({ color: 'red', message: 'Failed to delete account' });
    }
  };

  const handleRequestPremium = async () => {
    try {
      await usersApi.requestPremium();
      notifications.show({ color: 'teal', message: 'Request submitted — an admin will review it' });
    } catch {
      notifications.show({ color: 'blue', message: 'Premium upgrade requests coming soon' });
    }
  };

  const handleSteamImport = async () => {
    try {
      const result = await importSteam.mutateAsync(steamProfile.trim());
      setSteamResult(result);
      notifications.show({
        color: 'green',
        message: `Imported ${result.added.length} Steam ${result.added.length === 1 ? 'game' : 'games'}`,
      });
    } catch (err) {
      const detail = isAxiosError(err) ? err.response?.data?.detail : null;
      notifications.show({
        color: 'red',
        message: typeof detail === 'string' ? detail : 'Failed to import Steam library',
      });
    }
  };

  if (!user) return null;

  return (
    <Stack gap="lg" maw={600}>
      <Title order={2}>Profile</Title>

      <Group>
        <Avatar src={user.avatar_url ?? undefined} size={80} radius="xl" />
        <Stack gap={4}>
          <Text fw={600}>{user.display_name ?? user.email}</Text>
          <Text size="sm" c="dimmed">{user.email}</Text>
          <Badge
            size="sm"
            variant="light"
            color={user.role === 'admin' ? 'red' : user.role === 'premium' ? 'violet' : 'gray'}
          >
            {user.role}
          </Badge>
        </Stack>
      </Group>

      <form onSubmit={handleSubmit}>
        <Stack gap="sm">
          <TextInput
            label="Display name"
            {...form.getInputProps('display_name')}
          />
          <TextInput
            label="Avatar URL"
            placeholder="https://..."
            {...form.getInputProps('avatar_url')}
          />
          <Textarea
            label="Bio"
            placeholder="Tell us about your gaming taste..."
            rows={3}
            {...form.getInputProps('bio')}
          />
          <Button type="submit" w="fit-content">
            Save changes
          </Button>
        </Stack>
      </form>

      <Divider />

      <Stack gap="sm">
        <Stack gap={2}>
          <Text fw={600}>Steam Library Import</Text>
          <Text size="sm" c="dimmed">
            Add matching Steam-owned games to your backlog while keeping your existing cross-platform library intact.
          </Text>
        </Stack>
        <Group align="flex-end">
          <TextInput
            label="Steam profile"
            placeholder="SteamID64 or steamcommunity.com profile URL"
            value={steamProfile}
            onChange={(event) => setSteamProfile(event.currentTarget.value)}
            style={{ flex: 1 }}
          />
          <Button
            onClick={handleSteamImport}
            loading={importSteam.isPending}
            disabled={steamProfile.trim().length === 0}
          >
            Import Steam Library
          </Button>
        </Group>

        {steamResult && (
          <Alert color="teal" variant="light">
            <Stack gap="sm">
              <Text size="sm" fw={600}>
                {steamResult.profile_name ?? steamResult.steam_id}: {steamResult.added.length} added,{' '}
                {steamResult.already_in_library.length} already in library,{' '}
                {steamResult.skipped_low_confidence.length} skipped, {steamResult.unmatched.length} unmatched
              </Text>
              <Accordion variant="contained">
                <Accordion.Item value="added">
                  <Accordion.Control>Added ({steamResult.added.length})</Accordion.Control>
                  <Accordion.Panel><SteamResultList items={steamResult.added} /></Accordion.Panel>
                </Accordion.Item>
                <Accordion.Item value="already">
                  <Accordion.Control>Already in library ({steamResult.already_in_library.length})</Accordion.Control>
                  <Accordion.Panel><SteamResultList items={steamResult.already_in_library} /></Accordion.Panel>
                </Accordion.Item>
                <Accordion.Item value="skipped">
                  <Accordion.Control>Skipped low-confidence ({steamResult.skipped_low_confidence.length})</Accordion.Control>
                  <Accordion.Panel><SteamResultList items={steamResult.skipped_low_confidence} /></Accordion.Panel>
                </Accordion.Item>
                <Accordion.Item value="unmatched">
                  <Accordion.Control>Unmatched ({steamResult.unmatched.length})</Accordion.Control>
                  <Accordion.Panel><SteamResultList items={steamResult.unmatched} /></Accordion.Panel>
                </Accordion.Item>
              </Accordion>
            </Stack>
          </Alert>
        )}
      </Stack>

      {user.role === 'basic' && (
        <>
          <Divider />
          <Stack gap="xs">
            <Text fw={600}>Upgrade to Premium</Text>
            <Text size="sm" c="dimmed">
              Get AI-powered game explanations, Game DNA analysis, and higher rate limits.
            </Text>
            <Button
              variant="gradient"
              gradient={{ from: 'violet', to: 'cyan' }}
              w="fit-content"
              onClick={handleRequestPremium}
            >
              Request Premium Access
            </Button>
          </Stack>
        </>
      )}

      <Divider />

      <Stack gap="xs">
        <Text fw={600} c="red">Danger Zone</Text>
        <Text size="sm" c="dimmed">
          Permanently delete your account and all associated data. This cannot be undone.
        </Text>
        <Button color="red" variant="outline" w="fit-content" onClick={openDelete}>
          Delete Account
        </Button>
      </Stack>

      <Modal opened={deleteOpened} onClose={closeDelete} title="Delete account" centered>
        <Stack gap="md">
          <Text size="sm">
            Are you sure you want to delete your account? Your library, recommendations, and all data will be permanently removed.
          </Text>
          <Group justify="flex-end">
            <Button variant="default" onClick={closeDelete}>Cancel</Button>
            <Button color="red" onClick={handleDeleteAccount}>Yes, delete my account</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
