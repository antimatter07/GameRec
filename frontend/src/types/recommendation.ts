import type { GameListItem } from './game';

export interface RecommendationItem {
  id: number;
  rank: number;
  score: number;          // cosine similarity 0–1 (display as match %)
  game: GameListItem;
  explanation: string | null;   // null for basic users
  confidence: number | null;    // null for basic users
  because_you_liked?: string[] | null;
}

export interface Recommendation {
  id: number;
  generated_at: string;
  kind: 'cosine' | 'ai_picks';
  status: 'pending' | 'ready' | 'failed';
  summary: string | null;
  model_name: string | null;
  items: RecommendationItem[];
}

export interface AIPicksState {
  recommendation: Recommendation | null;
  is_stale: boolean;
  can_refresh: boolean;
  cache_hours: number;
  detail: string | null;
}

export interface FeedbackCreate {
  item_id: number;
  is_helpful: boolean;
}

/** Premium-only: taste profile analysis */
export interface GameDNA {
  top_genres: Array<{ name: string; weight: number }>;
  top_tags: Array<{ name: string; weight: number }>;
  preferred_era: string | null;
  description: string;        // LLM-generated paragraph
  confidence: number | null;
}
