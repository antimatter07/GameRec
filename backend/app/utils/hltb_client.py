"""
Wrapper around howlongtobeatpy for fetching HLTB playtime data.

Since HLTB has no official API, this library reverse-engineers their search
endpoint. Treat results as "nice to have" — the endpoint can change at any time.
"""
import asyncio
import logging

from howlongtobeatpy import HowLongToBeat
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

# Minimum fuzzy-match confidence (0–100) required to accept an HLTB result.
# Below this threshold the top result is considered a different game entirely.
HLTB_CONFIDENCE_THRESHOLD = 80

# Seconds to sleep between successive HLTB requests in the bulk script.
# The Celery task uses countdown staggering instead.
HLTB_RATE_LIMIT_SLEEP = 1.5


async def fetch_hltb(title: str) -> dict | None:
    """Fetch HowLongToBeat playtime data.

    Searches HowLongToBeat asynchronously, fuzzy-matches the best result, and
    returns playtime hours only when confidence is high enough.

    Args:
        title: Game title to search or normalize.

    Returns:
        dict | None when data is available; otherwise None."""
    try:
        results = await HowLongToBeat().async_search(title)
    except Exception as exc:
        logger.warning("HLTB search failed for %r: %s", title, exc)
        return None

    if not results:
        logger.debug("HLTB: no results for %r", title)
        return None

    best = results[0]
    score = fuzz.token_sort_ratio(title.lower(), best.game_name.lower())

    if score < HLTB_CONFIDENCE_THRESHOLD:
        logger.debug(
            "HLTB: low confidence for %r → %r (score=%d, threshold=%d)",
            title, best.game_name, score, HLTB_CONFIDENCE_THRESHOLD,
        )
        return None

    logger.debug("HLTB match: %r → %r (score=%d)", title, best.game_name, score)

    def _hours(val: float) -> float | None:
        """Convert an HLTB hour value.

        Treats HLTB sentinel and empty values as missing data while preserving
        positive playtime estimates as floats.

        Args:
            val: Raw HLTB hour value to normalize.

        Returns:
            float | None when data is available; otherwise None."""
        return float(val) if val and val > 0 else None

    return {
        "main":          _hours(best.main_story),
        "main_extra":    _hours(best.main_extra),
        "completionist": _hours(best.completionist),
    }
