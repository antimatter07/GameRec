---
target: the catalog page
total_score: 22
p0_count: 0
p1_count: 2
timestamp: 2026-05-24T13-47-08Z
slug: frontend-src-pages-games-catalogpage-tsx
---
#### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Loading, empty, error, result count, and pagination states exist; save/remove feedback depends on notifications outside the catalog context. |
| 2 | Match System / Real World | 2 | The catalog language is functional but not taste-led; labels like "15h avg" and "RAWG-style" metadata are not explained in context. |
| 3 | User Control and Freedom | 2 | Reset exists, but filters/page state are not URL-backed, pagination loses shareability, and destructive remove is one-click from a card. |
| 4 | Consistency and Standards | 2 | The catalog still uses hard-coded ember colors and negative letter spacing while newer polished areas use theme tokens and zero letter spacing. |
| 5 | Error Prevention | 2 | Dropdown filters prevent invalid genre/platform/year values, but save/remove actions are embedded in a clickable card and can be easy to misfire. |
| 6 | Recognition Rather Than Recall | 3 | Filters and card actions are visible; users still have to infer what playtime, catalog scope, and "Save as" statuses mean. |
| 7 | Flexibility and Efficiency | 2 | Search is debounced and Enter/blur commits, but there is no sort, no URL persistence, no page-size control, and no power-user batch path. |
| 8 | Aesthetic and Minimalist Design | 3 | The surface is clean and media-first, but the catalog is still mostly a generic filter panel plus card grid. |
| 9 | Error Recovery | 2 | The error copy is plain, but there is no inline retry action and no degraded/offline recovery path. |
| 10 | Help and Documentation | 1 | There is light instructional copy, but no contextual explanation for statuses, playtime source, filters, or saving behavior. |
| **Total** | | **22/40** | **Acceptable, significant improvements needed before users are happy** |

#### Anti-Patterns Verdict

**LLM assessment**: The catalog does not scream AI-generated, but it still has product-template tells: header, filter panel, results heading, uniform card grid. The cards are attractive enough and media-forward, but the overall composition does not yet feel like a confident cinematic game discovery surface. It feels competent, not memorable.

**Deterministic scan**: Attempted on `frontend/src/pages/games/CatalogPage.tsx`, `frontend/src/components/games/GameCard.tsx`, and `frontend/src/components/games/GameFilters.tsx`. All attempts failed with `Error: bundled detector not found.` No deterministic findings are available.

**Visual overlays**: Not available in this Codex session because browser automation tools are not exposed. No reliable user-visible overlay was created.

#### Overall Impression

The catalog is structurally sound: it has the right basics, including search, filters, loading skeletons, empty states, and a media-first card grid. The biggest opportunity is to turn it from a plain searchable database into a stronger discovery surface that helps users decide what is worth saving.

#### What's Working

1. **The card format is directionally right.** Large artwork, overlaid playtime, rating, compact metadata, and a direct save action support the product goal of making games feel like media rather than table rows.
2. **Core async states are present.** Loading skeletons, error panel, empty state, result count, and pagination make the page more trustworthy than a blank grid.
3. **The filter panel is understandable.** Search, genre, platform, year, and reset are visible and grouped together, so basic browsing requires little discovery.

#### Priority Issues

**[P1] The catalog does not help users decide why a game is worth saving**

**Why it matters**: GameRec's core promise is taste-aware discovery and backlog planning. The catalog currently shows generic media cards: title, genre/platform/year, rating, playtime, save. It does not surface fit, quality, relevance, owned/saved status nuance, or "why this belongs in your library." Users still have to inspect every card manually.

**Fix**: Add a compact discovery signal per card or per row: "Popular with RPG fans", "Short backlog pick", "Highly rated", "Recently enriched", "Already in wishlist", or "Good next-play length." Keep it restrained, one signal max, so the card does not become badge soup.

**Suggested command**: `$impeccable shape catalog discovery signals`

**[P1] Card click and nested save/remove controls create interaction risk**

**Why it matters**: The whole card is a link-like target, while the save/remove button and menu live inside it. The code stops propagation, but this pattern is fragile for keyboard users and screen readers. A user trying to save a game can accidentally open details, and a user tabbing through the page has a complicated nested interaction model.

**Fix**: Separate navigation and action zones more clearly. Make the cover/title the explicit detail link and keep the card body non-clickable, or keep the card clickable but move save actions into a stable footer with stronger focus treatment and test keyboard order. Add a confirmation or undo path for remove.

**Suggested command**: `$impeccable harden catalog card interactions`

**[P2] Filters are useful but too shallow for actual catalog browsing**

**Why it matters**: Genre, platform, and year are a start, but catalog browsing often needs sort, rating, runtime, release window, and saved/not-saved state. Without sort or saved-state filters, users who know what they want still have to paginate manually.

**Fix**: Add a compact sort control and one or two high-value filters: "Not in library", "Short games", "Highly rated", or "Recently released." Avoid exposing every backend field. Start with the filters that map to actual user intent.

**Suggested command**: `$impeccable shape catalog filters`

**[P2] State is not URL-backed, so the catalog is not shareable or resilient**

**Why it matters**: The TODO in `CatalogPage.tsx` is user-visible behavior. Search/filter/page state disappears on refresh and cannot be shared. That makes catalog browsing feel temporary and undermines serious backlog research.

**Fix**: Sync `search`, `genre`, `platform`, `year`, and `page` to URL search params. Preserve state on reload and browser back/forward. Debounce only the search param update, not every filter.

**Suggested command**: `$impeccable harden catalog state`

**[P2] Visual system drift remains inside catalog-specific CSS**

**Why it matters**: The rest of the polished product has moved toward theme-level ember tokens. Catalog CSS still contains hard-coded ember hex values and negative letter spacing. This compounds design drift and makes future theming harder.

**Fix**: Replace hard-coded `#d4674d`, `#b9543e`, `#fff1ec`, etc. with `var(--mantine-color-ember-*)`, set title letter spacing to `0`, and align card/button styles with the shared theme defaults.

**Suggested command**: `$impeccable polish catalog visual tokens`

#### Persona Red Flags

**Alex (Power User)**: Alex can search quickly, but cannot sort by rating, length, release date, or saved status. Pagination state is not URL-backed, so sharing or reopening a filtered research view fails. The page is browseable, but not efficient.

**Sam (Accessibility-Dependent User)**: The card-as-link plus nested button/menu pattern is the main risk. Keyboard focus can reach controls, but the mental model is mixed: a parent card with `role="link"` contains a button and menu. Images have alt text, focus exists, and filters are labeled via Mantine, but the interaction structure needs hardening.

**Casey (Distracted Mobile User)**: Filters stack on mobile, which is good, but the primary action is repeated inside each card and may sit low in a long scrolling grid. There is no sticky filter summary, no saved-state quick filter, and no URL persistence if Casey gets interrupted.

**Project persona, The Backlog Curator**: This user wants to reduce decision pressure and build an intentional queue. The catalog shows games, but does not yet frame which games are "queue-worthy" or why one result deserves attention over another. They may browse, save a few obvious titles, then stall.

#### Minor Observations

- The subtitle "collection-ready library feed" sounds internal and a bit abstract.
- "Catalog results" duplicates the page concept without adding much value.
- `15h avg` is compact but ambiguous unless users know it means RAWG average playtime fallback.
- The fixed filter option lists are likely incomplete versus the actual synced catalog.
- Skeleton cards are useful, but they do not reserve the exact same card action/footer rhythm as loaded cards.
- Empty state is polite but could offer a one-click "Clear filters" action.

#### Questions to Consider

- What if the catalog's job were not "show all games" but "help me find something worth saving in under 30 seconds"?
- Which one card signal would most reduce browsing fatigue: fit, quality, runtime, popularity, or saved status?
- Should removing a saved game from the catalog be a destructive action, or should it become an undoable status change?
