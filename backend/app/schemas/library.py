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
