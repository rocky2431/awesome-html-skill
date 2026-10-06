---
name: awesome-html
description: Build local, self-contained single-file HTML pages that open offline and can be sent to anyone as one file - explainers and visual answers, reports, project progress trackers, clickable prototypes and wireframes, slide decks, and chart pages. Use whenever the deliverable, or the clearest answer, is an HTML page, including requests like "make a page", "visualize this", "explain with a diagram", "track progress in HTML", "prototype/mockup/wireframe", "HTML slides", "做个页面", "画个图讲讲", "做个原型", "进度看板", "做个网页版 PPT". Not for features inside an existing web app's codebase, not for .pptx/.docx/.pdf files, and not when the user asks for plain text.
---

# Awesome HTML

One file that opens anywhere, needs no account and no network, and looks made for its subject.

`<skill-dir>` below means this skill's base directory: the folder that contains this SKILL.md, shown when the skill loads.

## Contract for every page

1. **One `.html` file, everything inside.** CSS in `<style>`, JS in `<script>`, images and fonts as `data:` URIs, diagrams as inline SVG. No CDN scripts, no web fonts, no remote images. Outbound `<a>` links are fine.
2. **Location.** The path the user names. Otherwise `html/<slug>.html` at the project root. Outside a project, or inside a configuration directory such as `~/.claude`, use `~/awesome-html/<slug>.html`. Do not commit generated pages unless asked.
3. **Title and language.** `<title>` is a short name: two to four words, about 4 to 10 Chinese characters, or a mix such as `awesome-html 工作原理`. `<html lang>` matches the content (`zh-CN` for Chinese).
4. **Theme.** Colors are tokens on `:root`; a designed dark theme under `prefers-color-scheme: dark`.
5. **Width.** Works at 400px wide with no sideways scrolling. Slide decks are the exception: they scale a 16:9 stage and are checked at 1280px.
6. **`file://` rules.** `fetch()` cannot read local files: embed data in `<script type="application/json">`. No ES module imports of separate files. Wrap `history.*` and `localStorage` in try/catch.
7. **Honest content.** Real content in the reader's vocabulary. Sample data is labeled as sample. Never invent metrics, quotes, or sources.

## Read what the page needs

| Page | Read | Start from |
|---|---|---|
| Any page, before choosing colors and type | `references/design.md` | — |
| Explainer, report, review, comparison | `references/explain.md` | `assets/base.html` |
| Project progress tracker | `references/track.md` | `scripts/track.py` (creates it from `assets/track.html`) |
| Prototype, mockup, wireframe | `references/prototype.md` | `assets/prototype.html` |
| Slide deck | `references/slides.md` | `assets/deck.html` |
| Charts, or numbers the reader compares | `references/charts.md` | — |
| Every page, before delivery | `references/checklist.md` | — |

A request can span types: read each reference that applies and give the page one coherent direction.

## Workflow

1. **Settle the brief:** audience and their job, page type, effort level (utilitarian or editorial), fidelity. Infer what you can from the request and the repository; ask only what changes the result. For prototypes, confirm the screen list first when the flow is not given.
2. **Find the existing design language** in the project (tokens, CSS, brand files) and follow it. Earlier pages count when the new page belongs to the same series (`references/design.md`). The placeholder tokens in this skill's templates are not a design language.
3. **Plan:** write the `:root` token block and a one-line layout comment first, then review it against the subject (`references/design.md`). Trackers skip this step and keep the template's look (`references/track.md`).
4. **Build:** copy the starting asset to the output path and replace its placeholders. Copy, never link to the asset.
5. **Inline:** if the page references local files (`vendor/chart.umd.min.js`, images, fonts), run `python3 <skill-dir>/scripts/inline.py <page>`. `vendor/` paths resolve to `<skill-dir>/assets/vendor/`.
6. **Check:** run `python3 <skill-dir>/scripts/check.py <page>`, adding `--fragment <state>` for each prototype screen and state or each slide. Fix every ✗; read every ! and confirm it in the screenshots. Open every tile it lists (pages are saved as 1200px-tall tiles, so they can be read at full size) and fix what you see: clipping, overlap, weak contrast in either theme, empty regions, broken states. While iterating, `--schemes light` or a single width cuts the number of tiles, and re-running into the same `--shots` folder marks tiles that did not change; the final run uses the defaults (decks: `--widths 1280`).
7. **Deliver:** the absolute path, one or two lines on what the page shows, the check result, and anything not verified. The file is the package: send it as is; zip only when there are several files.

## Updating a page

Small changes: edit the page in place and re-run the check. A rebuild starts again from the template and overwrites the page. Trackers: update the source file, then re-run `scripts/track.py` (`references/track.md`).

## Honesty

- If check.py cannot find Chrome, say the page was not rendered or looked at.
- Never describe a render you did not open. Report the check's ✓ and ✗ lines as printed.
