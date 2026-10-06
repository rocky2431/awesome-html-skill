# Awesome HTML

[中文](README.zh-CN.md)

An agent skill that builds HTML pages as **one self-contained file**: it opens offline in any browser, needs no account or hosted service, and can be sent to anyone as is.

Use it for:

- **Explainers and reports:** how a system works, why a bug happened, which option to pick.
- **Progress trackers:** a read-only board generated from a text file in your repository.
- **Clickable prototypes and wireframes:** several screens, real flows, sample data labeled.
- **Slide decks:** a fixed 16:9 stage, keyboard navigation, print to PDF.
- **Charts:** hand-written SVG, or the bundled Chart.js when readers need tooltips.

## Why

Hosted artifact pages live in an account, so you cannot hand the file to a partner. Template renderers produce files but every page looks the same. This skill keeps the design discipline, writes the page freely, and then proves the file stands alone.

## How a page is made

1. **Contract.** Every page is one `.html` file with its CSS, JS, images, fonts, and diagrams inside. No CDN, no web fonts, no remote images.
2. **Design.** The agent writes the page's palette and type as `:root` tokens first, checks them against the subject, and builds from a starting template (`assets/base.html`, `prototype.html`, or `deck.html`). Trackers are generated from a Markdown file by `scripts/track.py`.
3. **Inline.** `scripts/inline.py` folds local scripts, stylesheets, fonts, and images into the page. `vendor/chart.umd.min.js` resolves to the bundled Chart.js 4.5.1.
4. **Check.** `scripts/check.py` scans the markup for anything loaded from outside the file, then renders the page in your local Chrome with DNS blocked at 400 and 1280 px wide, in light and dark. It reports outside requests, JS errors, sideways scrolling, cut-off slides, and content cut off by `overflow: hidden`, and saves each render as 1200px-tall screenshot tiles for the agent to read.

```text
$ python3 scripts/check.py html/report.html
html/report.html (212 KB)
✓ static: nothing loads from outside the file
· rendered offline with Chrome/… (DNS blocked); screenshots in /tmp/awesome-html-shots-…
  page-400-light: 2310px tall → page-400-light-1.png … page-400-light-2.png (2 tiles)
  …
✓ browser: no outside requests, no JS errors, no sideways scroll
· open every tile listed above before calling the page done
```

All three scripts use only the Python standard library. The browser pass needs macOS or Linux and Chrome, Chromium, or Edge (set `AWESOME_HTML_CHROME` to point at another binary); without them, only the static pass runs and the script says the page was not rendered.

## Install

Set `AWESOME_HTML_REPO` to the absolute path of this checkout.

### Claude Code

```bash
claude plugin validate "$AWESOME_HTML_REPO/plugins/awesome-html" --json
claude plugin marketplace add "$AWESOME_HTML_REPO"
claude plugin install awesome-html@rocky-awesome-html
```

### Codex

```bash
codex plugin marketplace add "$AWESOME_HTML_REPO"
codex plugin add awesome-html@rocky-awesome-html
```

### Kimi Code and zCode

Kimi Code: run `/plugins install` with the absolute path to `<repo>/plugins/awesome-html`, then `/reload`. zCode: add the checkout through its plugin marketplace, then install Awesome HTML.

Reload plugins or start a new session afterwards. Installation syntax can vary between host versions; follow your host's help when it differs.

## Use

Ask for the page: "make a page explaining how our auth flow works", "turn docs/wip/launch.md into a progress board", "prototype the onboarding flow, three screens". Pages go to `html/<slug>.html` in the project unless you name a path. See [`examples/`](examples/) for pages built with the skill.

## Layout

```text
plugins/awesome-html/skills/awesome-html/
├── SKILL.md            contract, routing, workflow
├── references/         design, explainers, trackers, prototypes, slides, charts, checklist
├── assets/             base.html, prototype.html, track.html, deck.html, vendor/chart.umd.min.js
└── scripts/            inline.py, check.py, track.py
```

## Development

```bash
python3 tests/check_package.py
python3 -m unittest discover tests
```

Browser tests are skipped when no Chrome is found.

## License

MIT, see [LICENSE](LICENSE). Bundled Chart.js is MIT. Credits for the guidance this skill builds on are in [NOTICE](NOTICE); research notes are in [docs/research.md](docs/research.md).
