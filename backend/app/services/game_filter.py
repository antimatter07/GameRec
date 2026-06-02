import json
from datetime import date
from pathlib import Path
from typing import Any


ALLOWLIST_PATH = Path(__file__).resolve().parent.parent / "data" / "game_filter_allowlist.json"
EXCLUDED_TAG_SLUGS = {"soundtrack", "demo", "dlc", "expansion"}


def _load_allowlist() -> set[str]:
    """Load allowlist.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Returns:
        set[str] produced by the operation."""
    try:
        with open(ALLOWLIST_PATH, encoding="utf-8") as fh:
            payload = json.load(fh)
    except FileNotFoundError:
        return set()

    values: set[str] = set()
    if isinstance(payload, dict):
        for key in ("rawg_ids", "slugs"):
            for value in payload.get(key, []):
                values.add(str(value).lower())
    elif isinstance(payload, list):
        values = {str(value).lower() for value in payload}
    return values


ALLOWLIST = _load_allowlist()


def normalize_game_payload(raw: dict[str, Any]) -> dict[str, Any]:
    """Normalize game payload.

    Converts external or user-provided text into the canonical form used for comparison and persistence.

    Args:
        raw: RAWG API payload or game-like dictionary to normalize or evaluate.

    Returns:
        Dictionary containing serialized service state and metadata."""
    platforms = []
    for entry in raw.get("platforms") or []:
        if isinstance(entry, dict) and isinstance(entry.get("platform"), dict):
            platform = entry["platform"]
        else:
            platform = entry
        if isinstance(platform, dict):
            platforms.append({"id": platform.get("id"), "name": platform.get("name"), "slug": platform.get("slug")})

    genres = [
        {"id": item.get("id"), "name": item.get("name"), "slug": item.get("slug")}
        for item in (raw.get("genres") or [])
        if isinstance(item, dict)
    ]
    tags = [
        {
            "id": item.get("id"),
            "name": item.get("name"),
            "slug": item.get("slug") or _slugify(item.get("name")),
            "language": item.get("language", ""),
        }
        for item in (raw.get("tags") or [])
        if isinstance(item, dict)
    ]

    screenshots_raw = raw.get("screenshots") or raw.get("short_screenshots") or []
    screenshots = []
    for item in screenshots_raw:
        if isinstance(item, dict):
            image = item.get("image")
            if image:
                screenshots.append({"id": item.get("id"), "image": image})
        elif isinstance(item, str):
            screenshots.append({"image": item})

    stores = []
    for entry in raw.get("stores") or []:
        store = entry.get("store") if isinstance(entry, dict) else None
        if isinstance(store, dict):
            stores.append({"id": store.get("id"), "name": store.get("name"), "slug": store.get("slug")})
        elif isinstance(entry, dict):
            stores.append({"id": entry.get("id"), "name": entry.get("name"), "slug": entry.get("slug")})

    description = raw.get("description_raw") or raw.get("description") or None

    return {
        **raw,
        "description": description,
        "genres": genres,
        "platforms": platforms,
        "tags": tags,
        "screenshots": screenshots,
        "stores": stores,
    }


def passes_game_filters(raw: dict[str, Any]) -> tuple[bool, str]:
    """Evaluate whether game filters.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        raw: RAWG API payload or game-like dictionary to normalize or evaluate.

    Returns:
        Tuple containing the primary result and related status metadata."""
    game = normalize_game_payload(raw)
    rawg_id = game.get("id") or game.get("rawg_id")
    slug = game.get("slug")

    if _is_allowlisted(rawg_id, slug):
        return True, "allowlisted"

    released = _parse_date(game.get("released"))
    if released is not None and released > date.today():
        return False, "future_release"

    tags = game.get("tags") or []
    excluded = sorted(
        tag.get("slug") or _slugify(tag.get("name"))
        for tag in tags
        if isinstance(tag, dict) and (tag.get("slug") or _slugify(tag.get("name"))) in EXCLUDED_TAG_SLUGS
    )
    if excluded:
        return False, f"excluded_tag:{excluded[0]}"

    metadata_anchor_count = _metadata_anchor_count(game)
    if metadata_anchor_count < 1:
        return False, "no_metadata_anchor"

    if not (game.get("genres") or game.get("tags") or game.get("platforms")):
        return False, "no_classification_anchor"

    strong_keep_reason = _strong_keep_reason(game)
    if strong_keep_reason:
        return True, strong_keep_reason

    if _is_zero_traction(game, metadata_anchor_count):
        return False, "zero_traction"

    return True, "credible_metadata"


def needs_detail_for_filter(raw: dict[str, Any]) -> bool:
    """Determine whether detail for filter.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        raw: RAWG API payload or game-like dictionary to normalize or evaluate.

    Returns:
        True when the condition is met; otherwise False."""
    game = normalize_game_payload(raw)
    if _strong_keep_reason(game):
        return True
    if _metadata_anchor_count(game) < 2:
        return True
    if not game.get("description") and not game.get("screenshots"):
        return True
    return False


def needs_screenshots_for_filter(raw: dict[str, Any]) -> bool:
    """Determine whether screenshots for filter.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        raw: RAWG API payload or game-like dictionary to normalize or evaluate.

    Returns:
        True when the condition is met; otherwise False."""
    game = normalize_game_payload(raw)
    return not game.get("screenshots") and _metadata_anchor_count(game) < 2


def _metadata_anchor_count(game: dict[str, Any]) -> int:
    """Metadata anchor count.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        game: Game model or normalized game dictionary to inspect.

    Returns:
        Integer value produced by the operation."""
    anchors = [
        bool(game.get("description")),
        bool(game.get("background_image")),
        bool(game.get("screenshots")),
        bool(game.get("website")),
        bool(game.get("stores")),
        bool(game.get("platforms")),
        bool(game.get("genres")),
        bool(game.get("tags")),
    ]
    return sum(1 for value in anchors if value)


def _strong_keep_reason(game: dict[str, Any]) -> str | None:
    """Strong keep reason.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        game: Game model or normalized game dictionary to inspect.

    Returns:
        str | None when a matching value is available; otherwise None."""
    metacritic = _int_or_none(game.get("metacritic"))
    added = _int_or_none(game.get("added"))
    ratings_count = _int_or_none(game.get("ratings_count")) or 0
    rating = _float_or_none(game.get("rating")) or 0.0
    playtime = _int_or_none(game.get("playtime")) or 0

    if metacritic is not None and metacritic >= 60:
        return "metacritic"
    if added is not None and added >= 200:
        return "added"
    if ratings_count >= 100:
        return "ratings_count"
    if rating >= 3.6 and ratings_count >= 10:
        return "credible_rating"
    if rating >= 4.0 and ratings_count >= 5:
        return "cult_rating"
    if playtime > 0 and (added or 0) >= 50:
        return "playtime_added"
    return None


def _is_zero_traction(game: dict[str, Any], metadata_anchor_count: int) -> bool:
    """Check zero traction.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        game: Game model or normalized game dictionary to inspect.
        metadata_anchor_count: metadata anchor count value used by the operation.

    Returns:
        True when the condition is met; otherwise False."""
    ratings_count = _int_or_none(game.get("ratings_count")) or 0
    added = _int_or_none(game.get("added")) or 0
    playtime = _int_or_none(game.get("playtime")) or 0

    return (
        ratings_count == 0
        and added < 20
        and game.get("metacritic") is None
        and playtime == 0
        and metadata_anchor_count < 2
    )


def _is_allowlisted(rawg_id: Any, slug: Any) -> bool:
    """Check allowlisted.

    Evaluates service rules and returns a boolean or reason code without mutating application state.

    Args:
        rawg_id: RAWG game identifier used for allowlist matching.
        slug: Slug used for normalized matching.

    Returns:
        True when the condition is met; otherwise False."""
    return str(rawg_id).lower() in ALLOWLIST or (slug is not None and str(slug).lower() in ALLOWLIST)


def _parse_date(value: Any) -> date | None:
    """Parse date.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        value: Value to store or transform.

    Returns:
        date | None when a matching value is available; otherwise None."""
    if isinstance(value, date):
        return value
    if not value:
        return None
    try:
        return date.fromisoformat(str(value))
    except ValueError:
        return None


def _int_or_none(value: Any) -> int | None:
    """Parse or none.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        value: Value to store or transform.

    Returns:
        int | None when a matching value is available; otherwise None."""
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _float_or_none(value: Any) -> float | None:
    """Parse or none.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        value: Value to store or transform.

    Returns:
        float | None when a matching value is available; otherwise None."""
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _slugify(value: Any) -> str:
    """Create a slug for.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        value: Value to store or transform.

    Returns:
        String value produced by the operation."""
    return str(value or "").strip().lower().replace(" ", "-")
