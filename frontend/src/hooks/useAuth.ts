import { useNavigate } from 'react-router';
import { authApi, type LoginCredentials, type RegisterPayload } from '../api/auth';
import { usersApi } from '../api/users';
import { useAuthStore } from '../store/authStore';

export function useAuth() {
  const navigate = useNavigate();
  const { user, setAuth, setUser, logout: clearStore, isAuthenticated } = useAuthStore();

  const login = async (credentials: LoginCredentials) => {
    // TODO: Call authApi.login(credentials)
    // TODO: Call usersApi.getMe() to get the full user object
    // TODO: Call setAuth(user, tokens.access_token, tokens.refresh_token)
    // TODO: Navigate to /recommendations (or previous location)
    throw new Error('Not implemented');
  };

  const register = async (payload: RegisterPayload) => {
    // TODO: Call authApi.register(payload)
    // TODO: Auto-login after registration or redirect to /login
    throw new Error('Not implemented');
  };

  const logout = async () => {
    // TODO: Call authApi.logout(refreshToken) to blacklist the token server-side
    // TODO: Call clearStore()
    // TODO: Navigate to /login
    throw new Error('Not implemented');
  };

  const updateProfile = async (updates: Parameters<typeof usersApi.updateMe>[0]) => {
    // TODO: Call usersApi.updateMe(updates)
    // TODO: Call setUser(updatedUser) to reflect changes in the store
    throw new Error('Not implemented');
  };

  return { user, isAuthenticated, login, register, logout, updateProfile };
}
