"""Behavior tests for scripts/check.py, scripts/inline.py and scripts/track.py.

Run: python3 -m unittest discover tests
Browser tests need Chrome (or AWESOME_HTML_CHROME) and are skipped without it.
"""

import base64
import contextlib
import io
import json
import re
import sys
import tempfile
import unittest
from pathlib import Path

SKILL = Path(__file__).resolve().parents[1] / "plugins" / "awesome-html" / "skills" / "awesome-html"
sys.path.insert(0, str(SKILL / "scripts"))

import check  # noqa: E402
import inline  # noqa: E402
import track  # noqa: E402

PNG = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
HEAD = '<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1"><title>T</title>'


def run(main, *args):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = main([str(a) for a in args])
    return code, out.getvalue()


class SrcsetTest(unittest.TestCase):
    def test_data_uris_keep_their_commas(self):
        value = f"data:image/png;base64,{PNG} 1x, b.png 2x, c.png"
        self.assertEqual(
            check.srcset_candidates(value),
            [(f"data:image/png;base64,{PNG}", "1x"), ("b.png", "2x"), ("c.png", "")],
        )


class StaticScanTest(unittest.TestCase):
    def scan(self, body, head=HEAD):
        return check.static_scan(head + "</head><body>" + body + "</body></html>")

    def test_clean_page(self):
        scan = self.scan(f'<img alt="" src="data:image/png;base64,{PNG}"><a href="https://example.com">x</a><svg><use href="#i"/></svg>')
        self.assertEqual(scan.errors, [])
        self.assertEqual(scan.warnings, [])
        self.assertEqual(scan.links, 1)

    def test_external_and_local_resources_are_errors(self):
        scan = self.scan(
            '<script src="https://cdn.example/x.js"></script>'
            '<img src="pic.png"><div style="background:url(//x.io/a.png)"></div>',
            head=HEAD + '<link rel="stylesheet" href="site.css"><style>@import "https://f.io/a.css";</style>',
        )
        joined = "\n".join(scan.errors)
        for needle in ("cdn.example/x.js", "'pic.png' is a separate file", "//x.io/a.png", "site.css", "f.io/a.css"):
            self.assertIn(needle, joined)
        self.assertEqual(len(scan.errors), 5)

    def test_missing_basics_are_warnings(self):
        scan = check.static_scan("<html><body>hi</body></html>")
        self.assertEqual(scan.errors, [])
        self.assertEqual(len(scan.warnings), 4)

    def test_local_page_link_is_a_warning(self):
        scan = self.scan('<a href="other.html">next</a>')
        self.assertEqual(scan.errors, [])
        self.assertIn("other.html", scan.warnings[0])

    def test_bundled_assets_are_clean(self):
        for name in ("base.html", "track.html", "deck.html", "prototype.html"):
            scan = check.static_scan((SKILL / "assets" / name).read_text(encoding="utf-8"))
            self.assertEqual((scan.errors, scan.warnings), ([], []), name)


class InlineTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / "img").mkdir()
        (self.dir / "img" / "dot.png").write_bytes(base64.b64decode(PNG))
        (self.dir / "font.woff2").write_bytes(b"wOF2")
        (self.dir / "site.css").write_text('@font-face{font-family:X;src:url("font.woff2")}\nbody{background:url(img/dot.png)}\n')
        (self.dir / "app.js").write_text('document.body.insertAdjacentHTML("beforeend", "<script></script>");\n')

    def tearDown(self):
        self.tmp.cleanup()

    def page(self, body, head=""):
        path = self.dir / "page.html"
        path.write_text(HEAD + head + "</head><body>" + body + "</body></html>")
        return path

    def test_inlines_everything_and_is_idempotent(self):
        page = self.page(
            '<img alt="" src="img/dot.png" srcset="img/dot.png 1x, img/dot.png 2x">'
            '<script src="vendor/chart.umd.min.js"></script><script src="app.js" defer></script>',
            head='<link rel="stylesheet" href="site.css">',
        )
        code, _ = run(inline.main, page)
        self.assertEqual(code, 0)
        html = page.read_text()
        scan = check.static_scan(html)
        self.assertEqual(scan.errors, [])
        self.assertIn('data-inlined="vendor/chart.umd.min.js"', html)
        self.assertIn("Chart.js v4.5.1", html)
        self.assertIn("data:font/woff2;base64,", html)
        self.assertIn("<\\/script>", html)
        self.assertIn('<script defer data-inlined="app.js">', html)
        code, out = run(inline.main, page)
        self.assertEqual((code, page.read_text()), (0, html))
        self.assertIn("nothing local to inline", out)

    def test_missing_file_writes_nothing(self):
        page = self.page('<script src="nope.js"></script>')
        before = page.read_text()
        code, out = run(inline.main, page)
        self.assertEqual(code, 1)
        self.assertIn("nope.js", out)
        self.assertEqual(page.read_text(), before)

    def test_external_urls_are_left_for_check(self):
        page = self.page('<img alt="" src="https://example.com/a.png">')
        before = page.read_text()
        code, _ = run(inline.main, page)
        self.assertEqual((code, page.read_text()), (0, before))


SOURCE = """# Launch plan (WIP)

Updated: 2026-10-01

## Goal

Ignored section.

## Decisions

| Date | Decision | Who |
|---|---|---|
| 2026-09-30 | Ship `v1` first | owner |

## Progress

### Build

- [done] Parser. Evidence: commit abc123
- [进行中] 渲染器
- [blocked] Deploy. Evidence: waits for </script> review

### Later

- [dropped] Plugin API

## Not done

- No **Windows** support
"""


class TrackTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)
        (self.dir / ".git").mkdir()
        (self.dir / "docs").mkdir()
        self.source = self.dir / "docs" / "plan.md"
        self.source.write_text(SOURCE)
        self.page = self.dir / "html" / "progress.html"

    def tearDown(self):
        self.tmp.cleanup()

    def data(self):
        html = self.page.read_text()
        raw = re.search(r'id="track-data">(.*?)</script>', html, re.S).group(1)
        return json.loads(raw), html

    def test_parse_maps_the_layout(self):
        data, errors = track.parse(SOURCE)
        self.assertEqual(errors, [])
        self.assertEqual(data["title"], "Launch plan")
        self.assertEqual(data["updated"], "2026-10-01")
        self.assertEqual([m["name"] for m in data["milestones"]], ["Build", "Later"])
        self.assertEqual(data["milestones"][0]["items"][0], {"name": "Parser", "status": "done", "note": "Evidence: commit abc123"})
        self.assertEqual(data["milestones"][0]["items"][1], {"name": "渲染器", "status": "doing"})
        self.assertEqual(data["decisions"], [{"date": "2026-09-30", "decision": "Ship v1 first", "who": "owner"}])
        self.assertEqual(data["notDone"], ["No Windows support"])

    def test_bad_lines_are_reported_with_line_numbers(self):
        _, errors = track.parse("## Progress\n- [done] orphan\n### M\n- [someday] x\n")
        self.assertEqual(len(errors), 2)
        self.assertIn("L2: item before any ### milestone", errors[0])
        self.assertIn("L4: unknown status [someday]", errors[1])

    def test_creates_then_updates_without_losing_the_summary(self):
        code, out = run(track.main, self.source, self.page, "--summary", "Parser done; deploy waits on review.")
        self.assertEqual(code, 0, out)
        self.assertIn("✓ created", out)
        data, html = self.data()
        self.assertEqual(data["source"], "docs/plan.md")
        self.assertEqual(data["summary"], "Parser done; deploy waits on review.")
        self.assertIn("<title>Launch plan</title>", html)
        self.assertIn('<html lang="en">', html)
        self.assertNotIn("waits for </script>", html)
        self.assertEqual(data["milestones"][0]["items"][2]["note"], "Evidence: waits for </script> review")
        self.assertEqual(check.static_scan(html).errors, [])

        self.source.write_text(SOURCE.replace("[进行中] 渲染器", "[完成] 渲染器。证据：测试通过"))
        code, out = run(track.main, self.source, self.page)
        self.assertEqual(code, 0, out)
        data, _ = self.data()
        self.assertEqual(data["summary"], "Parser done; deploy waits on review.")
        self.assertEqual(data["milestones"][0]["items"][1], {"name": "渲染器", "status": "done", "note": "证据：测试通过"})

    def test_missing_summary_and_evidence_are_flagged(self):
        self.source.write_text(SOURCE.replace("Parser. Evidence: commit abc123", "Parser"))
        code, out = run(track.main, self.source, self.page)
        self.assertEqual(code, 0)
        self.assertIn("! done without evidence: Parser", out)
        self.assertIn("! no summary yet", out)

    def test_chinese_source_gets_a_chinese_page(self):
        self.source.write_text("# 发布计划\n\n## 进度\n\n### 构建\n\n- [待办] 解析器\n")
        run(track.main, self.source, self.page)
        _, html = self.data()
        self.assertIn('<html lang="zh-CN">', html)


@unittest.skipUnless(check.fcntl and check.find_chrome(), "needs Chrome on macOS or Linux")
class BrowserTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, body, *extra, head=""):
        page = self.dir / "page.html"
        page.write_text(HEAD + head + "</head><body>" + body + "</body></html>")
        return run(check.main, page, "--shots", self.dir / "shots", *extra)

    def test_offline_page_passes_and_writes_four_shots(self):
        code, out = self.check("<h1>Hello</h1><div style='overflow-x:auto'><div style='width:2000px'>wide but contained</div></div>")
        self.assertEqual(code, 0, out)
        self.assertEqual(len(list((self.dir / "shots").glob("*.png"))), 4)

    def test_script_requests_and_errors_are_reported(self):
        code, out = self.check("<script>fetch('https://example.com/data.json').catch(() => {}); throw new Error('boom');</script>")
        self.assertEqual(code, 1)
        self.assertIn("requested https://example.com/data.json [every render]", out)
        self.assertIn("JS exception: Error: boom", out)

    def test_sideways_scroll_is_reported_with_the_culprit(self):
        code, out = self.check('<div class="too-wide" style="width:900px">x</div>')
        self.assertEqual(code, 1)
        self.assertIn("page scrolls sideways", out)
        self.assertIn("div.too-wide", out)
        self.assertIn("[page-400-light, page-400-dark]", out)

    def test_long_pages_are_tiled_and_the_cap_is_reported(self):
        code, out = self.check('<div style="height:2500px">tall</div>', "--widths", "400", "--schemes", "light")
        self.assertEqual(code, 0, out)
        names = sorted(p.name for p in (self.dir / "shots").glob("*.png"))
        self.assertEqual(names, ["page-400-light-1.png", "page-400-light-2.png", "page-400-light-3.png"])
        self.assertIn("(3 tiles)", out)
        code, out = self.check('<div style="height:500px">short now</div>', "--widths", "400", "--schemes", "light")
        names = sorted(p.name for p in (self.dir / "shots").glob("*.png"))
        self.assertEqual(names, ["page-400-light.png"], "tiles left over from the longer render are removed")
        code, out = self.check('<div style="height:30000px">very tall</div>', "--widths", "400", "--schemes", "light")
        self.assertEqual(code, 0, out)
        self.assertIn(f"! only the top {check.TILE_HEIGHT * check.MAX_TILES}px", out)

    def test_fragment_names_are_safe_and_states_render(self):
        body = ("<p id='msg'>list</p><script>const [id, q = ''] = location.hash.slice(1).split('?');"
                "document.getElementById('msg').textContent = id + ' ' + new URLSearchParams(q).get('state');</script>")
        code, out = self.check(body, "--fragment", "orders/detail?state=empty", "--widths", "1280", "--schemes", "dark")
        self.assertEqual(code, 0, out)
        self.assertTrue((self.dir / "shots" / "orders_detail_state_empty-1280-dark.png").exists(), out)
        self.assertIn("orders/detail?state=empty-1280-dark", out)

    def test_clipped_boxes_warn_and_inner_scrollers_are_noted(self):
        code, out = self.check(
            '<div class="card" style="height:40px;overflow:hidden"><p>a</p><p>b</p><p>c</p><p>d</p></div>'
            '<div class="scroll-x" style="overflow-x:auto"><div style="width:2000px">wide</div></div>'
            '<span style="position:absolute;width:1px;height:1px;overflow:hidden">screen reader only text</span>',
            "--schemes", "light")
        self.assertEqual(code, 0, out)
        self.assertIn("! content is cut off inside: div.card", out)
        self.assertIn("· scrolls inside its own box: div.scroll-x", out)
        self.assertNotIn("span", out)

    def test_cut_off_slide_and_fragments(self):
        deck = (SKILL / "assets" / "deck.html").read_text(encoding="utf-8")
        deck = deck.replace("<p class=\"small\">Presenter, date</p>", "<p>" + "Too much text. " * 400 + "</p>")
        page = self.dir / "deck.html"
        page.write_text(deck)
        code, out = run(check.main, page, "--shots", self.dir / "shots", "--fragment", "2")
        self.assertEqual(code, 1)
        self.assertRegex(out, r"✗ slide s1: p is cut off \d+px past the slide edge")
        self.assertTrue((self.dir / "shots" / "2-1280-dark.png").exists())

    def test_slide_margin_is_a_warning_and_unchanged_tiles_are_counted(self):
        deck = (SKILL / "assets" / "deck.html").read_text(encoding="utf-8")
        page = self.dir / "deck.html"
        page.write_text(deck.replace('<p class="small">Presenter, date</p>', '<div style="height:740px;flex:none">tall</div>'))
        code, out = run(check.main, page, "--shots", self.dir / "shots", "--widths", "1280", "--schemes", "light")
        self.assertEqual(code, 0, out)
        self.assertRegex(out, r"! slide s1: div runs \d+px into the slide's margin")
        code, out = run(check.main, page, "--shots", self.dir / "shots", "--widths", "1280", "--schemes", "light")
        self.assertIn("unchanged since the last run", out)
        self.assertIn("1 tile(s) are byte-identical", out)


if __name__ == "__main__":
    unittest.main()
