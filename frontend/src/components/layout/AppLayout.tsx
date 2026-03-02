import { AppShell } from '@mantine/core';
import { Outlet } from 'react-router';
import { AppNavbar } from './AppNavbar';
import { AppHeader } from './AppHeader';

/**
 * Root layout wrapping all authenticated pages.
 * TODO: Handle AppShell navbar collapse on mobile using useDisclosure()
 */
export function AppLayout() {
  return (
    <AppShell
      header={{ height: 60 }}
      navbar={{ width: 220, breakpoint: 'sm' }}
      padding="md"
    >
      <AppShell.Header>
        <AppHeader />
      </AppShell.Header>

      <AppShell.Navbar>
        <AppNavbar />
      </AppShell.Navbar>

      <AppShell.Main>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
