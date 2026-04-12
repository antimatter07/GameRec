import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';
import '@mantine/dates/styles.css';

import { MantineProvider, createTheme } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router';

import { router } from './router';
import { useUIStore } from './store/uiStore';

const theme = createTheme({
  fontFamily: 'Inter, sans-serif',
  fontFamilyMonospace: 'monospace',
  headings: {
    fontFamily: 'Space Grotesk, sans-serif',
  },
});

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      // TODO: Configure global staleTime, gcTime defaults here
    },
  },
});

export default function App() {
  const colorScheme = useUIStore((s) => s.colorScheme);

  return (
    <QueryClientProvider client={queryClient}>
      <MantineProvider theme={theme} defaultColorScheme={colorScheme}>
        <Notifications position="top-right" />
        <RouterProvider router={router} />
      </MantineProvider>
    </QueryClientProvider>
  );
}
