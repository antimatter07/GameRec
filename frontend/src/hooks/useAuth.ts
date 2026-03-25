import { useNavigate } from 'react-router';
import { authApi, type LoginCredentials, type RegisterPayload } from '../api/auth';
import { usersApi } from '../api/users';
import { useAuthStore } from '../store/authStore';

export function useAuth() {
  const navigate = useNavigate();
  const { user, setAuth, setUser, logout: clearStore, isAuthenticated } = useAuthStore();

  const login = async (credentials: LoginCredentials) => {
    const tokens = await authApi.login(credentials);
    // Temporarily set the access token so the /users/me call is authenticated
    useAuthStore.getState().setAccessToken(tokens.access_token);
    const me = await usersApi.getMe();
    setAuth(me, tokens.access_token, tokens.refresh_token);
    navigate('/games');
  };

  const register = async (payload: RegisterPayload) => {
    await authApi.register(payload);
    // Auto-login after registration
    await login({ username: payload.email, password: payload.password });
  };

  const logout = async () => {
    const { refreshToken } = useAuthStore.getState();
    if (refreshToken) {
      try {
        await authApi.logout(refreshToken);
      } catch {
        // Ignore — clear locally regardless
      }
    }
    clearStore();
    navigate('/login');
  };

  const updateProfile = async (updates: Parameters<typeof usersApi.updateMe>[0]) => {
    const updatedUser = await usersApi.updateMe(updates);
    setUser(updatedUser);
  };

  return { user, isAuthenticated, login, register, logout, updateProfile };
}
