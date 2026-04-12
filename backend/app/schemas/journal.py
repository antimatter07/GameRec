from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.game import GameListOut


class SessionLogCreate(BaseModel):
    game_id:          int
    started_at:       datetime
    ended_at:         datetime | None = None
    duration_minutes: int | None      = Field(None, ge=1)
    notes:            str | None      = None
    is_milestone:     bool            = False
    milestone_label:  str | None      = None


class SessionLogUpdate(BaseModel):
    started_at:       datetime | None = None
    ended_at:         datetime | None = None
    duration_minutes: int | None      = Field(None, ge=1)
    notes:            str | None      = None
    is_milestone:     bool | None     = None
    milestone_label:  str | None      = None


class SessionLogOut(BaseModel):
    id:               int
    game_id:          int
    game:             GameListOut
    library_entry_id: int | None
    started_at:       datetime
    ended_at:         datetime | None
    duration_minutes: int | None
    notes:            str | None
    is_milestone:     bool
    milestone_label:  str | None
    created_at:       datetime
    updated_at:       datetime

    model_config = {"from_attributes": True}


class SessionLogListOut(BaseModel):
    total:   int
    results: list[SessionLogOut]


class TopGenreItem(BaseModel):
    genre: str
    hours: float


class JournalStats(BaseModel):
    total_hours_all_time:    float
    total_hours_this_month:  float
    sessions_this_month:     int
    games_played_this_month: int
    top_genres_this_month:   list[TopGenreItem]
    current_streak_days:     int
    longest_streak_days:     int
