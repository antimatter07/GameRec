---
name: GameRec
description: A cinematic, composed product UI for personal game discovery, backlog planning, and taste-aware recommendations.
colors:
  ember-0: "#fff1ec"
  ember-1: "#ffe1d6"
  ember-2: "#ffc4b2"
  ember-3: "#f99a7e"
  ember-4: "#e97d61"
  ember-5: "#d4674d"
  ember-6: "#b9543e"
  ember-7: "#944331"
  ember-8: "#733629"
  ember-9: "#552922"
  sea-glass: "#2fb8a6"
  archive-blue: "#5b8def"
  marquee-gold: "#e0b957"
  surface-hover-cinema: "#171b27"
  overlay-ink: "#0a0c12c7"
  divider-subtle: "#ffffff0a"
  danger-muted: "#8f4b5e"
  danger-muted-hover: "#7a3f50"
  danger-muted-active: "#6c3746"
typography:
  display:
    fontFamily: "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1.5rem"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "normal"
  headline:
    fontFamily: "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "normal"
  title:
    fontFamily: "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.86rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "normal"
  body:
    fontFamily: "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.875rem"
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: "normal"
  label:
    fontFamily: "Plus Jakarta Sans, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
    fontSize: "0.7rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.5px"
  mono:
    fontFamily: "Space Mono, JetBrains Mono, monospace"
    fontSize: "0.75rem"
    fontWeight: 500
    lineHeight: 1.4
rounded:
  xs: "0px"
  sm: "6px"
  md: "10px"
  lg: "14px"
  xl: "20px"
spacing:
  xs: "10px"
  sm: "12px"
  md: "16px"
  lg: "20px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.ember-5}"
    textColor: "{colors.ember-0}"
    rounded: "{rounded.sm}"
    height: "42px"
    padding: "0 16px"
  button-danger:
    backgroundColor: "{colors.danger-muted}"
    textColor: "{colors.ember-0}"
    rounded: "{rounded.sm}"
    height: "42px"
    padding: "0 16px"
  card-game:
    backgroundColor: "{colors.surface-hover-cinema}"
    textColor: "{colors.ember-0}"
    rounded: "{rounded.md}"
    padding: "0"
  input-compact:
    backgroundColor: "{colors.surface-hover-cinema}"
    textColor: "{colors.ember-0}"
    rounded: "{rounded.sm}"
    height: "42px"
    padding: "0 12px"
---

# Design System: GameRec

## 1. Overview

**Creative North Star: "The Private Screening Library"**

GameRec should feel like a refined personal media library for games: cinematic enough to make cover art and screenshots desirable, thoughtful enough to explain why a recommendation fits, and composed enough to help users decide what to play next without turning the app into inventory work.

The product uses a restrained dark interface because the likely scene is a player browsing their backlog or planning a queue in the evening, often in the same relaxed context where they play. The surface should stay calm and task-oriented, with game artwork carrying the emotion and burnished ember acting as a warm editorial system accent.

It explicitly rejects the generic SaaS analytics dashboard, the Steam clone, the neon-heavy gamer launcher, the overdesigned AI product, and the spreadsheet-style backlog tracker.

**Key Characteristics:**

- Dark, layered, compact product surfaces.
- Media-first browsing with strong cover art and screenshots.
- Burnished ember as the primary action and selection color.
- Small, useful metadata with tabular numeric treatment.
- Lightweight taste and progress visuals, not chart-heavy dashboards.

## 2. Colors

The palette is a restrained dark product system anchored by a warm ember ramp, with sea-glass teal, archive blue, marquee gold, and muted semantic colors reserved for compact status and data marks.

### Primary

- **Burnished Ember** (#d4674d): The primary action, active state, premium AI cue, and key recommendation highlight. It is warm, cinematic, and human, without drifting into neon gamer styling or purple AI-product convention.
- **Deep Ember Focus** (#b9543e): Focus outlines and selected borders, especially on cards and inputs.
- **Soft Ember Wash** (#fff1ec to #ffc4b2): Light-tint support for icon wells and subtle active backgrounds when a warm active surface is needed.

### Secondary

- **Sea-Glass Teal** (#2fb8a6): Completion, positive progress, and finished play states.
- **Archive Blue** (#5b8def): Neutral metrics, play status, and secondary insight.
- **Marquee Gold** (#e0b957): Ratings, streaks, calendar moments, and achievement-like emphasis.

### Tertiary

- **Mood Spectrum**: Use pink, orange, green, red, gray, and gold only for journal emotions, chart differentiation, and status semantics. These colors should annotate, not dominate.
- **Muted Danger Rose** (#8f4b5e): Destructive game-card actions. Keep it softer than pure red.

### Neutral

- **Mantine Dark Stack**: Use `dark-7` for default panels, `dark-6` for nested control surfaces, `dark-5` for tracks and subtle fills, and `dark-4` or `dark-3` for borders.
- **Cinema Hover Surface** (#171b27): Hover background for cards, rows, and metric panels.
- **Overlay Ink** (#0a0c12c7): Artwork overlay badges, cover controls, and compact media chips.
- **Subtle Divider** (#ffffff0a): Hairline separators inside dense cards.

### Named Rules

**The Artwork Carries Emotion Rule.** Let game artwork create drama. Interface color should clarify state, not compete with covers.

**The Ember Rarity Rule.** Ember is the product voice. Use it for primary actions, active selections, focus, and recommendation intelligence, not decoration.

## 3. Typography

**Display Font:** Plus Jakarta Sans with system fallbacks  
**Body Font:** Plus Jakarta Sans with system fallbacks  
**Label/Mono Font:** Space Mono or JetBrains Mono for numeric and technical support

**Character:** The type system is compact, modern, and controlled. It should feel closer to a premium media catalog than a marketing site or game launcher.

### Hierarchy

- **Display** (700, 1.5rem, 1.2): Page titles and major authenticated view headings only.
- **Headline** (600, 1rem, 1.35): Section headings, panel titles, and compact feature headers.
- **Title** (600, 0.8rem to 1rem, 1.35): Game-card titles, row titles, feed item names, and queue items.
- **Body** (400, 0.875rem, 1.5): Descriptions, recommendation explanations, journal snippets, and profile copy. Cap prose at 65 to 75 characters when it is not a table or compact metadata row.
- **Label** (600, 0.62rem to 0.75rem, 0.4px to 0.5px, often uppercase): Metric labels, compact metadata, reason labels, and status captions.
- **Numeric** (tabular numbers): Ratings, counts, playtime, percentages, dates, queue positions, and progress values.

### Named Rules

**The No Marketing Type Rule.** Internal product pages should not use hero-scale text. Keep headings modest and let media, hierarchy, and layout create presence.

## 4. Elevation

GameRec is flat by default and uses tonal layering instead of shadows. Depth comes from dark surface steps, thin borders, cover-image framing, overlay badges, and slight hover background shifts. Shadows are rare and should appear only when image or icon rendering needs separation.

### Shape Vocabulary

GameRec uses sharper structural edges and rounder interactive media elements. This keeps the app composed and editorial rather than soft everywhere.

- **Sharp structural panels:** `xs` radius (0px) for page panels, metric cards, dashboards, filters, auth cards, tables, and admin surfaces. Sharpness signals stability, hierarchy, and precision.
- **Soft controls:** `sm` radius (6px) for buttons, inputs, badges, tabs, icon wells, and compact controls. These still feel clickable without making the entire interface pill-like.
- **Flexible media cards:** `md` radius (10px) for game cards, queue cards, draggable cards, note cards, cover previews, and surfaces that can be opened, moved, saved, or rearranged. Roundness here signals flexibility and friendliness.
- **Large expressive surfaces:** `lg` and `xl` are reserved for landing-page illustration frames or rare media-led moments, not routine product panels.

### Shadow Vocabulary

- **Icon Image Separation** (`filter: drop-shadow(0 1px 2px rgba(0, 0, 0, 0.25))`): Used on small rating icons over dense card content.
- **No Panel Shadow** (`box-shadow: none`): The default for buttons, cards, filters, and action buttons.

### Named Rules

**The Tonal Layering Rule.** Prefer `dark-7`, `dark-6`, `dark-5`, border color, and hover background changes over drop shadows.

## 5. Components

### Buttons

Buttons are compact, stable, and direct.

- **Shape:** Mantine `sm` radius (8px).
- **Primary:** Burnished ember background, short label, optional Tabler icon at 14px to 16px, stable 42px height where grouped with inputs or game-card actions.
- **Hover / Focus:** Darker or lighter ember state; focus must remain visible with an ember outline or equivalent Mantine focus treatment.
- **Secondary / Ghost:** Use `subtle`, `light`, or bordered treatments for supporting actions. Do not create large decorative button treatments.
- **Danger:** Use muted rose (#8f4b5e) with hover (#7a3f50) and active (#6c3746), not bright red unless the action is highly destructive.

### Chips

Chips and badges annotate status without becoming the interface.

- **Style:** Small, radius `sm`, dimmed labels, and restrained color fills through Mantine light variants.
- **State:** Selected states may use ember or semantic color, but should also include text, icon, checkmark, or border treatment so meaning does not rely on hue alone.
- **Artwork Overlays:** Use overlay ink (#0a0c12c7), small white or gray text, and optional blur only for readable cover badges.

### Cards / Containers

Cards are for games, repeated items, metric blocks, and panels, not every page section.

- **Corner Style:** `xs` radius (0px) for structural panels and metric blocks; `md` radius (10px) for game cards, queue cards, draggable items, and note cards; `sm` (6px) for internal chip wells and cover controls.
- **Background:** `dark-7` for primary panels, `dark-6` for compact cards and controls, `dark-5` for tracks and internal wells, #171b27 on hover.
- **Shadow Strategy:** No box shadow at rest. Use borders and tonal layering.
- **Border:** One-pixel dark borders, usually Mantine `dark-4`, `dark-3` on hover.
- **Internal Padding:** `md` for panels, 10px to 14px for compact cards, `lg` for full page padding.
- **Media Cards:** Keep cover areas stable. Catalog cards use tall media regions, queue cards use compact 112px covers, and body text should truncate cleanly.

### Inputs / Fields

Inputs are dense and aligned with adjacent actions.

- **Style:** 42px minimum height, `dark-6` background, `dark-4` border, gray-0 text, gray-5 placeholder.
- **Focus:** Border shifts to ember-6. Do not add glowing focus effects.
- **Error / Disabled:** Use Mantine semantic variants, but keep supporting text concise and readable on dark surfaces.

### Navigation

Navigation is familiar and task-first.

- **App Shell:** 60px header, 220px sidebar, Mantine `sm` breakpoint.
- **Style:** Left navigation with Tabler icons around 18px, compact labels, and Mantine active state.
- **Header:** Brand on the left, user menu on the right. Keep profile actions predictable.
- **Mobile:** Collapse navigation structurally rather than shrinking text or hiding labels without an affordance.

### Game Cards

Game cards are the signature component.

- **Purpose:** Make each game feel like a piece of media, not a row in a database.
- **Media:** Use real artwork whenever available, object-fit cover, stable image height, and subtle bottom border.
- **Text:** Title first, then year/platform/genre metadata, then rating or action.
- **Interaction:** Hover deepens the surface and border. Focus-visible uses a 2px ember outline with 2px offset.

### Lightweight Data Visuals

Use compact progress bars, segmented bars, dot markers, mini heatmaps, and small rings.

- **Tracks:** Dark-5 or dark-8 backgrounds with `xs` radius.
- **Fills:** Semantic color based on meaning, animated with width transitions around 500ms using an ease-out curve.
- **Labels:** Inline and secondary. Avoid legends when labels can live near the mark.

## 6. Do's and Don'ts

### Do:

- **Do** foreground cover art, screenshots, and media metadata so games feel desirable and memorable.
- **Do** use ember-5 (#d4674d) for primary actions, selected states, focus, and AI recommendation intelligence.
- **Do** keep page titles near 1.5rem and section titles around small semibold text.
- **Do** use `Paper` with `withBorder`, `radius="xs"`, and dark layered backgrounds for dashboard and structural panels.
- **Do** use compact responsive grids: four-up metrics on desktop, two-up on tablet, one-up on narrow mobile.
- **Do** use tabular numbers for ratings, counts, percentages, queue order, and playtime.
- **Do** support WCAG AA, keyboard focus, reduced motion, and non-color cues for status.

### Don't:

- **Don't** make GameRec feel like a generic SaaS analytics dashboard.
- **Don't** make GameRec look like a Steam clone.
- **Don't** use neon-heavy gamer launcher styling, glowing effects, or loud saturated accents by default.
- **Don't** use violet or purple as the default accent for new UI. GameRec's default accent is Burnished Ember.
- **Don't** make AI features feel gimmicky with sparkle overload, gradient text, or theatrical motion.
- **Don't** turn backlog management into a spreadsheet-style tracker.
- **Don't** overwhelm users with charts, tables, badges, or metric cards.
- **Don't** use decorative gradients as the main visual idea.
- **Don't** use side-stripe borders, gradient text, glassmorphism as a default, nested cards, or modals as the first solution.
- **Don't** use `#000` or `#fff` for new design tokens; tint neutrals and use existing Mantine dark surfaces.
