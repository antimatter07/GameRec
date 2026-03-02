from datetime import date
from typing import Any

from pydantic import BaseModel


class GameOut(BaseModel):
    """Full game detail — used on the game detail page."""
    id:               int
    rawg_id:          int
    name:             str
    slug:             str
    description:      str | None
    released:         date | None
    background_image: str | None
    rating:           float | None
    ratings_count:    int
    metacritic:       int | None
    genres:           list[Any]
    platforms:        list[Any]
    tags:             list[Any]
    screenshots:      list[Any]

    model_config = {"from_attributes": True}


class GameListOut(BaseModel):
    """Lightweight game info — used in list/catalog views and nested in other schemas."""
    id:               int
    name:             str
    slug:             str
    released:         date | None
    background_image: str | None
    rating:           float | None
    genres:           list[Any]
    platforms:        list[Any]

    model_config = {"from_attributes": True}


class PaginatedGames(BaseModel):
    total:     int
    page:      int
    page_size: int
    results:   list[GameListOut]
