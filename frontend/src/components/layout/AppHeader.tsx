import { ActionIcon, Avatar, Group, Menu, Text, useMantineColorScheme } from '@mantine/core';
import { IconLogout, IconMoon, IconSun, IconUser } from '@tabler/icons-react';
import { Link } from 'react-router';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';

export function AppHeader() {
  const { colorScheme, toggleColorScheme } = useMantineColorScheme();
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();

  const displayName = user?.display_name ?? user?.email ?? '';

  return (
    <Group h="100%" px="md" justify="space-between">
      <Text fw={700} size="lg">
        🎮 GameRec
      </Text>

      <Group>
        <ActionIcon variant="default" onClick={toggleColorScheme} size="lg">
          {colorScheme === 'dark' ? <IconSun size={18} /> : <IconMoon size={18} />}
        </ActionIcon>

        <Menu position="bottom-end" withArrow>
          <Menu.Target>
            <Group gap="xs" style={{ cursor: 'pointer' }}>
              <Avatar radius="xl" size="sm" color="blue">
                {displayName.charAt(0).toUpperCase()}
              </Avatar>
              <Text size="sm">{displayName}</Text>
            </Group>
          </Menu.Target>

          <Menu.Dropdown>
            <Menu.Item leftSection={<IconUser size={16} />} component={Link} to="/profile">
              Profile
            </Menu.Item>
            <Menu.Divider />
            <Menu.Item
              leftSection={<IconLogout size={16} />}
              color="red"
              onClick={logout}
            >
              Log out
            </Menu.Item>
          </Menu.Dropdown>
        </Menu>
      </Group>
    </Group>
  );
}
