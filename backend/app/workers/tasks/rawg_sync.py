from datetime import date, datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app.models.game import Game
from app.models.rawg_sync_state import RawgSeenGame, RawgSyncState
from app.services import kv_store
from app.services.game_filter import normalize_game_payload, passes_game_filters
from app.utils.rawg_client import RAWGQuotaExceeded, RAWGRetryableError, rawg_client
from app.workers.celery_app import celery_app


PIPELINE_STATUS_KEY = "rawg_sync:last_run"
BACKFILL_PASSES = ("popular_added", "metacritic", "high_rating")


class RequestBudgetExceeded(RuntimeError):
    pass


@celery_app.task(name="rawg_sync.sync_games", bind=True, max_retries=3)
def sync_games(self, page_start: int = 1, page_end: int = 10):
    """
    Backward-compatible admin trigger for a bounded popular-games discovery pass.
    """
    return _run_discovery(
        pass_names=("popular_added",),
        max_requests=max(1, page_end - page_start + 1),
        page_override=page_start,
        max_pages=page_end - page_start + 1,
        retry_task=self,
    )


def run_sync_catalog(max_requests: int | None = None, retry_task: Any | None = None) -> dict[str, Any]:
    """
    Resume the monthly catalog fill. Most requests go to list-page discovery; the
    leftover budget enriches accepted games with full descriptions.
    """
    budget = max_requests or settings.RAWG_MONTHLY_REQUEST_BUDGET
    discovery_budget = max(1, int(budget * settings.RAWG_DISCOVERY_BUDGET_RATIO))
    discovery = _run_discovery(
        pass_names=BACKFILL_PASSES,
        max_requests=discovery_budget,
        retry_task=retry_task,
    )

    remaining = budget - discovery["requests_used"]
    if remaining > 0 and discovery["status"] == "success":
        enrichment = _run_enrichment(max_requests=remaining, retry_task=retry_task)
        discovery["enrichment"] = enrichment
        discovery["requests_used"] += enrichment["requests_used"]
    return discovery


@celery_app.task(name="rawg_sync.sync_catalog", bind=True, max_retries=3)
def sync_catalog(self, max_requests: int | None = None):
    return run_sync_catalog(max_requests, retry_task=self)


def run_sync_recent_releases(
    max_requests: int | None = None,
    days_back: int = 60,
    retry_task: Any | None = None,
) -> dict[str, Any]:
    """
    Fetch newly released games using list-page discovery only.
    """
    return _run_discovery(
        pass_names=("recent_releases",),
        max_requests=max_requests or settings.RAWG_RECENT_REQUEST_BUDGET,
        days_back=days_back,
        reset_completed=True,
        retry_task=retry_task,
    )


@celery_app.task(name="rawg_sync.sync_recent_releases", bind=True, max_retries=3)
def sync_recent_releases(self, max_requests: int | None = None, days_back: int = 60):
    return run_sync_recent_releases(max_requests, days_back, retry_task=self)


def run_enrich_known_games(max_requests: int | None = None, retry_task: Any | None = None) -> dict[str, Any]:
    return _run_enrichment(
        max_requests=max_requests or settings.RAWG_DETAIL_REFRESH_REQUEST_BUDGET,
        retry_task=retry_task,
    )


@celery_app.task(name="rawg_sync.enrich_known_games", bind=True, max_retries=3)
def enrich_known_games(self, max_requests: int | None = None):
    return run_enrich_known_games(max_requests, retry_task=self)


def run_sync_game_details(rawg_id: int) -> dict[str, Any]:
    """
    Refresh detail metadata for an already-known game.
    """
    db = SessionLocal()
    try:
        game = db.query(Game).filter(Game.rawg_id == rawg_id).first()
        if game is None:
            return {"status": "skipped", "reason": "not_found", "rawg_id": rawg_id}

        detail = rawg_client.get_game_detail(rawg_id)
        payload = normalize_game_payload({**_game_to_payload(game), **detail})
        _ensure_unique_slug(db, payload, rawg_id)
        _apply_game_payload(game, payload)
        db.commit()
        return {"status": "updated", "rawg_id": rawg_id}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@celery_app.task(name="rawg_sync.sync_game_details", bind=True, max_retries=3)
def sync_game_details(self, rawg_id: int):
    try:
        return run_sync_game_details(rawg_id)
    except RAWGRetryableError as exc:
        raise self.retry(exc=exc, countdown=60)


def _run_discovery(
    pass_names: tuple[str, ...],
    max_requests: int,
    days_back: int = 60,
    page_override: int | None = None,
    max_pages: int | None = None,
    reset_completed: bool = False,
    retry_task: Any | None = None,
) -> dict[str, Any]:
    db = SessionLocal()
    stats: dict[str, Any] = _initial_stats(phase="discovery")
    _write_status(stats)

    try:
        for pass_name in pass_names:
            state = _get_or_create_state(db, pass_name)
            if reset_completed and state.completed:
                state.completed = False
                state.next_page = 1

            if state.completed and page_override is None:
                continue

            page = page_override or state.next_page
            pages_done = 0
            while True:
                if max_pages is not None and pages_done >= max_pages:
                    break

                stats["current_pass"] = pass_name
                stats["page"] = page
                _write_status(stats)

                try:
                    _ensure_budget(stats, max_requests)
                    page_data = rawg_client.iter_catalog_pass(
                        pass_name,
                        page=page,
                        page_size=settings.RAWG_PAGE_SIZE,
                        days_back=days_back,
                    )
                    stats["requests_used"] += 1
                    results = page_data.get("results") or []

                    if not results:
                        _mark_completed(state, stats)
                        db.commit()
                        break

                    for item in results:
                        _process_discovery_item(db, item, pass_name, stats)

                    state.next_page = page + 1
                    state.completed = not bool(page_data.get("next"))
                    state.last_success_at = datetime.now(timezone.utc)
                    state.last_error = None
                    state.requests_used_this_run = stats["requests_used"]
                    state.updated_at = datetime.now(timezone.utc)
                    db.commit()

                    _write_status(stats)
                    if state.completed:
                        break
                    page += 1
                    pages_done += 1
                except (RAWGQuotaExceeded, RequestBudgetExceeded) as exc:
                    db.commit()
                    _mark_stopped(state, stats, str(exc) or "quota_or_budget_exhausted")
                    db.commit()
                    return stats

        stats["status"] = "success"
        stats["stop_reason"] = "completed"
        _write_status(stats)
        return stats
    except RAWGRetryableError as exc:
        db.rollback()
        _record_error(db, stats, exc)
        if retry_task is not None:
            raise retry_task.retry(exc=exc, countdown=60)
        return stats
    except Exception as exc:
        db.rollback()
        _record_error(db, stats, exc)
        raise
    finally:
        db.close()


def _run_enrichment(max_requests: int, retry_task: Any | None = None) -> dict[str, Any]:
    db = SessionLocal()
    stats: dict[str, Any] = _initial_stats(phase="enrichment")
    _write_status(stats)

    try:
        while True:
            if stats["requests_used"] >= max_requests:
                stats["status"] = "stopped"
                stats["stop_reason"] = "request_budget_exhausted"
                _write_status(stats)
                return stats

            game = (
                db.query(Game)
                .filter(Game.description.is_(None))
                .order_by(Game.synced_at.asc(), Game.id.asc())
                .first()
            )
            if game is None:
                stats["status"] = "success"
                stats["stop_reason"] = "completed"
                _write_status(stats)
                return stats

            try:
                detail = rawg_client.get_game_detail(game.rawg_id)
                stats["requests_used"] += 1
                payload = normalize_game_payload({**_game_to_payload(game), **detail})
                _ensure_unique_slug(db, payload, game.rawg_id)
                _apply_game_payload(game, payload)
                stats["enriched"] += 1
                db.commit()
                _write_status(stats)
            except (RAWGQuotaExceeded, RequestBudgetExceeded) as exc:
                db.rollback()
                stats["status"] = "stopped"
                stats["stop_reason"] = str(exc) or "quota_or_budget_exhausted"
                _write_status(stats)
                return stats
    except RAWGRetryableError as exc:
        db.rollback()
        stats["status"] = "error"
        stats["stop_reason"] = str(exc)
        _write_status(stats)
        if retry_task is not None:
            raise retry_task.retry(exc=exc, countdown=60)
        return stats
    finally:
        db.close()


def _process_discovery_item(
    db: Session,
    item: dict[str, Any],
    pass_name: str,
    stats: dict[str, Any],
) -> None:
    rawg_id = item["id"]
    game = db.query(Game).filter(Game.rawg_id == rawg_id).first()
    if game is not None:
        stats["skipped_duplicates"] += 1
        _record_seen(db, rawg_id, accepted=True, reason="already_inserted", source_pass=pass_name)
        return

    seen = db.get(RawgSeenGame, rawg_id)
    if seen and not seen.accepted and seen.recheck_after and _as_aware_utc(seen.recheck_after) > datetime.now(timezone.utc):
        stats["skipped_known_rejects"] += 1
        seen.times_seen += 1
        seen.last_seen_at = datetime.now(timezone.utc)
        seen.source_pass = pass_name
        return

    normalized = normalize_game_payload(item)
    passes, reason = passes_game_filters(normalized)
    if not passes:
        stats["rejected"] += 1
        _record_seen(db, rawg_id, accepted=False, reason=reason, source_pass=pass_name)
        return

    _ensure_unique_slug(db, normalized, rawg_id)
    game = Game(rawg_id=rawg_id)
    db.add(game)
    _apply_game_payload(game, normalized)
    _record_seen(db, rawg_id, accepted=True, reason=reason, source_pass=pass_name)
    stats["accepted"] += 1


def _record_seen(
    db: Session,
    rawg_id: int,
    accepted: bool,
    reason: str,
    source_pass: str,
) -> None:
    now = datetime.now(timezone.utc)
    seen = db.get(RawgSeenGame, rawg_id)
    if seen is None:
        seen = RawgSeenGame(rawg_id=rawg_id, first_seen_at=now)
        db.add(seen)
    seen.accepted = accepted
    seen.reason = reason
    seen.source_pass = source_pass
    seen.times_seen = (seen.times_seen or 0) + 1
    seen.last_seen_at = now
    seen.recheck_after = None if accepted else now + timedelta(days=settings.RAWG_REJECT_RECHECK_DAYS)


def _apply_game_payload(game: Game, payload: dict[str, Any]) -> None:
    game.name = payload["name"]
    game.slug = payload["slug"]
    game.description = payload.get("description")
    game.released = _parse_date(payload.get("released"))
    game.background_image = payload.get("background_image")
    game.rating = payload.get("rating")
    game.ratings_count = payload.get("ratings_count", 0) or 0
    game.metacritic = payload.get("metacritic")
    game.playtime = payload.get("playtime")
    game.genres = payload.get("genres") or []
    game.platforms = payload.get("platforms") or []
    game.tags = payload.get("tags") or []
    game.screenshots = payload.get("screenshots") or []
    game.synced_at = datetime.now(timezone.utc)


def _game_to_payload(game: Game) -> dict[str, Any]:
    return {
        "id": game.rawg_id,
        "name": game.name,
        "slug": game.slug,
        "description": game.description,
        "released": game.released.isoformat() if game.released else None,
        "background_image": game.background_image,
        "rating": game.rating,
        "ratings_count": game.ratings_count,
        "metacritic": game.metacritic,
        "genres": game.genres or [],
        "platforms": game.platforms or [],
        "tags": game.tags or [],
        "screenshots": game.screenshots or [],
        "playtime": game.playtime,
    }


def _ensure_unique_slug(db: Session, payload: dict[str, Any], rawg_id: int) -> None:
    slug = payload.get("slug") or f"rawg-{rawg_id}"
    existing = db.query(Game.rawg_id).filter(Game.slug == slug).first()
    if existing and existing[0] != rawg_id:
        slug = f"{slug}-{rawg_id}"
    payload["slug"] = slug


def _get_or_create_state(db: Session, pass_name: str) -> RawgSyncState:
    state = db.get(RawgSyncState, pass_name)
    if state is None:
        state = RawgSyncState(pass_name=pass_name, next_page=1, completed=False)
        db.add(state)
        db.flush()
    return state


def _mark_completed(state: RawgSyncState, stats: dict[str, Any]) -> None:
    state.completed = True
    state.last_success_at = datetime.now(timezone.utc)
    state.last_error = None
    state.requests_used_this_run = stats["requests_used"]
    state.updated_at = datetime.now(timezone.utc)


def _mark_stopped(state: RawgSyncState, stats: dict[str, Any], reason: str) -> None:
    stats["status"] = "stopped"
    stats["stop_reason"] = reason
    state.completed = False
    state.last_error = reason
    state.requests_used_this_run = stats["requests_used"]
    state.updated_at = datetime.now(timezone.utc)
    _write_status(stats)


def _record_error(db: Session, stats: dict[str, Any], exc: Exception) -> None:
    stats["status"] = "error"
    stats["stop_reason"] = str(exc)
    current_pass = stats.get("current_pass")
    if current_pass:
        state = _get_or_create_state(db, current_pass)
        state.completed = False
        state.last_error = str(exc)
        state.requests_used_this_run = stats["requests_used"]
        state.updated_at = datetime.now(timezone.utc)
        db.commit()
    _write_status(stats)


def _initial_stats(phase: str) -> dict[str, Any]:
    return {
        "last_run": datetime.now(timezone.utc).isoformat(),
        "phase": phase,
        "status": "running",
        "current_pass": None,
        "page": None,
        "accepted": 0,
        "rejected": 0,
        "skipped_duplicates": 0,
        "skipped_known_rejects": 0,
        "enriched": 0,
        "requests_used": 0,
        "stop_reason": None,
    }


def _ensure_budget(stats: dict[str, Any], max_requests: int) -> None:
    if stats["requests_used"] >= max_requests:
        raise RequestBudgetExceeded("request_budget_exhausted")


def _write_status(payload: dict[str, Any]) -> None:
    try:
        kv_store.set_json(PIPELINE_STATUS_KEY, payload)
    except Exception:
        pass


def _parse_date(value: Any) -> date | None:
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _as_aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
