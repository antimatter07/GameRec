import httpx

from app.config import settings


class RAWGClient:
    """
    Thin wrapper around the RAWG REST API.
    Docs: https://api.rawg.io/docs/
    """

    def __init__(self) -> None:
        self.base_url = settings.RAWG_BASE_URL
        self.api_key  = settings.RAWG_API_KEY

    def _params(self, extra: dict | None = None) -> dict:
        return {"key": self.api_key, **(extra or {})}

    def get_games(self, page: int = 1, page_size: int = 40, **filters) -> dict:
        """
        GET /games — paginated list with optional filters.

        Supported RAWG filter params (pass as keyword args):
          genres, platforms, tags, dates (YYYY-MM-DD,YYYY-MM-DD), ordering
        TODO: Handle non-200 responses gracefully (log + raise)
        TODO: Consider an async version (httpx.AsyncClient) if called from async routes
        """
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{self.base_url}/games",
                params=self._params({"page": page, "page_size": page_size, **filters}),
            )
            response.raise_for_status()
            return response.json()

    def get_game_detail(self, rawg_id: int) -> dict:
        """GET /games/{id} — full game detail including description."""
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{self.base_url}/games/{rawg_id}",
                params=self._params(),
            )
            response.raise_for_status()
            return response.json()

    def get_game_screenshots(self, rawg_id: int) -> dict:
        """GET /games/{id}/screenshots"""
        # TODO: Implement
        raise NotImplementedError

    # TODO: Add get_genres(), get_platforms(), get_tags() if you want to
    #       pre-populate filter dropdowns in the frontend


rawg_client = RAWGClient()
