from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_basic
from app.models.user import User
from app.schemas.library import (
    LibraryEntryCreate,
    LibraryEntryOut,
    LibraryEntryUpdate,
    LibraryEntryUpdateOut,
    LibraryStats,
    PaginatedLibraryEntries,
    PrioritizedBacklogOut,
    SteamImportRequest,
    SteamImportResponse,
)
from app.services import library_service
from app.services import steam_import_service
from app.services import task_queue

router = APIRouter()

DBDep = Annotated[Session, Depends(get_db)]
CurrentUserDep = Annotated[User, Depends(require_basic)]


@router.get("/", response_model=list[LibraryEntryOut])
def get_library(
    db: DBDep,
    current_user: CurrentUserDep,
    status_filter: Literal["all", "playing", "replaying", "completed", "backlog", "wishlist", "dropped"] = Query(
        "all",
        alias="status",
    ),
    search: str | None = Query(None),
    sort: Literal["added_at_desc", "added_at_asc", "status"] = Query("added_at_desc"),
):
    return library_service.get_user_library(
        db,
        current_user.id,
        status_filter=status_filter,
        search=search,
        sort=sort,
    )


@router.get("/paged", response_model=PaginatedLibraryEntries)
def get_library_page(
    db: DBDep,
    current_user: CurrentUserDep,
    status_filter: Literal["all", "playing", "replaying", "completed", "backlog", "wishlist", "dropped"] = Query(
        "all",
        alias="status",
    ),
    search: str | None = Query(None),
    sort: Literal["added_at_desc", "added_at_asc", "status"] = Query("added_at_desc"),
    page: int = Query(1, ge=1),
    page_size: int = Query(40, ge=1, le=100),
):
    return library_service.get_user_library_page(
        db,
        current_user.id,
        status_filter=status_filter,
        search=search,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/stats", response_model=LibraryStats)
def get_library_stats(db: DBDep, current_user: CurrentUserDep):
    return library_service.get_stats(db, current_user.id)


@router.post("/", response_model=LibraryEntryOut, status_code=status.HTTP_201_CREATED)
def add_to_library(entry: LibraryEntryCreate, db: DBDep, current_user: CurrentUserDep):
    result = library_service.add_game(db, current_user.id, entry)
    try:
        from app.services.ai_picks_service import invalidate_ai_picks_cache
        invalidate_ai_picks_cache(current_user.id)
        task_queue.enqueue_precompute_for_user(current_user.id)
    except Exception:
        pass  # Celery unavailable — recommendations will recompute on next request
    return result


@router.post("/import/steam", response_model=SteamImportResponse)
def import_steam_library(payload: SteamImportRequest, db: DBDep, current_user: CurrentUserDep):
    result = steam_import_service.import_steam_library(db, current_user.id, payload.steam_profile)
    if result["added"] or result["already_in_library"]:
        try:
            from app.services.ai_picks_service import invalidate_ai_picks_cache
            invalidate_ai_picks_cache(current_user.id)
            task_queue.enqueue_precompute_for_user(current_user.id)
        except Exception:
            pass
    return result


@router.get("/backlog/prioritized", response_model=PrioritizedBacklogOut)
def get_prioritized_backlog(
    db: DBDep,
    current_user: CurrentUserDep,
    mood_genre: str | None = Query(None, description="Filter to backlog games matching this genre name"),
    max_hours: int | None = Query(None, ge=1, description="Only include games with playtime <= this many hours"),
    sort: Literal["score", "playtime_asc", "playtime_desc", "added_at"] = Query("score"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    return library_service.get_prioritized_backlog(
        db, current_user.id, mood_genre, max_hours, sort, page, page_size
    )


@router.patch("/{entry_id}", response_model=LibraryEntryUpdateOut)
def update_library_entry(entry_id: int, updates: LibraryEntryUpdate, db: DBDep, current_user: CurrentUserDep):
    result = library_service.update_entry(db, current_user.id, entry_id, updates)
    try:
        from app.services.ai_picks_service import invalidate_ai_picks_cache
        invalidate_ai_picks_cache(current_user.id)
        task_queue.enqueue_precompute_for_user(current_user.id)
    except Exception:
        pass
    return result


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_library(entry_id: int, db: DBDep, current_user: CurrentUserDep):
    library_service.remove_game(db, current_user.id, entry_id)
    try:
        from app.services.ai_picks_service import invalidate_ai_picks_cache
        invalidate_ai_picks_cache(current_user.id)
        task_queue.enqueue_precompute_for_user(current_user.id)
    except Exception:
        pass  # Celery unavailable — recommendations will recompute on next request
