import { create } from 'zustand';

interface UIState {
  // TODO: Add more global UI state as needed (e.g. sidebar open/close, theme)
  colorScheme: 'light' | 'dark';
  toggleColorScheme: () => void;
}

export const useUIStore = create<UIState>((set, get) => ({
  colorScheme: 'dark',

  toggleColorScheme: () =>
    set({ colorScheme: get().colorScheme === 'dark' ? 'light' : 'dark' }),
}));
