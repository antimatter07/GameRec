from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.library import LibraryEntryCreate, LibraryEntryOut, LibraryEntryUpdate, LibraryStats
from app.services import library_service

router = APIRouter()

DBDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(require_basic)]


@router.get("/", response_model=list[LibraryEntryOut])
def get_library(db: DBDep, current_user: CurrentUserDep):
    return library_service.get_user_library(db, current_user.id)


@router.get("/stats", response_model=LibraryStats)
def get_library_stats(db: DBDep, current_user: CurrentUserDep):
    # TODO: Aggregate: total games, status breakdown, avg rating, top genres
    # TODO: Call library_service.get_stats(db, current_user.id)
    raise NotImplementedError


@router.post("/", response_model=LibraryEntryOut, status_code=status.HTTP_201_CREATED)
def add_to_library(entry: LibraryEntryCreate, db: DBDep, current_user: CurrentUserDep):
    result = library_service.add_game(db, current_user.id, entry)
    try:
        from app.workers.tasks.recommendation import precompute_for_user
        precompute_for_user.delay(current_user.id)
    except Exception:
        pass  # Celery unavailable — recommendations will recompute on next request
    return result


@router.patch("/{entry_id}", response_model=LibraryEntryOut)
def update_library_entry(entry_id: int, updates: LibraryEntryUpdate, db: DBDep, current_user: CurrentUserDep):
    # TODO: Verify entry_id belongs to current_user (raise 403 otherwise)
    # TODO: Call library_service.update_entry(db, entry_id, updates)
    raise NotImplementedError


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_library(entry_id: int, db: DBDep, current_user: CurrentUserDep):
    library_service.remove_game(db, current_user.id, entry_id)
    try:
        from app.workers.tasks.recommendation import precompute_for_user
        precompute_for_user.delay(current_user.id)
    except Exception:
        pass  # Celery unavailable — recommendations will recompute on next request
