# Before delivery

Run `scripts/check.py`, fix every ✗, then go through this list against the page and the screenshots.

## Offline and the file

- check.py reports nothing loaded from outside the file. Outbound links are fine.
- No link points at a local file the recipient will not have.
- The file name says what it is (`checkout-prototype.html`, not `page2.html`).
- Size is reasonable: under about 1 MB unless it embeds fonts, images, or Chart.js on purpose.
- Nothing private is embedded: personal data, credentials, data in a tracker's JSON the partner should not see. Repository-relative paths (`src/auth/login.ts:42`) are fine; absolute local paths (home directories, temp folders) are not.

## Looked at

- Every tile opened: 400px and 1280px (decks: 1280px), light and dark, every `--fragment` render, and every tile of a long page. On a re-run into the same `--shots` folder, check.py marks tiles that are byte-identical to the last run; those you have already seen.
- Every `!` line confirmed in the screenshots: content cut off by `overflow: hidden` that matters is a bug. Boxes check.py notes as "scrolls inside its own box" really are meant to scroll (scrollbars are hidden in the screenshots, so a cut-off edge there is expected).
- No clipped or overlapping text, no unreadable contrast in either theme, no empty areas where content failed to render.
- Long words, URLs, and identifiers wrap instead of widening the page.

## Semantics and keyboard

- `<button>` for actions, `<a href>` for navigation; nothing clickable is a bare `<div>`.
- Every control has a label; icon-only buttons have `aria-label`; images have `alt` (`alt=""` when decorative).
- Headings go in order; `lang` matches the content language.
- Every interactive element is reachable by keyboard and shows a focus ring; no `outline: none` without a replacement. Use `:focus-visible`, which already hides the ring after mouse clicks, including on headings focused by script.
- Status changes that appear without a page change (toasts, validation) use `aria-live="polite"`.

## Type and content

- An ellipsis is `…`; loading labels end with it ("Saving…").
- Number columns and changing numbers use `tabular-nums`; a number and its unit do not break across lines (`10&nbsp;MB`).
- Dates and numbers generated in script use `Intl.DateTimeFormat` and `Intl.NumberFormat`.
- No placeholder copy; sample data is labeled as sample; every figure has a source.

## Motion and interaction

- `prefers-reduced-motion` is honored; anything that moves or fades uses only `transform` and `opacity` (short hover color changes are fine); no `transition: all`.
- Zoom is not disabled (no `maximum-scale=1` or `user-scalable=no`).
- Destructive actions ask for confirmation or offer undo.
- Form fields use the right `type`, `inputmode`, and `autocomplete`, and never block paste.

## Dark theme

- `color-scheme` is set on `:root` for each theme so scrollbars and form controls follow.
- Native `<select>` and inputs have explicit background and text colors.

## The report to the user

- Absolute path to the file, and one or two lines on what it shows.
- What check.py printed (the ✓ and ✗ lines) and which screenshots you looked at.
- Anything not verified: no Chrome available, interactions not clicked through, data not confirmed.
- Never call a page checked or "looks good" for renders you did not open.
