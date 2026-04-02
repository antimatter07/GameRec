import {
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
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';
import { usersApi } from '../../api/users';

export default function ProfilePage() {
  const user = useAuthStore((s) => s.user);
  const { updateProfile, logout } = useAuth();
  const [deleteOpened, { open: openDelete, close: closeDelete }] = useDisclosure(false);

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
