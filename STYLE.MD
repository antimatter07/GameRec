# STYLE.MD

This file captures the visual language of the Journal page and turns it into a reusable UI reference for future work in this repository.

Use this as the default styling guide for new product UI unless a page already has a stronger local pattern.

## Source of truth

This style guide is derived from:

- `frontend/src/App.tsx`
- `frontend/src/pages/journal/JournalPage.tsx`
- `frontend/src/components/journal/Journal.module.css`
- `frontend/src/components/journal/JournalStatsCards.tsx`
- `frontend/src/components/journal/JournalFeedItem.tsx`
- `frontend/src/components/journal/LogSessionModal.tsx`
- `frontend/src/components/journal/MultiAxisRatingWidget.tsx`

## Core mood

The Journal page is not a marketing page. It feels like a compact personal dashboard:

- dark, layered, and calm
- data-dense but readable
- soft emphasis instead of loud contrast
- game-adjacent without becoming flashy
- analytical first, decorative second

New UI should feel like it belongs beside the Journal page, not beside a generic SaaS starter.

## Theme foundations

### Typography

- Primary font: `Plus Jakarta Sans`
- Monospace / numeric support: `Space Mono` or `JetBrains Mono`
- Headings are bold but not oversized
- Most section titles use `sm` text with `fw={600}`
- Supporting copy usually sits at `xs` or `sm`
- Numeric values should use tabular numbers when possible

### Radius

Follow the Mantine theme:

- `xs`: `4px`
- `sm`: `8px`
- `md`: `12px`
- `lg`: `16px`
- `xl`: `24px`

For Journal-like UI, prefer:

- card and panel framing: `md`
- small internal chips / cover blocks / tiny panels: `sm`
- progress bars and tight meters: `xs` to `sm`

### Color strategy

Base UI:

- main accent: Burnished Ember (`#d4674d`)
- base surfaces: `dark-7`, `dark-6`, `dark-5`
- borders: subtle dark border colors, never harsh outlines
- dimmed text is heavily used for metadata and labels

Functional accents:

- Burnished Ember (`#d4674d`): primary actions, active state, key highlights, recommendation intelligence
- Sea-Glass Teal (`#2fb8a6`): positive progress and completion
- Marquee Gold (`#e0b957`): ratings, streaks, trophies, achievement-like emphasis
- Archive Blue (`#5b8def`): neutral metrics and alternate highlights
- orange, pink, green, red, and gray: journal emotion and chart differentiation only

Rules:

- ember is the anchor, not the whole palette
- avoid violet or purple as the default accent for new UI
- avoid bright pure red unless the action is genuinely destructive
- avoid large flat color fields when a dark surface plus colored detail will do
- keep background contrast soft and layered

## Layout principles

### Page shell

- Pages should breathe with `lg`-scale outer padding
- Major sections are stacked with moderate vertical separation
- Use responsive grids instead of wide empty gutters
- Favor 2-column dashboard layouts that collapse cleanly to 1 column

Journal patterns to reuse:

- one primary header row with title, support text, and one clear action
- a top metrics strip
- mixed-width content bands beneath it
- framed sections using `Paper` with `withBorder`

### Spacing

Default spacing rhythm:

- dense internal spacing: `xs`
- standard internal spacing: `sm`
- section padding: `md`
- page / major section separation: `lg` to `xl`

In practice:

- use `12px` to `14px` internal card padding for compact objects
- use `md` panel padding for most data surfaces
- leave only enough whitespace to improve scanability

### Grid behavior

- metrics: 4-up desktop, 2-up tablet, 1-up narrow mobile
- equal content sections: 2 columns on desktop, 1 on mobile
- main dashboard split: asymmetric 1.4 / 1 ratio when one card deserves prominence

## Component language

### Panels and cards

Default panel recipe:

- Mantine `Paper`
- `p="md"`
- `radius="md"`
- `withBorder`
- dark surface background from the theme

Panels should feel structured, not ornamental. Avoid shadows unless there is a strong reason.

### Metric cards

Metric cards follow a very specific hierarchy:

- small uppercase label
- large numeric value
- tiny contextual subtext
- one compact icon block in the corner

Rules:

- labels are uppercase, tiny, and dimmed
- values are bold and color-tinted
- subtext stays compact and factual
- icon containers are small, soft, and color-coded

### Lists and feed items

Feed rows are compact horizontal items:

- left: small image or placeholder
- center: title + metadata
- optional emotion dots / status details
- right: short numeric or duration value

Rules:

- rows should feel click-ready
- hover should slightly lift contrast, not transform dramatically
- metadata is allowed to wrap lightly, but titles should truncate

### Tabs

- use pill-style tabs when switching between peer views
- tab labels stay compact
- icons should be small and familiar
- avoid oversized tab chrome

### Buttons

- button radius: `sm`
- icons around `14px` to `16px`
- primary button color: Burnished Ember (`#d4674d`)
- quiet secondary actions use `subtle` or `light`

Rules:

- one clear primary action per section or header
- prefer short labels
- keep button heights stable across sibling actions

### Chips, badges, and small status UI

- use them sparingly
- they should annotate, not dominate
- emotion chips and small badges are acceptable because they compress meaning efficiently
- small status items should usually stay at `xs`

### Charts and data visuals

The Journal page favors lightweight custom visuals over heavy chart chrome:

- horizontal progress bars
- mini cards
- tiny heatmap-like grids
- dot markers
- segmented bars
- ring / streak indicators

Rules:

- chart labels are small and secondary
- bars and tracks use dark backgrounds with colored fills
- animations should be soft and purposeful, especially width transitions
- avoid legends when the component can explain itself inline

## Typography hierarchy

Use this hierarchy by default:

- page title: strong heading, around `1.5rem`
- section title: `Text size="sm" fw={600}`
- card title / item title: `0.8rem` to `1rem`, semibold
- metadata: `0.7rem` to `0.75rem`, dimmed
- tiny labels: around `0.62rem` to `0.7rem`, often uppercase

Rules:

- rely on weight and color before increasing font size
- keep dashboards compact
- avoid marketing-scale typography on internal product pages

## Motion and interaction

Animation should be mild and functional:

- border-color transitions
- subtle background shifts on hover
- gentle width transitions for bars
- no bouncy or flashy motion

Hover behavior:

- cards and rows can deepen surface contrast
- borders can brighten slightly
- avoid large lifts, glows, or theatrical movement

## Copy style

Text should feel observational and grounded:

- "Hours per genre"
- "Weekly activity"
- "Recent sessions"
- "How gaming makes you feel"

Rules:

- keep headings literal
- keep supporting copy short and useful
- prefer concise insights over playful filler

## Reusable implementation rules

When building new UI in this style:

1. Start with `Paper` sections and dark layered surfaces.
2. Use Burnished Ember (`#d4674d`) as the default primary color.
3. Keep text mostly in `xs`, `sm`, and modest heading sizes.
4. Use responsive grids early; do not design only for wide desktop.
5. Prefer inline data visuals over large chart libraries unless the view truly needs one.
6. Use `font-variant-numeric: tabular-nums` for values, timers, counts, and ratings.
7. Let metadata be dimmed and quiet.
8. Keep controls dense and aligned rather than airy and oversized.

## Do / avoid

Do:

- build compact, legible, framed dashboards
- use small color accents for meaning
- keep hierarchy clear through weight, spacing, and muted metadata
- preserve stable component dimensions
- favor calm polish over spectacle

Avoid:

- huge hero typography
- floating marketing cards
- bright saturated red or neon accents by default
- oversized empty spacing
- decorative gradients as the main visual idea
- mixed component radii that feel arbitrary
- generic white-card SaaS styling

## Fast reference

If a new screen should feel like the Journal page, it should usually have:

- a restrained dark surface
- `Paper` sections with borders
- ember primary actions
- compact tab or filter controls
- small semibold section titles
- dimmed metadata everywhere it helps scanning
- one or two accent colors beyond ember, not ten
- lightweight data visuals instead of heavy chart scaffolding

## How to use this file

Use `STYLE.MD` as a design brief before implementing new frontend UI. When there is a conflict between this file and an already-established local page pattern, prefer the local page pattern. When there is no strong local pattern, default to this guide.
