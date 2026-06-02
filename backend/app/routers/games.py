from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Literal

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.game import GameOut, PaginatedGames
from app.services import game_service

router = APIRouter()


@router.get("/", response_model=PaginatedGames)
def list_games(
    page:       int        = Query(1,   ge=1),
    page_size:  int        = Query(20,  ge=1, le=100),
    search:     str | None = Query(None),
    genre:      str | None = Query(None),
    platform:   str | None = Query(None),
    year:       int | None = Query(None),
    min_rating: float | None = Query(None, ge=0, le=5),
    max_hours:  int | None = Query(None, ge=1),
    library_state: Literal["all", "saved", "not_saved"] = Query("all"),
    sort: Literal["rating_desc", "released_desc", "name_asc", "playtime_asc"] = Query("rating_desc"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    """List games.

    Returns a filtered, sorted page of catalog games for the current user.

    Args:
        page: One-based page number to return. Defaults to 1.
        page_size: Maximum number of records to return per page. Defaults to Query(20, ge=1, le=100).
        search: Optional search text used to filter returned records. Defaults to Query(None).
        genre: Optional genre filter reserved for recommendation queries. Defaults to Query(None).
        platform: Optional platform filter reserved for recommendation queries. Defaults to Query(None).
        year: Optional release year used to filter games. Defaults to Query(None).
        min_rating: Optional minimum rating threshold used to filter games. Defaults to Query(None, ge=0, le=5).
        max_hours: Optional maximum playtime threshold used to filter games. Defaults to Query(None, ge=1).
        library_state: Library inclusion filter for the current user. Defaults to "all".
        sort: Sort mode used to order returned records. Defaults to Query('rating_desc').
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_basic).

    Returns:
        Serialized response object or task result produced by the operation."""
    return game_service.list_games(
        db,
        current_user.id,
        page,
        page_size,
        search,
        genre,
        platform,
        year,
        min_rating,
        max_hours,
        library_state,
        sort,
    )


@router.get("/{game_id}", response_model=GameOut)
def get_game(
    game_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    """Get game.

    Returns one catalog game by ID or raises the service-layer not-found response.

    Args:
        game_id: ID of the game to read or update.
        db: SQLAlchemy database session used to query or persist application data. Defaults to Depends(get_db).
        current_user: Authenticated user supplied by the route dependency. Defaults to Depends(require_basic).

    Returns:
        Serialized response object or task result produced by the operation."""
    return game_service.get_game_by_id(db, game_id)
