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
        self.api_key = api_key if api_key is not None else settings.STEAM_API_KEY
        self.base_url = (base_url if base_url is not None else settings.STEAM_API_BASE_URL).rstrip("/")
        self.timeout = timeout

    def _require_key(self) -> None:
        if not self.api_key:
            raise SteamAPIError("Steam import is not configured. Set STEAM_API_KEY.")

    def _get(self, path: str, params: dict) -> dict:
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
        identifier = extract_steam_identifier(steam_profile)
        if _STEAM_ID_RE.match(identifier):
            return identifier

        payload = self._get("/ISteamUser/ResolveVanityURL/v1/", {"vanityurl": identifier})
        response = payload.get("response") or {}
        if response.get("success") != 1 or not response.get("steamid"):
            raise SteamProfileNotFoundError("Could not resolve that Steam vanity profile.")
        return str(response["steamid"])

    def ensure_public_profile(self, steam_id: str) -> dict:
        payload = self._get("/ISteamUser/GetPlayerSummaries/v2/", {"steamids": steam_id})
        players = (payload.get("response") or {}).get("players") or []
        if not players:
            raise SteamProfileNotFoundError("Steam profile was not found.")

        player = players[0]
        if player.get("communityvisibilitystate") != 3:
            raise SteamProfilePrivateError("That Steam profile or library is private. Make it public and try again.")
        return player

    def get_owned_games(self, steam_id: str) -> list[SteamOwnedGame]:
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
