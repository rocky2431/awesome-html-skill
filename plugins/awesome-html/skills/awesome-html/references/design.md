# Design

Read before choosing tokens for any page. The bar is a page that looks made for its subject, not one more instance of a house style.

## Who decides the look

1. The user's explicit instructions, including when they ask for a look listed under "Defaults" below.
2. The project's existing design language: tokens, CSS, brand files, nearby pages. Search the repository before inventing.
3. The subject, its audience, and the page's job.
4. Your own judgment.

## Pick the effort level

Every page gets designed; the question is how far.

The level follows the page's job, not its audience.

- **Utilitarian:** the page explains, reports, tracks, or is a tool someone operates: explainers, reports, trackers, internal tools and their prototypes, wireframes. Clear hierarchy, quiet palette, no hero. Still give it one detail that belongs to its subject. Most pages are this, including explainers sent to partners.
- **Editorial:** the page has to persuade or make a first impression: a deck presented to people outside the team, a customer-facing product's key screens, a launch page. Take one deliberate risk: an unusual type pairing, a strong color field, a distinctive composition. An internal status deck is utilitarian.

When unsure, a calm, well-composed page beats an over-designed one.

## Write the plan first

Before writing markup, write the `:root` block. It is the design plan. The values that ship in this skill's templates are placeholders, not a house style: replace them (trackers are the exception, see `references/track.md`).

Pages in the same series (the same project and audience, for example an explainer and the deck that presents it) reuse the earlier page's tokens so they read as one set; then apply the neighboring-topic check to the composition only. Unrelated pages get their own plan.

- **Color:** 4 to 6 named values: paper, surface, ink, muted, rule, accent (optionally a second accent). Name them by role, not by hue.
- **Type:** the families for body, display, and mono, each with a full fallback stack.
- **Layout:** one comment line naming the layout concept and the alignment.

Then review the plan against the subject. Would a neighboring topic produce the same plan? If yes, change one axis (color, type, or composition) so it belongs to this subject, and note what you changed and why. Distinctive choices come from the subject's own world: its materials, instruments, documents, and vocabulary.

## Color

- One accent carries meaning: links, the current state, the series that matters. Everything else stays neutral.
- Tint neutrals slightly toward the accent's hue so the page feels like one palette.
- Contrast: body text at least 4.5:1 against its background; large text, icons, and chart marks at least 3:1. Check both themes.
- Design the dark theme; do not invert. Lower the accent's saturation, keep surfaces slightly lighter than the paper for depth, avoid pure black backgrounds and pure white text.
- Never let color be the only signal: pair it with a label, an icon, or position.

Dark mode follows the system through `@media (prefers-color-scheme: dark)`. Only if the page ships its own theme switch, guard the media block with `:root:not([data-theme="light"])`, repeat the dark values under `:root[data-theme="dark"]`, and wrap the `localStorage` read in try/catch.

## Type

- System font stacks are the default: zero bytes, offline, native in every language. Keep the CJK fallbacks (`"PingFang SC"`, `"Hiragino Sans GB"`, `"Microsoft YaHei"`, `"Noto Sans CJK SC"`) in every stack.
- Embed a font only when the identity needs it: a woff2 subset with a license that allows embedding (OFL is fine), referenced as a local file and inlined by `scripts/inline.py`. Budget about 150 KB for all embedded fonts.
- Fixed scale: 4 or 5 steps with a consistent ratio. Body 16 to 18px.
- Line length 60 to 75 characters for Latin text, about 35 to 45 for Chinese. Line height 1.5 to 1.65 for Latin, 1.7 to 1.8 for Chinese.
- Headings in sentence case with `text-wrap: balance`. Numbers that line up use `font-variant-numeric: tabular-nums`.
- Chinese can break between any two characters, so a balanced heading may split a word ("不 / 渲染"). On Chinese headings set `word-break: keep-all` and put `<wbr>` between phrases, or wrap each phrase in `<span style="display:inline-block">`.
- One or two families. If two, make them clearly different.

## Layout

- Side gutter at least 16px. The body never scrolls sideways at 400px; only tables, code, and wide diagrams scroll, inside their own `overflow-x: auto` box.
- Give flex and grid children that hold text `min-width: 0`. Space with `gap`, not stacked margins.
- Structure is information. Number things only when they are a sequence. Use a card only for an object the reader acts on. Use borders and dividers to show grouping, not as decoration.
- Complete at rest: no content hidden until a scroll observer reveals it, no full-viewport hero that pushes the content off the first screen.
- Spend boldness in one place. Before shipping, remove one decoration that does not serve the subject.

## Defaults that read as generated

All of these are fine when the user asks for them. Otherwise, avoid spending design freedom on them:

- Warm cream background with a high-contrast serif and a terracotta or clay accent.
- Near-black background with one acid-green or vermilion accent.
- Purple-to-blue gradient hero; gradient washes as decoration.
- Content chopped into identical rounded cards with the same soft shadow and one radius everywhere.
- A tracked uppercase label above every heading; meta strings joined with middle dots; labels built as "WORD — fragment"; an arrow appended to every link.
- A big number with a small label as the default way to show any figure.
- One word of a headline set in italic, bold, or a different color.
- Emoji as bullets or section markers; everything centered.
- A fade-and-rise entrance on every section; hover lift on every card.

## Motion

Motion explains a change or answers an action: opening, expanding, confirming, moving between screens. One orchestrated moment beats scattered effects. Anything that moves or fades animates `transform` and `opacity` only. Short color changes on hover and focus (about 150ms on `color`, `background-color`, `border-color`) are fine. List properties instead of `transition: all`, and honor `prefers-reduced-motion`.

## Words

- Use the reader's vocabulary, not the system's internals.
- Active voice. A button says what happens ("Save changes"), and the same action keeps the same name throughout the flow.
- Errors say what happened and how to fix it. Empty states say what to do next.
- Sentence case, plain verbs, no filler. Each piece of text does one job.
- In Chinese, prefer plain verbs over padded phrasing (写"优化"，不写"进行优化").
