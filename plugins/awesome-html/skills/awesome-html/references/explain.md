# Explainers and reports

Pages that make something understood: how a system works, why a bug happened, which option to pick, what a review found.

## Page or plain text

Make a page when the answer has a shape that prose hides: a flow or call chain with branches, three or more parts that act on each other, a comparison across three or more dimensions, ranked findings, a timeline. A short factual answer stays in the chat.

## Structure

- Lead with the answer. The title names the subject; the first sentence under it is the conclusion or recommendation.
- One section per sub-question, ordered the way a newcomer needs them. Each section opens with its point, then the evidence.
- One claim per figure. If a figure needs two captions, it is two figures.
- End with what to do next, or the open questions and what would settle them.
- Distinguish verified facts from inference. Name the source of every number: a file and its function or section, a command and its output, a URL. Line numbers go stale as code changes; add `:line` only when the page also names the commit it describes. Never invent figures; label illustrative data as illustrative.
- Code: short excerpts with their file and function, not whole files. Cite repository-relative paths. When you quote real command output, shorten absolute local paths (home directories, temp folders) to repository-relative ones and say that you did.
- Long identifiers: `overflow-wrap: anywhere` in prose and captions; inside table cells use `overflow-wrap: break-word` (`anywhere` lets the table squeeze columns and break words mid-way) and offer break points with `<wbr>` after `/` in long paths.

## Diagrams

A diagram earns its place when the reader would otherwise have to assemble the mechanism from several paragraphs.

- Draw the mechanism, not its name: the actual steps, messages, and decisions, not a box labeled "Processing".
- For a comparison, draw the difference: the edge or step one option adds or removes.
- Label every arrow with a verb ("sends", "rejects", "caches"). Add a legend only when an encoding repeats.
- Match complexity to the stakes: usually 4 to 12 nodes. Split anything larger.
- Mark the one path or node that matters with the accent; keep the rest neutral.

### Inline SVG mechanics

Write diagrams as inline SVG so they stay sharp, searchable, and themeable.

```html
<figure class="diagram">
  <div class="scroll-x">
    <svg viewBox="0 0 640 140" role="img" aria-label="The page goes to inline.py, then check.py renders it">
      <defs>
        <marker id="d1-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
          <path d="M0 0 L10 5 L0 10 z" class="arrowhead"/>
        </marker>
      </defs>
      <g class="node"><rect x="8" y="38" width="152" height="64" rx="6"/><text x="84" y="70">Page draft</text></g>
      <g class="node"><rect x="244" y="38" width="152" height="64" rx="6"/><text x="320" y="70">inline.py</text></g>
      <g class="node key"><rect x="480" y="38" width="152" height="64" rx="6"/><text x="556" y="70">check.py</text></g>
      <path class="edge" d="M160 70 H242" marker-end="url(#d1-arrow)"/>
      <text class="edge-label" x="202" y="56">embeds</text>
      <path class="edge" d="M396 70 H478" marker-end="url(#d1-arrow)"/>
      <text class="edge-label" x="438" y="56">verifies</text>
    </svg>
  </div>
  <figcaption>Every page passes through the inliner, then the offline check.</figcaption>
</figure>
```

```css
.diagram svg { display: block; width: 100%; min-width: 560px; max-width: 800px; height: auto; color: var(--ink); font: 14px var(--font-body); }
.diagram .node rect { fill: var(--surface); stroke: currentColor; stroke-width: 1.25; }
.diagram .node.key rect { stroke: var(--accent); stroke-width: 2.5; }
.diagram text { fill: currentColor; text-anchor: middle; dominant-baseline: middle; }
.diagram .edge { fill: none; stroke: currentColor; stroke-width: 1.25; }
.diagram .arrowhead { fill: currentColor; }
.diagram .edge-label { fill: var(--muted); font-size: 12px; paint-order: stroke; stroke: var(--paper); stroke-width: 4px; }
```

- Size with `viewBox`; let CSS set the width, capped with `max-width` so text does not balloon on wide screens. Text shrinks with the SVG, so keep labels at 12px or more at the narrowest size.
- Narrow screens, three options: draw the diagram tall (top to bottom) once and place it beside the text on wide screens and above it on phones; or keep a short row of up to about 4 nodes at a `min-width` inside `.scroll-x` (check.py notes it as scrolling inside its box); or draw a long chain twice, wide and tall, and swap them with CSS:

```css
.diagram .tall { display: none; }
@media (max-width: 680px) { .diagram .wide { display: none; } .diagram .tall { display: block; } }
```
- Color strokes and text with `currentColor` and CSS variables so both themes work. Presentation attributes cannot read `var()`; use classes.
- Arrowheads are `<marker>` paths. Marker content takes its color from the SVG, not from the line, so make a second marker if an accent edge needs an accent arrowhead.
- The `paint-order: stroke` halo keeps a label readable where it crosses a line.
- Put each diagram in `<figure>` with a `<figcaption>` that states the takeaway, and give the SVG `role="img"` and an `aria-label`.
- Prefix every `id` per figure (`d1-`, `d2-`); all inline SVGs share one id space.
- No `<script>`, `<foreignObject>`, or external `href` inside the SVG. Align coordinates to an 8px grid.

## Tables and comparisons

- One row per option, one column per dimension; the dimension that decides goes first.
- Three or more columns: add `class="stacked"` to the table and a `data-label` to every cell, `<th scope="row">` included (the base template turns rows into labeled blocks below 600px), instead of a table that scrolls sideways on phones.
- Show status with text plus a mark (`✓ supported`, `✗ missing`, `! partial`), never color alone.
- Put the recommendation above the table, not hidden in a cell.

## Delivery note

State in the reply what the page concludes in one or two lines, plus the path. The page carries the detail.
