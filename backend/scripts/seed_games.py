"""
Seed the games table from backend/data/games.json.

Run from the backend/ directory:
    python scripts/seed_games.py
"""

import json
import sys
from pathlib import Path

# Allow `from app.xxx import yyy` when run from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.game import Game


def seed_games() -> None:
    data_path = Path(__file__).resolve().parent.parent / "data" / "games.json"
    with open(data_path, encoding="utf-8") as fh:
        raw_games: list[dict] = json.load(fh)

    db = SessionLocal()
    try:
        count = 0
        for raw in raw_games:
            rawg_id: int = raw["id"]

            # Normalize platforms — the RAWG list-endpoint wraps each platform inside
            # a "platform" key: [{"platform": {"id": 1, "name": "PC"}, ...}, ...]
            platforms_raw: list[dict] = raw.get("platforms") or []
            platforms: list[dict] = []
            for entry in platforms_raw:
                if isinstance(entry, dict) and "platform" in entry:
                    p = entry["platform"]
                    platforms.append({"id": p.get("id"), "name": p.get("name")})
                else:
                    platforms.append(entry)

            # Genres and tags are already flat: [{"id": 4, "name": "Action", ...}]
            genres: list[dict] = [
                {"id": g["id"], "name": g["name"]}
                for g in (raw.get("genres") or [])
            ]
            tags: list[dict] = [
                {
                    "id": t["id"],
                    "name": t["name"],
                    "slug": t.get("slug", ""),
                    "language": t.get("language", ""),
                }
                for t in (raw.get("tags") or [])
            ]

            game = db.query(Game).filter(Game.rawg_id == rawg_id).first()
            if game is None:
                game = Game(rawg_id=rawg_id)
                db.add(game)

            game.name = raw["name"]
            game.slug = raw["slug"]
            game.released = raw.get("released")  # SQLAlchemy accepts ISO string
            game.background_image = raw.get("background_image")
            game.rating = raw.get("rating")
            game.ratings_count = raw.get("ratings_count", 0) or 0
            game.metacritic = raw.get("metacritic")
            game.playtime = raw.get("playtime")
            game.genres = genres
            game.platforms = platforms
            game.tags = tags

            count += 1

        db.commit()
        print(f"Seeded {count} games.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_games()
