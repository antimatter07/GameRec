---
target: catalog page
total_score: 24
p0_count: 0
p1_count: 2
timestamp: 2026-05-24T03-20-12Z
slug: frontend-src-pages-games-catalogpage-tsx
---
#### Design Health Score

| # | Heuristic | Score | Key Issue |
|---|-----------|-------|-----------|
| 1 | Visibility of System Status | 3 | Loading, empty, error, result count, and pagination states exist. Search/filter application is not explicit, and active filters are summarized as a count instead of visible chips. |
| 2 | Match System / Real World | 2 | “Game Catalog,” “Catalog results,” “collection-ready library feed,” and `NR` feel database-like rather than player-centered. |
| 3 | User Control and Freedom | 3 | Reset and pagination exist, but URL state is TODO-only and individual filters cannot be removed from a visible active-filter strip. |
| 4 | Consistency and Standards | 3 | Mantine controls and dark styling are coherent. The card-as-link pattern with a nested save/remove action creates interaction ambiguity. |
| 5 | Error Prevention | 2 | Full-card navigation wraps an embedded library action, increasing accidental navigation risk and creating unclear keyboard semantics. |
| 6 | Recognition Rather Than Recall | 2 | Main controls are visible, but active filter meaning requires scanning the form controls. Filter inputs rely on placeholders instead of persistent labels. |
| 7 | Flexibility and Efficiency | 2 | No sort, saved views, URL-shareable filters, owned/unowned filter, or top pagination. Power browsing remains limited. |
| 8 | Aesthetic and Minimalist Design | 3 | Clean and restrained, but too panelized and generic for a cinematic discovery surface. |
| 9 | Error Recovery | 2 | The error state tells users to refresh manually but does not offer a retry action. |
| 10 | Help and Documentation | 2 | Empty state gives basic guidance, but first-time users do not get enough context about saving, backlog, or recommendation impact. |
| **Total** | | **24/40** | **Acceptable, solid scaffold with significant product-expression and interaction issues.** |

#### Anti-Patterns Verdict

**LLM assessment**: The page does not immediately look AI-generated, but it does look like a competent generic dark catalog. The slop tell is not garish visuals, it is safe wording and safe structure: title, bordered filter panel, “Catalog results,” uniform cards, bottom pagination. For GameRec, this misses the stronger product idea: a personal discovery shelf where game media and backlog decisions are the point.

**Deterministic scan**: The bundled detector could not run because the installed skill is missing its detector implementation. The attempted command returned `Error: bundled detector not found.` Source checks found no side-stripe borders, no gradient text, and no default glassmorphism. The image shade gradient is contextual, and the playtime badge blur is contained rather than a page-wide glass style.

**Visual overlays**: No reliable user-visible overlay is available. Browser automation/runtime was unavailable in this environment, and the detector script was missing its implementation.

#### Overall Impression

The catalog is usable, clean, and not embarrassing. It has the expected parts: search, filters, loading skeletons, empty/error states, cards, add buttons, and pagination. The problem is that it behaves and speaks like a database index, while GameRec wants to feel like a composed, cinematic, personal discovery product. The single biggest opportunity is to change the first screen from “filter a catalog” to “discover games worth adding to your backlog.”

#### What's Working

1. The game cards give artwork meaningful space. `GameCard.module.css` gives the media section a tall, stable region, which supports the media-first direction.

2. The state coverage is better than a happy-path UI. `CatalogPage.tsx` includes skeleton loading, error, empty, result count, and pagination states.

3. The color system is mostly restrained. Ember is used on action/focus/pagination states and does not become a neon gamer treatment.

#### Priority Issues

**[P1] Database framing weakens the product promise**

Why it matters: “Game Catalog,” “Browse games,” and “Catalog results” frame the page as an inventory table with cards. That clashes with GameRec’s purpose: reducing decision pressure and helping players build an intentional backlog.

Fix: Reframe the page around intent. Use a title like “Find your next game” or “Explore games for your backlog.” Replace “Browse your collection-ready library feed with compact filters and consistent game cards” with copy that says what the user can do and why it matters.

Suggested command: `$impeccable clarify catalog page`

**[P1] Card navigation conflicts with the save/remove action**

Why it matters: `GameCard.tsx` makes the entire card a keyboard-focusable pseudo-link, while `SaveToLibraryButton` lives inside the same clickable card. This risks accidental navigation, awkward event propagation, and confusing screen-reader semantics.

Fix: Separate click zones. Make image/title the detail link, and keep the save/remove button outside that link region. Prefer a real link for navigation instead of `role="link"` on the whole card.

Suggested command: `$impeccable harden game cards`

**[P2] Active filters require recall**

Why it matters: The UI says “2 active filters,” but the user must scan the form to remember which filters are active. This slows correction and makes filtered result sets less trustworthy.

Fix: Add removable active-filter chips beneath the filter row: `Action`, `PC`, `2024`, `Search: hollow knight`. Keep `Reset` as the broad escape hatch.

Suggested command: `$impeccable layout catalog filters`

**[P2] The cards do not yet help backlog decisions**

Why it matters: Players deciding whether to save a game need confidence: time commitment, platform fit, genre/mood, rating confidence, ownership status, or later recommendation fit. Current cards show metadata, rating, and add/remove, but not enough decision framing.

Fix: Promote one backlog-relevant signal per card. Keep playtime, add owned/saved state clarity, and later reserve space for a concise recommendation or taste signal without AI sparkle language.

Suggested command: `$impeccable shape catalog cards`

**[P3] The first mobile viewport is filter-heavy**

Why it matters: On mobile, the controls collapse to full-width fields, which is usable but likely pushes game artwork below the first view. That makes the page feel like a form before it feels like discovery.

Fix: Collapse secondary filters behind a “Filters” disclosure on mobile, keep search and result count visible, and show the first row of games sooner.

Suggested command: `$impeccable adapt catalog page`

#### Persona Red Flags

**Alex, power user**: Alex wants to quickly narrow and repeat searches. Red flags: no sort control, no URL persistence despite TODOs in `CatalogPage.tsx` and `GameFilters.tsx`, no active-filter chips, no saved filter views, and pagination only at the bottom.

**Jordan, first-timer**: Jordan needs to know what this page is for in five seconds. Red flags: “collection-ready library feed” is vague, “Catalog results” is mechanical, `NR` is unexplained, and adding a game does not communicate whether it goes to backlog, library, wishlist, or recommendations.

**Sam, accessibility-dependent user**: Sam benefits from visible focus states and keyboard handling, but the card interaction model is risky. Red flags: full-card pseudo-link plus nested button, filter fields without explicit labels in source, and placeholder-only field identification.

**Casey, distracted mobile user**: Casey needs to see useful content quickly and tap with low precision. Red flags: full-width filters may dominate the first mobile viewport, reset/filter controls are top-heavy, and the bottom-only pagination means long scroll recovery.

**Backlog discovery player**: This project-specific user wants confidence that saved games are worth future time. Red flags: every card has the same add action with little decision support, and the page does not explain how catalog actions improve queue, recommendations, or taste profile.

#### Minor Observations

- The fallback image points to `placehold.co`, which can break the cinematic tone and adds an external dependency for a common empty-media state.
- Yellow rating stars are understandable, but they compete with the ember system. Keep them only if rating is a primary comparison signal.
- Uppercase slash-separated metadata feels more storefront/launcher than reflective media library.
- The error state should include a retry button instead of only telling users to refresh.
- “Search games...” should be “Search by title” for clarity.
- Hardcoded colors appear across catalog/card/filter CSS. They match the current palette, but tokenizing would make future polish safer.

#### Questions to Consider

- Is this truly a catalog, or is it a discovery shelf for building a better backlog?
- What should a user understand after saving a game: library ownership, backlog intent, recommendation signal, or all three?
- What if filters were supporting tools, and the first dominant object on the page was game artwork?
- Which single card signal would most reduce “I do not know what to play next”?
