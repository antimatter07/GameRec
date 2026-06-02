import hashlib
import json
from datetime import datetime, timezone

from pydantic import BaseModel, Field
from sqlalchemy.orm import Session, joinedload

from app.config import settings
from app.models.library import LibraryEntry
from app.models.play_queue import PlayQueueEntry
from app.models.queue_suggestion import QueueSuggestion, QueueSuggestionItem
from app.schemas.play_queue import PlayQueueReorder
from app.services import play_queue_service
from app.services.llm_provider import LLMProviderError, get_default_llm_provider

_MIN_QUEUE_ITEMS = 2


class QueueSuggestionPosition(BaseModel):
    """One line item in the AI-generated suggested play order."""
    original_position: int = Field(ge=1)
    game_name: str = Field(min_length=1)
    suggested_position: int = Field(ge=1)
    reason: str


class QueueSuggestionSelection(BaseModel):
    """Structured Gemini response for a queue reorder suggestion."""
    overall_explanation: str
    positions: list[QueueSuggestionPosition]


def compute_queue_fingerprint(entry_ids: list[int]) -> str:
    """Compute queue fingerprint.

    Aggregates source data for recommendation and AI workflows.

    Args:
        entry_ids: Ordered queue entry IDs used to compute a fingerprint.

    Returns:
        String value produced by the operation."""
    raw = ",".join(str(entry_id) for entry_id in entry_ids)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _load_queue_rows(db: Session, user_id: int) -> list[PlayQueueEntry]:
    """Load queue rows.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        List of matching records or serialized service objects."""
    return (
        db.query(PlayQueueEntry)
        .filter(PlayQueueEntry.user_id == user_id)
        .order_by(PlayQueueEntry.position)
        .options(joinedload(PlayQueueEntry.entry).joinedload(LibraryEntry.game))
        .all()
    )


def _latest_for_fingerprint(db: Session, user_id: int, queue_fingerprint: str) -> QueueSuggestion | None:
    """Load the latest for fingerprint.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        queue_fingerprint: Stable fingerprint representing the current queue order.

    Returns:
        QueueSuggestion | None when a matching value is available; otherwise None."""
    return (
        db.query(QueueSuggestion)
        .options(joinedload(QueueSuggestion.items).joinedload(QueueSuggestionItem.entry).joinedload(LibraryEntry.game))
        .filter(
            QueueSuggestion.user_id == user_id,
            QueueSuggestion.queue_fingerprint == queue_fingerprint,
        )
        .order_by(QueueSuggestion.requested_at.desc())
        .first()
    )


def _latest_overall(db: Session, user_id: int) -> QueueSuggestion | None:
    """Load the latest overall.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.

    Returns:
        QueueSuggestion | None when a matching value is available; otherwise None."""
    return (
        db.query(QueueSuggestion)
        .options(joinedload(QueueSuggestion.items).joinedload(QueueSuggestionItem.entry).joinedload(LibraryEntry.game))
        .filter(QueueSuggestion.user_id == user_id)
        .order_by(QueueSuggestion.requested_at.desc())
        .first()
    )


def _latest_overall_with_status(db: Session, user_id: int, status: str) -> QueueSuggestion | None:
    """Load the latest overall with status.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        status: status value used by the operation.

    Returns:
        QueueSuggestion | None when a matching value is available; otherwise None."""
    return (
        db.query(QueueSuggestion)
        .options(joinedload(QueueSuggestion.items).joinedload(QueueSuggestionItem.entry).joinedload(LibraryEntry.game))
        .filter(
            QueueSuggestion.user_id == user_id,
            QueueSuggestion.status == status,
        )
        .order_by(QueueSuggestion.requested_at.desc())
        .first()
    )


def _state_from_suggestion(
    suggestion: QueueSuggestion | None,
    *,
    is_stale: bool,
    is_generating: bool,
    can_generate: bool,
    detail: str | None,
) -> dict:
    """State from suggestion.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        suggestion: suggestion value used by the operation.
        is_stale: is stale value used by the operation.
        is_generating: is generating value used by the operation.
        can_generate: can generate value used by the operation.
        detail: detail value used by the operation.

    Returns:
        Dictionary containing serialized service state and metadata."""
    return {
        "suggestion": suggestion,
        "is_stale": is_stale,
        "is_generating": is_generating,
        "can_generate": can_generate,
        "can_adopt": suggestion is not None and suggestion.status == "ready",
        "detail": detail,
    }


def _normalize_game_name(name: str) -> str:
    """Normalize game name.

    Converts external or user-provided text into the canonical form used for comparison and persistence.

    Args:
        name: Display name or normalized name used for matching.

    Returns:
        String value produced by the operation."""
    return " ".join(name.casefold().split())


def _validate_selection(
    selection: QueueSuggestionSelection,
    queue_rows: list[PlayQueueEntry],
) -> QueueSuggestionSelection:
    """Validate selection.

    Normalizes and checks incoming values before they are used in database writes or AI workflows.

    Args:
        selection: AI-selected queue suggestion candidate to validate.
        queue_rows: Current queue entries used as suggestion context.

    Returns:
        QueueSuggestionSelection produced by the operation.

    Raises:
        ValueError: When supplied input cannot be validated or mapped to application data."""
    if not selection.overall_explanation.strip():
        raise ValueError("Queue suggestion is missing an overall explanation.")
    queue_size = len(queue_rows)
    if len(selection.positions) != queue_size:
        raise ValueError("Queue suggestion did not return the same number of positions as the queue.")

    seen_original: set[int] = set()
    seen_suggested: set[int] = set()
    expected_positions = set(range(1, queue_size + 1))
    position_map = {row.position: row for row in queue_rows}

    for item in selection.positions:
        if item.original_position in seen_original:
            raise ValueError("Queue suggestion returned duplicate original positions.")
        if item.suggested_position in seen_suggested:
            raise ValueError("Queue suggestion returned duplicate suggested positions.")
        queue_row = position_map.get(item.original_position)
        if queue_row is None:
            raise ValueError(f"Queue suggestion referenced unknown original position {item.original_position}.")
        expected_name = _normalize_game_name(queue_row.entry.game.name)
        actual_name = _normalize_game_name(item.game_name)
        if actual_name != expected_name:
            raise ValueError(
                "Queue suggestion mismatched a game name for its original position: "
                f"expected {queue_row.entry.game.name!r}, got {item.game_name!r}."
            )
        if not item.reason.strip():
            raise ValueError("Queue suggestion returned an empty item explanation.")
        seen_original.add(item.original_position)
        seen_suggested.add(item.suggested_position)

    if seen_original != expected_positions or seen_suggested != expected_positions:
        raise ValueError("Queue suggestion did not return a complete 1..N position mapping.")

    if all(item.original_position == item.suggested_position for item in selection.positions):
        raise ValueError("Queue suggestion kept the exact original order instead of proposing an alternative.")

    return selection


def _build_prompt(queue_rows: list[PlayQueueEntry]) -> str:
    """Build prompt.

    Aggregates source data for recommendation and AI workflows.

    Args:
        queue_rows: Current queue entries used as suggestion context.

    Returns:
        String value produced by the operation."""
    queue_lines = [f"{row.position}. {row.entry.game.name}" for row in queue_rows]

    return (
        "Suggest a meaningfully different play order for the following games in the user's queue.\n\n"
        "This feature is intentionally a devil's-advocate alternative to the user's current order.\n"
        "Do not preserve the current sequence by default. Propose a genuinely different order that is still sensible and easy to justify.\n\n"
        "Consider these factors when deciding the order:\n\n"
        "1. Accessibility\n"
        "- Prefer games that are easier to start, shorter, or lower-commitment earlier.\n"
        "- Avoid putting very long, complex, or mechanically demanding games first unless there is a strong reason.\n\n"
        "2. Variety and pacing\n"
        "- Avoid placing very similar games back-to-back when possible.\n"
        "- Create a good rhythm across genres, moods, difficulty levels, and session intensity.\n"
        "- A queue should feel enjoyable over time, not monotonous.\n\n"
        "3. Player momentum\n"
        "- Put games that can hook the user quickly near the front.\n"
        "- Use lighter or shorter games as palate cleansers between heavier games.\n\n"
        "4. Franchise or story dependencies\n"
        "- If games appear to belong to the same series, preserve a logical story or release order when appropriate.\n"
        "- Do not assume deep franchise knowledge unless the game titles clearly imply it.\n\n"
        "5. Popularity and critical reception\n"
        "- Highly acclaimed or broadly loved games may be prioritized, but they should not automatically go first.\n"
        "- Balance quality with pacing and approachability.\n\n"
        "6. Devil's-advocate sequencing\n"
        "- Challenge the user's current ordering with a fresh, defensible sequence.\n"
        "- Make at least one meaningful move, and preferably several when a stronger flow is available.\n"
        "- Every move should be explainable in terms of pacing, momentum, variety, accessibility, or series logic.\n\n"
        "Important constraints:\n"
        "- Each object in positions represents the same game from one current queue row.\n"
        "- Copy original_position from the current queue exactly.\n"
        "- Copy game_name exactly from the current queue for that same original_position.\n"
        "- suggested_position is the new slot for that same game, not a separate ranked list row.\n"
        "- The reason must explain why that specific game fits that specific suggested_position.\n"
        "- You must propose a different final order from the current queue.\n"
        "- At least one game must move to a different suggested_position.\n"
        "- You must include every game exactly once.\n"
        "- suggested_position must be a 1-based integer.\n"
        "- Across all items, suggested_position values must cover 1 through the queue length exactly once.\n"
        "- Do not skip or duplicate positions.\n"
        "- Reasons should be concise, specific, and player-facing.\n"
        "- Do not invent games, titles, metadata, platforms, genres, or user preferences.\n\n"
        "Current queue:\n"
        + "\n".join(queue_lines)
    )


def _generate_selection_once(queue_rows: list[PlayQueueEntry], *, stricter: bool) -> QueueSuggestionSelection:
    """Generate selection once.

    Produces AI-backed content and validates it before storage or return.

    Args:
        queue_rows: Current queue entries used as suggestion context.
        stricter: Whether to apply stricter validation on a retry attempt.

    Returns:
        QueueSuggestionSelection produced by the operation."""
    provider = get_default_llm_provider(settings.QUEUE_SUGGESTION_MODEL)
    user_prompt = _build_prompt(queue_rows)
    if stricter:
        user_prompt += (
            "\n\nRepair mode: you must return exactly one item for every original position, "
            "copy the matching game_name for that original_position exactly, "
            "use a full 1..N suggested ordering with no duplicates, "
            "and change at least one suggested_position from its original_position."
        )

    return provider.generate_structured(
        system_prompt=(
            "You are an expert video game backlog curator. "
            "Your task is to suggest the best play order for a user's current game queue. "
            "You must reorder only the games provided. Do not add, remove, rename, or invent games. "
            "Your recommendation should feel useful to a real player deciding what to play next, "
            "not like a generic ranking. Prioritize a satisfying play journey across the queue."
        ),
        user_prompt=user_prompt,
        schema=QueueSuggestionSelection,
    )


def get_queue_suggestion_state(user_id: int, db: Session) -> dict:
    """Get queue suggestion state.

    Loads the requested service state and applies the missing-resource behavior expected by API callers.

    Args:
        user_id: ID of the user whose data should be read or modified.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Dictionary containing serialized service state and metadata."""
    if not settings.GEMINI_API_KEY:
        return _state_from_suggestion(
            None,
            is_stale=False,
            is_generating=False,
            can_generate=False,
            detail="AI queue suggestions are not configured yet.",
        )

    latest_ready = _latest_overall_with_status(db, user_id, "ready")
    queue_rows = _load_queue_rows(db, user_id)
    if len(queue_rows) < _MIN_QUEUE_ITEMS:
        detail = "Add at least 2 games to your queue to get an AI suggested play order."
        if latest_ready is not None:
            detail = (
                "Your current queue is too small for a new AI order, so the last generated suggestion is still shown."
            )
        return _state_from_suggestion(
            latest_ready,
            is_stale=latest_ready is not None,
            is_generating=False,
            can_generate=False,
            detail=detail,
        )

    entry_ids = [row.entry_id for row in queue_rows]
    current_fingerprint = compute_queue_fingerprint(entry_ids)
    matching = _latest_for_fingerprint(db, user_id, current_fingerprint)
    latest = _latest_overall(db, user_id)
    is_stale = latest_ready is not None and latest_ready.queue_fingerprint != current_fingerprint

    if matching is not None and matching.status == "ready":
        return _state_from_suggestion(
            matching,
            is_stale=False,
            is_generating=False,
            can_generate=True,
            detail=None,
        )

    if matching is not None and matching.status == "pending":
        detail = (
            "A fresh AI suggested play order is being generated. Your previous suggestion will stay visible until it is ready."
            if latest_ready is not None and latest_ready.queue_fingerprint != current_fingerprint
            else "AI is generating a suggested play order."
        )
        return _state_from_suggestion(
            latest_ready if is_stale else matching,
            is_stale=is_stale,
            is_generating=True,
            can_generate=False,
            detail=detail,
        )

    if matching is not None and matching.status == "failed":
        if latest_ready is not None and latest_ready.queue_fingerprint != current_fingerprint:
            return _state_from_suggestion(
                latest_ready,
                is_stale=True,
                is_generating=False,
                can_generate=True,
                detail=matching.error_detail or "AI could not generate a fresh suggested play order.",
            )
        return _state_from_suggestion(
            matching,
            is_stale=False,
            is_generating=False,
            can_generate=True,
            detail=matching.error_detail or "AI could not generate a suggested play order.",
        )

    if latest_ready is not None:
        return _state_from_suggestion(
            latest_ready,
            is_stale=True,
            is_generating=False,
            can_generate=True,
            detail="Your queue changed since the last AI order. The previous suggestion is still shown until you generate a fresh one.",
        )

    detail = (
        "Your queue changed since the last AI order. A fresh suggestion is needed."
        if latest is not None and latest.queue_fingerprint != current_fingerprint
        else "No AI suggested order has been generated for this queue yet."
    )
    return _state_from_suggestion(None, is_stale=False, is_generating=False, can_generate=True, detail=detail)


def ensure_queue_suggestion(user_id: int, trigger_source: str, db: Session) -> tuple[dict, bool, int | None]:
    """Ensure queue suggestion.

    Performs the service operation behind a stable module-level interface.

    Args:
        user_id: ID of the user whose data should be read or modified.
        trigger_source: String describing what action requested the suggestion.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        tuple[dict, bool, int | None] when a matching value is available; otherwise None."""
    state = get_queue_suggestion_state(user_id, db)
    if not state["can_generate"]:
        return state, False, None

    queue_rows = _load_queue_rows(db, user_id)
    entry_ids = [row.entry_id for row in queue_rows]
    queue_fingerprint = compute_queue_fingerprint(entry_ids)
    matching = _latest_for_fingerprint(db, user_id, queue_fingerprint)
    if matching is not None and matching.status == "pending":
        return get_queue_suggestion_state(user_id, db), False, None
    suggestion = QueueSuggestion(
        user_id=user_id,
        queue_fingerprint=queue_fingerprint,
        status="pending",
        trigger_source=trigger_source,
        model_name=settings.QUEUE_SUGGESTION_MODEL,
    )
    db.add(suggestion)
    db.commit()
    db.refresh(suggestion)
    return get_queue_suggestion_state(user_id, db), True, suggestion.id


def generate_queue_suggestion_for_user(suggestion_id: int, user_id: int, db: Session) -> QueueSuggestion:
    """Generate queue suggestion for user.

    Produces AI-backed content and validates it before storage or return.

    Args:
        suggestion_id: ID of the queue suggestion row to process.
        user_id: ID of the user whose data should be read or modified.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        QueueSuggestion produced by the operation.

    Raises:
        ValueError: When supplied input cannot be validated or mapped to application data."""
    suggestion = (
        db.query(QueueSuggestion)
        .options(joinedload(QueueSuggestion.items))
        .filter(QueueSuggestion.id == suggestion_id, QueueSuggestion.user_id == user_id)
        .first()
    )
    if suggestion is None:
        raise ValueError(f"Queue suggestion {suggestion_id} not found.")

    queue_rows = _load_queue_rows(db, user_id)
    if len(queue_rows) < _MIN_QUEUE_ITEMS:
        raise ValueError("Add at least 2 games to your queue to generate a suggested order.")

    current_fingerprint = compute_queue_fingerprint([row.entry_id for row in queue_rows])
    if current_fingerprint != suggestion.queue_fingerprint:
        raise ValueError("Queue changed before suggestion generation could finish. Please generate a fresh order.")

    try:
        selection = _generate_selection_once(queue_rows, stricter=False)
        selection = _validate_selection(selection, queue_rows)
    except (ValueError, LLMProviderError):
        selection = _generate_selection_once(queue_rows, stricter=True)
        selection = _validate_selection(selection, queue_rows)

    suggestion.items.clear()
    position_map = {row.position: row for row in queue_rows}

    for item in sorted(selection.positions, key=lambda row: row.suggested_position):
        queue_row = position_map[item.original_position]
        suggestion.items.append(
            QueueSuggestionItem(
                entry_id=queue_row.entry_id,
                original_position=item.original_position,
                suggested_position=item.suggested_position,
                reason=item.reason.strip(),
            )
        )

    suggestion.status = "ready"
    suggestion.generated_at = datetime.now(timezone.utc)
    suggestion.overall_explanation = selection.overall_explanation.strip()
    suggestion.error_detail = None
    suggestion.model_name = settings.QUEUE_SUGGESTION_MODEL
    db.commit()
    db.refresh(suggestion)
    return suggestion


def adopt_queue_suggestion(user_id: int, db: Session) -> dict:
    """Adopt queue suggestion.

    Performs the service operation behind a stable module-level interface.

    Args:
        user_id: ID of the user whose data should be read or modified.
        db: SQLAlchemy database session used to query or persist application data.

    Returns:
        Dictionary containing serialized service state and metadata.

    Raises:
        ValueError: When supplied input cannot be validated or mapped to application data."""
    queue_rows = _load_queue_rows(db, user_id)
    if len(queue_rows) < _MIN_QUEUE_ITEMS:
        raise ValueError("Your queue is too small to adopt an AI suggested order.")

    current_fingerprint = compute_queue_fingerprint([row.entry_id for row in queue_rows])
    suggestion = _latest_for_fingerprint(db, user_id, current_fingerprint)
    if suggestion is None or suggestion.status != "ready":
        raise ValueError("No ready AI suggested order is available for your current queue.")

    ordered_entry_ids = [
        item.entry_id
        for item in sorted(suggestion.items, key=lambda row: row.suggested_position)
    ]
    if ordered_entry_ids != [row.entry_id for row in queue_rows]:
        return play_queue_service.reorder(
            db,
            user_id,
            PlayQueueReorder(ordered_entry_ids=ordered_entry_ids),
        )
    return play_queue_service.get_queue(db, user_id)
