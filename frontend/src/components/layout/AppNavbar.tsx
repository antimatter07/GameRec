import { NavLink, Stack } from '@mantine/core';
import { NavLink as RouterNavLink } from 'react-router';
import {
  IconCompass,
  IconBooks,
  IconNotebook,
  IconStars,
  IconUser,
  IconLayoutDashboard,
  IconDna,
} from '@tabler/icons-react';
import { useAuthStore } from '../../store/authStore';

const NAV_ITEMS = [
  { label: 'Catalog',         to: '/games',           icon: IconCompass       },
  { label: 'My Library',      to: '/library',         icon: IconBooks         },
  { label: 'Journal',         to: '/journal',         icon: IconNotebook      },
  { label: 'Recommendations', to: '/recommendations', icon: IconStars         },
  { label: 'Profile',         to: '/profile',         icon: IconUser          },
];

const PREMIUM_ITEMS = [
  { label: 'Game DNA', to: '/recommendations/game-dna', icon: IconDna },
];

const ADMIN_ITEMS = [
  { label: 'Admin Dashboard', to: '/admin', icon: IconLayoutDashboard },
];

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
            <NavLink
              label={item.label}
              active={isActive}
              leftSection={<item.icon size={18} />}
            />
          )}
        </RouterNavLink>
      ))}
    </Stack>
  );
}
