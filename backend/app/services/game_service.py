from fastapi import HTTPException, status
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
    # TODO: Build base query: db.query(Game).filter(Game...)
    # TODO: search  → Game.name.ilike(f"%{search}%")
    # TODO: year    → extract(year, Game.released) == year
    # TODO: min_rating → Game.rating >= min_rating
    # TODO: genre / platform → PostgreSQL JSON containment:
    #         Game.genres.contains([{"name": genre}])   (works with JSONB cast)
    #         Or use func.jsonb_path_exists() for more flexible matching
    # TODO: Paginate: query.offset((page-1)*page_size).limit(page_size).all()
    # TODO: Return PaginatedGames(total=count, page=page, page_size=page_size, results=games)
    raise NotImplementedError


def get_game_by_id(db: Session, game_id: int) -> Game:
    # TODO: game = db.query(Game).filter(Game.id == game_id).first()
    # TODO: if not game: raise HTTPException(status_code=404)
    raise NotImplementedError
