# LLM Embeddings + pgvector Recommender Upgrade

> **Note:** Upon plan approval, copy this file to the project root as `LLM_RECOMMENDATIONS_PLAN.md` so it lives with the code for future reference (the user originally requested it in root; plan mode restricted the initial write location).

## Context

The current recommender (`backend/app/services/recommendation_service.py`, `backend/scripts/build_vectors.py`) uses a sparse multi-hot vector of genres + top-150 tags + 2 scalar features (metacritic, rating), L2-normalized, stored as JSON on `Game.feature_vector`, and cosine-similarity searched in-process with NumPy.

This works but has three limits:
1. **No semantic understanding** — "atmospheric exploration game with minimal combat" cannot match a game whose tags/genres don't literally contain those words.
2. **In-process similarity** scales poorly past ~100k games.
3. **Cold-start / sparse catalog entries** with few tags get weak vectors.

The upgrade: embed each game's `description` (+ name + genres + tags as a composed text document) via an LLM embedding model → store in a native `pgvector` column → search via Postgres KNN. Keep the existing sparse vector alongside as a blended signal (hybrid). This slots in cleanly because `Game.description` is already populated, `anthropic` SDK is already in `requirements.txt`, `RecommendationItem.explanation` already exists, and `ai_service.generate_explanations()` is already wired.

## Scale target

RAWG has ~900k games. The full catalog does not fit on Supabase free tier as vectors. **Aggressively filter to ~40–80k meaningful games** (see Filter Strategy below). At that scale with Voyage 512-dim vectors: ~100–200 MB storage (fits free tier comfortably), ~$0.30–$0.60 one-time embedding cost (likely covered by Voyage free-tier credits).

---

## 1. Filter Strategy (Do This First)

Goal: exclude shovelware, vaporware, and extremely obscure entries while preserving niche indie hits (e.g. Graveyard Keeper: metacritic 74, rating ~4.0, modest ratings_count — easily passes).

### Hard gates (must ALL pass, or the game is discarded)

| Gate | Rationale |
|---|---|
| `description` non-null, `len(description) >= 50` chars | Required to embed meaningfully. |
| `released` non-null AND `released <= today` | Drops vaporware / unreleased entries. |
| `len(genres) >= 1` | Drops stubs / unclassified entries. |
| `background_image` non-null | Games without artwork are almost always shovelware, delisted, or placeholder rows. |

### Signal gates (keep if ANY ONE passes — the "hidden gem escape hatches")

| Gate | Catches |
|---|---|
| `metacritic >= 60` | Critically reviewed. Graveyard Keeper (74) ✓, most reviewed indies ✓. |
| `rating >= 3.8` AND `ratings_count >= 30` | Niche audience love. A cult hit with 40 enthusiastic ratings survives. |
| `added >= 200` | RAWG's cumulative-library-adds popularity signal. Catches games with an audience but no critic reviews. |
| `ratings_count >= 100` | Any game this many users cared enough to rate is worth keeping. |

**Why 4 signal gates OR'd together:** each catches a different kind of meaningful game. Shovelware fails all four simultaneously; hidden gems usually hit at least one. Graveyard-Keeper-style games typically hit 3–4 of them.

### Optional exclusion tags (post-filter)
- Drop entries where `tags` contain any of: `dlc`, `expansion`, `soundtrack`, `demo` (keep these as separate entities if needed later — they pollute the recommender).

### Two-layer application

1. **RAWG sync-time filter** (`app/workers/tasks/rawg_sync.py`): use `ordering=-added` and `ordering=-metacritic` passes to page through RAWG efficiently; stop paging when the tail drops below thresholds. Saves RAWG API quota vs. fetching everything.
2. **Ingestion filter** (helper `app/services/game_filter.py` — new): final pass before `INSERT` / `UPSERT`. Centralizes the rules above so they're also applied to any manual seed scripts and re-applied if filter thresholds are tuned.

Estimate: 900k → ~40–80k games. Log drop reasons per game to verify thresholds during first run.

---

## 2. Embeddings Provider

**Voyage AI `voyage-3-lite`** (primary), with **local `sentence-transformers` (`all-MiniLM-L6-v2`)** as a documented fallback for contributors who don't want to sign up for a key.

- Voyage is Anthropic's recommended embeddings partner — keeps the stack Anthropic-aligned.
- 512-dim output keeps storage small (1/3 of OpenAI's 1536-dim).
- Free-tier credits likely cover the entire one-time catalog embed.
- Local fallback runs on CPU, no API key needed, ~5–15 min to embed 50k games.

Expose the choice via a single env var:
```
EMBEDDING_PROVIDER=voyage  # voyage | local
VOYAGE_API_KEY=...
EMBEDDING_DIM=512          # must match provider; used by pgvector column
```

---

## 3. Vector Design (Hybrid)

Keep two separate columns on `Game`:

| Column | Purpose |
|---|---|
| `feature_vector` (existing JSON) | Sparse multi-hot (genres + tags + scalars). Preserves explicit categorical signal — lets us filter "more like X but indie" or "in genre Y". |
| `embedding` (new, `vector(512)` via pgvector) | Dense semantic embedding of composed text. Captures vibes / themes / tone. |

At query time, compute **two cosine similarities** and blend:
```
final_score = α * cosine(taste_embedding, game_embedding)
            + (1 - α) * cosine(taste_sparse, game_sparse)
```
with `α` configurable (start at 0.7, tune later). This preserves the existing pipeline as a safety net — if embeddings are disabled or the provider is unreachable, `α = 0.0` degrades gracefully to today's behavior.

**Composed text for embedding** (per game):
```
{name}

Genres: {", ".join(genre names)}
Tags: {", ".join(top 20 English non-noise tags by frequency)}

{description}
```
Truncate to ~500 tokens to control cost and stay within model limits.

---

## 4. pgvector Setup on Supabase

pgvector is available on all Supabase tiers (including free). Enable via:
```sql
CREATE EXTENSION IF NOT EXISTS vector;
```
in an Alembic migration.

**New migration:** `alembic revision -m "add_pgvector_and_embedding_column"`
- `CREATE EXTENSION IF NOT EXISTS vector;`
- `ALTER TABLE games ADD COLUMN embedding vector(512);`
- `CREATE INDEX games_embedding_hnsw ON games USING hnsw (embedding vector_cosine_ops);`

Use HNSW over IVFFlat: no training step required, better recall at our scale.

Add `pgvector==0.3.6` (or latest) to `requirements.txt` for the SQLAlchemy type.

---

## 5. Files to Change / Create

### New

| Path | Purpose |
|---|---|
| `backend/app/services/game_filter.py` | `passes_filters(game_dict) -> tuple[bool, str]`. Single source of truth for all hard + signal gates. Used by RAWG sync and any manual seed script. |
| `backend/app/services/embedding_service.py` | Provider-agnostic wrapper: `embed_texts(texts: list[str]) -> list[list[float]]`. Dispatches to Voyage or local based on `settings.EMBEDDING_PROVIDER`. Batches calls (Voyage supports up to 128/request). |
| `backend/app/workers/tasks/embeddings.py` | Celery tasks: `embed_game(game_id)` and `embed_games_batch(game_ids)`. Called from RAWG sync after new games are inserted. |
| `backend/scripts/build_embeddings.py` | One-shot script to embed the entire existing catalog. Mirrors `build_vectors.py` structure. |
| `backend/alembic/versions/xxxx_add_pgvector_and_embedding_column.py` | Migration above. |

### Modified

| Path | Change |
|---|---|
| `backend/app/models/game.py` | Add `embedding: Mapped[Optional[list[float]]] = mapped_column(Vector(512), nullable=True)`. Import `from pgvector.sqlalchemy import Vector`. |
| `backend/app/config.py` | Add `EMBEDDING_PROVIDER`, `VOYAGE_API_KEY`, `EMBEDDING_DIM`, `EMBEDDING_BLEND_ALPHA` settings. |
| `backend/app/services/recommendation_service.py` | `build_user_taste_profile()` → build two taste vectors (sparse + dense). `compute_recommendations()` → run a pgvector KNN query for top-K by dense similarity, rescore top-K by blended score, return top-20. This keeps the expensive semantic pass indexed (Postgres) and the cheap rescoring in Python. |
| `backend/app/workers/tasks/rawg_sync.py` | After UPSERT, if the game passed filters AND is newly inserted or its `description` changed, enqueue `embed_game.delay(game_id)`. |
| `backend/requirements.txt` | Add `pgvector`, `voyageai` (uncomment/add); add `sentence-transformers` as optional extras-only. |
| `backend/.env.example` | Document new env vars. |
| `backend/scripts/build_vectors.py` | Leave as-is — still builds the sparse vector, now one half of the hybrid. |

### Existing reuse (do NOT rewrite)

| Path | Why it's already right |
|---|---|
| `backend/app/services/ai_service.py` | `generate_explanations()` already uses Claude Haiku. Enhance it later to take top-matching embedding snippets as grounding, but not required for v1. |
| `backend/app/models/recommendation.py` | `RecommendationItem.explanation` + `.confidence` already exist. No schema change needed for LLM explanations. |
| `backend/app/routers/recommendations.py` | `/recommendations` endpoint already dispatches `generate_ai_explanations` Celery task for premium users (lines 40–47). No changes needed. |
| `frontend/src/pages/recommendations/RecommendationsPage.tsx` | Already renders `item.explanation` when present. No frontend changes required for v1. |

---

## 6. Implementation Order

1. **Filter service** (`game_filter.py`) — pure function, testable in isolation. Write + unit-test first so thresholds can be tuned against a dev RAWG sample before investing in embeddings.
2. **Implement RAWG sync** (`rawg_sync.py` is currently stubbed per CLAUDE.md). Apply filter at ingestion. Run against RAWG to build a filtered catalog of ~50k games. Verify count and spot-check hidden-gem survival (Graveyard Keeper, Outer Wilds, Disco Elysium, Hollow Knight, etc.).
3. **pgvector migration + `Game.embedding` column**. Run `alembic upgrade head` against Supabase.
4. **Embedding service** (`embedding_service.py`) — Voyage + local. Unit test with a handful of games.
5. **Embedding Celery task + backfill script** (`build_embeddings.py`). Run once to embed the full filtered catalog.
6. **Hook embedding task into RAWG sync** so new games get embedded automatically.
7. **Update `recommendation_service.py`** to do hybrid scoring with pgvector KNN + sparse rescore.
8. **(Optional v2)** Ground `ai_service.generate_explanations()` with a nearest-neighbor snippet from embeddings — e.g. tell Claude "this game is semantically close to games X/Y the user rated highly" before asking for the explanation.

---

## 7. Verification

- **Filter**: after step 2, `SELECT COUNT(*) FROM games;` should be in 40k–80k range. Query for 10 known hidden gems by name — all should be present.
- **pgvector**: `SELECT COUNT(*) FROM games WHERE embedding IS NOT NULL;` equals total game count after backfill.
- **KNN sanity**: manually query `SELECT name FROM games ORDER BY embedding <=> (SELECT embedding FROM games WHERE name = 'Hollow Knight') LIMIT 10;` — results should be thematically related (Ori, Dead Cells, Blasphemous, etc.).
- **End-to-end**: log in as a test user, add 5 games to library with varied ratings, hit `GET /api/recommendations`, verify response has 20 items with sensible scores. Confirm `item.explanation` populates within ~10s for premium users (Celery task).
- **Graceful degradation**: set `EMBEDDING_BLEND_ALPHA=0.0` and confirm the recommender still works identically to today — embeddings are additive, not a hard dependency.

---

## 8. Open Items for Later

- Automate `build_vectors.py` at the end of `rawg_sync` (already a known TODO in CLAUDE.md). Same for `build_embeddings.py`.
- Incremental embedding: only re-embed games whose description changed since `synced_at`, not every game on every sync.
- User-provided semantic search bar ("games with minimal combat and atmospheric exploration") → embed the query string → pgvector KNN → return results. This falls out for free once embeddings exist.
- Consider `voyage-3` (non-lite) for query-time embeddings if retrieval quality matters more than cost; catalog embeddings can stay on `voyage-3-lite`.
