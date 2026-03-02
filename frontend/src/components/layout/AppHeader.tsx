import { ActionIcon, Group, Text, useMantineColorScheme } from '@mantine/core';
import { IconMoon, IconSun } from '@tabler/icons-react';
import { useAuthStore } from '../../store/authStore';

/**
 * Top header bar.
 * TODO: Install @tabler/icons-react: npm install @tabler/icons-react
 * TODO: Add Spotlight search trigger (Mantine Spotlight) for quick game search
 * TODO: Add user avatar / dropdown menu linking to profile and logout
 */
export function AppHeader() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const user = useAuthStore((s) => s.user);

  return (
    <Group h="100%" px="md" justify="space-between">
      <Text fw={700} size="lg">
        🎮 GameRec
      </Text>

      <Group>
        {/* TODO: Replace with Mantine Spotlight trigger for game search */}

        <ActionIcon variant="default" onClick={toggleColorScheme} size="lg">
          {colorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
        </ActionIcon>

        {/* TODO: Add Avatar + Menu with Profile, Settings, Logout links */}
        <Text size="sm" c="dimmed">
          {user?.display_name ?? user?.email}
        </Text>
      </Group>
    </Group>
  );
}
