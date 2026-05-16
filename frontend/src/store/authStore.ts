import { create } from 'zustand';
import type { User } from '../types/user';

interface AuthState {
  user: User | null;
  setUser: (user: User | null) => void;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()((set, get) => ({
  user: null,

  setUser: (user) => set({ user }),

  logout: () => set({ user: null }),

  isAuthenticated: () => get().user !== null,
}));
