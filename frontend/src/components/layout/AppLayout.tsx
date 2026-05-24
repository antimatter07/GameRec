import { AppShell, Burger } from '@mantine/core';
import { useDisclosure } from '@mantine/hooks';
import { Outlet } from 'react-router';
import { AppNavbar } from './AppNavbar';
import { AppHeader } from './AppHeader';
import classes from './AppLayout.module.css';

export function AppLayout() {
  const [opened, { toggle, close }] = useDisclosure(false);

  return (
    <AppShell
      className={classes.shell}
      header={{ height: 60 }}
      navbar={{ width: 236, breakpoint: 'sm', collapsed: { mobile: !opened } }}
      padding={0}
    >
      <AppShell.Header className={classes.header}>
        <AppHeader
          mobileToggle={<Burger opened={opened} onClick={toggle} hiddenFrom="sm" size="sm" aria-label="Toggle navigation" />}
        />
      </AppShell.Header>

      <AppShell.Navbar className={classes.navbar}>
        <AppNavbar onNavigate={close} />
      </AppShell.Navbar>

      <AppShell.Main className={classes.main}>
        <Outlet />
      </AppShell.Main>
    </AppShell>
  );
}
