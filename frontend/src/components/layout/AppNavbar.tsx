import { Divider, NavLink, Stack } from '@mantine/core';
import { NavLink as RouterNavLink } from 'react-router';
import {
  IconCompass,
  IconBooks,
  IconListNumbers,
  IconNotebook,
  IconSparkles,
  IconStars,
  IconUser,
  IconLayoutDashboard,
  IconDna,
} from '@tabler/icons-react';
import { useAuthStore } from '../../store/authStore';
import classes from './AppLayout.module.css';

const NAV_ITEMS = [
  { label: 'Catalog',         to: '/games',           icon: IconCompass       },
  { label: 'My Library',      to: '/library',         icon: IconBooks         },
  { label: 'Queue',           to: '/queue',           icon: IconListNumbers   },
  { label: 'Journal',         to: '/journal',         icon: IconNotebook      },
  { label: 'Recommendations', to: '/recommendations', icon: IconStars         },
  { label: 'AI Picks',        to: '/recommendations/ai-picks', icon: IconSparkles },
  { label: 'Profile',         to: '/profile',         icon: IconUser          },
];

const PREMIUM_ITEMS = [
  { label: 'Game DNA', to: '/recommendations/game-dna', icon: IconDna },
];

const ADMIN_ITEMS = [
  { label: 'Admin Dashboard', to: '/admin', icon: IconLayoutDashboard },
];

export function AppNavbar({ onNavigate }: { onNavigate?: () => void }) {
  const user = useAuthStore((s) => s.user);

  const showPremium = user?.role === 'premium' || user?.role === 'admin';
  const showAdmin = user?.role === 'admin';

  return (
    <Stack gap={4} className={classes.navbarStack}>
      {NAV_ITEMS.map((item) => (
        <RouterNavLink key={item.to} to={item.to} className={classes.navAnchor} onClick={onNavigate}>
          {({ isActive }) => (
            <NavLink
              className={classes.navItem}
              label={item.label}
              active={isActive}
              leftSection={<item.icon size={18} />}
            />
          )}
        </RouterNavLink>
      ))}

      {showPremium && (
        <>
          <Divider my={6} color="dark.4" />
          <div className={classes.navSection}>Premium</div>
          {PREMIUM_ITEMS.map((item) => (
            <RouterNavLink key={item.to} to={item.to} className={classes.navAnchor} onClick={onNavigate}>
              {({ isActive }) => (
                <NavLink
                  className={classes.navItem}
                  label={item.label}
                  active={isActive}
                  leftSection={<item.icon size={18} />}
                />
              )}
            </RouterNavLink>
          ))}
        </>
      )}

      {showAdmin && (
        <>
          <Divider my={6} color="dark.4" />
          <div className={classes.navSection}>Admin</div>
          {ADMIN_ITEMS.map((item) => (
            <RouterNavLink key={item.to} to={item.to} className={classes.navAnchor} onClick={onNavigate}>
              {({ isActive }) => (
                <NavLink
                  className={classes.navItem}
                  label={item.label}
                  active={isActive}
                  leftSection={<item.icon size={18} />}
                />
              )}
            </RouterNavLink>
          ))}
        </>
      )}
    </Stack>
  );
}
