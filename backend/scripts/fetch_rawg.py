"""
Fetch games from the RAWG API and save to a local JSON file.
Run from the backend/ directory with the virtualenv active:

    python scripts/fetch_rawg.py

Optional args:
    --pages     Number of pages to fetch (default: 1, each page = 40 games)
    --all       Fetch every available page (overrides --pages)
    --out       Output file path (default: scripts/rawg_games.json)

Example:
    python scripts/fetch_rawg.py --pages 5 --out data/games.json
    python scripts/fetch_rawg.py --all --out data/games.json
"""

import argparse
import json
import sys
from pathlib import Path

# Allow imports from backend/app
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.utils.rawg_client import rawg_client


def fetch_games(pages: int | None, out_path: Path) -> None:
    all_games = []
    page = 1

    while True:
        label = f"{page}/{pages}" if pages else str(page)
        print(f"Fetching page {label}...")
        data = rawg_client.get_games(page=page, page_size=40)
        results = data.get("results", [])
        all_games.extend(results)
        print(f"  Got {len(results)} games (total so far: {len(all_games)})")

        if not data.get("next"):
            print("No more pages available, stopping.")
            break

        page += 1
        if pages is not None and page > pages:
            break

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(all_games, indent=2, default=str))
    print(f"\nSaved {len(all_games)} games to {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch games from RAWG API to JSON")
    parser.add_argument("--pages", type=int, default=1, help="Number of pages to fetch (40 games each)")
    parser.add_argument("--all", action="store_true", help="Fetch all available pages (overrides --pages)")
    parser.add_argument("--out", type=Path, default=Path("scripts/rawg_games.json"), help="Output JSON file path")
    args = parser.parse_args()

    fetch_games(pages=None if args.all else args.pages, out_path=args.out)


if __name__ == "__main__":
    main()
