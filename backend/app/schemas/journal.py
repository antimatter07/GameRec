from datetime import datetime

from pydantic import BaseModel, Field


# ─── Session Logs ─────────────────────────────────────────────────────────────

class SessionLogCreate(BaseModel):
    game_id:          int
    library_entry_id: int | None    = None
    started_at:       datetime
    ended_at:         datetime | None = None
    duration_minutes: int | None    = Field(None, ge=1)
    notes:            str | None    = None
    is_milestone:     bool          = False
    milestone_label:  str | None    = None
    emotions:         list[str] | None = None  # stored in future migration; ignored for now


class SessionLogUpdate(BaseModel):
    started_at:       datetime | None = None
    ended_at:         datetime | None = None
    duration_minutes: int | None      = Field(None, ge=1)
    notes:            str | None      = None
    is_milestone:     bool | None     = None
    milestone_label:  str | None      = None
    emotions:         list[str] | None = None  # ignored until emotions column exists


class SessionLogOut(BaseModel):
    id:               int
    user_id:          int
    game_id:          int
    library_entry_id: int | None
    started_at:       datetime
    ended_at:         datetime | None
    duration_minutes: int | None
    notes:            str | None
    is_milestone:     bool
    milestone_label:  str | None
    emotions:         list[str] | None
    created_at:       datetime
    # Joined / derived fields
    game_title:       str | None
    game_cover_url:   str | None
    game_genres:      list[str]

    model_config = {"from_attributes": False}


class PaginatedSessionsOut(BaseModel):
    items:    list[SessionLogOut]
    total:    int
    page:     int
    per_page: int
    has_next: bool


# ─── Stats ────────────────────────────────────────────────────────────────────

class TopGenreItem(BaseModel):
    genre: str
    hours: float


class DailyHoursItem(BaseModel):
    day:   str    # short weekday name: "Mon", "Tue", …
    hours: float


class JournalStats(BaseModel):
    total_hours_all_time:      float
    total_hours_this_month:    float
    total_hours_this_week:     float
    sessions_this_month:       int
    games_played_this_month:   int
    top_genres_this_month:     list[TopGenreItem]
    current_streak_days:       int
    longest_streak_days:       int
    # Weekly detail
    daily_hours_this_week:     list[DailyHoursItem]
    hours_change_pct_week:     float   # +/- vs previous 7-day window
    sessions_change_pct_month: float   # +/- vs previous calendar month
    # Library summary
    games_completed:           int
    games_in_backlog:          int
    games_playing:             int
    # Emotion fields (null until emotions backend is implemented)
    dominant_emotion_this_month: str | None
    emotion_coverage_pct:        float | None
