# Progress trackers

A tracker page shows where a project stands. It is a view, never the record.

## Source of truth

- Progress lives in a Markdown file in the repository, usually the project's WIP document (`docs/wip/<slug>.md`). The page is regenerated from it by `scripts/track.py`; never record progress only in the HTML.
- If the user tells you a status, update the source file first, then regenerate.
- If no source exists, propose `docs/wip/<slug>.md` in the layout below and confirm where it should live.

## Source layout

`track.py` reads only these parts; other sections (goals, notes, links) are ignored and stay in the source.

```markdown
# Project name (WIP)

Updated: 2026-10-06

## Decisions

| Date | Decision | Who |
|---|---|---|
| 2026-10-06 | What was decided, and why | owner |

## Progress

### Milestone name

- [done] Item. Evidence: commit abc1234, `pytest` 18 passed
- [doing] Item
- [blocked] Item. Evidence: waits for API keys from ops
- [todo] Item
- [dropped] Item. Evidence: cut, because ...

## Not done

- Deliberate omission or deferred work
```

- Chinese works the same: `## 已定决策`, `## 进度`, `## 还没做`, `更新：`, `证据：`, and the statuses `[完成] [进行中] [阻塞] [待办] [已放弃]`.
- `(WIP)` / `（WIP）` is dropped from the title. A parenthetical in a milestone heading stays part of its name.
- Text after `Evidence:` / `证据：` becomes the item's note. URLs in a note become links on the page; backticks and other Markdown marks are removed.
- `Who` is free text. Keep the source's wording, including distinctions like "agent (owner approved)".
- One item per line. An unknown status or an item outside a `###` milestone stops the script with the line number.

## Create or update

```bash
python3 <skill-dir>/scripts/track.py docs/wip/<slug>.md html/progress.html --summary "One sentence: where it stands and what is next."
python3 <skill-dir>/scripts/check.py html/progress.html
```

- The first run copies `assets/track.html` and picks `lang` from the content (`zh-CN` when it is mostly Chinese; `--lang` overrides). Later runs replace the data block and the `<title>` (and `lang` when `--lang` is given); everything else in the page survives.
- `--summary` is your judgment, written from the source: what is done, what is in progress or blocked, what comes next. Without it, the page keeps its previous summary; refresh it whenever the picture changes.
- `updated` comes from the source's `Updated:` line, else today's date.
- The script warns about `done` items without evidence and `blocked` items that do not say what blocks them. Do not invent evidence: report the gaps to the user, or fix them in the source if you know the facts.

## The template

Trackers are utilitarian and should look the same from one update to the next, so keep the template's layout and tokens; change the tokens only to match a project's existing palette. If a screenshot shows a problem in the template itself, fix it in the page and tell the user, so the skill's template can be fixed too.

Milestones show a status label only when the data sets one; the item count beside each milestone already shows how far along it is.

## Before sending to a partner

The whole data block travels with the file: item names, notes, decisions, and the repository-relative `source` path. Remove anything the partner should not see from the source (or from a partner copy of it the user approves), then regenerate.
