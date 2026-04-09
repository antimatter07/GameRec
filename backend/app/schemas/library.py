from datetime import datetime

from pydantic import BaseModel, Field

from app.models.library import LibraryStatus
from app.schemas.game import GameListOut


class LibraryEntryCreate(BaseModel):
    game_id: int
    status:  LibraryStatus        = LibraryStatus.BACKLOG
    rating:  float | None         = Field(None, ge=1, le=5)
    review:  str | None           = None


class LibraryEntryUpdate(BaseModel):
    status: LibraryStatus | None  = None
    rating: float | None          = Field(None, ge=1, le=5)
    review: str | None            = None


class LibraryEntryOut(BaseModel):
    id:         int
    game:       GameListOut
    status:     LibraryStatus
    rating:     float | None
    review:     str | None
    added_at:   datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class LibraryStats(BaseModel):
    total_games: int
    by_status:   dict[str, int]   # {"playing": 3, "completed": 10, ...}
    avg_rating:  float | None
    top_genres:  list[dict]       # [{"genre": "Action", "count": 5}, ...]
    # TODO: Consider adding total_playtime if you add a hours_played field to LibraryEntry


class PrioritizedBacklogItem(BaseModel):
    entry_id:       int
    game:           GameListOut
    playtime_hours: float | None  # hltb_main_hours if set, else RAWG playtime, else None
    taste_score:    float | None  # cosine score from latest rec batch; None if no batch exists
    priority_score: float         # composite: 0.5*taste + 0.3*staleness + 0.2*playtime
    stale_months:   int | None    # months since LibraryEntry.updated_at

    model_config = {"from_attributes": True}


class PrioritizedBacklogOut(BaseModel):
    total:   int
    results: list[PrioritizedBacklogItem]
