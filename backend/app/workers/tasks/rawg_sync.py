from app.workers.celery_app import celery_app


@celery_app.task(name="rawg_sync.sync_games", bind=True, max_retries=3)
def sync_games(self, page_start: int = 1, page_end: int = 10):
    """
    Fetch a range of pages from the RAWG /games endpoint and upsert into the DB.

    TODO: Import rawg_client from app.utils.rawg_client
    TODO: Create a DB session (use SessionLocal directly — not the FastAPI dependency)
    TODO: Loop pages page_start..page_end:
          - Call rawg_client.get_games(page=p)
          - For each result, upsert a Game record by rawg_id
            (INSERT ... ON CONFLICT (rawg_id) DO UPDATE)
          - Dispatch sync_game_details.delay(rawg_id) for full description / screenshots
    TODO: On HTTP error, use self.retry(exc=exc, countdown=60) for backoff
    TODO: Write final status (success/failure, games_synced count) to Redis
          so the admin pipeline/status endpoint can read it
    TODO (hltb): After upserting new games, call enrich_all_hltb.delay() to
          auto-enrich any games that don't yet have HLTB data.
    """
    raise NotImplementedError


@celery_app.task(name="rawg_sync.sync_game_details", bind=True, max_retries=3)
def sync_game_details(self, rawg_id: int):
    """
    Fetch full detail for a single game and update its DB record.

    TODO: Call rawg_client.get_game_detail(rawg_id)
    TODO: Update Game.description, Game.screenshots, Game.tags, etc.
    TODO: Update Game.synced_at timestamp
    TODO: Optionally recompute the game's feature vector and store it
    """
    raise NotImplementedError
