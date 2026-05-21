from datetime import datetime

from pydantic import BaseModel

from app.schemas.library import LibraryEntryOut


class PlayQueueEntryOut(BaseModel):
    id:       int
    entry_id: int
    position: int
    added_at: datetime
    entry:    LibraryEntryOut

    model_config = {"from_attributes": True}


class PlayQueueOut(BaseModel):
    total:   int
    entries: list[PlayQueueEntryOut]


class PlayQueueEnqueue(BaseModel):
    entry_id: int


class PlayQueueReorder(BaseModel):
    ordered_entry_ids: list[int]


class QueueSuggestionEnsureIn(BaseModel):
    trigger_source: str = "queue_tab"


class QueueSuggestionItemOut(BaseModel):
    id:                 int
    entry_id:           int
    original_position:  int
    suggested_position: int
    reason:             str
    entry:              LibraryEntryOut

    model_config = {"from_attributes": True}


class QueueSuggestionOut(BaseModel):
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
    suggestion:    QueueSuggestionOut | None
    is_stale:      bool
    is_generating: bool
    can_generate:  bool
    can_adopt:     bool
    detail:        str | None = None
