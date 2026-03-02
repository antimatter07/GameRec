export type UserRole = 'basic' | 'premium' | 'admin';

export interface User {
  id: number;
  email: string;
  display_name: string | null;
  avatar_url: string | null;
  bio: string | null;
  role: UserRole;
  created_at: string;
}

export interface UserUpdate {
  display_name?: string;
  avatar_url?: string;
  bio?: string;
}

/** Admin-only extended view */
export interface UserAdminView extends User {
  is_active: boolean;
  updated_at: string;
}
