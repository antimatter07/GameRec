from app.models.recommendation import RecommendationItem
from app.models.user import User


def generate_explanations(user: User, items: list[RecommendationItem]) -> list[str]:
    """
    Generate LLM explanations for why each recommended game matches the user's taste.
    Returns one explanation string per item, in the same order.

    TODO: Build a system prompt describing the task (persona: expert game curator)
    TODO: For each item, include:
          - Game name, genres, tags, short description snippet
          - 2-3 games from the user's library (highest-rated) as reference points
    TODO: Call your chosen LLM provider (OpenAI / Anthropic) with the prompt
          Tip: batch all items in a single call to reduce latency / cost
    TODO: Parse the response into individual explanation strings
    TODO: Cache responses in Redis keyed by (user_id, game_id) with a reasonable TTL
    TODO: Populate RecommendationItem.explanation and .confidence fields
    """
    raise NotImplementedError


def generate_game_dna(user: User) -> dict:
    """
    Produce a full taste profile analysis for a premium user.
    Return value should match the GameDNAOut schema.

    TODO: Gather user's library: top-rated games, favorite genres/tags, preferred era
    TODO: Craft a prompt asking the LLM to produce:
          - top_genres  (name + weight)
          - top_tags    (name + weight)
          - preferred_era
          - description (a 2-3 sentence "gaming identity" paragraph)
          - confidence
    TODO: Cache in Redis (key="game_dna:{user_id}"); invalidate on library change
    TODO: Return the structured dict
    """
    raise NotImplementedError
