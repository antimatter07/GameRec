# Future Features — Implementation Plans

This document captures high-level implementation plans for five planned features.
Each section describes what needs to be built, how it integrates with the existing codebase, and which user roles can access it.
It is intended as a reference when scoping and implementing each feature, not as step-by-step implementation instructions.

---

## Table of Contents

1. [Backlog Manager / "Play Next" Prioritizer](#1-backlog-manager--play-next-prioritizer)
2. [Cross-Platform Library Unifier](#2-cross-platform-library-unifier)
3. [Gaming Journal / Session Logger](#3-gaming-journal--session-logger)
4. [Wishlist Price Tracker + Release Calendar](#4-wishlist-price-tracker--release-calendar)
5. [Collection Completionist Tracker](#5-collection-completionist-tracker)

---

## 1. Backlog Manager / "Play Next" Prioritizer

### Overview

Users who have games in `backlog` status have no guidance on what to tackle next.
The app already has `Game.playtime` (RAWG average playtime, stored as an integer on the `Game` model) and the recommendation engine already computes a cosine similarity score between the user's taste profile and every game in the catalog.
This feature surfaces a ranked, filterable "Play Next" view that re-uses both of those existing signals to help users pick their next game from their own backlog — not from the broader catalog.

### New DB Models

No new models are required.
The feature reads from existing `LibraryEntry`, `Game`, and potentially `Recommendation`/`RecommendationItem` rows.

One optional addition is a `BacklogPriority` table that lets users manually pin or dismiss games from the prioritized list:

```
backlog_priorities
  id           Integer PK
  user_id      Integer FK → users.id  NOT NULL
  game_id      Integer FK → games.id  NOT NULL
  pinned       Boolean  default False   -- user manually promoted to top
  dismissed    Boolean  default False   -- user hid from suggestions
  updated_at   DateTime auto-updated
  UNIQUE (user_id, game_id)
```

This table is entirely optional for an MVP — the prioritizer works without it and the table only becomes valuable once the "pin/dismiss" interaction is implemented.

### New API Endpoints

All endpoints require at minimum `require_basic`.

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/library/backlog/prioritized` | BASIC+ | Returns the user's backlog entries ranked by priority score |
| `PATCH` | `/api/library/backlog/{entry_id}/pin` | BASIC+ | Pin a game to the top of the prioritized list |
| `PATCH` | `/api/library/backlog/{entry_id}/dismiss` | BASIC+ | Hide a game from the prioritized list |

**`GET /api/library/backlog/prioritized` query parameters:**

- `mood_genre: str | None` — filter to backlog games matching a genre name (e.g. "RPG", "Action")
- `max_hours: int | None` — only include games with `Game.playtime <= max_hours` (RAWG playtime)
- `sort: "score" | "playtime_asc" | "playtime_desc" | "added_at"` — default `"score"`
- `page: int`, `page_size: int` — pagination

**Response shape (new Pydantic schema `PrioritizedBacklogItem`):**

```python
class PrioritizedBacklogItem(BaseModel):
    entry_id: int
    game: GameListOut
    playtime_hours: int | None       # Game.playtime from RAWG
    taste_score: float | None        # cosine similarity from latest Recommendation batch, null if no recs yet
    priority_score: float            # composite score described below
    pinned: bool
    dismissed: bool
    stale_months: int | None         # months since entry was last touched (updated_at)
```

### Priority Score Computation

Computed server-side in a new `backlog_service.py` (or added to `library_service.py`):

```
priority_score = (taste_weight * taste_score_normalized)
               + (staleness_weight * staleness_score)
               + (playtime_weight * playtime_score)
```

Where:
- `taste_score_normalized` — the game's cosine similarity score from the user's most recent `Recommendation` batch. Look up by joining `RecommendationItem` on `game_id` for the latest `Recommendation` for this user. If no recommendation batch exists, default to `0.5`.
- `staleness_score` — `min(1.0, months_since_updated_at / 6)`. A game untouched for 6+ months scores 1.0.
- `playtime_score` — `1 - min(1.0, Game.playtime / 100)`. Short games (under 10h) score near 1.0; 100h+ games score near 0.0. This surfaces completable games higher by default. Set to `0.5` when `playtime` is null.
- Default weights: `taste_weight=0.5`, `staleness_weight=0.3`, `playtime_weight=0.2`. These can be made user-configurable in a future iteration.

No new Celery tasks are needed — this is a synchronous computation on request. The most expensive step is the taste score lookup, which just queries the existing `recommendation_items` table.

### New Celery Tasks

None required for MVP. If the priority score computation becomes slow (large backlogs), a `recompute_backlog_priorities` task can be dispatched after `precompute_for_user` completes.

### Frontend Pages and Components

**New page:** `frontend/src/pages/library/BacklogPage.tsx`

- Route: `/library/backlog` — add to `router.tsx` as a child of the authenticated layout.
- Link from `LibraryPage.tsx`: add a "Play Next" button or tab on the Backlog tab panel.

**New components:**

- `BacklogPriorityCard` — extends `GameCard` to show `priority_score` as a small colored badge, `playtime_hours` (e.g. "~12h to beat"), a staleness nudge ("Added 8 months ago"), and pin/dismiss action buttons.
- `BacklogFilters` — a horizontal filter bar with a genre select (populated from the user's distinct backlog genres) and a "Max hours" number input. Can be built with Mantine `Select` and `NumberInput`.

**State:** All server state via TanStack Query (`queryKey: ['library', 'backlog', 'prioritized', filters]`). Pin/dismiss use `useMutation` with optimistic updates.

### Integration with Existing Models

- Reads `LibraryEntry` rows where `status = 'backlog'` and `dismissed = False` (or from `BacklogPriority`).
- Reads `Game.playtime` — already stored on the `Game` model, no new sync needed.
- Reads cosine scores from `RecommendationItem` joined to the latest `Recommendation` for the user — no new recommendation computation required.
- Does not modify or retrigger the recommendation engine.
- Mood/genre filtering uses `Game.genres` JSON array, already in the DB.

### External APIs

None. All data is already in the database (`Game.playtime` comes from RAWG sync, `RecommendationItem.score` from the recommendation engine).

If higher-quality completion time data is desired in the future, the HowLongToBeat API (unofficial, community-maintained) could be queried by game title and cached on `Game` as a separate `hltb_main_story_hours` column. This is out of scope for MVP given `Game.playtime` already covers the core use case.

### User Role Access

| Feature | BASIC | PREMIUM | ADMIN |
|---------|-------|---------|-------|
| View prioritized backlog | Yes | Yes | Yes |
| Pin / Dismiss | Yes | Yes | Yes |
| Mood/genre filter | Yes | Yes | Yes |
| Taste score shown (requires recommendation batch) | Yes | Yes | Yes |

This is a BASIC-tier feature — it uses data the user already has and requires no premium AI calls.

### UX Flow

1. User navigates to `/library` and clicks the "Backlog" tab. A "Play Next" button appears in the tab header.
2. Clicking "Play Next" navigates to `/library/backlog`.
3. The page shows a ranked list of backlog games in `BacklogPriorityCard` format. Above the list, a filter bar lets the user pick a mood genre or set a max-hours ceiling.
4. Each card shows: game art, name, genre badges, "~N hours to beat" (from `playtime_hours`), a match percentage (from `taste_score`), and a staleness nudge ("You added this 9 months ago") when `stale_months >= 6`.
5. The user can pin a game (it floats to the top) or dismiss it (it disappears from the list). These actions call the PATCH endpoints and use optimistic updates so the list reorders instantly.
6. A "Start Playing" button on each card changes the library status to `playing` via the existing PATCH `/library/{entry_id}` endpoint (which needs to be implemented — it is currently a stub).

### Impact on Recommendation Engine

None. This feature reads from existing recommendation output but does not modify the taste profile computation or trigger new recommendation batches.

---

## 2. Cross-Platform Library Unifier

### Overview

Users play games across Steam, GOG, PlayStation, Xbox, and Nintendo Switch. Today they must add every game manually. This feature lets users connect external accounts (where public APIs exist) to import their libraries in bulk, automatically deduplicating against what is already in RAWG and in the local `games` table.

Of the major platforms, Steam is the only one with a reliable, public, unauthenticated API (`ISteamUser`/`IPlayerService`). GOG, PlayStation, Xbox, and Nintendo do not expose public OAuth flows for third-party apps. The implementation plan therefore focuses on Steam as the primary integration and provides a "manual import" CSV path as a fallback for all other platforms.

### New DB Models

```
connected_accounts
  id              Integer PK
  user_id         Integer FK → users.id  NOT NULL
  platform        Enum('steam', 'gog', 'playstation', 'xbox', 'switch')  NOT NULL
  external_id     String(255) NOT NULL        -- Steam64 ID, PSN ID, etc.
  display_name    String(255) nullable         -- display name on that platform
  access_token    String(1000) nullable        -- OAuth token if applicable (encrypted at rest)
  refresh_token   String(1000) nullable
  token_expires_at DateTime nullable
  last_synced_at  DateTime nullable
  is_active       Boolean default True
  created_at      DateTime
  UNIQUE (user_id, platform)

platform_game_imports
  id              Integer PK
  user_id         Integer FK → users.id  NOT NULL
  platform        Enum (same as above)
  platform_game_id  String(255) NOT NULL    -- e.g. Steam AppID
  platform_game_name String(255) NOT NULL
  matched_game_id Integer FK → games.id nullable  -- null if no RAWG match found
  match_confidence Float nullable              -- 0-1, name-match score
  status          Enum('pending', 'matched', 'unmatched', 'ignored')
  hours_played    Float nullable               -- from Steam API
  last_played_at  DateTime nullable
  imported_at     DateTime
  library_entry_id Integer FK → library_entries.id nullable  -- set after user confirms import
```

### New API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/integrations/accounts` | BASIC+ | List the user's connected platform accounts |
| `POST` | `/api/integrations/accounts/steam` | BASIC+ | Connect a Steam account by Steam64 ID (no OAuth — Steam public API) |
| `DELETE` | `/api/integrations/accounts/{account_id}` | BASIC+ | Disconnect a platform account |
| `POST` | `/api/integrations/accounts/{account_id}/sync` | BASIC+ | Trigger a library sync for a connected account (dispatches Celery task) |
| `GET` | `/api/integrations/imports` | BASIC+ | List pending/matched import items for the user |
| `POST` | `/api/integrations/imports/confirm` | BASIC+ | Confirm selected import items → create `LibraryEntry` rows |
| `PATCH` | `/api/integrations/imports/{import_id}` | BASIC+ | Update match: re-match to a different `game_id` or mark ignored |
| `POST` | `/api/integrations/imports/csv` | BASIC+ | Upload a CSV of game names for bulk manual import |

**`POST /api/integrations/accounts/steam` request body:**

```python
class SteamConnectRequest(BaseModel):
    steam64_id: str   # 17-digit Steam Community ID
```

Steam's `IPlayerService/GetOwnedGames/v1` endpoint is unauthenticated when the user's profile is public — it just requires the Steam Web API key (added to `settings` as `STEAM_API_KEY`) and the Steam64 ID.

**`POST /api/integrations/imports/confirm` request body:**

```python
class ImportConfirmRequest(BaseModel):
    import_ids: list[int]          # platform_game_imports.id values to confirm
    default_status: LibraryStatus  # status to assign to all confirmed entries
```

### New Celery Tasks

```python
# app/workers/tasks/platform_sync.py

@celery_app.task(name="platform_sync.sync_steam_library", bind=True, max_retries=3)
def sync_steam_library(self, user_id: int, account_id: int) -> None:
    """
    1. Load ConnectedAccount, call Steam IPlayerService/GetOwnedGames API.
    2. For each game, attempt fuzzy name match against games table (normalize name, use
       pg_trgm or Python rapidfuzz).
    3. Upsert PlatformGameImport rows (update hours_played, last_played_at).
    4. Update ConnectedAccount.last_synced_at.
    5. Write sync result to Redis (key "platform_sync:{user_id}:{account_id}").
    """

@celery_app.task(name="platform_sync.match_unresolved_imports")
def match_unresolved_imports(user_id: int) -> None:
    """
    Re-attempt RAWG match for PlatformGameImport rows with status='unmatched'.
    Called after rawg_sync.sync_games completes (new games may now match).
    """
```

### Frontend Pages and Components

**New page:** `frontend/src/pages/integrations/IntegrationsPage.tsx`

- Route: `/integrations` — add to `router.tsx`.
- Link from `ProfilePage.tsx` or a new "Integrations" navbar item.

**Page sections:**

1. **Connected Accounts panel** — list of platform tiles (Steam, GOG, PlayStation, Xbox, Switch) showing connection status. Steam shows a text field for Steam64 ID + Connect button. Others show "Coming soon" or a "Add manually" fallback.
2. **Import Queue** — shown after a sync completes. A table of matched/unmatched games with confidence score, a "match to different game" search input for low-confidence matches, an "ignore" button per row, and a bulk "Import N games" confirm button.
3. **CSV Upload** — a `Mantine Dropzone` that accepts a `.csv` file with a single `game_name` column. Uploaded games go through the same matching pipeline.

**New components:**

- `PlatformConnectCard` — card per platform with connect/disconnect/sync actions and last-synced timestamp.
- `ImportMatchRow` — table row showing platform game name, matched RAWG game (with confidence badge), and action buttons.
- `GameSearchInput` — async autocomplete that calls `GET /api/games?search=` to let users manually correct a bad match.

### Integration with Existing Models

- On import confirmation, creates `LibraryEntry` rows using the same schema as `POST /api/library/`. Reuses `library_service.add_game()` so the recommendation precompute is triggered automatically.
- `hours_played` from Steam is not currently a field on `LibraryEntry`. It can be added as an optional `Float` column to `LibraryEntry` at this time (see also Feature 3 which needs this too).
- `last_played_at` from Steam gives a signal for the staleness score in Feature 1. It can be stored on `LibraryEntry` as `last_played_at DateTime nullable`.
- Deduplication: before creating a `LibraryEntry`, check for an existing row with the same `(user_id, game_id)` — the `uq_user_game` unique constraint already handles this at DB level.

### External APIs or Services

- **Steam Web API** (`api.steampowered.com`): `IPlayerService/GetOwnedGames/v1` — requires `STEAM_API_KEY` (free, developer key from Steamcommunity). Returns AppID, name, `playtime_forever` (minutes), `rtime_last_played` (Unix timestamp).
- **rapidfuzz** Python library (or PostgreSQL `pg_trgm` extension) for fuzzy name matching between Steam game titles and `Game.name` in the local DB. `rapidfuzz` is the simpler path as it has no DB migration dependency.
- No OAuth for MVP — Steam public API only.

Add `STEAM_API_KEY: str = ""` to `app/config.py` Settings.

### User Role Access

| Feature | BASIC | PREMIUM | ADMIN |
|---------|-------|---------|-------|
| Connect Steam account | Yes | Yes | Yes |
| Sync library | Yes | Yes | Yes |
| CSV import | Yes | Yes | Yes |
| Auto-sync on schedule (Celery Beat) | No | Yes | Yes |

BASIC users can connect and manually trigger syncs. PREMIUM users get automatic periodic re-sync via a Celery Beat schedule (`sync_steam_library` dispatched daily per connected account).

### UX Flow

1. User goes to `/profile` (or `/integrations` via a new nav link) and sees "Connected Accounts."
2. They click the Steam tile, enter their Steam64 ID (or public Steam profile URL — the backend parses the ID), and click "Connect."
3. The backend calls the Steam API, creates a `ConnectedAccount` record, and dispatches `sync_steam_library`.
4. A notification fires ("Syncing your Steam library..."). The import queue shows a loading skeleton.
5. When sync completes, the import queue loads: a list of all Steam games with match status. Matched games show the RAWG cover art and a green "Matched" badge. Unmatched games show an orange "No match" badge and a search field.
6. The user reviews the list, corrects any bad matches, unchecks games they don't want imported, and clicks "Import 47 games."
7. The backend creates `LibraryEntry` rows in bulk and triggers `precompute_for_user`. A success notification fires.

### Impact on Recommendation Engine

Importing games via this feature creates `LibraryEntry` rows identically to manual adds. The existing `precompute_for_user` Celery task is triggered after bulk import, so the recommendation engine automatically updates to reflect the newly imported library. No changes to `recommendation_service.py` required.

---

## 3. Gaming Journal / Session Logger

### Overview

Today, `LibraryEntry` supports a single `review` text field and a `rating` (1–5 float). This feature expands the app into a Letterboxd-style gaming journal: users can log individual play sessions with time tracking, multi-axis ratings (story, gameplay, visuals, soundtrack), session notes, and milestone notes (e.g. "just beat the final boss"). Structured multi-axis ratings feed richer signal into the recommendation engine as an alternative to the single composite rating.

### New DB Models

```
session_logs
  id              Integer PK
  user_id         Integer FK → users.id  NOT NULL
  game_id         Integer FK → games.id  NOT NULL
  library_entry_id Integer FK → library_entries.id nullable
  started_at      DateTime NOT NULL
  ended_at        DateTime nullable        -- null = session still active / manually omitted
  duration_minutes Integer nullable        -- computed from started/ended or manually entered
  notes           Text nullable
  is_milestone    Boolean default False    -- user can flag "beat the game", "finished act 1", etc.
  milestone_label String(255) nullable     -- e.g. "Completed", "Finished Act 2"
  created_at      DateTime

multi_axis_ratings
  id              Integer PK
  user_id         Integer FK → users.id  NOT NULL
  game_id         Integer FK → games.id  NOT NULL
  library_entry_id Integer FK → library_entries.id nullable
  story           Float nullable   -- 1–5
  gameplay        Float nullable   -- 1–5
  visuals         Float nullable   -- 1–5
  soundtrack      Float nullable   -- 1–5
  overall         Float nullable   -- 1–5 (may differ from LibraryEntry.rating)
  created_at      DateTime
  updated_at      DateTime
  UNIQUE (user_id, game_id)
```

Note: `LibraryEntry.rating` remains the primary signal for the recommendation engine (single float, weighted by status). `multi_axis_ratings.overall` can optionally sync to `LibraryEntry.rating` when saved, keeping the recommendation engine unchanged.

### New API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `POST` | `/api/journal/sessions` | BASIC+ | Log a new play session |
| `GET` | `/api/journal/sessions` | BASIC+ | List the user's session logs (paginated, filterable by game_id or date range) |
| `PATCH` | `/api/journal/sessions/{session_id}` | BASIC+ | Edit a session log |
| `DELETE` | `/api/journal/sessions/{session_id}` | BASIC+ | Delete a session log |
| `GET` | `/api/journal/sessions/stats` | BASIC+ | Aggregate stats: total hours, hours by genre this month, games played, etc. |
| `PUT` | `/api/journal/ratings/{game_id}` | BASIC+ | Upsert multi-axis rating for a game |
| `GET` | `/api/journal/ratings/{game_id}` | BASIC+ | Get multi-axis rating for a game |
| `GET` | `/api/journal/feed` | BASIC+ | Chronological journal feed (sessions + milestones) for the user |

**`GET /api/journal/sessions/stats` response (new `JournalStats` schema):**

```python
class JournalStats(BaseModel):
    total_hours_all_time: float
    total_hours_this_month: float
    sessions_this_month: int
    top_genres_this_month: list[dict]   # [{"genre": "RPG", "hours": 22.5}]
    games_played_this_month: int
    current_streak_days: int             # consecutive days with at least one session
    longest_streak_days: int
```

### New Celery Tasks

None required. All stats are computed synchronously from `session_logs` on request.
If stats become slow, a `recompute_journal_stats` task can be dispatched nightly and results cached in Redis.

### Frontend Pages and Components

**New page:** `frontend/src/pages/journal/JournalPage.tsx`

- Route: `/journal` — add to `router.tsx` and `AppNavbar`.

**Page tabs:**

1. **Feed tab** — chronological log of sessions and milestones, grouped by date. Each entry shows game art thumbnail, session duration, and notes excerpt.
2. **Stats tab** — summary cards: "40 hours of RPGs this month," "current streak: 5 days," top genres bar chart (Mantine `BarChart` or a simple horizontal progress stack).
3. **By Game tab** — a list of games in the user's library sorted by total logged hours, clicking through to a per-game journal view.

**New components:**

- `LogSessionModal` — `Mantine Modal` triggered from `GameDetailPage` ("Log Session" button) or from a global floating action. Fields: start time (datetime picker), duration (number input, minutes), notes (Textarea), milestone toggle + label.
- `MultiAxisRatingWidget` — five `Mantine Rating` components (story, gameplay, visuals, soundtrack, overall) in a compact grid. Shown on `GameDetailPage` below the existing single-star rating. Available to all users; replaces or supplements `LibraryEntry.rating`.
- `JournalFeedItem` — a timeline-style card for a single session or milestone entry.
- `JournalStatsCard` — summary card component used in the Stats tab.

**Integration with `GameDetailPage`:**

- Add a "Log Session" button alongside the existing "Add to Library" button.
- Show the multi-axis rating widget below the RAWG rating if the user has a library entry for the game.
- Show a compact session history (last 3 sessions) at the bottom of the page.

### Integration with Existing Models

- `session_logs` links to `LibraryEntry` via `library_entry_id` (nullable — a user can log a session without a formal library entry, e.g. they played a demo).
- When `multi_axis_ratings.overall` is saved, optionally sync it to `LibraryEntry.rating` so the recommendation engine benefits immediately. This sync should happen in `journal_service.upsert_rating()` with a DB write to `LibraryEntry` followed by dispatching `precompute_for_user`.
- `JournalStats.top_genres_this_month` requires joining `session_logs` → `games` → `games.genres` (JSON). This is a JSON-array extraction query in SQLAlchemy; manageable but slightly complex.

### External APIs or Services

None. All data is user-generated.

### User Role Access

| Feature | BASIC | PREMIUM | ADMIN |
|---------|-------|---------|-------|
| Log sessions | Yes | Yes | Yes |
| Multi-axis ratings | Yes | Yes | Yes |
| Journal stats | Yes | Yes | Yes |
| Journal feed | Yes | Yes | Yes |
| AI journal summary ("Your month in gaming") | No | Yes | Yes |

**Premium extension — AI journal summary:** Once per month, PREMIUM users can request a natural-language summary of their gaming month, generated by calling `ai_service` with their `JournalStats` and top session notes as context. Dispatched as a Celery task and stored as a `Text` field on a new `journal_summaries` table.

### UX Flow

1. User opens a game's detail page (`/games/:gameId`) and clicks "Log Session."
2. `LogSessionModal` opens with the current time pre-filled as start time and an empty duration field. User types notes ("Got to the first dungeon, controls feel great") and clicks Save.
3. The session is saved. If the game was in `backlog`, the status is optionally promoted to `playing` (with a confirmation prompt: "Move this to Playing?").
4. On the `/journal` page, the new session appears at the top of the Feed tab.
5. The Stats tab shows updated totals. If the user is on a streak, a subtle streak counter badge appears in the navbar (next to the Journal link).
6. When the user completes the game, they log a final session and tick the milestone checkbox labeled "Completed." This creates a milestone `session_log` entry and updates `LibraryEntry.status` to `completed`.

### Impact on Recommendation Engine

When `multi_axis_ratings.overall` is synced to `LibraryEntry.rating`, the existing weighted average in `build_user_taste_profile` automatically benefits from the richer signal (a 4.5 overall from structured ratings is more reliable than a single star click). No changes to `recommendation_service.py` are required.

---

### Mood / Emotion Tracker

This sub-feature extends the Session Logger with per-session emotion tagging. It serves two goals simultaneously: a **mood board** aesthetic in the journal UI (expressive, colorful, personal) and a **queryable data signal** for a future User Statistics page answering questions like "what games make me feel frustrated?" or "what genres put me in a flow state?"

#### Emotion List

A fixed vocabulary of 11 emotions, chosen to cover the full range of post-session gaming states without overlap or ambiguity:

| Emotion | Rationale |
|---|---|
| **Frustrated** | Died repeatedly, puzzle stumped you, controls fighting back — the most useful negative signal for difficulty-preference matching |
| **Happy** | Broad positive valence; the default "good session" emotion |
| **Sad** | Emotionally heavy narrative moments — games like *Disco Elysium* or *This War of Mine* produce this intentionally |
| **Angry** | Distinct from frustrated: sharper, less cognitive — rage-quit energy, unfair losses in competitive games |
| **Relaxed** | Cozy games, farming sims, low-stakes exploration — a positive meaningfully different from Happy |
| **Bored** | Grinding, repetitive filler, pacing problems — critical negative signal for engagement |
| **Proud** | Cleared a hard boss, finished a difficult platinum step, cracked a puzzle solo. Maps well to completionist behavior |
| **Creeped out** | Horror games, psychological thrillers, liminal dread — a genre-specific signal for future "games that unsettle you" stats |
| **Disappointed** | Hyped for a session that under-delivered — a nuanced negative distinct from Bored (boredom is flat affect; disappointment implies prior expectation) |

Deliberately excluded: "Tired" (physical state, not a game response), "Confused" (too ambiguous between good complexity and bad design).

#### DB Schema Addition

**Design decision: allow multiple emotions per session, stored as a PostgreSQL array.**

A session is rarely monotone — 40 minutes of *Dark Souls* might genuinely produce Frustrated + Proud. Forcing a single choice loses signal. The array also enables richer aggregation ("35% of your Elden Ring sessions included Frustrated *and* Proud").

**Addition to `session_logs` table:**

```
session_logs (additions only)
  emotions   ARRAY(VARCHAR(32)) nullable   -- e.g. ["frustrated", "proud"]
                                           -- values from the fixed EmotionType enum
                                           -- null = user skipped the picker
                                           -- empty array is distinct from null
```

**New backend enum (in `app/models/journal.py` or a shared `enums.py`):**

```python
class EmotionType(str, Enum):
    FRUSTRATED   = "frustrated"
    HAPPY        = "happy"
    SAD          = "sad"
    ANGRY        = "angry"
    RELAXED      = "relaxed"
    BORED        = "bored"
    PROUD        = "proud"
    CREEPED_OUT  = "creeped_out"
    DISAPPOINTED = "disappointed"
```

**No new tables required.** The emotions array on `session_logs` is sufficient for all planned queries.

Add a GIN index so `WHERE 'frustrated' = ANY(emotions)` queries stay fast as session volume grows:

```sql
CREATE INDEX ix_session_logs_emotions ON session_logs USING GIN (emotions);
```

#### Updated `session_logs` Table (Full, with Emotion Addition)

```
session_logs
  id                Integer PK
  user_id           Integer FK → users.id  NOT NULL
  game_id           Integer FK → games.id  NOT NULL
  library_entry_id  Integer FK → library_entries.id nullable
  started_at        DateTime NOT NULL
  ended_at          DateTime nullable
  duration_minutes  Integer nullable
  notes             Text nullable
  is_milestone      Boolean default False
  milestone_label   String(255) nullable
  emotions          ARRAY(VARCHAR(32)) nullable     -- list of EmotionType values
  created_at        DateTime

INDEX ix_session_logs_emotions ON session_logs USING GIN (emotions)
```

#### API Additions

**Modified existing endpoints** — `POST /api/journal/sessions` and `PATCH /api/journal/sessions/{session_id}` gain an `emotions` field:

```python
# In SessionLogCreate and SessionLogUpdate schemas
emotions: list[EmotionType] | None = None
# Validation: max 5 emotions per session; reject unknown values with 422
```

`GET /api/journal/sessions`, `GET /api/journal/feed` — include `emotions` in each `SessionLogOut` response. No schema restructuring needed.

**New endpoint:**

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/journal/emotions/stats` | BASIC+ | Emotion frequency and game/genre correlations for the user |

**Query parameters:**
- `period: "7d" | "30d" | "90d" | "all"` — default `"30d"`
- `game_id: int | None` — scope to a single game
- `genre: str | None` — scope to sessions on games with a given genre

**Response schema:**

```python
class EmotionFrequencyItem(BaseModel):
    emotion: EmotionType
    session_count: int
    percentage: float           # session_count / total_sessions_in_period * 100

class EmotionGameCorrelation(BaseModel):
    game_id: int
    game_title: str
    cover_url: str | None
    dominant_emotion: EmotionType
    session_count: int

class EmotionGenreCorrelation(BaseModel):
    genre: str
    dominant_emotion: EmotionType
    session_count: int
    emotion_breakdown: list[EmotionFrequencyItem]

class EmotionMonthlyBucket(BaseModel):
    month: str                              # "2025-11", "2025-12", etc.
    frequency: list[EmotionFrequencyItem]

class EmotionStats(BaseModel):
    period: str
    total_sessions_with_emotions: int
    total_sessions: int
    frequency: list[EmotionFrequencyItem]   # sorted descending by session_count
    most_common_emotion: EmotionType | None
    top_positive_game: EmotionGameCorrelation | None  # happy/proud/relaxed
    top_negative_game: EmotionGameCorrelation | None  # frustrated/angry/bored/disappointed/sad/creeped_out
    per_game: list[EmotionGameCorrelation]
    per_genre: list[EmotionGenreCorrelation]
    monthly_breakdown: list[EmotionMonthlyBucket]   # only populated when period="all"
```

Stats computation notes:
- `per_genre` requires `session_logs JOIN games` then extracting genre names from `games.genres` (JSON array of `{"id": int, "name": str}`) — same pattern as `top_genres_this_month` in `JournalStats`, extended to also unnest emotions.
- Positive emotions: `happy`, `proud`, `relaxed`. Negative: `frustrated`, `angry`, `bored`, `disappointed`, `sad`, `creeped_out`.
- Cache result in Redis under `journal_emotion_stats:{user_id}:{period}` with a 1-hour TTL, invalidated on any `session_logs` write, if performance degrades.

**Updated `JournalStats` schema:**

```python
class JournalStats(BaseModel):
    total_hours_all_time: float
    total_hours_this_month: float
    sessions_this_month: int
    top_genres_this_month: list[dict]
    games_played_this_month: int
    current_streak_days: int
    longest_streak_days: int
    dominant_emotion_this_month: EmotionType | None   # NEW
    emotion_coverage_pct: float | None                # NEW: % of sessions with emotions logged
```

#### UX: LogSessionModal Emotion Picker

The emotion picker is the last field before Save — after notes and milestone toggle. This respects the natural temporal sequence (log what happened first, then reflect on how you felt) and keeps it optional without visual guilt.

**Visual treatment — Emotion Chip Grid:**

Use Mantine `Chip.Group` with `multiple` and max 5 selections. Render in a 3-column grid (2-column on mobile). Each chip has a small icon to the left and a distinct background color when selected.

Section header copy: **"How did this session feel? (optional — pick up to 5)"**

**Emotion palette:**

| Emotion | Icon (Tabler) | Selected color |
|---|---|---|
| Frustrated | `IconMoodConfuzed` | `orange.6` |
| Happy | `IconMoodSmile` | `yellow.5` |
| Sad | `IconMoodSad` | `blue.4` |
| Angry | `IconFlame` | `red.6` |
| Relaxed | `IconLeaf` | `teal.5` |
| Bored | `IconZzz` | `gray.5` |
| Proud | `IconTrophy` | `yellow.7` |
| Creeped out | `IconGhost` | `grape.6` |
| Disappointed | `IconMoodEmpty` | `gray.6` |

If the user saves without selecting any emotion, `emotions` is stored as `null`. No sticky state between sessions. `Chip.Group` renders as grouped checkboxes, which is natively accessible — color reinforces meaning but is never the sole differentiator.

#### UX: Feed Tab — JournalFeedItem Emotion Display

A feed item already carries: game thumbnail, title, date, duration, notes excerpt, and milestone badge. Full text chips would clutter it.

**Treatment — Colored Dot Cluster:**

A horizontal cluster of small filled circles (14px diameter), each colored with the emotion's palette color, appearing in the bottom-left corner of the card. On hover/focus, each dot expands into a Mantine `Tooltip` showing the emotion label. Maximum 5 dots shown (matching input cap).

This gives the feed a mood board texture at a glance — a card with red/orange dots reads differently from one with yellow/teal — without adding text density. Sessions with no emotions show nothing (no placeholder).

If `is_milestone = true`, emotion dots move to bottom-right to avoid overlap with the milestone badge.

#### UX: Stats Tab — Emotion Stat Cards

Add a collapsible section to the Stats tab: **"How gaming makes you feel"**, below existing streak and hours cards.

**Card 1 — Dominant Emotion This Month:** Large emotion icon (48px), label in `h3`, subtext: "Your most common feeling this month — across X sessions." Secondary line: "Followed by [emotion 2] and [emotion 3]."

**Card 2 — Emotion Frequency Bar (horizontal):** Mantine `BarChart` or `Progress.Root` stack. Each bar is colored with the emotion palette color and labeled with name and percentage. Only emotions with at least one session are shown.

**Card 3 — Per-Game Emotion Snapshot:** 2-column mini-card grid, one card per game logged this month. Each shows: game cover (48×48), title (1 line), up to 3 emotion dots. Clicking navigates to the By Game tab for that game.

**Insight callouts (template strings, no LLM):**
- "Your happiest game this month: [Game Title]" — from `top_positive_game`
- "Most frustrating: [Game Title] — but you kept going" — from `top_negative_game` (only shown if a negative-dominant game exists)

#### UX: Future User Statistics Page (`/profile/stats`)

The `EmotionStats` endpoint supports all planned queries for the future stats page because it already accepts `period="all"` and returns `per_genre` and `monthly_breakdown`.

**Recommended emotion section layout — "Your Gaming Mood Profile":**

**Subsection 1 — All-Time Emotion Breakdown:** A Mantine `DonutChart` where each segment is one emotion, sized by all-time frequency, colored with the palette. Center shows the dominant emotion label and icon. Legend beneath lists each emotion with count and percentage. This is the mood board centerpiece of the stats page.

**Subsection 2 — Emotion by Genre (Heatmap Table):** A Mantine `Table` where rows are genres the user has logged sessions for, columns are the 11 emotions, and cells have `background-color` at opacity proportional to frequency (0 sessions = transparent; max for that genre = full opacity). Shows cross-genre emotional patterns at a glance without any filtering interaction.

**Subsection 3 — Emotional Journey Over Time:** A Mantine `AreaChart` with monthly buckets on the X-axis and areas for the top 4 emotions by frequency. Powered by `monthly_breakdown` in `EmotionStats`. Shows seasonal patterns ("always bored in summer", "immersed for 3 months during that RPG phase").

**Subsection 4 — Games That Made You Feel [Emotion]:** A horizontal pill row of emotion chips (using the palette). Selecting an emotion filters a game grid showing all library games where that emotion appeared in at least one session, sorted by frequency. Each game card shows a count ("Frustrated 4x"). Backed by: `GROUP BY game_id WHERE '{emotion}' = ANY(emotions)` on `session_logs`.

#### Role Access (Additions to Section 3 Role Table)

| Feature | BASIC | PREMIUM | ADMIN |
|---|---|---|---|
| Emotion picker in LogSessionModal | Yes | Yes | Yes |
| Emotion dots on Feed items | Yes | Yes | Yes |
| Emotion stat cards in Stats tab | Yes | Yes | Yes |
| Emotion section on `/profile/stats` | Yes | Yes | Yes |
| AI Mood Narrative (monthly) | No | Yes | Yes |

**Premium extension — AI Mood Narrative:** Once per month, PREMIUM users can request a paragraph-length reflection on their emotional gaming patterns, generated by `ai_service` with `EmotionStats` as context (e.g., "You spent most of October feeling immersed — mostly in Baldur's Gate 3. Your frustration spikes on weekends, suggesting you take on harder content when you have more time."). Dispatched as a Celery task; result stored on `journal_summaries` alongside the existing AI journal summary.

---

## 4. Wishlist Price Tracker + Release Calendar

### Overview

Users want to track games they're interested in but haven't bought yet. Today, the only statuses are playing/completed/backlog/dropped — there is no "wishlist" concept for games not yet in the user's possession. This feature adds a dedicated wishlist, a unified release calendar for upcoming games, and price drop alerts via the IsThereAnyDeal API (ITAD). Celery handles polling and notifications.

### New DB Models

```
wishlist_entries
  id              Integer PK
  user_id         Integer FK → users.id  NOT NULL
  game_id         Integer FK → games.id  NOT NULL
  target_price    Float nullable          -- user's desired price in USD
  notes           Text nullable
  added_at        DateTime
  notified_at     DateTime nullable       -- last time a price alert was sent
  UNIQUE (user_id, game_id)

price_alerts
  id              Integer PK
  user_id         Integer FK → users.id  NOT NULL
  game_id         Integer FK → games.id  NOT NULL
  wishlist_entry_id Integer FK → wishlist_entries.id NOT NULL
  store_name      String(100)             -- e.g. "Steam", "GOG", "Epic"
  price_usd       Float
  original_price_usd Float nullable
  discount_pct    Integer nullable        -- 0-100
  deal_url        String(500)
  detected_at     DateTime
  expires_at      DateTime nullable       -- sale end date if available from ITAD

itad_game_cache
  id              Integer PK
  game_id         Integer FK → games.id  UNIQUE NOT NULL
  itad_id         String(100) nullable    -- ITAD plain ID (e.g. "witcher3")
  last_price_usd  Float nullable
  last_checked_at DateTime
```

Note: `itad_game_cache` acts as a lookup table to avoid re-resolving the ITAD game ID on every price check. The ITAD `/games/lookup` endpoint maps a game title to its ITAD ID.

### New API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/wishlist` | BASIC+ | List the user's wishlist entries with latest price data |
| `POST` | `/api/wishlist` | BASIC+ | Add a game to the wishlist |
| `PATCH` | `/api/wishlist/{entry_id}` | BASIC+ | Update target price or notes |
| `DELETE` | `/api/wishlist/{entry_id}` | BASIC+ | Remove from wishlist |
| `GET` | `/api/wishlist/calendar` | BASIC+ | Upcoming release dates for wishlisted + recommended games |
| `GET` | `/api/wishlist/deals` | BASIC+ | Current deals for wishlisted games (from ITAD cache) |
| `POST` | `/api/wishlist/{entry_id}/check-price` | BASIC+ | Manually trigger an immediate price check for one game |

**`GET /api/wishlist` response item (`WishlistEntryOut` schema):**

```python
class WishlistEntryOut(BaseModel):
    id: int
    game: GameListOut
    target_price: float | None
    notes: str | None
    added_at: datetime
    latest_deal: PriceAlertOut | None     # most recent price_alerts row for this entry
    on_sale: bool                          # True if latest_deal.discount_pct > 0
```

**`GET /api/wishlist/calendar` response:**

Returns a list of games with release dates, sorted ascending by `Game.released`. Includes:
- All wishlisted games (regardless of release date)
- Up to 10 upcoming recommendations whose `Game.released` is in the future
- Groups by month for the frontend to render as a calendar

### New Celery Tasks

```python
# app/workers/tasks/price_tracker.py

@celery_app.task(name="price_tracker.check_wishlist_prices")
def check_wishlist_prices() -> None:
    """
    Scheduled task (Celery Beat, runs daily at 9:00 UTC).
    1. Load all active wishlist_entries joined to itad_game_cache.
    2. For entries whose game hasn't been checked in >24h, call ITAD /games/prices.
    3. If any store price <= wishlist_entry.target_price (or any deal found when
       target_price is null), create a price_alerts row.
    4. Dispatch notify_price_drop.delay(user_id, wishlist_entry_id) per match.
    5. Update itad_game_cache.last_checked_at.
    """

@celery_app.task(name="price_tracker.notify_price_drop")
def notify_price_drop(user_id: int, wishlist_entry_id: int) -> None:
    """
    Send an in-app notification (stored in a new notifications table, or
    emailed if SMTP is configured). Updates wishlist_entry.notified_at.
    """

@celery_app.task(name="price_tracker.resolve_itad_id", bind=True, max_retries=2)
def resolve_itad_id(self, game_id: int) -> None:
    """
    Called when a game is added to the wishlist if itad_game_cache row is missing.
    Calls ITAD /games/lookup?title=<game.name> and stores the itad_id.
    """
```

Celery Beat schedule entry (add to `celery_app.conf.beat_schedule`):

```python
"daily-price-check": {
    "task": "price_tracker.check_wishlist_prices",
    "schedule": crontab(hour=9, minute=0),
}
```

### Frontend Pages and Components

**New page:** `frontend/src/pages/wishlist/WishlistPage.tsx`

- Route: `/wishlist` — add to `router.tsx` and `AppNavbar`.

**Page tabs:**

1. **Wishlist tab** — grid of wishlisted games. Each card shows current lowest price, a "On Sale" badge when discounted, target price input, and a "Move to Library" action.
2. **Deals tab** — list of all current active deals for wishlisted games, sorted by discount percentage descending.
3. **Release Calendar tab** — a month-by-month view of upcoming release dates. Each game tile is clickable to the game detail page.

**New components:**

- `WishlistGameCard` — extends `GameCard` with: current price badge, "On Sale X% off" indicator, target price input field (inline edit), store links from ITAD.
- `ReleaseCalendarGrid` — groups games by release month. Uses Mantine `SimpleGrid` with month headings. Games with no confirmed release date are shown in an "Unconfirmed" section at the bottom.
- `PriceHistoryBadge` — compact component showing current price and whether it is at/below target.

**Add to library flow from wishlist:** "Move to Library" button calls `POST /api/library/` and then `DELETE /api/wishlist/{entry_id}`, transitioning the game from wishlist to library in one action.

### Integration with Existing Models

- `WishlistEntry` is independent from `LibraryEntry` — a game can be in both (e.g. a user wishlisted a game for price tracking but also owns a copy).
- `Game.released` is already a `Date` column on the `Game` model — the calendar feature requires no new game fields.
- "Upcoming release dates" for the calendar can use `Game.released > today` filtered from the catalog, combined with wishlisted games. The recommendation engine can optionally surface not-yet-released games in future work.

### External APIs or Services

- **IsThereAnyDeal API v2** (`api.isthereanydeal.com`): requires a free API key. Key endpoints:
  - `GET /games/lookup/v1?title=<name>` — resolve game title to ITAD plain ID
  - `GET /games/prices/v3` (POST with list of ITAD IDs) — returns current prices across all stores
  - Add `ITAD_API_KEY: str = ""` to `app/config.py` Settings.
- No email/SMS service is required for MVP — price alerts are stored as `price_alerts` rows and surfaced in the Deals tab. An email notification layer (via SendGrid or SMTP) can be added in a later iteration using the same `notify_price_drop` Celery task.

### User Role Access

| Feature | BASIC | PREMIUM | ADMIN |
|---------|-------|---------|-------|
| Wishlist (manual) | Yes (up to 20 games) | Yes (unlimited) | Yes |
| Release calendar | Yes | Yes | Yes |
| Price drop alerts (daily Celery check) | No | Yes | Yes |
| Manual price check | Yes (1/day per game) | Yes (unlimited) | Yes |
| Email notifications for price drops | No | Yes | Yes |

The 20-game cap for BASIC users is enforced in `wishlist_service.add_game()` by counting existing `WishlistEntry` rows for the user.

### UX Flow

1. On any `GameCard` or `GameDetailPage`, a new heart/bookmark icon appears alongside "Add to Library." Clicking it opens a small popover: "Add to Wishlist" with an optional target price input (e.g. "$15 or less").
2. The game appears on the `/wishlist` page under the Wishlist tab. If ITAD can resolve the game, a current price badge appears within seconds (ITAD resolution is synchronous on add, or via `resolve_itad_id` task if slow).
3. When the daily Celery price check runs and finds a price at or below the target, a notification badge appears on the Wishlist nav item. Clicking through shows the game highlighted in the Deals tab with a banner: "Witcher 3 is $4.99 on GOG — 75% off!"
4. The user clicks "Move to Library" to add it to their library and remove it from the wishlist.
5. The Release Calendar tab gives users a forward-looking view of when their wishlisted and recommended games are coming out, helping them plan purchases.

### Impact on Recommendation Engine

No direct impact. If desired, the recommendation engine could be extended to up-weight games that are on sale (increasing their cosine score slightly when `itad_game_cache.last_price_usd` is below a threshold), but this is not required for the core feature and would require changes to `compute_recommendations`.

---

## 5. Collection Completionist Tracker

### Overview

Many players track their progress toward 100% achievement completion. Today there is no way to log achievement progress within the app. This feature adds per-game achievement tracking: current achievement count, total achievements, completion percentage, and optionally a list of individual achievements with completion status. It surfaces a "completion goals" page where users can set a target (e.g. "get to 80% on Elden Ring this month") and see progress. Achievement data is sourced from the Steam Web API and RAWG (RAWG has basic achievement counts for some games).

### New DB Models

```
game_achievements
  id                Integer PK
  game_id           Integer FK → games.id  NOT NULL
  source            Enum('steam', 'rawg', 'manual')
  external_id       String(255) nullable     -- Steam achievement API name
  name              String(255) NOT NULL
  description       Text nullable
  icon_url          String(500) nullable
  is_hidden         Boolean default False
  global_completion_pct Float nullable       -- % of all players who unlocked it (from Steam)
  created_at        DateTime
  UNIQUE (game_id, source, external_id)

user_achievement_progress
  id                Integer PK
  user_id           Integer FK → users.id  NOT NULL
  game_id           Integer FK → games.id  NOT NULL
  achievement_id    Integer FK → game_achievements.id nullable  -- null for aggregate-only rows
  unlocked          Boolean default False
  unlocked_at       DateTime nullable
  updated_at        DateTime
  UNIQUE (user_id, achievement_id)

completion_goals
  id                Integer PK
  user_id           Integer FK → users.id  NOT NULL
  game_id           Integer FK → games.id  NOT NULL
  target_pct        Integer NOT NULL        -- 0-100, e.g. 80 for "80% complete"
  deadline          Date nullable
  completed_at      DateTime nullable       -- set when progress >= target_pct
  created_at        DateTime
  UNIQUE (user_id, game_id)

-- Aggregate view (can be a DB view or computed on read):
-- achievement_summaries: user_id, game_id, unlocked_count, total_count, completion_pct
-- Stored in a separate table to avoid re-counting on every request:

achievement_summaries
  user_id           Integer FK → users.id  NOT NULL
  game_id           Integer FK → games.id  NOT NULL
  total_achievements Integer default 0
  unlocked_count    Integer default 0
  completion_pct    Float default 0.0      -- 0.0-100.0
  last_synced_at    DateTime
  PRIMARY KEY (user_id, game_id)
```

### New API Endpoints

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| `GET` | `/api/achievements/games/{game_id}` | BASIC+ | List all achievements for a game (from `game_achievements`) |
| `GET` | `/api/achievements/progress/{game_id}` | BASIC+ | Get the user's progress summary + individual unlocks for a game |
| `POST` | `/api/achievements/progress/{game_id}/sync` | BASIC+ | Trigger Steam achievement sync for a game (requires Steam integration from Feature 2) |
| `PATCH` | `/api/achievements/progress/{game_id}/{achievement_id}` | BASIC+ | Manually toggle an achievement as unlocked/locked |
| `GET` | `/api/achievements/summary` | BASIC+ | User's overall completion stats across all library games |
| `GET` | `/api/achievements/goals` | BASIC+ | List the user's completion goals |
| `POST` | `/api/achievements/goals` | BASIC+ | Create a completion goal |
| `PATCH` | `/api/achievements/goals/{goal_id}` | BASIC+ | Update or delete a goal |

**`GET /api/achievements/summary` response (`AchievementSummaryOut`):**

```python
class AchievementSummaryOut(BaseModel):
    total_achievements_across_library: int
    total_unlocked: int
    overall_completion_pct: float
    fully_completed_games: int         # completion_pct == 100
    games_with_progress: int           # unlocked_count > 0
    nearest_completion: GameCompletionOut | None   # game closest to 100%
    estimated_hours_to_full_completion: float | None   # sum of remaining achievements * avg time per achievement
```

### New Celery Tasks

```python
# app/workers/tasks/achievement_sync.py

@celery_app.task(name="achievement_sync.sync_game_achievements", bind=True, max_retries=2)
def sync_game_achievements(self, game_id: int) -> None:
    """
    Fetch the achievement list for a game from Steam (by AppID) or RAWG.
    Upsert game_achievements rows. Does not touch user progress.
    Triggered when a game is added to the library (if Steam is connected) or
    when a user manually requests a sync.
    """

@celery_app.task(name="achievement_sync.sync_user_achievements", bind=True, max_retries=2)
def sync_user_achievements(self, user_id: int, game_id: int) -> None:
    """
    Fetch the user's unlocked achievements for a game from Steam
    (ISteamUserStats/GetPlayerAchievements/v1).
    Upsert user_achievement_progress rows and update achievement_summaries.
    Requires Feature 2 (ConnectedAccount for Steam) to be set up.
    """

@celery_app.task(name="achievement_sync.check_completion_goals")
def check_completion_goals() -> None:
    """
    Scheduled task (Celery Beat, daily).
    For each incomplete completion_goal, compare target_pct to achievement_summaries.completion_pct.
    If met, set completion_goals.completed_at and (optionally) send a notification.
    """
```

### Frontend Pages and Components

**New page:** `frontend/src/pages/achievements/CompletionistPage.tsx`

- Route: `/completionist` — add to `router.tsx` and `AppNavbar`.

**Page tabs:**

1. **Overview tab** — overall completion stats across the library. Progress rings per game (Mantine `RingProgress`), sorted by completion percentage. A "Nearest to completion" spotlight card.
2. **Goals tab** — list of active completion goals with a progress bar and deadline countdown. A "Set New Goal" button.
3. **Achievements tab** — a game picker; after selecting a game, shows the full achievement list with lock/unlock icons, global completion percentages, and a manual toggle for each.

**New components:**

- `GameCompletionCard` — card showing a game's completion ring, unlocked/total count, and a "Sync" button. Appears in the Overview tab grid.
- `AchievementListItem` — row in the achievement list: icon, name, description, global completion %, and a checkbox for manual toggle.
- `CompletionGoalCard` — goal card with circular progress, deadline badge, and edit/delete actions.
- `SetGoalModal` — Mantine Modal with game search (async autocomplete on `/api/games`), target % slider, and optional deadline date picker.

**Integration with `GameDetailPage`:**

- Add a "Completion" section below the game description showing the user's achievement progress summary (`unlocked_count / total_achievements`) and a link to the full achievement list on `/completionist`.
- If no progress exists, show "0 / N achievements" with a "Start tracking" button.

### Integration with Existing Models

- Achievement sync via Steam requires the `ConnectedAccount` (Feature 2) — specifically the `external_id` (Steam64 ID). If Feature 2 is not yet implemented, manual toggle is the only input mechanism.
- `achievement_summaries.completion_pct` can feed into the backlog prioritizer from Feature 1: games with 80-99% completion could be surfaced in "Close to 100%!" mode in the Play Next view.
- When a game reaches 100% completion (`achievement_summaries.completion_pct == 100.0`), optionally update `LibraryEntry.status` to `completed` — prompt the user: "You've unlocked all achievements! Mark as Completed?"
- The `Game` model already has a `playtime` field. RAWG does not expose individual achievement lists via the public API reliably, so the primary data source for achievement metadata is the Steam API (requiring the Steam integration) or manual entry.

### External APIs or Services

- **Steam Web API** (`api.steampowered.com`):
  - `ISteamUserStats/GetSchemaForGame/v2?appid=<appid>` — game achievement list (names, descriptions, icons). Requires `STEAM_API_KEY`.
  - `ISteamUserStats/GetPlayerAchievements/v1?appid=<appid>&steamid=<steam64id>` — user's unlock status per achievement. Requires `STEAM_API_KEY` + user's Steam64 ID.
  - `ISteamUserStats/GetGlobalAchievementPercentagesForApp/v2?gameid=<appid>` — global completion rates per achievement (for difficulty context).
- **RAWG API** (`api.rawg.io/api/games/{slug}/achievements`) — basic achievement count is available for some games but does not include individual unlock status. Useful for games not on Steam.
- Mapping Steam AppID to `Game.rawg_id`: RAWG stores `platforms` as JSON, but does not expose the Steam AppID directly. The mapping must be maintained either via the `itad_game_cache.itad_id` (Feature 4 overlap) or by storing `steam_appid` as a new nullable integer column on `Game`.

Add `steam_appid: Integer nullable` to the `Game` model — used by both Feature 2 and Feature 5.

### User Role Access

| Feature | BASIC | PREMIUM | ADMIN |
|---------|-------|---------|-------|
| Manual achievement tracking (toggle) | Yes | Yes | Yes |
| View achievement lists (from DB) | Yes | Yes | Yes |
| Steam achievement sync | Yes (manual trigger) | Yes (auto on library add) | Yes |
| Completion goals | Yes (up to 5) | Yes (unlimited) | Yes |
| Completion insights ("Nearest to 100%", estimated hours) | Yes | Yes | Yes |
| AI-generated "Next achievement to chase" suggestions | No | Yes | Yes |

**Premium extension — AI achievement advisor:** For PREMIUM users, a Celery task calls `ai_service` with the user's remaining locked achievements (name + description) and asks Claude to recommend which to pursue next based on their playstyle signals (genres, tags from Game DNA). The result is cached per game and surfaced as a "Suggested next achievement" card in the achievement list.

### UX Flow

1. User opens a game's detail page. If the game is in their library and has achievement data, a "Completion" section shows "12 / 47 achievements (25%)." A "View all" link goes to the achievement list on `/completionist`.
2. If the user has Steam connected (Feature 2), a "Sync from Steam" button appears. Clicking it dispatches `sync_user_achievements` and shows a spinner, then refreshes the list.
3. On `/completionist`, the Overview tab shows all library games as completion rings. The user can sort by "Nearest to 100%" to find games close to completion.
4. The user clicks "Set Goal" for a game at 60%. A modal opens — they set a target of 100% and a deadline of one month from now.
5. As they play and unlock achievements (either synced from Steam or manually toggled), the goal's progress bar fills. When they hit 100%, a success notification fires and the goal is marked complete.
6. PREMIUM users see a "Next achievement to chase" card above the achievement list — a short Claude-generated suggestion tailored to their playstyle.

### Impact on Recommendation Engine

Achievement completion percentage adds a weak but meaningful signal: games with 100% completion can increase the weight of the game's genres and tags in `build_user_taste_profile`. Specifically, fully completed games indicate deeper engagement than simply `status=completed`, and could be weighted at `5.5` (slightly above the current max rating of `5.0`) in `_STATUS_WEIGHTS`. This change would be a small modification to `recommendation_service.build_user_taste_profile` to check `achievement_summaries.completion_pct == 100.0` when assigning weights.

This enhancement is optional and should be deferred until `achievement_summaries` is populated with real data.

---

## Cross-Feature Dependencies

The five features have the following dependencies that should inform implementation order:

| Feature | Depends on |
|---------|-----------|
| 1. Backlog Manager | Requires PATCH /library/{entry_id} to be implemented (currently a stub) to support the "Start Playing" action |
| 2. Cross-Platform Unifier | No dependencies on other planned features; can be built independently |
| 3. Gaming Journal | Benefits from `hours_played` field on `LibraryEntry` (also needed by Feature 2); otherwise independent |
| 4. Wishlist Tracker | Requires no other planned features; benefits from `Game.released` already being populated via RAWG sync |
| 5. Completionist Tracker | Shares `steam_appid` on `Game` and `ConnectedAccount` model with Feature 2 — building Feature 2 first reduces duplication |

**Recommended implementation order:**
1. Feature 2 (Cross-Platform Unifier) — foundational: provides `ConnectedAccount`, `steam_appid` on `Game`, and bulk import infrastructure that Features 3 and 5 depend on.
2. Feature 1 (Backlog Manager) — highest daily active user value; requires only that PATCH /library/{entry_id} be un-stubbed.
3. Feature 3 (Gaming Journal) — deepens engagement; reuses library infrastructure and feeds better recommendation signals.
4. Feature 4 (Wishlist Tracker) — adds a new pre-purchase user journey; mostly self-contained.
5. Feature 5 (Completionist Tracker) — most external API surface area; best built after Feature 2 validates the Steam integration.
