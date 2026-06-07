<p align="center">
  <img src="frontend/src/assets/logo/gamerec-logo-title-transparent.png" alt="GameRec" width="360">
</p>

# GameRec - AI-Powered Video Game Recommender and Library Management System

A full-stack game discovery, library, and backlog planning app that helps players decide what to play next. GameRec combines a searchable RAWG-powered catalog, personal library tracking, play queue management, journaling, content-based recommendations, and AI-assisted taste analysis that gives users tailor-made recommendations on both video games and a suggested play order of current library.

This project features authenticated API design, asynchronous data pipelines, recommendation logic, external API ingestion, role-based access control, modern React UI, automated tests, and deployable cloud infrastructure.

Deployed on Cloudflare with backend on AWS Services (Lambda, SQS, API Gateway) and PostgreSQL dastabase on Supabase: 
app.gamerec.uk [app.gamerec.uk](app.gamerec.uk)

## Highlights

- Personalized game recommendations using content-based filtering over genre, tag, rating, and Metacritic feature vectors.
- Full-stack authentication with JWT access tokens, refresh sessions, Google OAuth support, CSRF protection, and role-based authorization.
- Game catalog ingestion from RAWG with durable crawl checkpoints, duplicate protection, quality filtering, and request-budget awareness.
- Library, backlog, play queue, and journal workflows for tracking owned games, play status, ratings, sessions, notes, and mood.
- AI-assisted features for taste summaries, "AI picks", and queue reorder suggestions using structured LLM outputs.
- Steam library import with external ID matching, fuzzy title matching, sequel conflict checks, and confidence scoring.
- Async processing through Celery/Redis locally, with AWS Lambda/SQS/DynamoDB deployment support.
- Admin pipeline visibility for catalog sync status and operational monitoring.
- Typed React frontend with Mantine, TanStack Query, Zustand, React Router, and a cinematic media-library UI direction.

## Product Snapshot

GameRec is designed for players with growing libraries or backlogs who want recommendations that feel more personal than popularity charts. The app helps users answer four practical questions:

- What should I play next?
- Why does this game fit my taste?
- What have I enjoyed or abandoned before?
- How should I organize my backlog into an intentional queue with a play order that makes sense?

The product direction is closer to a private screening library for games than a generic dashboard: cover art, game metadata, ratings, notes, and taste signals are treated as the main interface.

## Tech Stack

| Layer | Technologies |
| --- | --- |
| Frontend | React.js, TypeScript, Vite, Mantine, React Router, TanStack Query (State Management), Zustand, Axios |
| Backend | FastAPI, SQLAlchemy, Pydantic Settings, Alembic, SlowAPI |
| Data | PostgreSQL, Redis, JSON feature vectors, RAWG API, Steam Web API, HowLongToBeat enrichment (data retrieved through rate-limited web scraping) |
| Recommendations | NumPy, scikit-learn-ready feature pipeline, cosine similarity, feedback adjustments |
| Async work | Celery and Redis locally; AWS Lambda, SQS, DynamoDB, and optional ECS/Fargate RAWG worker in production |
| Auth and security | JWT, refresh tokens, Redis blacklist (local, DynamoDB for production), CSRF cookie/header validation, role-based dependencies, CORS allowlist (implemented through Cloudflare DNS in production)|
| AI | Gemini/Anthropic-compatible provider layer for AI picks and queue suggestions |
| Testing | Pytest backend tests, frontend TypeScript build and ESLint |
| Infrastructure | AWS SAM, Lambda container images (AWS Lambda, API Gateway, SQS), SSM Parameter Store configuration |

## Architecture

```mermaid
flowchart LR
  U["User"] --> FE["React + Vite frontend"]
  FE --> API["FastAPI API"]
  API --> AUTH["JWT, CSRF, RBAC"]
  API --> DB[("PostgreSQL")]
  API --> REDIS[("Redis / KV")]
  API --> REC["Recommendation service"]
  API --> AI["AI services"]
  API --> QUEUE["Task backend"]
  QUEUE --> CELERY["Celery workers"]
  QUEUE --> SQS["AWS SQS workers"]
  CELERY --> RAWG["RAWG sync"]
  CELERY --> HLTB["HLTB enrichment"]
  SQS --> RAWG
  SQS --> HLTB
  RAWG --> DB
  HLTB --> DB
  REC --> DB
  AI --> DB
```

## Core Features

### Game Catalog

- Browse and filter games from a RAWG-backed catalog.
- Store rich game metadata including genres, platforms, tags, screenshots, ratings, Metacritic score, stores, and playtime signals.
- Filter ingestion through a centralized quality gate to reduce shovelware, duplicates, DLC/demo entries, future releases, and low-signal records.
- Preserve accepted/rejected RAWG IDs so repeated syncs can resume safely and avoid wasting monthly quota.

### Library and Backlog

- Save games into a personal library.
- Track statuses such as playing, replaying, completed, backlog, wishlist, dropped, and related queue states.
- Manage backlog and queue views separately so discovery, ownership, and "what next" planning stay distinct.

### Recommendations

- Build L2-normalized game feature vectors from genres, high-signal tags, Metacritic, and rating values.
- Aggregate a user taste profile from library entries, ratings, and play status.
- Compute cosine similarity against candidate games not already in the user's library.
- Apply feedback adjustments from thumbs-up/thumbs-down recommendation feedback.
- Cache fresh recommendation batches for one hour before regeneration.

### AI Picks and Queue Suggestions

- Build compact taste dossiers from library history, ratings, journal notes, session logs, emotions, tags, platforms, and favorite/disliked games.
- Generate structured AI recommendations with explanations and confidence scores.
- Resolve AI-proposed titles back to local catalog entries with fuzzy matching and popularity tie-breakers.
- Suggest an alternate play queue order with item-level reasoning and validation before adoption.

### Journal and Ratings

- Log play sessions and playthrough notes.
- Capture richer rating dimensions and mood/emotion context.
- Use journal history as part of the broader taste signal for AI-assisted features.

### Steam Import

- Import a user's Steam-owned games.
- Match Steam app IDs where known, then fall back to normalized and fuzzy title matching.
- Protect against common false positives such as sequel number mismatches.
- Return confidence scores and match reasons for review.

### Admin and Operations

- Admin-only API routes for pipeline status.
- Celery Beat schedules for monthly catalog sync, weekly recent-release sync, and daily detail enrichment.
- AWS SAM infrastructure for production-style Lambda workers and API deployment.

## Repository Structure

```text
.
|-- backend/
|   |-- app/
|   |   |-- core/          # Security, rate limiting, Redis/KV helpers
|   |   |-- models/        # SQLAlchemy ORM models
|   |   |-- routers/       # FastAPI route modules
|   |   |-- schemas/       # Pydantic request/response schemas
|   |   |-- services/      # Business logic and recommendation workflows
|   |   |-- utils/         # RAWG, Steam, and HLTB clients
|   |   `-- workers/       # Celery app and async task definitions
|   |-- alembic/           # Database migrations
|   |-- scripts/           # Catalog seeding, RAWG fetch, vector building
|   `-- tests/             # Pytest suite
|-- frontend/
|   |-- src/
|   |   |-- api/           # Axios API modules
|   |   |-- components/    # Shared UI components
|   |   |-- hooks/         # TanStack Query hooks
|   |   |-- pages/         # Route-level pages
|   |   |-- store/         # Zustand stores
|   |   `-- types/         # Frontend TypeScript models
|   `-- package.json
|-- infrastructure/        # AWS SAM deployment template and config example
|-- PRODUCT.md            # Product strategy and positioning notes
|-- DESIGN.md             # Visual design system
`-- AGENTS.md             # Local engineering instructions
```

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL
- Redis
- RAWG API key for catalog ingestion
- Optional: Steam Web API key, Gemini or Anthropic API key, AWS SAM CLI

### Backend Setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt
```

Create `backend/.env` with local settings:

```env
APP_ENV=development
APP_RUNTIME=local
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/gamerec
REDIS_URL=redis://localhost:6379/0
SECRET_KEY=replace-with-a-local-secret
RAWG_API_KEY=your-rawg-key
RAWG_BASE_URL=https://api.rawg.io/api
ALLOWED_ORIGINS=http://localhost:5173
GOOGLE_CLIENT_ID=
STEAM_API_KEY=
GEMINI_API_KEY=
ANTHROPIC_API_KEY=
```

Run migrations and start the API:

```bash
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

The API health check is available at:

```text
http://localhost:8000/api/health
```

FastAPI documentation is available at:

```text
http://localhost:8000/docs
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The frontend runs on:

```text
http://localhost:5173
```

### Async Workers

Start Redis, then run a Celery worker from `backend/`:

```bash
source .venv/bin/activate
celery -A app.workers.celery_app worker --loglevel=info
```

Optional scheduled jobs:

```bash
celery -A app.workers.celery_app beat --loglevel=info
```

## Data Pipeline

### RAWG Catalog Sync

The catalog sync is designed to use RAWG's monthly request budget carefully. It performs discovery-first list-page crawling, inserts acceptable games without requiring expensive detail calls, and treats full details as later enrichment.

Manually trigger a monthly-style catalog run:

```bash
cd backend
source .venv/bin/activate
python -c "from app.workers.tasks.rawg_sync import sync_catalog; sync_catalog.delay(19000)"
```

Other useful tasks:

```bash
python -c "from app.workers.tasks.rawg_sync import sync_recent_releases; sync_recent_releases.delay(1000, 60)"
python -c "from app.workers.tasks.rawg_sync import enrich_known_games; enrich_known_games.delay(500)"
python -c "from app.workers.tasks.hltb_sync import enrich_all_hltb; enrich_all_hltb.delay()"
```

### Feature Vector Build

After games are loaded, build recommendation vectors:

```bash
cd backend
source .venv/bin/activate
python scripts/build_vectors.py
```

The vector builder stores normalized vectors on game rows and writes a stable vocabulary to `backend/data/vocab.json`.

## Testing and Quality

Run backend tests:

```bash
cd backend
source .venv/bin/activate
pytest
```

Run frontend checks:

```bash
cd frontend
npm run lint
npm run build
```

The backend test suite covers auth, security, library behavior, recommendation-adjacent services, RAWG filtering and sync, Steam import, play queue logic, journal services, task queues, and Lambda/SQS handlers.

## Security Considerations

- JWT access tokens are short-lived and refresh tokens are validated separately.
- Refresh tokens can be blacklisted through Redis-backed logout behavior.
- CSRF protection requires a matching CSRF cookie and `X-CSRF-Token` header for unsafe API methods.
- Role-based dependencies separate basic, premium, and admin-only actions.
- CORS is configured through `ALLOWED_ORIGINS` for browser access control.
- SlowAPI rate limiting is present, with role-specific rate-limit settings available in configuration.
- Secrets are read from environment variables locally and can be loaded from AWS SSM Parameter Store in production.

## Deployment

The project includes AWS SAM infrastructure for production-style deployment:

- FastAPI served through a Lambda container image.
- Worker Lambda functions for recommendation, AI, HLTB, and RAWG queues.
- SQS task backend option for serverless async processing.
- DynamoDB KV backend option for production token/cache storage.
- SSM Parameter Store support for secrets and environment configuration.
- Optional ECS/Fargate integration for long-running RAWG catalog jobs.

Example deployment configuration lives in:

```text
infrastructure/samconfig.toml.example
infrastructure/template.yaml
```

## BE Development Decisions

- The recommendation pipeline separates deterministic content-based scoring from optional AI explanation layers so the app can still provide useful recommendations without relying on an LLM.
- RAWG ingestion is checkpointed by crawl pass and tracks accepted/rejected IDs to support safe monthly resume behavior under a fixed API quota.
- Steam import matching combines exact external IDs, normalized title matching, fuzzy scoring, and sequel-number safeguards to reduce incorrect imports.
- AI outputs are parsed as structured Pydantic models and validated before being persisted or applied to user queues.
- The backend keeps route handlers thin and puts business rules in service modules, making the codebase easier to test and reason about.
- The frontend uses query hooks and API modules to keep network behavior, caching, and page composition separated.

## Current Status

Implemented:

- Auth, registration, login, refresh, Google OAuth support, RBAC, and CSRF guard.
- Game catalog browsing and game detail pages.
- Library, backlog, play queue, queue suggestions, journal, and profile flows.
- Content-based recommendation generation and persisted recommendation batches.
- AI picks and queue suggestions through a provider abstraction.
- RAWG, HLTB, and Steam integration paths.
- Backend test coverage across major service and infrastructure modules.
- AWS SAM deployment scaffolding.

To Implement:

- Steam Account import of games
- Premium users with more powerful LLM powered features and less rate limits on LLMs
- More polished UI / branding 
