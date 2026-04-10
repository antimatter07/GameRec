import type { LibraryEntry } from './library';

export interface PlayQueueEntry {
  id: number;
  entry_id: number;
  position: number;
  added_at: string;
  entry: LibraryEntry;
}

export interface PlayQueue {
  total: number;
  entries: PlayQueueEntry[];
}

export interface LibraryEntryUpdateOut {
  entry: LibraryEntry;
  queue_advanced: boolean;
  next_game: LibraryEntry | null;
}
