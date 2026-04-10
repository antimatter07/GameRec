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
