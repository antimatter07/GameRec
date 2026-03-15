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

# Run Celery Beat scheduler (RAWG sync)
celery -A app.workers.celery_app beat --loglevel=info
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

## Coding conventions

- **Unimplemented stubs** raise `NotImplementedError` (backend) or `throw new Error('Not implemented')` (frontend) with `// TODO:` comments explaining the expected implementation. Follow this pattern when scaffolding new stubs.
- **Backend env** is read via `pydantic-settings` (`app/config.py → settings`). All secrets come from `.env` (copy `.env.example`). `alembic.ini` has its own `sqlalchemy.url` that must be kept in sync.
- **LLM provider** is not yet committed — uncomment either `openai` or `anthropic` in `requirements.txt` and add the corresponding key to `config.py`/`.env`.
- **scikit-learn / numpy** are also commented out in `requirements.txt` pending recommendation engine implementation.
- Genres, platforms, and tags on `Game` are stored as JSON arrays of `{"id": int, "name": str}` dicts — not normalized tables (see TODO in `game.py` for future GIN index approach).
