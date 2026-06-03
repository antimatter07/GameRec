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

const ember: MantineColorsTuple = [
  '#fff1ec',
  '#ffe1d6',
  '#ffc4b2',
  '#f99a7e',
  '#e97d61',
  '#d4674d',
  '#b9543e',
  '#944331',
  '#733629',
  '#552922',
];

const theme = createTheme({
  primaryColor: 'ember',
  colors: {
    ember,
    violet: ember,
  },

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
        shadow: 'none',
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
          fontWeight: '600',
          fontSize: '0.8rem',
        },
      },
    },
    Modal: {
      defaultProps: {
        overlayProps: { backgroundOpacity: 0.7, blur: 2 },
        radius: 'md',
      },
      styles: {
        content: {
          background: 'var(--mantine-color-dark-7)',
          border: '1px solid var(--mantine-color-dark-4)',
        },
        header: {
          background: 'var(--mantine-color-dark-7)',
          borderBottom: '1px solid rgba(255, 255, 255, 0.06)',
        },
        title: {
          fontSize: '0.95rem',
          fontWeight: 700,
        },
      },
    },
    TextInput: {
      defaultProps: {
        radius: 'sm',
      },
    },
    PasswordInput: {
      defaultProps: {
        radius: 'sm',
      },
    },
    Select: {
      defaultProps: {
        radius: 'sm',
      },
    },
    Textarea: {
      defaultProps: {
        radius: 'sm',
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

const PUBLIC_PATHS = new Set(['/', '/login', '/register']);

function isPublicPath(pathname: string) {
  return PUBLIC_PATHS.has(pathname);
}

function AuthBootstrap() {
  const [isBootstrapping, setIsBootstrapping] = useState(true);
  const hasStarted = useRef(false);

  useEffect(() => {
    if (hasStarted.current) return;
    hasStarted.current = true;

    if (isPublicPath(window.location.pathname)) {
      setIsBootstrapping(false);
      return;
    }

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
