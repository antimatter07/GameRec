import { NavLink, Stack } from '@mantine/core';
import { NavLink as RouterNavLink } from 'react-router';
import { useAuthStore } from '../../store/authStore';

const NAV_ITEMS = [
  { label: 'Catalog',         to: '/games'           },
  { label: 'My Library',      to: '/library'         },
  { label: 'Recommendations', to: '/recommendations'  },
  { label: 'Profile',         to: '/profile'         },
];

const PREMIUM_ITEMS = [
  { label: 'Game DNA',        to: '/recommendations/game-dna' },
];

const ADMIN_ITEMS = [
  { label: 'Admin Dashboard', to: '/admin' },
];

/**
 * Left sidebar navigation.
 * TODO: Add icons to each nav item using @tabler/icons-react
 * TODO: Highlight active route using NavLink's "active" prop
 */
export function AppNavbar() {
  const user = useAuthStore((s) => s.user);

  const items = [
    ...NAV_ITEMS,
    ...(user?.role === 'premium' || user?.role === 'admin' ? PREMIUM_ITEMS : []),
    ...(user?.role === 'admin' ? ADMIN_ITEMS : []),
  ];

  return (
    <Stack p="sm" gap="xs">
      {items.map((item) => (
        <RouterNavLink key={item.to} to={item.to}>
          {({ isActive }) => (
            <NavLink label={item.label} active={isActive} />
          )}
        </RouterNavLink>
      ))}
    </Stack>
  );
}
