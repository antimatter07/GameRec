import httpx
import pytest

from app.config import settings
from app.utils.rawg_client import RAWGClient, RAWGQuotaExceeded, RAWGRetryableError


def _client_with_transport(monkeypatch, handler):
    transport = httpx.MockTransport(handler)
    real_client = httpx.Client

    def factory(*args, **kwargs):
        kwargs["transport"] = transport
        return real_client(*args, **kwargs)

    monkeypatch.setattr(httpx, "Client", factory)
    return RAWGClient()


def test_get_games_page_passes_query_params(monkeypatch):
    def handler(request):
        assert request.url.params["key"] == settings.RAWG_API_KEY
        assert request.url.params["page"] == "2"
        assert request.url.params["page_size"] == "20"
        assert request.url.params["ordering"] == "-added"
        return httpx.Response(200, json={"results": []})

    client = _client_with_transport(monkeypatch, handler)

    assert client.get_games_page(page=2, page_size=20, ordering="-added") == {"results": []}


def test_get_game_screenshots_parses_results(monkeypatch):
    def handler(request):
        assert request.url.path.endswith("/games/123/screenshots")
        return httpx.Response(200, json={"results": [{"id": 1, "image": "cover.jpg"}]})

    client = _client_with_transport(monkeypatch, handler)

    assert client.get_game_screenshots(123)["results"][0]["image"] == "cover.jpg"


def test_429_raises_quota_error(monkeypatch):
    client = _client_with_transport(monkeypatch, lambda request: httpx.Response(429, json={}))

    with pytest.raises(RAWGQuotaExceeded):
        client.get_games_page()


def test_5xx_raises_retryable_error(monkeypatch):
    client = _client_with_transport(monkeypatch, lambda request: httpx.Response(503, json={}))

    with pytest.raises(RAWGRetryableError):
        client.get_games_page()
