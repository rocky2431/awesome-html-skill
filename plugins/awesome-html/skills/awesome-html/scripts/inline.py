#!/usr/bin/env python3
"""Inline a page's local resources so the page becomes one offline file.

Usage: inline.py PAGE.html [-o OUT.html]

Rewrites the page (in place unless -o is given):
  <script src="x.js"></script>          -> <script data-inlined="x.js">...</script>
  <link rel="stylesheet" href="x.css">  -> <style data-inlined="x.css">...</style>
  src/srcset/poster/href on img, source, video, audio, track, image -> data: URI
  url(...) and @import inside <style>, style="" and inlined CSS      -> inlined

Paths resolve against the page's folder first, then this skill's assets/
folder, so vendor/chart.umd.min.js works from any page. External URLs are
left alone for check.py to report. A missing local file is an error and
nothing is written. Running it again on its own output changes nothing.

Ceiling: tags are rewritten with regular expressions, which is enough for
hand-written pages. Markup with '>' inside attribute values or commented-out
tags may need manual inlining; switch to a real tokenizer if that turns up.
"""

import argparse
import base64
import mimetypes
import re
import sys
from pathlib import Path
from urllib.parse import unquote

from check import classify, srcset_candidates

ASSETS = Path(__file__).resolve().parent.parent / "assets"
MIME = {
    ".woff2": "font/woff2",
    ".woff": "font/woff",
    ".ttf": "font/ttf",
    ".otf": "font/otf",
    ".svg": "image/svg+xml",
    ".webp": "image/webp",
    ".avif": "image/avif",
    ".png": "image/png",
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".gif": "image/gif",
    ".ico": "image/x-icon",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mp3": "audio/mpeg",
    ".vtt": "text/vtt",
}
SCRIPT_TAG = re.compile(r"<script\b([^>]*?)\ssrc\s*=\s*([\"'])(.*?)\2([^>]*)>\s*</script\s*>", re.I | re.S)
SCRIPT_BLOCK = re.compile(r"(<script\b[^>]*>.*?</script\s*>)", re.I | re.S)
LINK_TAG = re.compile(r"<link\b[^>]*>", re.I)
MEDIA_TAG = re.compile(r"<(img|source|video|audio|track|image)\b[^>]*>", re.I)
STYLE_BLOCK = re.compile(r"(<style\b[^>]*>)(.*?)(</style\s*>)", re.I | re.S)
STYLE_ATTR = re.compile(r"(\sstyle\s*=\s*)([\"'])(.*?)\2", re.I | re.S)
ATTR = re.compile(r"([\w:-]+)\s*=\s*([\"'])(.*?)\2", re.S)
CSS_URL = re.compile(r"url\(\s*([\"']?)(.*?)\1\s*\)", re.I | re.S)
CSS_IMPORT = re.compile(r"@import\s+(?:url\(\s*)?([\"']?)([^\"')\s;]+)\1\s*\)?\s*([^;]*);", re.I)


class Missing(Exception):
    pass


def is_local(ref):
    return classify(ref) == "local"


class Inliner:
    def __init__(self, page):
        self.page_dir = page.parent
        self.done = []
        self.missing = []

    def resolve(self, ref, base):
        clean = unquote(re.split(r"[?#]", ref.strip(), maxsplit=1)[0])
        for root in (base, self.page_dir, ASSETS):
            candidate = (root / clean).resolve()
            if candidate.is_file():
                return candidate
        self.missing.append(ref)
        raise Missing(ref)

    def data_uri(self, ref, base):
        path = self.resolve(ref, base)
        mime = MIME.get(path.suffix.lower()) or mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.done.append((ref, path.stat().st_size))
        fragment = ref[ref.index("#"):] if "#" in ref else ""
        return f"data:{mime};base64,{base64.b64encode(path.read_bytes()).decode()}{fragment}"

    def css(self, text, base):
        def url(match):
            quote, ref = match.group(1), match.group(2)
            if not is_local(ref):
                return match.group(0)
            try:
                return f"url({quote}{self.data_uri(ref, base)}{quote})"
            except Missing:
                return match.group(0)

        def imported(match):
            ref, media = match.group(2), match.group(3).strip()
            if not is_local(ref):
                return match.group(0)
            try:
                path = self.resolve(ref, base)
            except Missing:
                return match.group(0)
            self.done.append((ref, path.stat().st_size))
            body = self.css(path.read_text(encoding="utf-8"), path.parent)
            return f"@media {media} {{\n{body}\n}}" if media else body

        return CSS_URL.sub(url, CSS_IMPORT.sub(imported, text))

    def script(self, match):
        before, ref, after = match.group(1), match.group(3), match.group(4)
        if not is_local(ref):
            return match.group(0)
        try:
            path = self.resolve(ref, self.page_dir)
        except Missing:
            return match.group(0)
        self.done.append((ref, path.stat().st_size))
        code = re.sub(r"</(script)", r"<\\/\1", path.read_text(encoding="utf-8"), flags=re.I)
        attrs = (before + after).strip()
        attrs = f" {attrs}" if attrs else ""
        return f'<script{attrs} data-inlined="{ref}">\n{code}\n</script>'

    def link(self, match):
        tag = match.group(0)
        attrs = {name.lower(): value for name, _, value in ATTR.findall(tag)}
        ref = attrs.get("href", "")
        if "stylesheet" not in attrs.get("rel", "").lower().split() or not is_local(ref):
            if "icon" in attrs.get("rel", "").lower().split() and is_local(ref):
                return self.media(match)
            return tag
        try:
            path = self.resolve(ref, self.page_dir)
        except Missing:
            return tag
        self.done.append((ref, path.stat().st_size))
        body = self.css(path.read_text(encoding="utf-8"), path.parent)
        body = re.sub(r"</(style)", r"<\\/\1", body, flags=re.I)
        media = f' media="{attrs["media"]}"' if attrs.get("media") else ""
        return f'<style{media} data-inlined="{ref}">\n{body}\n</style>'

    def media(self, match):
        def attr(found):
            name, quote, value = found.group(1), found.group(2), found.group(3)
            if name.lower() not in ("src", "href", "xlink:href", "poster", "srcset"):
                return found.group(0)
            try:
                if name.lower() == "srcset":
                    parts = []
                    for url, descriptor in srcset_candidates(value):
                        if is_local(url):
                            url = self.data_uri(url, self.page_dir)
                        parts.append(f"{url} {descriptor}".strip())
                    return f"{name}={quote}{', '.join(parts)}{quote}"
                if is_local(value):
                    return f"{name}={quote}{self.data_uri(value, self.page_dir)}{quote}"
            except Missing:
                pass
            return found.group(0)

        return ATTR.sub(attr, match.group(0))

    def markup(self, html):
        html = LINK_TAG.sub(self.link, html)
        html = MEDIA_TAG.sub(self.media, html)
        html = STYLE_BLOCK.sub(lambda m: m.group(1) + self.css(m.group(2), self.page_dir) + m.group(3), html)
        return STYLE_ATTR.sub(lambda m: m.group(1) + m.group(2) + self.css(m.group(3), self.page_dir) + m.group(2), html)

    def run(self, html):
        html = SCRIPT_TAG.sub(self.script, html)
        # Leave script bodies alone: library code can contain text that looks like markup.
        pieces = SCRIPT_BLOCK.split(html)
        return "".join(piece if index % 2 else self.markup(piece) for index, piece in enumerate(pieces))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Inline local resources into one HTML file.")
    parser.add_argument("page", type=Path)
    parser.add_argument("-o", "--output", type=Path, help="write here instead of overwriting PAGE")
    args = parser.parse_args(argv)
    page = args.page.resolve()
    if not page.is_file():
        print(f"✗ no such file: {page}")
        return 2
    inliner = Inliner(page)
    html = inliner.run(page.read_text(encoding="utf-8"))
    if inliner.missing:
        for ref in dict.fromkeys(inliner.missing):
            print(f"✗ cannot find {ref!r} next to the page or in the skill's assets/")
        print("nothing written")
        return 1
    out = (args.output or page).resolve()
    out.write_text(html, encoding="utf-8")
    counts = {}
    for ref, size in inliner.done:
        counts[ref] = (counts.get(ref, (0, size))[0] + 1, size)
    for ref, (count, size) in counts.items():
        times = f" ×{count}" if count > 1 else ""
        print(f"· inlined {ref}{times} ({size / 1000:.0f} kB)")
    if not inliner.done:
        print("· nothing local to inline")
    print(f"✓ {out} ({out.stat().st_size / 1000:.0f} kB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
