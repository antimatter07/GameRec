---
target: library page
total_score: 23
p0_count: 0
p1_count: 3
timestamp: 2026-05-25T04-53-19Z
slug: frontend-src-pages-library-librarypage-tsx
---
#### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Loading and mutation feedback exist, but the 3-second search delay gives no clear "searching soon" or "applied" state. |
| 2 | Match System / Real World | 3 | Most labels fit a game library, but catalog language like "Discovery pick" and "In your library" leaks into a page where everything is already in the library. |
| 3 | User Control and Freedom | 2 | There is cancel in edit, but no clear search reset, no undo for remove, and destructive removal is one click. |
| 4 | Consistency and Standards | 2 | The library card repeats status and rating outside the game card while the game card also shows generic discovery signals and RAWG-style rating. |
| 5 | Error Prevention | 1 | Remove has no confirmation or undo, and clearing a rating likely cannot persist because zero maps to undefined. |
| 6 | Recognition Rather Than Recall | 3 | Tabs, filters, and labels are visible; icon-only edit/remove actions are labeled for screen readers but not visually self-explanatory. |
| 7 | Flexibility and Efficiency of Use | 2 | Good direct filters, but no bulk edit, no quick status changes in place, and common library maintenance remains one item at a time. |
| 8 | Aesthetic and Minimalist Design | 2 | Four metric cards plus two overview panels push the actual library below the fold and make the page feel more dashboard than media shelf. |
| 9 | Error Recovery | 2 | Errors are plain, but generic. They do not suggest retry, preserve context explicitly, or offer a recovery action. |
| 10 | Help and Documentation | 1 | Empty states are readable, but there is no contextual guidance for ratings, statuses, queue behavior, or Play Next. |
| **Total** | | **23/40** | **Acceptable: useful foundation, but the page needs stronger prioritization before it feels effortless.** |

#### Anti-Patterns Verdict

**LLM assessment**: This does not look like a blatant AI-generated interface. It uses the established Mantine vocabulary, real media cards, restrained dark surfaces, and the GameRec ember accent correctly. The problem is subtler: it has a "product dashboard before product shelf" shape. A library page should make saved games feel browsable and desirable immediately; this page first asks the user to consume metrics, status distribution, top genres, tabs, search, and sort.

The largest AI-slop tell is the repeated metric-card pattern and generic insight copy. "Total games", "Playing now", "Completed", and "Average rating" are useful, but together they create a familiar SaaS dashboard rhythm that the product context explicitly rejects. The top of the page needs one strong library action and a compact read on state, not six analytic panels.

**Deterministic scan**: Attempted `detect.mjs --json frontend/src/pages/library/LibraryPage.tsx`, but this skill install returned `Error: bundled detector not found.` No deterministic rule output was available. Manual scan found no absolute-ban issues like gradient text, side-stripe borders, or default glassmorphism on this page. The `GameCard` playtime badge does use blur, but it is purposeful for image readability rather than decorative glassmorphism.

**Visual overlays**: Browser overlay was not available in this Codex session, so no reliable user-visible overlay exists. Fallback signal: source review of `LibraryPage.tsx`, `LibraryPage.module.css`, `GameCard.tsx`, and `GameCard.module.css`.

#### Overall Impression

The page is competently built, visually consistent, and on-brand at the component level. Its main weakness is information priority: it treats the library like an analytics report before it treats it like a personal media shelf. The single biggest opportunity is to make the saved games grid the hero of the page, with stats collapsed into a compact summary band or secondary insight.

#### What's Working

1. **The base visual system is coherent.** Dark layered panels, ember primary actions, compact type, and media-first cards align with the GameRec design system.
2. **Status taxonomy is clear.** Playing, replaying, completed, backlog, wishlist, and dropped map well to how players think about backlog management.
3. **The page has useful operational controls.** Search, sort, status tabs, inline edit, loading states, and pagination cover the practical maintenance workflow.

#### Priority Issues

**[P1] The actual library starts too late**

**Why it matters**: The user came to see and manage saved games, but the first major surface is four metric cards followed by two overview panels. That makes the page feel like a dashboard, and it delays the emotional payoff of cover art.

**Fix**: Move the tabs/search/grid up directly under the header. Compress stats into one slim summary row or a collapsible "Library pulse" panel below the first row of games.

**Suggested command**: `layout`

**[P1] Library cards mix two mental models**

**Why it matters**: In the library context, `GameCard` still shows catalog discovery signals like "In your library", playtime badges, and external game rating, while the page adds local status, user rating, added date, and genres underneath. The user has to parse two separate cards per game and decide which metadata matters.

**Fix**: Create a library-specific card variant that puts cover art, title, user status, user rating, added date, primary genre/platform, and quick actions into one integrated component. Hide discovery signals when `showAdd` is false or add an explicit `context="library"` prop.

**Suggested command**: `craft`

**[P1] Destructive removal is too easy**

**Why it matters**: The trash icon removes an entry immediately. For a backlog app, removing a saved game is a high-regret action because it affects tracking history and recommendation signals.

**Fix**: Use an inline confirmation state on the card: first click changes the action area to "Remove?" with Cancel and Remove. Add undo in the notification after removal.

**Suggested command**: `harden`

**[P2] Search behavior is under-communicated**

**Why it matters**: Search applies after 3 seconds or Enter, but the page does not tell the user whether the query is pending, applied, or stale. That creates doubt on slow connections.

**Fix**: Apply search on a shorter debounce, show a compact "Searching..." state beside the input, and add a clear button when a query is active.

**Suggested command**: `clarify`

**[P2] The overview visuals rely too much on color and add cognitive load**

**Why it matters**: The status overview repeats the tab counts in another format. It is visually neat but it asks users to compare six colors and bars before they reach the library. It also depends on color as the main distinction.

**Fix**: Either remove it from the primary page or turn it into a secondary collapsed insight. If kept, label each bar with percent and count, and use fewer colors with status text doing the work.

**Suggested command**: `distill`

#### Persona Red Flags

**Alex, Power User**

Alex wants to sweep through a backlog quickly. The page gives search, sort, and tabs, but every edit opens a modal and every remove is one item at a time. There is no bulk status change, no multi-select, no quick inline status dropdown, and no keyboard accelerator for "mark completed", "rate", or "move to playing".

**Sam, Accessibility-Dependent User**

Most Mantine controls should be keyboard reachable, and focus styles exist on game card buttons. Red flags: status distribution uses color bars as the primary visual signal, edit/remove action labels are generic rather than game-specific, the decorative game image uses empty alt text even though the cover is the primary media object, and async notifications may not be enough for screen reader confirmation without checking live-region behavior.

**Maya, Backlog Planner**

Maya is trying to reduce decision pressure. The page starts with totals, completion rate, top genres, and distribution before the games. That can make the backlog feel like inventory work. "Play next" is present, but the page does not explain which game deserves attention or surface a prioritized next candidate until after an edit side effect.

#### Minor Observations

- The `Average rating` metric uses ratings from currently loaded entries, while `stats.avg_rating` may represent the full library. The metric value and sublabel can refer to different scopes.
- `Edit entry` and `Remove from library` should include the game name in the accessible label.
- The empty state has no direct "Browse catalog" action despite saying to browse the catalog.
- `rating: editRating > 0 ? editRating : undefined` makes it unclear whether a user can clear an existing rating.
- The status tabs expose seven options at once. It is workable, but it is above the four-option cognitive-load comfort zone.

#### Questions to Consider

- What if the first screen showed the user's saved games immediately, with stats as a supporting layer rather than the opening act?
- Should a library card answer "what is this, where am I with it, and what can I do next" without needing a second metadata card underneath?
- Is the page meant for reflection on taste, or fast backlog maintenance? Right now it is trying to be both at equal volume.
