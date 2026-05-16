import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

import { GoogleOAuthProvider } from '@react-oauth/google';
import { useEffect, useRef, useState } from 'react';
import { Center, Loader, MantineProvider, createTheme, type MantineColorsTuple } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router';

import { usersApi } from './api/users';
import { router } from './router';
import { useAuthStore } from './store/authStore';
import { useUIStore } from './store/uiStore';

// ─── Custom violet ramp ────────────────────────────────────────────────────────
const violet: MantineColorsTuple = [
  '#f3f0ff',
  '#e5dbff',
  '#d0bfff',
  '#b197fc',
  '#9d84fd',
  '#7c5cfc',
  '#7048e8',
  '#6741d9',
  '#5f3dc4',
  '#5235ab',
];

// ─── Gamematch theme ──────────────────────────────────────────────────────────
const theme = createTheme({
  primaryColor: 'violet',
  colors: { violet },

  fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
  fontFamilyMonospace: "'Space Mono', 'JetBrains Mono', monospace",
  headings: {
    fontFamily: "'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif",
    fontWeight: '700',
  },

  radius: {
    xs: '4px',
    sm: '8px',
    md: '12px',
    lg: '16px',
    xl: '24px',
  },
  defaultRadius: 'md',

  components: {
    Paper: {
      defaultProps: {
        bg: 'var(--mantine-color-dark-7)',
      },
    },
    Button: {
      defaultProps: {
        radius: 'sm',
      },
    },
    Badge: {
      defaultProps: {
        radius: 'sm',
      },
    },
    Tabs: {
      styles: {
        tab: {
          fontWeight: '500',
          fontSize: '0.8rem',
        },
      },
    },
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
    },
  },
});

function AuthBootstrap() {
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    async function bootstrap() {
      const { setUser, logout } = useAuthStore.getState();
      try {
        const me = await usersApi.getMe();
        setUser(me);
      } catch {
        logout();
      } finally {
        setIsBootstrapping(false);
      }
    }

    void bootstrap();
  }, []);

  if (isBootstrapping) {
    return (
      <Center h="100vh">
        <Loader />
      </Center>
    );
  }

  return <RouterProvider router={router} />;
}

export default function App() {
  const colorScheme = useUIStore((s) => s.colorScheme);

  const googleClientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;

  const inner = (
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme} defaultColorScheme={colorScheme}>
        <Notifications position="top-right" />
        <AuthBootstrap />
      </MantineProvider>
    </QueryClientProvider>
  );

  return googleClientId ? (
    <GoogleOAuthProvider clientId={googleClientId}>{inner}</GoogleOAuthProvider>
  ) : (
    inner
  );
}
