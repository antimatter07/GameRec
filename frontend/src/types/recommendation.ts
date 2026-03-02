import type { GameListItem } from './game';

export interface RecommendationItem {
  rank: number;
  score: number;          // cosine similarity 0–1 (display as match %)
  game: GameListItem;
  explanation: string | null;   // null for basic users
  confidence: number | null;    // null for basic users
}

export interface Recommendation {
  id: number;
  generated_at: string;
  items: RecommendationItem[];
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
