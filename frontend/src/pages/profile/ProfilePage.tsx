import {
  Accordion,
  Alert,
  Avatar,
  Badge,
  Button,
  Group,
  Modal,
  Paper,
  SimpleGrid,
  Stack,
  Text,
  TextInput,
  Textarea,
} from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { notifications } from '@mantine/notifications';
import { useForm } from '@mantine/form';
import { useState } from 'react';
import { isAxiosError } from 'axios';
import {
  IconAlertTriangle,
  IconBrandSteam,
  IconCrown,
  IconDeviceGamepad2,
  IconId,
  IconPencil,
  IconShield,
  IconTrash,
  IconUserCircle,
} from '@tabler/icons-react';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';
import { usersApi } from '../../api/users';
import { useImportSteamLibrary } from '../../hooks/useLibrary';
import type { SteamImportGameResult, SteamImportResponse } from '../../types/library';
import type { User } from '../../types/user';
import classes from './ProfilePage.module.css';

const roleColors = {
  admin: 'red',
  premium: 'ember',
  basic: 'gray',
} as const;

function getProfileCompletion(user: User) {
  const fields = [user.display_name, user.bio, user.avatar_url];
  const completed = fields.filter((field) => Boolean(field?.trim())).length;
  return Math.round((completed / fields.length) * 100);
}

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
    <Stack gap="lg" className={classes.page}>
      <div className={classes.header}>
        <div>
          <Text className={classes.headerTitle}>
            Player <span className={classes.headerAccent}>Profile</span>
          </Text>
          <Text size="xs" c="dimmed" className={classes.headerSubtitle}>
            Manage identity, account access, and library imports from one compact dashboard.
          </Text>
        </div>

        <Button leftSection={<IconPencil size={16} />} color="ember" type="submit" form="profile-form">
          Save changes
        </Button>
      </div>

      <div className={classes.metricsGrid}>
        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-ember-light)' }}>
            <IconUserCircle size={18} color="var(--mantine-color-ember-5)" />
          </div>
          <div className={classes.metricLabel}>Profile</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-ember-4)' }}>
            {getProfileCompletion(user)}%
          </div>
          <div className={classes.metricSub}>Display name, bio, and avatar</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-blue-light)' }}>
            <IconShield size={18} color="var(--mantine-color-blue-5)" />
          </div>
          <div className={classes.metricLabel}>Access</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-blue-4)' }}>
            {user.role}
          </div>
          <div className={classes.metricSub}>Current account tier</div>
        </Paper>

        <Paper className={classes.metricCard} p="md" radius="md" withBorder>
          <div className={classes.metricIcon} style={{ background: 'var(--mantine-color-teal-light)' }}>
            <IconBrandSteam size={18} color="var(--mantine-color-teal-5)" />
          </div>
          <div className={classes.metricLabel}>Steam import</div>
          <div className={classes.metricValue} style={{ color: 'var(--mantine-color-teal-4)' }}>
            {steamResult ? steamResult.added.length : 0}
          </div>
          <div className={classes.metricSub}>Games added this session</div>
        </Paper>
      </div>

      <div className={classes.overviewGrid}>
        <Paper p="md" radius="md" withBorder>
          <Stack gap="md">
            <Group className={classes.panelHeader} justify="space-between">
              <div>
                <Text size="sm" fw={600}>Account identity</Text>
                <Text size="xs" c="dimmed">Public-facing details used across your library and recommendations.</Text>
              </div>
              <Badge
                size="sm"
                variant="light"
                color={roleColors[user.role]}
                leftSection={<IconId size={12} />}
              >
                {user.role}
              </Badge>
            </Group>

            <Group align="center" gap="md" className={classes.identityRow}>
              <Avatar src={user.avatar_url ?? undefined} size={82} radius="md" className={classes.avatar}>
                <IconDeviceGamepad2 size={30} />
              </Avatar>
              <Stack gap={4} className={classes.identityInfo}>
                <Text className={classes.identityName}>{user.display_name ?? user.email}</Text>
                <Text size="xs" c="dimmed">{user.email}</Text>
                {user.bio && <Text size="xs" c="dimmed" lineClamp={2}>{user.bio}</Text>}
              </Stack>
            </Group>

            <form id="profile-form" onSubmit={handleSubmit}>
              <Stack gap="sm">
                <TextInput
                  className={classes.input}
                  label="Display name"
                  {...form.getInputProps('display_name')}
                />
                <TextInput
                  className={classes.input}
                  label="Avatar URL"
                  placeholder="https://..."
                  {...form.getInputProps('avatar_url')}
                />
                <Textarea
                  className={classes.input}
                  label="Bio"
                  placeholder="Tell us about your gaming taste..."
                  rows={3}
                  autosize
                  minRows={3}
                  {...form.getInputProps('bio')}
                />
              </Stack>
            </form>
          </Stack>
        </Paper>

        <Stack gap="sm">
          {user.role === 'basic' && (
            <Paper p="md" radius="md" withBorder className={classes.sidePanel}>
              <Stack gap="sm">
                <Group gap="xs">
                  <IconCrown size={16} color="var(--mantine-color-yellow-5)" />
                  <Text size="sm" fw={600}>Premium access</Text>
                </Group>
                <Text size="xs" c="dimmed">
                  AI explanations, Game DNA analysis, and higher request limits.
                </Text>
                <Button
                  color="ember"
                  variant="light"
                  leftSection={<IconCrown size={15} />}
                  onClick={handleRequestPremium}
                >
                  Request access
                </Button>
              </Stack>
            </Paper>
          )}

          <Paper p="md" radius="md" withBorder className={classes.dangerPanel}>
            <Stack gap="sm">
              <Group gap="xs">
                <IconAlertTriangle size={16} color="var(--mantine-color-red-5)" />
                <Text size="sm" fw={600}>Danger zone</Text>
              </Group>
              <Text size="xs" c="dimmed">
                Permanently delete your account, library, recommendations, and profile data.
              </Text>
              <Button
                color="red"
                variant="subtle"
                leftSection={<IconTrash size={15} />}
                onClick={openDelete}
              >
                Delete account
              </Button>
            </Stack>
          </Paper>
        </Stack>
      </div>

      <Paper p="md" radius="md" withBorder>
        <Stack gap="md">
          <Group className={classes.panelHeader} justify="space-between">
            <div>
              <Text size="sm" fw={600}>Steam library import</Text>
              <Text size="xs" c="dimmed">
                Add matching Steam-owned games to your backlog while preserving your cross-platform library.
              </Text>
            </div>
            <Badge size="sm" variant="light" color="teal" leftSection={<IconBrandSteam size={12} />}>
              Steam
            </Badge>
          </Group>

          <Group align="flex-end" className={classes.importRow}>
            <TextInput
              className={classes.steamInput}
              label="Steam profile"
              placeholder="SteamID64 or steamcommunity.com profile URL"
              value={steamProfile}
              onChange={(event) => setSteamProfile(event.currentTarget.value)}
            />
            <Button
              color="ember"
              onClick={handleSteamImport}
              loading={importSteam.isPending}
              disabled={steamProfile.trim().length === 0}
              leftSection={<IconBrandSteam size={16} />}
            >
              Import library
            </Button>
          </Group>

          {steamResult && (
            <Alert color="teal" variant="light" className={classes.resultAlert}>
              <Stack gap="sm">
                <SimpleGrid cols={{ base: 2, sm: 4 }} spacing="xs">
                  <div className={classes.resultStat}>
                    <Text className={classes.resultValue}>{steamResult.added.length}</Text>
                    <Text className={classes.resultLabel}>Added</Text>
                  </div>
                  <div className={classes.resultStat}>
                    <Text className={classes.resultValue}>{steamResult.already_in_library.length}</Text>
                    <Text className={classes.resultLabel}>Existing</Text>
                  </div>
                  <div className={classes.resultStat}>
                    <Text className={classes.resultValue}>{steamResult.skipped_low_confidence.length}</Text>
                    <Text className={classes.resultLabel}>Skipped</Text>
                  </div>
                  <div className={classes.resultStat}>
                    <Text className={classes.resultValue}>{steamResult.unmatched.length}</Text>
                    <Text className={classes.resultLabel}>Unmatched</Text>
                  </div>
                </SimpleGrid>

                <Text size="xs" c="dimmed">
                  {steamResult.profile_name ?? steamResult.steam_id}
                </Text>

                <Accordion variant="contained" className={classes.resultAccordion}>
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
      </Paper>

      <Modal opened={deleteOpened} onClose={closeDelete} title="Delete account" centered size="sm">
        <Stack gap="md">
          <Group gap="sm" align="flex-start" wrap="nowrap" className={classes.deleteWarning}>
            <span className={classes.deleteModalIcon}>
              <IconAlertTriangle size={18} />
            </span>
            <div>
              <Text size="sm" fw={600}>This permanently removes your GameRec data.</Text>
              <Text size="xs" c="dimmed" mt={4}>
                Your profile, library, queue, recommendations, and saved account data will be deleted.
              </Text>
            </div>
          </Group>
          <Group justify="flex-end">
            <Button variant="default" onClick={closeDelete}>Cancel</Button>
            <Button color="red" onClick={handleDeleteAccount}>Delete account</Button>
          </Group>
        </Stack>
      </Modal>
    </Stack>
  );
}
