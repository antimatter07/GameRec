import { Navigate, Outlet, createBrowserRouter } from 'react-router';
import { AppLayout } from './components/layout/AppLayout';
import { useAuthStore } from './store/authStore';

// Pages — lazy-loaded for better code splitting
import LoginPage          from './pages/auth/LoginPage';
import RegisterPage       from './pages/auth/RegisterPage';
import CatalogPage        from './pages/games/CatalogPage';
import GameDetailPage     from './pages/games/GameDetailPage';
import LibraryPage        from './pages/library/LibraryPage';
import BacklogPage        from './pages/library/BacklogPage';
import PlayQueuePage      from './pages/library/PlayQueuePage';
import RecommendationsPage from './pages/recommendations/RecommendationsPage';
import ProfilePage        from './pages/profile/ProfilePage';
import AdminDashboardPage from './pages/admin/AdminDashboardPage';

// TODO: Switch to lazy() + Suspense for code splitting:
//       const CatalogPage = lazy(() => import('./pages/games/CatalogPage'));

/** Redirects unauthenticated users to /login */
function ProtectedRoute() {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated());
  return isAuthenticated ? <Outlet /> : <Navigate to="/login" replace />;
}

/** Redirects non-admin users to /games */
function AdminRoute() {
  const user = useAuthStore((s) => s.user);
  return user?.role === 'admin' ? <Outlet /> : <Navigate to="/games" replace />;
}

export const router = createBrowserRouter([
  // --- Public routes ---
  { path: '/login',    element: <LoginPage /> },
  { path: '/register', element: <RegisterPage /> },

  // --- Authenticated routes ---
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { index: true,                    element: <Navigate to="/games" replace /> },
          { path: '/games',                 element: <CatalogPage /> },
          { path: '/games/:gameId',         element: <GameDetailPage /> },
          { path: '/library',               element: <LibraryPage /> },
          { path: '/library/backlog',       element: <BacklogPage /> },
          { path: '/library/queue',         element: <PlayQueuePage /> },
          { path: '/recommendations',       element: <RecommendationsPage /> },
          { path: '/profile',              element: <ProfilePage /> },

          // --- Admin only ---
          {
            element: <AdminRoute />,
            children: [
              { path: '/admin', element: <AdminDashboardPage /> },
            ],
          },

          // TODO: Add /recommendations/game-dna route (premium guard)
          // TODO: Add /recommendations/history route
          // TODO: Add 404 catch-all route
        ],
      },
    ],
  },
]);
