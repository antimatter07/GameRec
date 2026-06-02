import type { ReactNode } from 'react';
import { Avatar, Group, Menu, Text, UnstyledButton } from '@mantine/core';
import { IconDeviceGamepad2, IconLogout, IconUser } from '@tabler/icons-react';
import { Link } from 'react-router';
import { useAuth } from '../../hooks/useAuth';
import { useAuthStore } from '../../store/authStore';
import classes from './AppLayout.module.css';

export function AppHeader({ mobileToggle }: { mobileToggle?: ReactNode }) {
  const user = useAuthStore((s) => s.user);
  const { logout } = useAuth();

  const displayName = user?.display_name ?? user?.email ?? '';
  const avatarLabel = displayName ? displayName.charAt(0).toUpperCase() : '?';

  return (
    <Group h="100%" justify="space-between" className={classes.headerInner} wrap="nowrap">
      <Group gap="sm" wrap="nowrap" miw={0}>
        {mobileToggle}
        <Link to="/games" className={classes.brandLink}>
          <span className={classes.brandMark}>
            <IconDeviceGamepad2 size={19} stroke={1.9} />
          </span>
          <span className={classes.brandText}>
            <span className={classes.brandName}>GameRec</span>
            
          </span>
        </Link>
      </Group>

      <Group wrap="nowrap">
        <Menu position="bottom-end" withArrow width={190}>
          <Menu.Target>
            <UnstyledButton className={classes.userTarget}>
              <Group gap="xs" wrap="nowrap">
                <Avatar radius="sm" size="sm" color="ember">
                  {avatarLabel}
                </Avatar>
                <Text size="sm" truncate className={classes.userName}>{displayName}</Text>
              </Group>
            </UnstyledButton>
          </Menu.Target>

          <Menu.Dropdown>
            <Menu.Item leftSection={<IconUser size={16} />} component={Link} to="/profile">
              Profile
            </Menu.Item>
            <Menu.Divider />
            <Menu.Item
              leftSection={<IconLogout size={16} />}
              color="red.4"
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
