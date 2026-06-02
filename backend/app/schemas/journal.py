from datetime import datetime

from pydantic import BaseModel, Field

JournalNoteKind = str
JournalNoteStatus = str


# ─── Session Logs ─────────────────────────────────────────────────────────────

class SessionLogCreate(BaseModel):
    """Request schema for creating a journal play session."""
    game_id:          int
    library_entry_id: int | None       = None
    ended_at:         datetime | None  = None
    duration_minutes: int | None       = Field(None, ge=1)
    notes:            str | None       = None
    is_milestone:     bool             = False
    milestone_label:  str | None       = None
    emotions:         list[str] | None = None
    follow_up_note_title: str | None   = Field(None, min_length=1, max_length=255)


class SessionLogUpdate(BaseModel):
    """Request schema for updating journal play session fields."""
    ended_at:         datetime | None  = None
    duration_minutes: int | None       = Field(None, ge=1)
    notes:            str | None       = None
    is_milestone:     bool | None      = None
    milestone_label:  str | None       = None
    emotions:         list[str] | None = None


class SessionLogOut(BaseModel):
    """Response schema for a journal play session with derived game fields."""
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
    """Paginated response schema for journal sessions."""
    items:    list[SessionLogOut]
    total:    int
    page:     int
    per_page: int
    has_next: bool


# ─── Scratchpad Notes ─────────────────────────────────────────────────────────

class PlaythroughNoteCreate(BaseModel):
    """Request schema for creating a playthrough note."""
    game_id:             int
    library_entry_id:    int | None = None
    session_log_id:      int | None = None
    kind:                JournalNoteKind = "note"
    title:               str = Field(..., min_length=1, max_length=255)
    body:                str | None = None
    status:              JournalNoteStatus = "open"
    pinned:              bool = False
    remind_next_session: bool = False


class PlaythroughNoteUpdate(BaseModel):
    """Request schema for updating a playthrough note."""
    kind:                JournalNoteKind | None = None
    title:               str | None = Field(None, min_length=1, max_length=255)
    body:                str | None = None
    status:              JournalNoteStatus | None = None
    pinned:              bool | None = None
    remind_next_session: bool | None = None


class PlaythroughNoteOut(BaseModel):
    """Response schema for a playthrough note with derived game fields."""
    id:                  int
    user_id:             int
    game_id:             int
    library_entry_id:    int | None
    session_log_id:      int | None
    kind:                JournalNoteKind
    title:               str
    body:                str | None
    status:              JournalNoteStatus
    pinned:              bool
    remind_next_session: bool
    completed_at:        datetime | None
    created_at:          datetime
    updated_at:          datetime
    game_title:          str | None
    game_cover_url:      str | None

    model_config = {"from_attributes": False}


class PaginatedPlaythroughNotesOut(BaseModel):
    """Paginated response schema for playthrough notes."""
    items:    list[PlaythroughNoteOut]
    total:    int
    page:     int
    per_page: int
    has_next: bool


# ─── Stats ────────────────────────────────────────────────────────────────────

class TopGenreItem(BaseModel):
    """Response schema for playtime grouped by genre."""
    genre: str
    hours: float


class DailyHoursItem(BaseModel):
    """Response schema for playtime grouped by weekday."""
    day:   str    # short weekday name: "Mon", "Tue", …
    hours: float


class JournalStats(BaseModel):
    """Response schema containing aggregate journal and emotion statistics."""
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
    # Emotion summary
    dominant_emotion_this_month: str | None
    emotion_coverage_pct:        float | None


# ─── Multi-Axis Ratings ───────────────────────────────────────────────────────

class MultiAxisRatingUpsert(BaseModel):
    """Request schema for creating or updating multi-axis game ratings."""
    story:      float | None = Field(None, ge=0, le=5)
    gameplay:   float | None = Field(None, ge=0, le=5)
    visuals:    float | None = Field(None, ge=0, le=5)
    soundtrack: float | None = Field(None, ge=0, le=5)
    overall:    float | None = Field(None, ge=0, le=5)


class MultiAxisRatingOut(BaseModel):
    """Response schema for a multi-axis game rating."""
    id:               int
    user_id:          int
    game_id:          int
    library_entry_id: int | None
    story:            float | None
    gameplay:         float | None
    visuals:          float | None
    soundtrack:       float | None
    overall:          float | None
    created_at:       datetime
    updated_at:       datetime
    game_title:       str | None
    game_cover_url:   str | None

    model_config = {"from_attributes": False}


# ─── Emotion Stats ────────────────────────────────────────────────────────────

class EmotionFrequencyItem(BaseModel):
    """Response schema for one emotion frequency bucket."""
    emotion:       str
    session_count: int
    percentage:    float


class EmotionGameCorrelation(BaseModel):
    """Response schema for emotion patterns associated with a game."""
    game_id:          int
    game_title:       str
    cover_url:        str | None
    dominant_emotion: str
    session_count:    int


class EmotionGenreCorrelation(BaseModel):
    """Response schema for emotion patterns associated with a genre."""
    genre:             str
    dominant_emotion:  str
    session_count:     int
    emotion_breakdown: list[EmotionFrequencyItem]


class EmotionMonthlyBucket(BaseModel):
    """Response schema for monthly emotion frequency data."""
    month:     str
    frequency: list[EmotionFrequencyItem]


class EmotionStats(BaseModel):
    """Response schema containing detailed journal emotion analytics."""
    period:                       str
    total_sessions_with_emotions: int
    total_sessions:               int
    frequency:                    list[EmotionFrequencyItem]
    most_common_emotion:          str | None
    top_positive_game:            EmotionGameCorrelation | None
    top_negative_game:            EmotionGameCorrelation | None
    per_game:                     list[EmotionGameCorrelation]
    per_genre:                    list[EmotionGenreCorrelation]
    monthly_breakdown:            list[EmotionMonthlyBucket]
