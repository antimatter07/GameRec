import '@mantine/core/styles.css';
import '@mantine/notifications/styles.css';

import { MantineProvider } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider } from 'react-router';

import { router } from './router';
import { useUIStore } from './store/uiStore';

// TODO: Customize the Mantine theme (colors, fonts, defaultRadius, etc.)
//       https://mantine.dev/theming/theme-object/
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
      <MantineProvider defaultColorScheme={colorScheme}>
        <Notifications position="top-right" />
        <RouterProvider router={router} />
      </MantineProvider>
    </QueryClientProvider>
  );
}
