import type { GameListItem } from './game';

export interface SessionLog {
  id:               number;
  game_id:          number;
  game:             GameListItem;
  library_entry_id: number | null;
  started_at:       string;
  ended_at:         string | null;
  duration_minutes: number | null;
  notes:            string | null;
  is_milestone:     boolean;
  milestone_label:  string | null;
  created_at:       string;
  updated_at:       string;
}

export interface SessionLogCreate {
  game_id:          number;
  started_at:       string;
  ended_at?:        string;
  duration_minutes?: number;
  notes?:           string;
  is_milestone?:    boolean;
  milestone_label?: string;
}

export interface SessionLogUpdate {
  started_at?:      string;
  ended_at?:        string;
  duration_minutes?: number;
  notes?:           string;
  is_milestone?:    boolean;
  milestone_label?: string;
}

export interface SessionLogListOut {
  total:   number;
  results: SessionLog[];
}

export interface TopGenreItem {
  genre: string;
  hours: number;
}

export interface JournalStats {
  total_hours_all_time:    number;
  total_hours_this_month:  number;
  sessions_this_month:     number;
  games_played_this_month: number;
  top_genres_this_month:   TopGenreItem[];
  current_streak_days:     number;
  longest_streak_days:     number;
}
