from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.library import LibraryEntryCreate, LibraryEntryOut, LibraryEntryUpdate, LibraryStats

router = APIRouter()


@router.get("/", response_model=list[LibraryEntryOut])
def get_library(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Call library_service.get_user_library(db, current_user.id)
    raise NotImplementedError


@router.get("/stats", response_model=LibraryStats)
def get_library_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Aggregate: total games, status breakdown, avg rating, top genres
    # TODO: Call library_service.get_stats(db, current_user.id)
    raise NotImplementedError


@router.post("/", response_model=LibraryEntryOut, status_code=status.HTTP_201_CREATED)
def add_to_library(
    entry: LibraryEntryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Call library_service.add_game(db, current_user.id, entry)
    # TODO: Raise HTTP 409 if game already in library (uq_user_game constraint)
    # TODO: Optionally dispatch Celery task to recompute recommendations
    raise NotImplementedError


@router.patch("/{entry_id}", response_model=LibraryEntryOut)
def update_library_entry(
    entry_id: int,
    updates: LibraryEntryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Verify entry_id belongs to current_user (raise 403 otherwise)
    # TODO: Call library_service.update_entry(db, entry_id, updates)
    raise NotImplementedError


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_library(
    entry_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_basic),
):
    # TODO: Verify entry_id belongs to current_user
    # TODO: Call library_service.remove_game(db, entry_id)
    raise NotImplementedError
