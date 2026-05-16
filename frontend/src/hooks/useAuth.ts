import { useNavigate } from 'react-router';
import { authApi, type LoginCredentials, type RegisterPayload } from '../api/auth';
import { usersApi } from '../api/users';
import { useAuthStore } from '../store/authStore';

export function useAuth() {
  const navigate = useNavigate();
  const { user, setUser, logout: clearStore, isAuthenticated } = useAuthStore();

  const login = async (credentials: LoginCredentials) => {
    const authenticatedUser = await authApi.login(credentials);
    setUser(authenticatedUser);
    navigate('/games');
  };

  const register = async (payload: RegisterPayload) => {
    await authApi.register(payload);
    // Auto-login after registration
    await login({ username: payload.email, password: payload.password });
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } catch {
      // Ignore — clear locally regardless
    }
    clearStore();
    navigate('/login');
  };

  const updateProfile = async (updates: Parameters<typeof usersApi.updateMe>[0]) => {
    const updatedUser = await usersApi.updateMe(updates);
    setUser(updatedUser);
  };

  const loginWithGoogle = async (idToken: string) => {
    const authenticatedUser = await authApi.googleLogin(idToken);
    setUser(authenticatedUser);
    navigate('/games');
  };

  return { user, isAuthenticated, login, loginWithGoogle, register, logout, updateProfile };
}
