"""
Bulk-enrich games with HowLongToBeat playtime data.

Run from the backend/ directory:
    python scripts/enrich_hltb.py           # all un-enriched games
    python scripts/enrich_hltb.py --limit 5 # test run on 5 games

This script is the recommended way to do the initial backfill. After that,
the hltb_sync.enrich_all_hltb Celery task keeps new games enriched automatically.
"""
import argparse
import asyncio
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

# Make sure the backend package is importable when run from backend/
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.database import SessionLocal
from app.models.game import Game
from app.utils.hltb_client import HLTB_RATE_LIMIT_SLEEP, fetch_hltb


def main() -> None:
    parser = argparse.ArgumentParser(description="Enrich games with HLTB playtime data.")
    parser.add_argument(
        "--limit", type=int, default=None,
        help="Maximum number of games to process (useful for testing).",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        query = (
            db.query(Game)
            .filter(Game.hltb_synced_at.is_(None))
            .order_by(Game.id)
        )
        if args.limit:
            query = query.limit(args.limit)
        games = query.all()
    except Exception:
        db.close()
        raise

    total = len(games)
    print(f"Enriching {total} game(s) with HLTB data …\n")

    matched = 0
    skipped = 0

    for i, game in enumerate(games, start=1):
        print(f"[{i}/{total}] {game.name!r} (id={game.id}) … ", end="", flush=True)
        try:
            result = asyncio.run(fetch_hltb(game.name))
        except Exception as exc:
            print(f"ERROR: {exc}")
            game.hltb_synced_at = datetime.now(timezone.utc)
            skipped += 1
        else:
            if result is not None:
                game.hltb_main_hours          = result["main"]
                game.hltb_main_extra_hours    = result["main_extra"]
                game.hltb_completionist_hours = result["completionist"]
                print(
                    f"main={result['main']}h  "
                    f"main+extra={result['main_extra']}h  "
                    f"completionist={result['completionist']}h"
                )
                matched += 1
            else:
                print("no confident match")
                skipped += 1
            game.hltb_synced_at = datetime.now(timezone.utc)

        # Commit in batches of 50 to avoid long-running transactions.
        if i % 50 == 0:
            db.commit()
            print(f"  — committed batch at game {i}")

        if i < total:
            time.sleep(HLTB_RATE_LIMIT_SLEEP)

    db.commit()
    db.close()

    print(f"\nDone. matched={matched}  skipped/no-match={skipped}  total={total}")


if __name__ == "__main__":
    main()
