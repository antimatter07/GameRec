"""
Compute and store L2-normalised feature vectors for all Game rows.

Run from the backend/ directory:
    python scripts/build_vectors.py

Vector layout (per game):
    [ multi-hot genres (len=G) | multi-hot top-150 tags (len=150)
      | metacritic/100 | rating/5 ]

The vocabulary is saved to data/vocab.json so the recommendation service can
reconstruct taste profiles using the same index ordering.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np

# Allow `from app.xxx import yyy` when run from the backend/ directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.database import SessionLocal
from app.models.game import Game

# ---------------------------------------------------------------------------
# Tag slugs to exclude before building the tag vocabulary (noise / platform
# meta-data that carries no semantic signal for recommendation).
# ---------------------------------------------------------------------------
NOISE_SLUGS: set[str] = {
    "steam-achievements",
    "steam-cloud",
    "steam-trading-cards",
    "steam-workshop",
    "full-controller-support",
    "xbox-live",
    "playstation-network",
    "online-co-op",
    "remote-play",
    "vr-support",
    "hdr",
    "partial-controller-support",
}

TOP_TAG_LIMIT = 150


def build_vectors() -> None:
    db = SessionLocal()
    try:
        games: list[Game] = db.query(Game).all()
        if not games:
            print("No games found in the database. Run seed_games.py first.")
            return

        # ------------------------------------------------------------------
        # 1. Build genre vocabulary (all unique genre IDs, sorted for stability)
        # ------------------------------------------------------------------
        genre_id_set: set[int] = set()
        for game in games:
            for g in (game.genres or []):
                genre_id_set.add(g["id"])
        genre_ids: list[int] = sorted(genre_id_set)
        genre_index: dict[int, int] = {gid: i for i, gid in enumerate(genre_ids)}

        # ------------------------------------------------------------------
        # 2. Build tag vocabulary — English only, no noise slugs, top 150 by
        #    frequency across all games.
        # ------------------------------------------------------------------
        tag_counter: Counter = Counter()
        tag_meta: dict[int, dict] = {}  # id -> {slug, name}
        for game in games:
            seen_in_game: set[int] = set()
            for t in (game.tags or []):
                tid = t["id"]
                slug = t.get("slug", "")
                lang = t.get("language", "")
                if lang and lang != "eng":
                    continue
                if slug in NOISE_SLUGS:
                    continue
                if tid not in seen_in_game:
                    tag_counter[tid] += 1
                    seen_in_game.add(tid)
                if tid not in tag_meta:
                    tag_meta[tid] = {"slug": slug, "name": t.get("name", "")}

        top_tag_ids: list[int] = [tid for tid, _ in tag_counter.most_common(TOP_TAG_LIMIT)]
        tag_index: dict[int, int] = {tid: i for i, tid in enumerate(top_tag_ids)}

        # ------------------------------------------------------------------
        # 3. Compute per-game feature vectors and store them.
        # ------------------------------------------------------------------
        vector_dim = len(genre_ids) + TOP_TAG_LIMIT + 2  # +2 for metacritic & rating

        updated = 0
        for game in games:
            vec = np.zeros(vector_dim, dtype=np.float32)

            # Multi-hot genres
            for g in (game.genres or []):
                idx = genre_index.get(g["id"])
                if idx is not None:
                    vec[idx] = 1.0

            # Multi-hot top-150 tags (English, non-noise only)
            tag_offset = len(genre_ids)
            for t in (game.tags or []):
                tid = t["id"]
                lang = t.get("language", "")
                slug = t.get("slug", "")
                if lang and lang != "eng":
                    continue
                if slug in NOISE_SLUGS:
                    continue
                idx = tag_index.get(tid)
                if idx is not None:
                    vec[tag_offset + idx] = 1.0

            # Scalar features
            mc_offset = tag_offset + TOP_TAG_LIMIT
            vec[mc_offset] = (game.metacritic / 100.0) if game.metacritic else 0.0
            vec[mc_offset + 1] = (game.rating / 5.0) if game.rating else 0.0

            # L2 normalise
            norm = float(np.linalg.norm(vec))
            if norm > 0:
                vec = vec / norm

            game.feature_vector = vec.tolist()
            updated += 1

        db.commit()

        # ------------------------------------------------------------------
        # 4. Save vocabulary for use by the recommendation service.
        # ------------------------------------------------------------------
        vocab_path = Path(__file__).resolve().parent.parent / "data" / "vocab.json"
        vocab = {
            "genres": genre_ids,
            "tags": top_tag_ids,
        }
        with open(vocab_path, "w", encoding="utf-8") as fh:
            json.dump(vocab, fh)

        print(
            f"Built vectors for {updated} games, "
            f"vocab: {len(genre_ids)} genres, {len(top_tag_ids)} tags."
        )
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    build_vectors()
