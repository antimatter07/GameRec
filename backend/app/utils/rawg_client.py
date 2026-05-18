from datetime import date, timedelta
from typing import Any

import httpx

from app.config import settings


class RAWGClientError(RuntimeError):
    pass


class RAWGRetryableError(RAWGClientError):
    pass


class RAWGQuotaExceeded(RAWGRetryableError):
    pass


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

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        with httpx.Client(timeout=20) as client:
            try:
                response = client.get(f"{self.base_url}{path}", params=self._params(params))
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                status_code = exc.response.status_code
                if status_code == 429:
                    raise RAWGQuotaExceeded("RAWG request limit exceeded") from exc
                if status_code >= 500:
                    raise RAWGRetryableError(f"RAWG server error: {status_code}") from exc
                raise RAWGClientError(f"RAWG request failed: {status_code}") from exc
            except httpx.RequestError as exc:
                raise RAWGRetryableError("RAWG request failed before receiving a response") from exc

    def get_games_page(self, page: int = 1, page_size: int | None = None, **filters) -> dict:
        """
        GET /games — paginated list with optional filters.

        Supported RAWG filter params (pass as keyword args):
          genres, platforms, tags, dates (YYYY-MM-DD,YYYY-MM-DD), ordering,
          metacritic
        TODO: Consider an async version (httpx.AsyncClient) if called from async routes
        """
        clean_filters = {key: value for key, value in filters.items() if value is not None}
        return self._get(
            "/games",
            {"page": page, "page_size": page_size or settings.RAWG_PAGE_SIZE, **clean_filters},
        )

    def get_games(self, page: int = 1, page_size: int = 40, **filters) -> dict:
        return self.get_games_page(page=page, page_size=page_size, **filters)

    def get_game_detail(self, rawg_id: int) -> dict:
        """GET /games/{id} — full game detail including description."""
        return self._get(f"/games/{rawg_id}")

    def get_game_screenshots(self, rawg_id: int) -> dict:
        """GET /games/{id}/screenshots"""
        return self._get(f"/games/{rawg_id}/screenshots")

    def iter_catalog_pass(
        self,
        pass_name: str,
        page: int = 1,
        page_size: int | None = None,
        days_back: int = 60,
    ) -> dict:
        return self.get_games_page(
            page=page,
            page_size=page_size,
            **catalog_pass_filters(pass_name, days_back=days_back),
        )

    # TODO: Add get_genres(), get_platforms(), get_tags() if you want to
    #       pre-populate filter dropdowns in the frontend


def catalog_pass_filters(pass_name: str, days_back: int = 60) -> dict[str, str]:
    if pass_name == "popular_added":
        return {"ordering": "-added"}
    if pass_name == "metacritic":
        return {"metacritic": "60,100", "ordering": "-metacritic"}
    if pass_name == "high_rating":
        return {"ordering": "-rating"}
    if pass_name == "recent_releases":
        today = date.today()
        start = today - timedelta(days=days_back)
        return {"dates": f"{start.isoformat()},{today.isoformat()}", "ordering": "-released"}
    raise ValueError(f"Unknown RAWG catalog pass: {pass_name}")


rawg_client = RAWGClient()
