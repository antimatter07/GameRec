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

export interface QueueSuggestionItem {
  id: number;
  entry_id: number;
  original_position: number;
  suggested_position: number;
  reason: string;
  entry: LibraryEntry;
}

export interface QueueSuggestion {
  id: number;
  queue_fingerprint: string;
  status: 'pending' | 'ready' | 'failed';
  trigger_source: string;
  requested_at: string;
  generated_at: string | null;
  model_name: string | null;
  overall_explanation: string | null;
  error_detail: string | null;
  items: QueueSuggestionItem[];
}

export interface QueueSuggestionState {
  suggestion: QueueSuggestion | null;
  is_stale: boolean;
  is_generating: boolean;
  can_generate: boolean;
  can_adopt: boolean;
  detail: string | null;
}

export interface LibraryEntryUpdateOut {
  entry: LibraryEntry;
  queue_advanced: boolean;
  next_game: LibraryEntry | null;
}
