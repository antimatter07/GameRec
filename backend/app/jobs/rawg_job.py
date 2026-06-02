import argparse
import logging
import subprocess
import sys

from app.config import settings
from app.workers.tasks.rawg_sync import (
    run_enrich_known_games,
    run_sync_catalog,
    run_sync_recent_releases,
)


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def _build_vectors() -> int:
    result = subprocess.run([sys.executable, "scripts/build_vectors.py"], check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Run RAWG and catalog maintenance jobs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    sync_catalog = subparsers.add_parser("sync-catalog")
    sync_catalog.add_argument("--max-requests", type=int, default=settings.RAWG_MONTHLY_REQUEST_BUDGET)

    sync_recent = subparsers.add_parser("sync-recent")
    sync_recent.add_argument("--max-requests", type=int, default=settings.RAWG_RECENT_REQUEST_BUDGET)
    sync_recent.add_argument("--days-back", type=int, default=60)

    enrich_known = subparsers.add_parser("enrich-known")
    enrich_known.add_argument("--max-requests", type=int, default=settings.RAWG_DETAIL_REFRESH_REQUEST_BUDGET)

    subparsers.add_parser("build-vectors")

    args = parser.parse_args()

    if args.command == "sync-catalog":
        logger.info("Starting RAWG catalog sync with max_requests=%s", args.max_requests)
        logger.info("Result: %s", run_sync_catalog(args.max_requests))
        return 0
    if args.command == "sync-recent":
        logger.info(
            "Starting RAWG recent sync with max_requests=%s days_back=%s",
            args.max_requests,
            args.days_back,
        )
        logger.info("Result: %s", run_sync_recent_releases(args.max_requests, args.days_back))
        return 0
    if args.command == "enrich-known":
        logger.info("Starting RAWG known-game enrichment with max_requests=%s", args.max_requests)
        logger.info("Result: %s", run_enrich_known_games(args.max_requests))
        return 0
    if args.command == "build-vectors":
        return _build_vectors()

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
