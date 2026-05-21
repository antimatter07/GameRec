import type { GameListItem } from './game';

export type LibraryStatus = 'playing' | 'completed' | 'backlog' | 'dropped' | 'wishlist' | 'replaying';
export type LibraryStatusFilter = LibraryStatus | 'all';
export type LibrarySort = 'added_at_desc' | 'added_at_asc' | 'status';

export interface LibraryEntry {
  id: number;
  game: GameListItem;
  status: LibraryStatus;
  rating: number | null;
  review: string | null;
  added_at: string;
  updated_at: string;
}

export interface LibraryEntryCreate {
  game_id: number;
  status?: LibraryStatus;
  rating?: number;
  review?: string;
}

export interface LibraryEntryUpdate {
  status?: LibraryStatus;
  rating?: number;
  review?: string;
}

export interface LibraryQueryParams {
  status?: LibraryStatusFilter;
  search?: string;
  sort?: LibrarySort;
}

export interface LibraryStats {
  total_games: number;
  by_status: Record<LibraryStatus, number>;
  avg_rating: number | null;
  top_genres: Array<{ genre: string; count: number }>;
}

export interface LibraryEntryUpdateOut {
  entry: LibraryEntry;
  queue_removed: boolean;
  next_game_candidate: LibraryEntry | null;
  queue_advanced: boolean;
  next_game: LibraryEntry | null;
}

export interface SteamImportGameResult {
  steam_app_id: number;
  steam_name: string;
  game: GameListItem | null;
  library_entry_id: number | null;
  match_confidence: number | null;
  reason: string | null;
}

export interface SteamImportResponse {
  steam_id: string;
  profile_name: string | null;
  added: SteamImportGameResult[];
  already_in_library: SteamImportGameResult[];
  skipped_low_confidence: SteamImportGameResult[];
  unmatched: SteamImportGameResult[];
}
