from dataclasses import dataclass
from urllib.parse import urlparse
import re

import httpx

from app.config import settings


class SteamAPIError(RuntimeError):
    pass


class SteamProfilePrivateError(SteamAPIError):
    pass


class SteamProfileNotFoundError(SteamAPIError):
    pass


@dataclass(frozen=True)
class SteamOwnedGame:
    appid: int
    name: str
    playtime_forever: int | None = None
    playtime_2weeks: int | None = None
    rtime_last_played: int | None = None


_STEAM_ID_RE = re.compile(r"^\d{17}$")


def extract_steam_identifier(value: str) -> str:
    """Extract a Steam profile identifier.

    Accepts SteamID64 values and common Steam profile URL forms, normalizing
    them to an identifier for later Steam Web API resolution.

    Args:
        value: Raw user-provided Steam profile value to parse.

    Returns:
        SteamID64 or vanity identifier extracted from the input.

    Raises:
        SteamProfileNotFoundError: When a Steam profile identifier cannot be parsed or resolved."""
    raw = value.strip()
    if not raw:
        raise SteamProfileNotFoundError("Enter a SteamID64 or Steam profile URL.")
    if _STEAM_ID_RE.match(raw):
        return raw

    parsed = urlparse(raw if "://" in raw else f"https://{raw}")
    parts = [part for part in parsed.path.split("/") if part]
    if parsed.netloc and "steamcommunity.com" not in parsed.netloc.lower():
        raise SteamProfileNotFoundError("Enter a valid steamcommunity.com profile URL.")

    if len(parts) >= 2 and parts[0].lower() == "profiles" and _STEAM_ID_RE.match(parts[1]):
        return parts[1]
    if len(parts) >= 2 and parts[0].lower() == "id":
        return parts[1]
    if len(parts) == 1 and parts[0]:
        return parts[0]

    raise SteamProfileNotFoundError("Could not read a Steam profile from that value.")


class SteamClient:
    def __init__(self, api_key: str | None = None, base_url: str | None = None, timeout: float = 15.0):
        """Initialize the client.

        Stores endpoint, credential, and timeout configuration used by subsequent client calls.

        Args:
            api_key: Optional API key override. Defaults to the configured service API key.
            base_url: Optional API base URL override. Defaults to application settings.
            timeout: HTTP request timeout in seconds. Defaults to 15.0.

        Returns:
            None."""
        self.api_key = api_key if api_key is not None else settings.STEAM_API_KEY
        self.base_url = (base_url if base_url is not None else settings.STEAM_API_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _require_key(self) -> None:
        """Require a configured Steam API key.

        Verifies that Steam imports are configured before making outbound
        requests that would otherwise fail with ambiguous provider errors.

        Returns:
            None.

        Raises:
            SteamAPIError: When the Steam Web API is unavailable, misconfigured, or returns invalid data."""
        if not self.api_key:
            raise SteamAPIError("Steam import is not configured. Set STEAM_API_KEY.")

    def _get(self, path: str, params: dict) -> dict:
        """Send a GET request to the Steam Web API.

        Adds authentication and JSON format parameters, performs the HTTP
        request, and maps transport or decoding failures to `SteamAPIError`.

        Args:
            path: API path to request, relative to the configured base URL.
            params: Query parameters to send with the API request.

    Returns:
            Decoded Steam Web API JSON response.

        Raises:
            SteamAPIError: When the Steam Web API is unavailable, misconfigured, or returns invalid data."""
        self._require_key()
        try:
            response = httpx.get(
                f"{self.base_url}{path}",
                params={**params, "key": self.api_key, "format": "json"},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except httpx.HTTPError as exc:
            raise SteamAPIError("Steam API request failed. Please try again later.") from exc
        except ValueError as exc:
            raise SteamAPIError("Steam API returned an unreadable response.") from exc

    def resolve_steam_id(self, steam_profile: str) -> str:
        """Resolve steam ID.

        Converts a SteamID64 or vanity profile input into a canonical SteamID64
        using the Steam vanity resolution endpoint when needed.

        Args:
            steam_profile: Steam vanity URL, profile URL, or Steam ID to resolve.

    Returns:
            Canonical SteamID64 for the supplied profile.

        Raises:
            SteamProfileNotFoundError: When a Steam profile identifier cannot be parsed or resolved."""
        identifier = extract_steam_identifier(steam_profile)
        if _STEAM_ID_RE.match(identifier):
            return identifier

        payload = self._get("/ISteamUser/ResolveVanityURL/v1/", {"vanityurl": identifier})
        response = payload.get("response") or {}
        if response.get("success") != 1 or not response.get("steamid"):
            raise SteamProfileNotFoundError("Could not resolve that Steam vanity profile.")
        return str(response["steamid"])

    def ensure_public_profile(self, steam_id: str) -> dict:
        """Ensure public profile.

        Loads the Steam player summary and verifies that the community profile
        is public before library import continues.

        Args:
            steam_id: SteamID64 value used for Steam Web API requests.

    Returns:
            Steam player summary payload for the public profile.

        Raises:
            SteamProfileNotFoundError: When a Steam profile identifier cannot be parsed or resolved.
            SteamProfilePrivateError: When the Steam profile or owned-games library is private."""
        payload = self._get("/ISteamUser/GetPlayerSummaries/v2/", {"steamids": steam_id})
        players = (payload.get("response") or {}).get("players") or []
        if not players:
            raise SteamProfileNotFoundError("Steam profile was not found.")

        player = players[0]
        if player.get("communityvisibilitystate") != 3:
            raise SteamProfilePrivateError("That Steam profile or library is private. Make it public and try again.")
        return player

    def get_owned_games(self, steam_id: str) -> list[SteamOwnedGame]:
        """Get owned games.

        Performs the external API request, validates the response, and returns normalized response data.

        Args:
            steam_id: SteamID64 value used for Steam Web API requests.

        Returns:
            List of normalized result objects.

        Raises:
            SteamProfilePrivateError: When the Steam profile or owned-games library is private."""
        payload = self._get(
            "/IPlayerService/GetOwnedGames/v1/",
            {
                "steamid": steam_id,
                "include_appinfo": "true",
                "include_played_free_games": "true",
            },
        )
        response = payload.get("response") or {}
        games = response.get("games")
        if games is None:
            if response.get("game_count") == 0:
                return []
            raise SteamProfilePrivateError("Steam did not return an owned-games list. Check library privacy settings.")

        owned: list[SteamOwnedGame] = []
        for game in games:
            appid = game.get("appid")
            name = game.get("name")
            if appid is None or not name:
                continue
            owned.append(
                SteamOwnedGame(
                    appid=int(appid),
                    name=str(name),
                    playtime_forever=game.get("playtime_forever"),
                    playtime_2weeks=game.get("playtime_2weeks"),
                    rtime_last_played=game.get("rtime_last_played"),
                )
            )
        return owned
