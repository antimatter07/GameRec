from datetime import datetime

from pydantic import BaseModel

from app.schemas.library import LibraryEntryOut


class PlayQueueEntryOut(BaseModel):
    """Response schema for one play queue entry."""
    id:       int
    entry_id: int
    position: int
    added_at: datetime
    entry:    LibraryEntryOut

    model_config = {"from_attributes": True}


class PlayQueueOut(BaseModel):
    """Response schema for the current ordered play queue."""
    total:   int
    entries: list[PlayQueueEntryOut]


class PlayQueueEnqueue(BaseModel):
    """Request schema for adding a library entry to the play queue."""
    entry_id: int


class PlayQueueReorder(BaseModel):
    """Request schema for submitting a complete play queue ordering."""
    ordered_entry_ids: list[int]


class QueueSuggestionEnsureIn(BaseModel):
    """Request schema for creating or refreshing a queue suggestion."""
    trigger_source: str = "queue_tab"


class QueueSuggestionItemOut(BaseModel):
    """Response schema for one item in an AI queue suggestion."""
    id:                 int
    entry_id:           int
    original_position:  int
    suggested_position: int
    reason:             str
    entry:              LibraryEntryOut

    model_config = {"from_attributes": True}


class QueueSuggestionOut(BaseModel):
    """Response schema for an AI-generated queue suggestion batch."""
    id:                  int
    queue_fingerprint:   str
    status:              str
    trigger_source:      str
    requested_at:        datetime
    generated_at:        datetime | None
    model_name:          str | None
    overall_explanation: str | None
    error_detail:        str | None
    items:               list[QueueSuggestionItemOut]

    model_config = {"from_attributes": True}


class QueueSuggestionStateOut(BaseModel):
    """Response schema describing current queue suggestion state."""
    suggestion:    QueueSuggestionOut | None
    is_stale:      bool
    is_generating: bool
    can_generate:  bool
    can_adopt:     bool
    detail:        str | None = None
