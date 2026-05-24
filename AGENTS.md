# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

A full-stack video game recommender with content-based filtering (cosine similarity on genre/tag feature vectors), JWT auth with role-based access control, a Celery task queue for async work, and an optional LLM layer for premium AI features (explanations, Game DNA). Game data is sourced from the RAWG API.

## Commands

### Backend (run from `backend/`)

```bash
# Activate virtualenv
source .venv/bin/activate   # Linux/macOS
.venv\Scripts\activate      # Windows

# Run dev server
uvicorn app.main:app --reload --port 8000

# Database migrations
alembic revision --autogenerate -m "<message>"
alembic upgrade head
alembic downgrade -1

# Run Celery worker
celery -A app.workers.celery_app worker --loglevel=info

# Check if a Celery worker is running (requires Redis to be reachable)
celery -A app.workers.celery_app inspect ping
# Alternative: ps aux | grep "celery worker"

# Run Celery Beat scheduler (RAWG sync)
celery -A app.workers.celery_app beat --loglevel=info

# Manually trigger a HLTB task (worker must be running)
python -c "from app.workers.tasks.hltb_sync import enrich_game_hltb; enrich_game_hltb.delay(<game_id>)"

# Run HLTB enrichment for games that don't have HLTB data
python -c "from app.workers.tasks.hltb_sync import enrich_all_hltb; enrich_all_hltb.delay()"

# Manually trigger monthly RAWG catalog discovery/enrichment (worker must be running).
# Use this once per month if you want to spend most of the RAWG monthly quota.
# Do not run Celery Beat at the same time unless you also want scheduled weekly/daily jobs.
python -c "from app.workers.tasks.rawg_sync import sync_catalog; sync_catalog.delay(19000)"

# Manually trigger recent-release discovery only
python -c "from app.workers.tasks.rawg_sync import sync_recent_releases; sync_recent_releases.delay(1000, 60)"

# Manually enrich already-inserted games with full RAWG details/descriptions
python -c "from app.workers.tasks.rawg_sync import enrich_known_games; enrich_known_games.delay(500)"


# Build game feature vectors (must be run manually after populating the games table,
# and re-run after each RAWG sync that adds new games)
# TODO: automate this as a Celery task triggered at the end of the rawg_sync task
python scripts/build_vectors.py
```

### Frontend (run from `frontend/`)

```bash
npm run dev       # Vite dev server on :5173
npm run build     # TypeScript check + Vite production build
npm run lint      # ESLint
npm run preview   # Preview production build
```

## Architecture

### Backend request flow

```
HTTP request
  → SlowAPI rate limiter (keyed per user role: 30/100/200 req/min)
  → FastAPI router  (app/routers/)
  → Dependency injection  (dependencies.py)
      ├─ get_db()            → SQLAlchemy Session
      └─ get_current_user()  → decodes JWT, fetches User from DB
          ├─ require_basic   (BASIC | PREMIUM | ADMIN)
          ├─ require_premium (PREMIUM | ADMIN)
          └─ require_admin   (ADMIN only)
  → Service layer  (app/services/)
  → SQLAlchemy ORM models  (app/models/)
```

AI features (explanations, Game DNA) are **premium-only** and dispatched as Celery tasks so the HTTP response is not blocked.

### RAWG catalog ingestion

The RAWG ingestion pipeline is designed to maximize accepted games per API request while avoiding shovelware and duplicate rows.

**Manual monthly workflow:**

1. Run migrations:
   ```bash
   cd backend
   source .venv/bin/activate
   alembic upgrade head
   ```
2. Start a Celery worker:
   ```bash
   celery -A app.workers.celery_app worker --loglevel=info
   ```
3. In a second backend terminal, queue the monthly catalog run:
   ```bash
   python -c "from app.workers.tasks.rawg_sync import sync_catalog; sync_catalog.delay(19000)"
   ```

`sync_catalog(19000)` uses a 19,000-request budget, leaving some room below RAWG's 20,000/month free-tier limit. About 90% of the budget goes to cheap `/games` list-page discovery, and the remainder enriches already-inserted games with full detail descriptions.

**Discovery-first design:**

- `sync_catalog` crawls these passes with independent Postgres checkpoints: `popular_added`, `metacritic`, `high_rating`.
- `sync_recent_releases(max_requests=1000, days_back=60)` crawls `recent_releases`.
- Discovery inserts from RAWG list payloads only. These include `id`, `name`, `slug`, `released`, `background_image`, `rating`, `ratings_count`, `metacritic`, `added`, `playtime`, `genres`, `platforms`, `tags`, stores, and `short_screenshots`.
- Full detail calls are treated as enrichment, not as a prerequisite for inserting catalog rows.

**Filter behavior:**

- The single source of truth is `app/services/game_filter.py`.
- The filter keeps popular, reviewed, highly rated, played/tracked, niche, cult, and allowlisted games.
- It rejects future releases, soundtrack/demo/DLC/expansion entries, rows with no metadata anchor, rows with no genre/tag/platform classification, and zero-traction entries.
- The allowlist lives at `app/data/game_filter_allowlist.json`.

**Duplicate and resume behavior:**

- `Game.rawg_id` is unique and is the external identity used to prevent duplicate game rows.
- The sync checks `Game.rawg_id` before insert, so overlapping RAWG passes and repeated monthly runs skip existing games.
- Postgres remains the final guarantee against duplicate RAWG ids.
- `rawg_sync_state` stores durable crawl checkpoints by pass (`next_page`, `completed`, last error/success).
- `rawg_seen_games` tracks accepted/rejected RAWG ids. Rejected ids are skipped until `RAWG_REJECT_RECHECK_DAYS` elapses, default 90 days.
- If the configured request budget or RAWG quota is exhausted, the task stops safely without advancing the current page checkpoint. The next monthly run resumes from the saved state.

**Scheduled jobs:**

Celery Beat is configured in `app/workers/celery_app.py`:

- Monthly catalog sync: day 1 at 03:00 UTC, task `rawg_sync.sync_catalog`
- Weekly recent-release sync: Monday at 03:00 UTC, task `rawg_sync.sync_recent_releases`
- Daily detail enrichment: 03:30 UTC, task `rawg_sync.enrich_known_games`

For a manual once-per-month quota-spending workflow, run only the Celery worker and trigger `sync_catalog(19000)` manually. Do not run Beat unless you want the scheduled jobs too.

**Status monitoring:**

- Admin endpoint: `GET /api/admin/pipeline/status`
- Redis key: `rawg_sync:last_run`

### Auth flow

- Login → `POST /api/auth/login` → returns `access_token` (30 min, HS256 JWT) + `refresh_token` (7 days)
- `decode_access_token` in `core/security.py` validates type claim (`"type": "access"`)
- Refresh tokens are blacklisted in Redis on logout
- Frontend stores both tokens via Zustand `persist` middleware (localStorage key `auth-storage`)
- Axios interceptor in `api/client.ts` attaches Bearer token and retries on 401 with refresh

### Recommendation pipeline (not yet implemented)

1. `build_user_taste_profile` — aggregates rated library entries into a weighted multi-hot vector (genres + tags), normalized L2
2. `compute_recommendations` — cosine similarity between taste vector and per-game feature vectors; stores `Recommendation` + `RecommendationItem` rows
3. `get_or_generate` — returns a cached recommendation if generated within the last hour
4. Feature vectors: not yet stored on `Game` model — see TODO in `app/models/game.py` for options (JSON column, pgvector, Redis cache)

### Frontend data flow

```
Page component
  → Custom hook (hooks/useGames, useRecommendations, useAuth)
      → TanStack Query (caching, background refetch)
          → API module (api/*.ts)
              → Axios client (api/client.ts, baseURL: localhost:8000/api)
  → Zustand store (authStore, uiStore) for global UI/auth state
```

Routes are split into public (`/login`, `/register`) and authenticated (everything else, wrapped in `ProtectedRoute`). Admin routes are further guarded by `AdminRoute` which checks `user.role === 'admin'`.

### DB models

| Model | Key relationships |
|---|---|
| `User` | has many `LibraryEntry`, `Recommendation` |
| `Game` | genres/platforms/tags stored as JSON arrays; has many `LibraryEntry`, `RecommendationItem` |
| `LibraryEntry` | join of User ↔ Game with status + rating |
| `Recommendation` | batch header (user, timestamp); has many `RecommendationItem` |
| `RecommendationItem` | rank, cosine score, optional LLM explanation (premium) |
| `RecommendationFeedback` | thumbs up/down on a `RecommendationItem` |

## Security notes

- **CORS** (`main.py`) restricts browser cross-origin requests to `settings.ALLOWED_ORIGINS`. It does **not** block `curl`, Postman, bots, or server-to-server requests — those bypass CORS entirely.
- **Real server-side protection** comes from JWT auth (`require_basic/premium/admin` dependencies) and SlowAPI rate limiting.
- **Rate limiter TODO:** Currently keyed by IP address (`get_remote_address`) — not by user role. The `app/core/rate_limiter.py` user-aware key function needs to be wired up in `main.py` so BASIC/PREMIUM/ADMIN users get their respective limits (30/100/200 req/min) instead of a flat per-IP limit.

## Coding conventions

- **Unimplemented stubs** raise `NotImplementedError` (backend) or `throw new Error('Not implemented')` (frontend) with `// TODO:` comments explaining the expected implementation. Follow this pattern when scaffolding new stubs.
- **Backend env** is read via `pydantic-settings` (`app/config.py → settings`). All secrets come from `.env` (copy `.env.example`). `alembic.ini` has its own `sqlalchemy.url` that must be kept in sync.
- **LLM provider** is not yet committed — uncomment either `openai` or `anthropic` in `requirements.txt` and add the corresponding key to `config.py`/`.env`.
- **scikit-learn / numpy** are also commented out in `requirements.txt` pending recommendation engine implementation.
- Genres, platforms, and tags on `Game` are stored as JSON arrays of `{"id": int, "name": str}` dicts — not normalized tables (see TODO in `game.py` for future GIN index approach).
