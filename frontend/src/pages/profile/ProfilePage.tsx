import { Avatar, Button, Group, Stack, Text, TextInput, Textarea, Title } from '@mantine/core';
import { useForm } from '@mantine/form';
import { useAuthStore } from '../../store/authStore';
import { useAuth } from '../../hooks/useAuth';

/**
 * User profile page.
 * TODO: Add avatar upload (Mantine Dropzone → upload to Supabase Storage or S3)
 * TODO: Add "Request Premium Access" button (calls usersApi.requestPremium())
 *       — show only for basic users, with confirmation modal
 * TODO: Add "Delete Account" with a confirmation modal (useModals)
 * TODO: Show current role badge
 */
export default function ProfilePage() {
  const user        = useAuthStore((s) => s.user);
  const { updateProfile } = useAuth();

  const form = useForm({
    initialValues: {
      display_name: user?.display_name ?? '',
      bio:          user?.bio          ?? '',
      avatar_url:   user?.avatar_url   ?? '',
    },
  });

  const handleSubmit = form.onSubmit(async (values) => {
    // TODO: Call updateProfile(values)
    // TODO: Show success notification
  });

  if (!user) return null;

  return (
    <Stack gap="lg" maw={600}>
      <Title order={2}>Profile</Title>

      <Group>
        <Avatar src={user.avatar_url ?? undefined} size={80} radius="xl" />
        <Stack gap={4}>
          <Text fw={600}>{user.display_name ?? user.email}</Text>
          <Text size="sm" c="dimmed">{user.email}</Text>
          <Text size="xs" tt="uppercase" c="dimmed">{user.role}</Text>
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

      {/* TODO: "Request Premium Access" section for basic users */}
      {/* TODO: "Danger Zone" section with Delete Account */}
    </Stack>
  );
}
