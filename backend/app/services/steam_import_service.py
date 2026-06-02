from dataclasses import dataclass
from datetime import datetime, timezone
import re

from fastapi import HTTPException, status
from rapidfuzz import fuzz
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.models.game import Game
from app.models.game_external_id import GameExternalId
from app.models.library import LibraryEntry, LibraryStatus
from app.schemas.library import SteamImportGameResult
from app.utils.steam_client import (
    SteamAPIError,
    SteamClient,
    SteamOwnedGame,
    SteamProfileNotFoundError,
    SteamProfilePrivateError,
)

STEAM_PROVIDER = "steam"
AUTO_IMPORT_THRESHOLD = 92.0
LOW_CONFIDENCE_THRESHOLD = 80.0

_EDITION_WORDS = {
    "anniversary",
    "bundle",
    "collection",
    "complete",
    "definitive",
    "deluxe",
    "edition",
    "enhanced",
    "gold",
    "goty",
    "hd",
    "remaster",
    "remastered",
    "standard",
    "ultimate",
}
_ROMAN_NUMERALS = {
    "i": 1,
    "ii": 2,
    "iii": 3,
    "iv": 4,
    "v": 5,
    "vi": 6,
    "vii": 7,
    "viii": 8,
    "ix": 9,
    "x": 10,
}
_NON_WORD_RE = re.compile(r"[^a-z0-9]+")
_SPACE_RE = re.compile(r"\s+")


@dataclass(frozen=True)
class MatchCandidate:
    game: Game
    confidence: float
    reason: str


def normalize_game_title(title: str) -> str:
    """Normalize game title.

    Converts external or user-provided text into the canonical form used for comparison and persistence.

    Args:
        title: Game title to normalize or inspect.

    Returns:
        String value produced by the operation."""
    lowered = title.lower()
    lowered = lowered.replace("&", " and ")
    lowered = lowered.replace("™", " ").replace("®", " ")
    lowered = re.sub(r"\bgame\s+of\s+the\s+year\b", " goty ", lowered)
    cleaned = _NON_WORD_RE.sub(" ", lowered)
    tokens = []
    for token in _SPACE_RE.split(cleaned.strip()):
        if not token or token in _EDITION_WORDS:
            continue
        tokens.append(str(_ROMAN_NUMERALS.get(token, token)))
    return " ".join(tokens)


def sequel_tokens(title: str) -> set[int]:
    """Sequel tokens.

    Performs the service operation behind a stable module-level interface.

    Args:
        title: Game title to normalize or inspect.

    Returns:
        set[int] produced by the operation."""
    normalized = normalize_game_title(title)
    tokens: set[int] = set()
    for token in normalized.split():
        if token.isdigit():
            number = int(token)
            if 0 < number < 100:
                tokens.add(number)
    return tokens


def _has_sequel_conflict(steam_title: str, candidate_title: str) -> bool:
    """Check whether sequel conflict.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        steam_title: Steam game title being matched.
        candidate_title: Candidate game title being compared.

    Returns:
        True when the condition is met; otherwise False."""
    steam_numbers = sequel_tokens(steam_title)
    candidate_numbers = sequel_tokens(candidate_title)
    return bool(steam_numbers and candidate_numbers and steam_numbers != candidate_numbers)


def _score_candidate(steam_title: str, candidate_title: str) -> float:
    """Score candidate.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        steam_title: Steam game title being matched.
        candidate_title: Candidate game title being compared.

    Returns:
        Floating-point value produced by the operation."""
    if _has_sequel_conflict(steam_title, candidate_title):
        return 0.0

    steam_normalized = normalize_game_title(steam_title)
    candidate_normalized = normalize_game_title(candidate_title)
    if not steam_normalized or not candidate_normalized:
        return 0.0

    score = float(fuzz.WRatio(steam_normalized, candidate_normalized))
    steam_numbers = sequel_tokens(steam_title)
    candidate_numbers = sequel_tokens(candidate_title)
    if steam_numbers != candidate_numbers and (steam_numbers or candidate_numbers):
        score -= 15.0
    return max(0.0, min(100.0, score))


def _best_by_popularity(games: list[Game]) -> Game:
    """Select the best by popularity.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        games: Candidate game records considered by the matching algorithm.

    Returns:
        Game produced by the operation."""
    return max(
        games,
        key=lambda game: (
            game.ratings_count or 0,
            game.rating or 0,
            game.metacritic or 0,
        ),
    )


def _build_result(
    steam_game: SteamOwnedGame,
    candidate: MatchCandidate | None = None,
    entry: LibraryEntry | None = None,
    reason: str | None = None,
) -> SteamImportGameResult:
    """Build result.

    Aggregates source data for recommendation and AI workflows.

    Args:
        steam_game: Steam library game returned by the Steam API client.
        candidate: AI pick candidate or game candidate to resolve. Defaults to None.
        entry: entry value used by the operation. Defaults to None.
        reason: reason value used by the operation. Defaults to None.

    Returns:
        SteamImportGameResult produced by the operation."""
    return SteamImportGameResult(
        steam_app_id=steam_game.appid,
        steam_name=steam_game.name,
        game=candidate.game if candidate else None,
        library_entry_id=entry.id if entry else None,
        match_confidence=candidate.confidence if candidate else None,
        reason=reason or (candidate.reason if candidate else None),
    )


def _find_match(db: Session, steam_game: SteamOwnedGame, games: list[Game], exact_index: dict[str, list[Game]]) -> MatchCandidate | None:
    """Find match.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        steam_game: Steam library game returned by the Steam API client.
        games: Candidate game records considered by the matching algorithm.
        exact_index: exact index value used by the operation.

    Returns:
        MatchCandidate | None when a matching value is available; otherwise None."""
    external = (
        db.query(GameExternalId)
        .options(joinedload(GameExternalId.game))
        .filter(GameExternalId.provider == STEAM_PROVIDER, GameExternalId.external_id == str(steam_game.appid))
        .first()
    )
    if external:
        return MatchCandidate(game=external.game, confidence=100.0, reason="steam_app_id")

    normalized = normalize_game_title(steam_game.name)
    exact_matches = [game for game in exact_index.get(normalized, []) if not _has_sequel_conflict(steam_game.name, game.name)]
    if exact_matches:
        return MatchCandidate(game=_best_by_popularity(exact_matches), confidence=100.0, reason="exact_title")

    best_game: Game | None = None
    best_score = 0.0
    for game in games:
        score = _score_candidate(steam_game.name, game.name)
        if score > best_score:
            best_game = game
            best_score = score

    if best_game and best_score >= LOW_CONFIDENCE_THRESHOLD:
        return MatchCandidate(game=best_game, confidence=round(best_score, 2), reason="fuzzy_title")
    return None


def _steam_datetime(timestamp: int | None) -> datetime | None:
    """Convert a Steam timestamp to datetime.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        timestamp: Unix timestamp value returned by Steam.

    Returns:
        datetime | None when a matching value is available; otherwise None."""
    if not timestamp:
        return None
    return datetime.fromtimestamp(int(timestamp), tz=timezone.utc)


def _apply_steam_metadata(entry: LibraryEntry, steam_game: SteamOwnedGame, confidence: float) -> None:
    """Apply steam metadata.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        entry: entry value used by the operation.
        steam_game: Steam library game returned by the Steam API client.
        confidence: Match confidence score assigned to the imported library entry.

    Returns:
        None."""
    entry.steam_app_id = steam_game.appid
    entry.steam_playtime_forever_minutes = steam_game.playtime_forever
    entry.steam_playtime_2weeks_minutes = steam_game.playtime_2weeks
    entry.steam_last_played_at = _steam_datetime(steam_game.rtime_last_played)
    entry.steam_imported_at = datetime.now(timezone.utc)
    entry.steam_import_name = steam_game.name[:255]
    entry.steam_match_confidence = confidence


def _ensure_external_id(db: Session, game_id: int, steam_app_id: int) -> None:
    """Ensure external ID.

    Encapsulates reusable service-layer logic used by the public functions in this module.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        game_id: ID of the game to read, update, or associate with the operation.
        steam_app_id: Steam application ID associated with the game.

    Returns:
        None."""
    existing = (
        db.query(GameExternalId)
        .filter(GameExternalId.provider == STEAM_PROVIDER, GameExternalId.external_id == str(steam_app_id))
        .first()
    )
    if existing:
        return
    db.add(GameExternalId(provider=STEAM_PROVIDER, external_id=str(steam_app_id), game_id=game_id))


def import_steam_library(db: Session, user_id: int, steam_profile: str, client: SteamClient | None = None) -> dict:
    """Import steam library.

    Performs the service operation behind a stable module-level interface.

    Args:
        db: SQLAlchemy database session used to query or persist application data.
        user_id: ID of the user whose data should be read or modified.
        steam_profile: Steam vanity URL, profile URL, or Steam ID to import from.
        client: Optional Steam API client instance. Defaults to the production client.

    Returns:
        Dictionary containing serialized service state and metadata.

    Raises:
        HTTPException: When the resource is missing or the user cannot perform the operation."""
    steam = client or SteamClient()
    try:
        steam_id = steam.resolve_steam_id(steam_profile)
        profile = steam.ensure_public_profile(steam_id)
        owned_games = steam.get_owned_games(steam_id)
    except SteamProfilePrivateError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except SteamProfileNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except SteamAPIError as exc:
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    games = db.query(Game).all()
    exact_index: dict[str, list[Game]] = {}
    for game in games:
        exact_index.setdefault(normalize_game_title(game.name), []).append(game)

    added: list[SteamImportGameResult] = []
    already_in_library: list[SteamImportGameResult] = []
    skipped_low_confidence: list[SteamImportGameResult] = []
    unmatched: list[SteamImportGameResult] = []

    existing_entries = {
        entry.game_id: entry
        for entry in db.query(LibraryEntry).filter(LibraryEntry.user_id == user_id).all()
    }

    for steam_game in owned_games:
        candidate = _find_match(db, steam_game, games, exact_index)
        if not candidate:
            unmatched.append(_build_result(steam_game, reason="No local catalog match"))
            continue

        if candidate.confidence < AUTO_IMPORT_THRESHOLD:
            skipped_low_confidence.append(_build_result(steam_game, candidate, reason="Low confidence match"))
            continue

        existing_entry = existing_entries.get(candidate.game.id)
        if existing_entry:
            _apply_steam_metadata(existing_entry, steam_game, candidate.confidence)
            _ensure_external_id(db, candidate.game.id, steam_game.appid)
            already_in_library.append(_build_result(steam_game, candidate, existing_entry, "Already in library"))
            continue

        entry = LibraryEntry(
            user_id=user_id,
            game_id=candidate.game.id,
            status=LibraryStatus.BACKLOG,
        )
        _apply_steam_metadata(entry, steam_game, candidate.confidence)
        db.add(entry)
        db.flush()
        existing_entries[candidate.game.id] = entry
        _ensure_external_id(db, candidate.game.id, steam_game.appid)
        added.append(_build_result(steam_game, candidate, entry, "Imported as backlog"))

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Steam import conflicted with existing data.") from exc

    for result in [*added, *already_in_library]:
        if result.library_entry_id is not None:
            entry = (
                db.query(LibraryEntry)
                .filter(LibraryEntry.id == result.library_entry_id)
                .options(joinedload(LibraryEntry.game))
                .first()
            )
            if entry:
                result.game = entry.game

    return {
        "steam_id": steam_id,
        "profile_name": profile.get("personaname"),
        "added": added,
        "already_in_library": already_in_library,
        "skipped_low_confidence": skipped_low_confidence,
        "unmatched": unmatched,
    }
