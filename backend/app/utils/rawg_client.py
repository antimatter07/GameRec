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
        """Initialize the client.

        Stores endpoint, credential, and timeout configuration used by subsequent client calls.

        Returns:
            None."""
        self.base_url = settings.RAWG_BASE_URL
        self.api_key  = settings.RAWG_API_KEY

    def _params(self, extra: dict | None = None) -> dict:
        """Build RAWG request parameters.

        Adds the configured RAWG API key to optional caller-provided filters so
        every outbound request has the required authentication parameter.

        Args:
            extra: Optional additional query parameters to merge into the request. Defaults to None.

    Returns:
            Dictionary containing the RAWG API key plus any additional parameters."""
        return {"key": self.api_key, **(extra or {})}

    def _get(self, path: str, params: dict[str, Any] | None = None) -> dict:
        """Send a GET request to the RAWG API.

        Performs a synchronous HTTP request, decodes the JSON response, and
        maps RAWG quota, server, and client failures to application exceptions.

        Args:
            path: API path to request, relative to the configured base URL.
            params: Query parameters to send with the API request. Defaults to None.

    Returns:
            Decoded RAWG JSON response payload.

        Raises:
            RAWGClientError: When RAWG returns a non-retryable client error.
            RAWGRetryableError: When RAWG returns a transient failure that Celery may retry.
            RAWGQuotaExceeded: When RAWG reports that the request quota has been exhausted."""
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
        """Get games page.

        Requests a paginated `/games` result set from RAWG, dropping any filters
        whose values are None before sending the request.

        Args:
            page: One-based page number to request. Defaults to 1.
            page_size: Number of records to request per page. Defaults to None.
            filters: Additional RAWG filter parameters to include in the request.

    Returns:
            RAWG paginated games response payload."""
        clean_filters = {key: value for key, value in filters.items() if value is not None}
        return self._get(
            "/games",
            {"page": page, "page_size": page_size or settings.RAWG_PAGE_SIZE, **clean_filters},
        )

    def get_games(self, page: int = 1, page_size: int = 40, **filters) -> dict:
        """Get games.

        Backward-compatible wrapper around `get_games_page` with a default page
        size of 40 for older service code.

        Args:
            page: One-based page number to request. Defaults to 1.
            page_size: Number of records to request per page. Defaults to 40.
            filters: Additional RAWG filter parameters to include in the request.

    Returns:
            RAWG paginated games response payload."""
        return self.get_games_page(page=page, page_size=page_size, **filters)

    def get_game_detail(self, rawg_id: int) -> dict:
        """Get game detail.

        Requests the full RAWG detail payload for one game, including fields not
        present on list responses such as the long description.

        Args:
            rawg_id: RAWG game identifier to fetch or synchronize.

    Returns:
            RAWG game detail response payload."""
        return self._get(f"/games/{rawg_id}")

    def get_game_screenshots(self, rawg_id: int) -> dict:
        """Get game screenshots.

        Requests the RAWG screenshots payload for one game so filters and
        catalog enrichment can use media presence as a metadata anchor.

        Args:
            rawg_id: RAWG game identifier to fetch or synchronize.

    Returns:
            RAWG screenshot response payload."""
        return self._get(f"/games/{rawg_id}/screenshots")

    def iter_catalog_pass(
        self,
        pass_name: str,
        page: int = 1,
        page_size: int | None = None,
        days_back: int = 60,
    ) -> dict:
        """Fetch catalog pass.

        Resolves a named catalog pass to RAWG filters and requests the matching
        page of list results.

        Args:
            pass_name: Named RAWG catalog pass that determines filter parameters.
            page: One-based page number to request. Defaults to 1.
            page_size: Number of records to request per page. Defaults to None.
            days_back: Number of recent days to include for recent-release discovery. Defaults to 60.

    Returns:
            RAWG paginated games response payload for the selected pass."""
        return self.get_games_page(
            page=page,
            page_size=page_size,
            **catalog_pass_filters(pass_name, days_back=days_back),
        )

    # TODO: Add get_genres(), get_platforms(), get_tags() if you want to
    #       pre-populate filter dropdowns in the frontend


def catalog_pass_filters(pass_name: str, days_back: int = 60) -> dict[str, str]:
    """Build pass filters.

    Maps application catalog pass names to RAWG query filters, including date windows for recent releases.

    Args:
        pass_name: Named RAWG catalog pass that determines filter parameters.
        days_back: Number of recent days to include for recent-release discovery. Defaults to 60.

    Returns:
        RAWG filter dictionary for the selected catalog pass.

    Raises:
        ValueError: When supplied input cannot be validated or mapped to a supported operation."""
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
