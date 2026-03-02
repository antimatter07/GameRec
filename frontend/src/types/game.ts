export interface Genre {
  id: number;
  name: string;
  slug: string;
}

export interface Platform {
  id: number;
  name: string;
  slug: string;
}

export interface Tag {
  id: number;
  name: string;
  slug: string;
}

export interface Screenshot {
  id: number;
  image: string;
}

/** Lightweight — used in lists and catalog */
export interface GameListItem {
  id: number;
  name: string;
  slug: string;
  released: string | null;
  background_image: string | null;
  rating: number | null;
  genres: Genre[];
  platforms: Platform[];
}

/** Full detail — used on the game detail page */
export interface Game extends GameListItem {
  rawg_id: number;
  description: string | null;
  ratings_count: number;
  metacritic: number | null;
  tags: Tag[];
  screenshots: Screenshot[];
}

export interface PaginatedGames {
  total: number;
  page: number;
  page_size: number;
  results: GameListItem[];
}

export interface GameFilters {
  search?: string;
  genre?: string;
  platform?: string;
  year?: number;
  min_rating?: number;
}
