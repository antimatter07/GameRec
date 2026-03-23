from fastapi import HTTPException, status
from sqlalchemy import Text, cast, extract
from sqlalchemy.orm import Session

from app.models.game import Game
from app.schemas.game import PaginatedGames


def list_games(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: str | None = None,
    genre: str | None = None,
    platform: str | None = None,
    year: int | None = None,
    min_rating: float | None = None,
) -> PaginatedGames:
    query = db.query(Game)

    if search:
        query = query.filter(Game.name.ilike(f"%{search}%"))
    if year:
        query = query.filter(extract("year", Game.released) == year)
    if min_rating is not None:
        query = query.filter(Game.rating >= min_rating)
    if genre:
        query = query.filter(cast(Game.genres, Text).ilike(f'%"name": "{genre}"%'))
    if platform:
        query = query.filter(cast(Game.platforms, Text).ilike(f'%"name": "{platform}"%'))

    total = query.count()
    games = query.offset((page - 1) * page_size).limit(page_size).all()

    return PaginatedGames(total=total, page=page, page_size=page_size, results=games)


def get_game_by_id(db: Session, game_id: int) -> Game:
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Game not found")
    return game
