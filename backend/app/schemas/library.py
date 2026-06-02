from datetime import datetime

from pydantic import BaseModel, Field

from app.models.library import LibraryStatus
from app.schemas.game import GameListOut


class LibraryEntryCreate(BaseModel):
    """Request schema for adding a game to a user library."""
    game_id: int
    status:  LibraryStatus        = LibraryStatus.WISHLIST
    rating:  float | None         = Field(None, ge=1, le=5)
    review:  str | None           = None


class LibraryEntryUpdate(BaseModel):
    """Request schema for changing library status, rating, or review fields."""
    status: LibraryStatus | None  = None
    rating: float | None          = Field(None, ge=1, le=5)
    review: str | None            = None


class LibraryEntryOut(BaseModel):
    """Response schema for a library entry with nested game details."""
    id:         int
    game:       GameListOut
    status:     LibraryStatus
    rating:     float | None
    review:     str | None
    added_at:   datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class PaginatedLibraryEntries(BaseModel):
    """Paginated response schema for user library entries."""
    total:     int
    page:      int
    page_size: int
    results:   list[LibraryEntryOut]


class LibraryStats(BaseModel):
    """Response schema containing aggregate library counts and rating statistics."""
    total_games: int
    by_status:   dict[str, int]   # {"playing": 3, "completed": 10, ...}
    avg_rating:  float | None
    top_genres:  list[dict]       # [{"genre": "Action", "count": 5}, ...]
    # TODO: Consider adding total_playtime if you add a hours_played field to LibraryEntry


class PrioritizedBacklogItem(BaseModel):
    """Response schema for one scored backlog recommendation item."""
    entry_id:       int
    game:           GameListOut
    playtime_hours: float | None  # hltb_main_hours if set, else RAWG playtime, else None
    taste_score:    float | None  # cosine score from latest rec batch; None if no batch exists
    priority_score: float         # composite: 0.5*taste + 0.3*staleness + 0.2*playtime
    stale_months:   int | None    # months since LibraryEntry.updated_at

    model_config = {"from_attributes": True}


class PrioritizedBacklogOut(BaseModel):
    """Response schema for prioritized backlog results."""
    total:   int
    results: list[PrioritizedBacklogItem]


class LibraryEntryUpdateOut(BaseModel):
    """Response schema for library updates and any queue side effects."""
    entry:         LibraryEntryOut
    queue_removed: bool               = False
    next_game_candidate: LibraryEntryOut | None = None
    # Backwards-compatible fields for older clients during the transition away
    # from auto-advancing the queue.
    queue_advanced: bool               = False
    next_game:      LibraryEntryOut | None = None


class SteamImportRequest(BaseModel):
    """Request schema for importing a public Steam library."""
    steam_profile: str = Field(..., min_length=1, max_length=255)


class SteamImportGameResult(BaseModel):
    """Response schema for one Steam import match or skipped game."""
    steam_app_id: int
    steam_name: str
    game: GameListOut | None = None
    library_entry_id: int | None = None
    match_confidence: float | None = None
    reason: str | None = None


class SteamImportResponse(BaseModel):
    """Response schema summarizing a Steam library import run."""
    steam_id: str
    profile_name: str | None = None
    added: list[SteamImportGameResult]
    already_in_library: list[SteamImportGameResult]
    skipped_low_confidence: list[SteamImportGameResult]
    unmatched: list[SteamImportGameResult]
