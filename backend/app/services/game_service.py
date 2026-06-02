from fastapi import HTTPException, status
from sqlalchemy import Text, cast, extract, func
from sqlalchemy.orm import Session
from typing import Literal

from app.models.game import Game
from app.models.library import LibraryEntry
from app.schemas.game import PaginatedGames


def list_games(
    db: Session,
    user_id: int,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    genre: str | None = None,
    platform: str | None = None,
    year: int | None = None,
    min_rating: float | None = None,
    max_hours: int | None = None,
    library_state: Literal["all", "saved", "not_saved"] = "all",
    sort: Literal["rating_desc", "released_desc", "name_asc", "playtime_asc"] = "rating_desc",
) -> PaginatedGames:
    """List games.

    Builds the database query, applies caller-provided filters, and returns the requested slice of results.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        page: One-based page number to return. Defaults to 1.
        page_size: Maximum number of records to return per page. Defaults to 20.
        search: Optional text used to filter records by name or other searchable fields. Defaults to None.
        genre: Optional genre slug or name used to filter games. Defaults to None.
        platform: Optional platform slug or name used to filter games. Defaults to None.
        year: Optional release year used to filter games. Defaults to None.
        min_rating: Optional minimum rating threshold used to filter games. Defaults to None.
        max_hours: Optional maximum playtime threshold used to filter games. Defaults to None.
        library_state: Library inclusion filter for the current user. Defaults to "all".
        sort: Sort mode used to order returned records. Defaults to 'rating_desc'.

    Returns:
        PaginatedGames produced by the operation."""
    query = db.query(Game)

    if search:
        query = query.filter(Game.name.ilike(f"%{search}%"))
    if year:
        query = query.filter(extract("year", Game.released) == year)
    if min_rating is not None:
        query = query.filter(Game.rating >= min_rating)
    if genre:
        genre_text = cast(Game.genres, Text)
        query = query.filter(
            genre_text.ilike(f'%"slug": "{genre}"%')
            | genre_text.ilike(f'%"name": "{genre}"%')
        )
    if platform:
        platform_text = cast(Game.platforms, Text)
        query = query.filter(
            platform_text.ilike(f'%"slug": "{platform}"%')
            | platform_text.ilike(f'%"name": "{platform}"%')
        )
    if max_hours is not None:
        query = query.filter(func.coalesce(Game.hltb_main_hours, Game.playtime) <= max_hours)

    if library_state != "all":
        saved_game_ids = db.query(LibraryEntry.game_id).filter(LibraryEntry.user_id == user_id)
        if library_state == "saved":
            query = query.filter(Game.id.in_(saved_game_ids))
        else:
            query = query.filter(~Game.id.in_(saved_game_ids))

    total = query.count()

    playtime_hours = func.coalesce(Game.hltb_main_hours, Game.playtime)
    if sort == "released_desc":
        query = query.order_by(Game.released.desc().nullslast(), Game.rating.desc().nullslast(), Game.id.asc())
    elif sort == "name_asc":
        query = query.order_by(Game.name.asc(), Game.id.asc())
    elif sort == "playtime_asc":
        query = query.order_by(playtime_hours.asc().nullslast(), Game.rating.desc().nullslast(), Game.id.asc())
    else:
        query = query.order_by(Game.rating.desc().nullslast(), Game.ratings_count.desc(), Game.id.asc())

    games = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedGames(total=total, page=page, page_size=page_size, results=games)


def get_game_by_id(db: Session, game_id: int) -> Game:
    """Get game by ID.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        game_id: ID of the game to read, update, or associate with the operation.

    Returns:
        Game produced by the operation.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game
