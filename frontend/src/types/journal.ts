// ─── Emotion types ────────────────────────────────────────────────────────────
// Note: Using const object + type union instead of enum due to erasableSyntaxOnly

export const EmotionType = {
  FRUSTRATED:   'frustrated',
  HAPPY:        'happy',
  SAD:          'sad',
  ANGRY:        'angry',
  RELAXED:      'relaxed',
  BORED:        'bored',
  PROUD:        'proud',
  CREEPED_OUT:  'creeped_out',
  DISAPPOINTED: 'disappointed',
} as const;

export type EmotionType = typeof EmotionType[keyof typeof EmotionType];

export const EMOTION_CONFIG: Record<EmotionType, { label: string; icon: string; color: string }> = {
  frustrated:   { label: 'Frustrated',   icon: 'IconMoodConfuzed', color: 'orange.6' },
  happy:        { label: 'Happy',         icon: 'IconMoodSmile',    color: 'yellow.5' },
  sad:          { label: 'Sad',           icon: 'IconMoodSad',      color: 'blue.4'   },
  angry:        { label: 'Angry',         icon: 'IconFlame',        color: 'red.6'    },
  relaxed:      { label: 'Relaxed',       icon: 'IconLeaf',         color: 'teal.5'   },
  bored:        { label: 'Bored',         icon: 'IconZzz',          color: 'gray.5'   },
  proud:        { label: 'Proud',         icon: 'IconTrophy',       color: 'yellow.7' },
  creeped_out:  { label: 'Creeped out',  icon: 'IconGhost',        color: 'grape.6'  },
  disappointed: { label: 'Disappointed', icon: 'IconMoodEmpty',    color: 'gray.6'   },
};

export const POSITIVE_EMOTIONS: EmotionType[] = ['happy', 'proud', 'relaxed'];
export const NEGATIVE_EMOTIONS: EmotionType[] = ['frustrated', 'angry', 'bored', 'disappointed', 'sad', 'creeped_out'];

// ─── Session Logs ─────────────────────────────────────────────────────────────

export interface SessionLogCreate {
  game_id:           number;
  library_entry_id?: number | null;
  ended_at?:         string | null;
  duration_minutes?: number | null;
  notes?:            string | null;
  is_milestone?:     boolean;
  milestone_label?:  string | null;
  emotions?:         EmotionType[] | null;
}

export interface SessionLogUpdate {
  ended_at?:         string | null;
  duration_minutes?: number | null;
  notes?:            string | null;
  is_milestone?:     boolean;
  milestone_label?:  string | null;
  emotions?:         EmotionType[] | null;
}

export interface SessionLog {
  id:               number;
  user_id:          number;
  game_id:          number;
  library_entry_id: number | null;
  started_at:       string;
  ended_at:         string | null;
  duration_minutes: number | null;
  notes:            string | null;
  is_milestone:     boolean;
  milestone_label:  string | null;
  emotions:         EmotionType[] | null;
  created_at:       string;
  // Joined fields
  game_title?:      string;
  game_cover_url?:  string | null;
  game_genres?:     string[];
}

// ─── Multi-Axis Ratings ───────────────────────────────────────────────────────

export interface MultiAxisRatingUpsert {
  story?:     number | null;
  gameplay?:  number | null;
  visuals?:   number | null;
  soundtrack?: number | null;
  overall?:   number | null;
}

export interface MultiAxisRating {
  id:               number;
  user_id:          number;
  game_id:          number;
  library_entry_id: number | null;
  story:            number | null;
  gameplay:         number | null;
  visuals:          number | null;
  soundtrack:       number | null;
  overall:          number | null;
  created_at:       string;
  updated_at:       string;
  game_title?:      string;
  game_cover_url?:  string | null;
}

// ─── Journal Stats ────────────────────────────────────────────────────────────

export interface GenreHours {
  genre: string;
  hours: number;
}

export interface DailyHours {
  day:   string;
  hours: number;
}

export interface JournalStats {
  total_hours_all_time:      number;
  total_hours_this_month:    number;
  total_hours_this_week:     number;
  sessions_this_month:       number;
  top_genres_this_month:     GenreHours[];
  games_played_this_month:   number;
  current_streak_days:       number;
  longest_streak_days:       number;
  daily_hours_this_week:     DailyHours[];
  hours_change_pct_week:     number;
  sessions_change_pct_month: number;
  games_completed:           number;
  games_in_backlog:          number;
  games_playing:             number;
  dominant_emotion_this_month: EmotionType | null;
  emotion_coverage_pct:        number | null;
}

// ─── Emotion Stats ────────────────────────────────────────────────────────────

export interface EmotionFrequencyItem {
  emotion:       EmotionType;
  session_count: number;
  percentage:    number;
}

export interface EmotionGameCorrelation {
  game_id:          number;
  game_title:       string;
  cover_url:        string | null;
  dominant_emotion: EmotionType;
  session_count:    number;
}

export interface EmotionGenreCorrelation {
  genre:            string;
  dominant_emotion: EmotionType;
  session_count:    number;
  emotion_breakdown: EmotionFrequencyItem[];
}

export interface EmotionMonthlyBucket {
  month:     string;
  frequency: EmotionFrequencyItem[];
}

export type EmotionStatsPeriod = '7d' | '30d' | '90d' | 'all';

export interface EmotionStats {
  period:                       string;
  total_sessions_with_emotions: number;
  total_sessions:               number;
  frequency:                    EmotionFrequencyItem[];
  most_common_emotion:          EmotionType | null;
  top_positive_game:            EmotionGameCorrelation | null;
  top_negative_game:            EmotionGameCorrelation | null;
  per_game:                     EmotionGameCorrelation[];
  per_genre:                    EmotionGenreCorrelation[];
  monthly_breakdown:            EmotionMonthlyBucket[];
}

// ─── Journal Feed ─────────────────────────────────────────────────────────────

export interface JournalFeedItem {
  type:       'session' | 'milestone';
  session:    SessionLog;
  date_group: string;
}

// ─── Paginated Response ───────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items:    T[];
  total:    number;
  page:     number;
  per_page: number;
  has_next: boolean;
}
