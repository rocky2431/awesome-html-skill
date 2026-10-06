# Slide decks

Decks as one HTML file: open it, press the arrow keys, print to PDF when someone needs a PDF.

## Start from the template

Copy `assets/deck.html`. Every slide is a `<section class="slide" id="sN">` on a fixed 1920 × 1080 stage that scales to the window, so a slide looks the same on a laptop and a projector. Navigation: arrow keys, space, Page Up/Down, Home/End, click (left third goes back), swipe. Each slide has a URL fragment (`deck.html#4`). Printing produces one slide per page.

Sizes in a deck are stage pixels: a 40px body on the stage is about 26px on a 1280px-wide window. A deck is made for a 16:9 screen; on a phone it shows as a small thumbnail, which is expected.

## Writing slides

- One idea per slide. The title states the takeaway as a sentence ("Checkout drop-off halves after the address fix"), not a topic ("Checkout").
- About 30 words (about 60 Chinese characters) of body text at most. Move detail to speaker notes (`<aside class="notes">`, hidden on screen and in print) or to a separate explainer page.
- Title 64 to 112px, body 32 to 44px on the stage; captions and source lines 24 to 28px (`.small`). If text does not fit at those sizes, the slide has too much on it.
- Chinese titles: the template sets `word-break: keep-all` on headings so lines break only at spaces and `<wbr>`; put a `<wbr>` between phrases of a long title.
- Keep the same margins, grid, and title position on every slide; change layout only when the content changes kind (title, statement, comparison, chart, quote).
- Charts and diagrams follow `references/charts.md` and `references/explain.md`, with the viewBox in stage pixels and labels at 28 to 40px.
- Plan the deck as a list of slide titles first. Read the titles alone; they should tell the story.

## Check

```bash
python3 <skill-dir>/scripts/check.py deck.html --widths 1280 --fragment 2 --fragment 3 ...
```

The plain render shows slide 1, so pass `--fragment 2` up to the last slide. Use `--widths 1280`: the phone width only shows the scaled-down thumbnail. check.py names the element and the distance when content runs into a slide's margin (!) or past its edge (✗). Look at every tile anyway, since overlapping elements are not caught.

## When the template is not enough

Presenter view, fragments that build a slide step by step, and an overview grid are not in the template. If the user needs them, say so and ask before adding a library: reveal.js 6.0.2 (MIT) is about 173 kB inlined with its CSS and would need to be vendored first.
