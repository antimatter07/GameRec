from collections import defaultdict

from sqlalchemy.orm import Session, joinedload

from app.models.library import LibraryEntry, LibraryStatus
from app.models.recommendation import RecommendationItem
from app.models.user import User

_STATUS_WEIGHTS: dict[LibraryStatus, float] = {
    LibraryStatus.COMPLETED: 4.0,
    LibraryStatus.PLAYING:   3.0,
    LibraryStatus.BACKLOG:   2.0,
    LibraryStatus.DROPPED:   1.0,
}


def generate_game_dna(user: User, db: Session) -> dict:
    """
    Build the premium Game DNA summary from the user's library history.

    This powers the premium game-taste feature by turning a user's tracked and
    rated games into weighted genre, tag, and era signals, then shaping those
    signals into a human-readable summary plus a confidence estimate.
    """
    entries: list[LibraryEntry] = (
        db.query(LibraryEntry)
        .options(joinedload(LibraryEntry.game))
        .filter(LibraryEntry.user_id == user.id)
        .all()
    )

    if not entries:
        return {
            "top_genres":    [],
            "top_tags":      [],
            "preferred_era": None,
            "description":   "Add and rate games in your library to unlock your Game DNA.",
            "confidence":    None,
        }

    genre_weights: dict[str, float] = defaultdict(float)
    tag_weights:   dict[str, float] = defaultdict(float)
    era_weights:   dict[str, float] = defaultdict(float)
    total_weight = 0.0

    for entry in entries:
        if not entry.game:
            continue
        weight = float(entry.rating) if entry.rating is not None else _STATUS_WEIGHTS.get(entry.status, 2.0)
        total_weight += weight

        for genre in (entry.game.genres or []):
            genre_weights[genre["name"]] += weight

        for tag in (entry.game.tags or []):
            if tag.get("language", "eng") not in ("eng", ""):
                continue
            tag_weights[tag["name"]] += weight

        if entry.game.released:
            year = entry.game.released.year
            decade = f"{(year // 10) * 10}s"
            era_weights[decade] += weight

    if total_weight == 0:
        total_weight = 1.0  # avoid division by zero

    top_genres = sorted(
        [{"name": k, "weight": round(v / total_weight, 3)} for k, v in genre_weights.items()],
        key=lambda x: x["weight"],
        reverse=True,
    )[:8]

    top_tags = sorted(
        [{"name": k, "weight": round(v / total_weight, 3)} for k, v in tag_weights.items()],
        key=lambda x: x["weight"],
        reverse=True,
    )[:10]

    preferred_era = max(era_weights, key=era_weights.__getitem__) if era_weights else None

    # Build a description from the computed data
    genre_names = [g["name"] for g in top_genres[:3]]
    tag_names   = [t["name"] for t in top_tags[:3]]
    parts: list[str] = []
    if genre_names:
        parts.append(f"Your gaming identity leans toward {', '.join(genre_names)} games")
    if tag_names:
        parts.append(f"with a love for titles featuring {', '.join(tag_names)}")
    if preferred_era:
        parts.append(f"particularly from the {preferred_era}")
    description = (
        " ".join(parts).capitalize() + "."
        if parts
        else "Keep playing and rating games to build your Game DNA."
    )

    # Confidence scales with library size (saturates at 20 entries → 1.0)
    confidence = round(min(1.0, len(entries) / 20.0), 2)

    return {
        "top_genres":    top_genres,
        "top_tags":      top_tags,
        "preferred_era": preferred_era,
        "description":   description,
        "confidence":    confidence,
    }


def generate_explanations(user: User, items: list[RecommendationItem], db: Session) -> list[str]:
    """
    Generate premium LLM explanations for a recommendation batch.

    Each returned string explains why the matching game fits the user's taste
    profile, and the result order always matches the incoming recommendation
    items.

    Requires ANTHROPIC_API_KEY to be set in settings.  Returns empty strings
    for all items when the key is absent so callers can safely ignore the result.
    """
    from app.config import settings

    if not settings.ANTHROPIC_API_KEY:
        return ["" for _ in items]

    import anthropic

    # Load top-rated games from the user's library as reference points
    top_entries: list[LibraryEntry] = (
        db.query(LibraryEntry)
        .options(joinedload(LibraryEntry.game))
        .filter(
            LibraryEntry.user_id == user.id,
            LibraryEntry.rating.isnot(None),
        )
        .order_by(LibraryEntry.rating.desc())
        .limit(5)
        .all()
    )
    reference_games = [
        f"{e.game.name} ({e.rating}/5)"
        for e in top_entries
        if e.game
    ]

    # Build numbered game list for the prompt
    game_lines: list[str] = []
    for i, item in enumerate(items, start=1):
        game = item.game
        genres = ", ".join(g["name"] for g in (game.genres or [])[:4])
        tags = ", ".join(
            t["name"]
            for t in (game.tags or [])
            if t.get("language", "eng") in ("eng", "")
        )[:120]
        game_lines.append(f"{i}. {game.name} | Genres: {genres} | Tags: {tags}")

    ref_str = ", ".join(reference_games) if reference_games else "not provided"
    prompt = (
        f"The user's favourite games are: {ref_str}.\n\n"
        f"Write a concise 1-2 sentence explanation of why each game below would appeal to this user. "
        f"Be specific about gameplay mechanics and themes.\n\n"
        + "\n".join(game_lines)
        + f"\n\nFormat your response as a numbered list matching the order above "
        f"(1. through {len(items)}.), one explanation per line."
    )

    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system="You are an expert game curator helping users discover games they will love.",
        messages=[{"role": "user", "content": prompt}],
    )

    response_text: str = message.content[0].text
    lines = [ln.strip() for ln in response_text.strip().splitlines() if ln.strip()]

    # Parse numbered lines back into per-item explanations
    explanations: list[str] = [""] * len(items)
    for line in lines:
        for i in range(len(items)):
            prefix_dot   = f"{i + 1}."
            prefix_paren = f"{i + 1})"
            if line.startswith(prefix_dot) or line.startswith(prefix_paren):
                explanations[i] = line[len(prefix_dot):].strip()
                break

    return explanations
