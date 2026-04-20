import { Avatar, Group, Menu, Text } from '@mantine/core';
import { IconLogout, IconUser } from '@tabler/icons-react';
import { Link } from 'react-router';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';

export function AppHeader() {
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();

  const displayName = user?.display_name ?? user?.email ?? '';
  const avatarLabel = displayName ? displayName.charAt(0).toUpperCase() : '?';

  return (
    <Group h="100%" px="md" justify="space-between">
      <Text fw={700} size="lg">
        🎮 GameRec
      </Text>

      <Group>
        <Menu position="bottom-end" withArrow>
          <Menu.Target>
            <Group gap="xs" style={{ cursor: 'pointer' }}>
              <Avatar radius="xl" size="sm" color="blue">
                {avatarLabel}
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
