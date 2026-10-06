#!/usr/bin/env python3
"""Check that a single-file HTML page works offline, then render it for review.

Usage: check.py PAGE.html [--no-browser] [--shots DIR] [--fragment F ...]
                         [--widths 400,1280] [--schemes light,dark]

Static pass (stdlib html.parser): every resource the page loads must already
be inside the file (inline <script>/<style>, a data: URI, or an in-page
#fragment). External URLs and local paths that were never inlined are errors.
Outbound <a href> links are counted but allowed: the page still renders
without them.

Browser pass (Chrome over --remote-debugging-pipe, DNS blocked): loads the
page at 400 and 1280 CSS px wide, in light and dark, and records requests
that leave the file, JS exceptions, console errors, sideways scrolling, and
cut-off slides (errors), content cut off by overflow:hidden (warnings), and
boxes that scroll on their own (notes). Each render is saved as 1200px-tall
PNG tiles so the whole page can be read at full size.

Exit status: 0 clean, 1 problems found, 2 usage or environment error.
"""

import argparse
import base64
import json
import os
import re
import select
import shutil
import subprocess
import sys
import tempfile
import time
from html.parser import HTMLParser
from pathlib import Path

try:
    import fcntl  # POSIX only; the static pass still runs without it
except ImportError:
    fcntl = None

RESOURCE_ATTRS = {
    "script": ("src",),
    "link": ("href",),
    "img": ("src", "srcset"),
    "source": ("src", "srcset"),
    "video": ("src", "poster"),
    "audio": ("src",),
    "track": ("src",),
    "iframe": ("src",),
    "embed": ("src",),
    "object": ("data",),
    "input": ("src",),
    "image": ("href", "xlink:href"),
    "use": ("href", "xlink:href"),
    "feimage": ("href", "xlink:href"),
}
CSS_URL = re.compile(r"url\(\s*(['\"]?)(.*?)\1\s*\)", re.I | re.S)
CSS_IMPORT = re.compile(r"@import\s+(?:url\(\s*)?['\"]?([^'\")\s;]+)", re.I)
WIDTHS = (400, 1280)
SCHEMES = ("light", "dark")
TILE_HEIGHT = 1200  # tall enough to read, short enough that image viewers do not shrink it
MAX_TILES = 15
LOCAL_SCHEMES = ("file", "data", "blob", "about", "chrome", "devtools")


def srcset_candidates(value):
    """Split a srcset into (url, descriptor) pairs. URLs may contain commas (data: URIs)."""
    pairs, i, n = [], 0, len(value)
    while i < n:
        while i < n and (value[i].isspace() or value[i] == ","):
            i += 1
        start = i
        while i < n and not value[i].isspace():
            i += 1
        url, descriptor = value[start:i], ""
        if url.endswith(","):
            url = url.rstrip(",")
        else:
            end = value.find(",", i)
            end = n if end < 0 else end
            descriptor, i = value[i:end].strip(), end
        if url:
            pairs.append((url, descriptor))
    return pairs


def classify(ref):
    """Return 'inline', 'external', 'local', or 'other' for a resource reference."""
    ref = ref.strip()
    lower = ref.lower()
    if not ref or ref.startswith("#") or lower.startswith(("data:", "blob:", "about:")):
        return "inline"
    if lower.startswith(("http:", "https:", "//")):
        return "external"
    if re.match(r"[a-z][a-z0-9+.-]*:", lower):
        return "other"
    return "local"


class StaticScan(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.errors = []
        self.warnings = []
        self.links = 0
        self.seen = set()
        self.in_style = False

    def _ref(self, ref, where):
        kind = classify(ref)
        line = self.getpos()[0]
        if kind == "external":
            self.errors.append(f"L{line} {where}: loads {ref!r} from the network")
        elif kind == "local":
            self.errors.append(f"L{line} {where}: {ref!r} is a separate file; inline it (scripts/inline.py)")

    def _css(self, css, where):
        for _, ref in CSS_URL.findall(css):
            self._ref(ref, f"{where} url()")
        for ref in CSS_IMPORT.findall(css):
            self._ref(ref, f"{where} @import")

    def handle_decl(self, decl):
        if decl.lower().startswith("doctype"):
            self.seen.add("doctype")

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "style":
            self.in_style = True
        if tag == "title":
            self.seen.add("title")
        if tag == "meta":
            if attrs.get("name", "").lower() == "viewport":
                self.seen.add("viewport")
            if "charset" in attrs or attrs.get("http-equiv", "").lower() == "content-type":
                self.seen.add("charset")
        if tag == "a" and attrs.get("href"):
            kind = classify(attrs["href"])
            if kind == "external":
                self.links += 1
            elif kind == "local":
                self.warnings.append(
                    f"L{self.getpos()[0]} <a href={attrs['href']!r}>: links to a file the recipient will not have"
                )
        for name in RESOURCE_ATTRS.get(tag, ()):
            value = attrs.get(name)
            if not value:
                continue
            refs = [url for url, _ in srcset_candidates(value)] if name == "srcset" else [value]
            for ref in refs:
                self._ref(ref, f"<{tag} {name}>")
        if attrs.get("style"):
            self._css(attrs["style"], f"<{tag} style>")

    handle_startendtag = handle_starttag

    def handle_endtag(self, tag):
        if tag == "style":
            self.in_style = False

    def handle_data(self, data):
        if self.in_style:
            self._css(data, "<style>")

    def finish(self):
        for key, message in (
            ("doctype", "missing <!doctype html>"),
            ("charset", 'missing <meta charset="utf-8">'),
            ("viewport", "missing <meta name=viewport>"),
            ("title", "missing <title>"),
        ):
            if key not in self.seen:
                self.warnings.append(message)


def static_scan(text):
    scan = StaticScan()
    scan.feed(text)
    scan.close()
    scan.finish()
    return scan


def find_chrome():
    configured = os.environ.get("AWESOME_HTML_CHROME")
    if configured:
        return configured
    for path in (
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    ):
        if os.path.exists(path):
            return path
    for name in ("google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "chrome", "microsoft-edge"):
        found = shutil.which(name)
        if found:
            return found
    return None


class Chrome:
    """Minimal DevTools Protocol client over Chrome's fd 3/4 pipe (POSIX only)."""

    def __init__(self, binary):
        self.profile = tempfile.mkdtemp(prefix="awesome-html-chrome-")
        to_chrome_r, self.to_chrome_w = os.pipe()
        self.from_chrome_r, from_chrome_w = os.pipe()

        def wire_pipe():
            # Park both ends above 4 first: dup2(3, 3) is a no-op that would
            # keep the close-on-exec flag os.pipe() sets.
            parked = [fcntl.fcntl(fd, fcntl.F_DUPFD, 10) for fd in (to_chrome_r, from_chrome_w)]
            for target, fd in zip((3, 4), parked):
                os.dup2(fd, target)
                os.set_inheritable(target, True)

        self.proc = subprocess.Popen(
            [
                binary,
                "--headless",
                "--remote-debugging-pipe",
                f"--user-data-dir={self.profile}",
                "--no-first-run",
                "--no-default-browser-check",
                "--disable-extensions",
                "--disable-background-networking",
                "--disable-component-update",
                "--disable-sync",
                "--hide-scrollbars",
                "--mute-audio",
                "--no-proxy-server",
                "--host-resolver-rules=MAP * ~NOTFOUND",
                "about:blank",
            ],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=False,
            preexec_fn=wire_pipe,
        )
        os.close(to_chrome_r)
        os.close(from_chrome_w)
        self.buffer = b""
        self.inbox = []
        self.events = []
        self.last_id = 0

    def _pump(self, timeout):
        ready, _, _ = select.select([self.from_chrome_r], [], [], max(timeout, 0))
        if not ready:
            return
        chunk = os.read(self.from_chrome_r, 1 << 20)
        if not chunk:
            raise RuntimeError("Chrome closed the DevTools pipe")
        self.buffer += chunk
        while b"\0" in self.buffer:
            raw, self.buffer = self.buffer.split(b"\0", 1)
            message = json.loads(raw)
            self.inbox.append(message)
            if "method" in message:
                self.events.append(message)

    def wait(self, match, timeout=20):
        deadline = time.monotonic() + timeout
        while True:
            for index, message in enumerate(self.inbox):
                if match(message):
                    del self.inbox[index]
                    if "error" in message:
                        raise RuntimeError(message["error"].get("message", str(message["error"])))
                    return message
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("Chrome did not answer in time")
            self._pump(remaining)

    def send(self, method, params=None, session=None, timeout=20):
        self.last_id += 1
        message_id = self.last_id
        message = {"id": message_id, "method": method, "params": params or {}}
        if session:
            message["sessionId"] = session
        data = json.dumps(message).encode() + b"\0"
        while data:
            data = data[os.write(self.to_chrome_w, data):]
        return self.wait(lambda m: m.get("id") == message_id, timeout).get("result", {})

    def close(self):
        try:
            self.send("Browser.close", timeout=5)
        except Exception:
            pass
        try:
            self.proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        for fd in (self.to_chrome_w, self.from_chrome_r):
            try:
                os.close(fd)
            except OSError:
                pass
        shutil.rmtree(self.profile, ignore_errors=True)


LAYOUT_PROBE = """(() => {
  const root = document.documentElement, width = root.clientWidth;
  const name = (el) => el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') +
    (el.classList.length ? '.' + [...el.classList].join('.') : '');
  const culprits = [], scrollers = [], boxes = [];
  for (const el of document.body ? document.body.querySelectorAll('*') : []) {
    const style = getComputedStyle(el), box = el.getBoundingClientRect();
    if (box.width === 0 && box.height === 0) continue;
    if (culprits.length < 5 && box.right > width + 1) {
      let parent = el.parentElement, contained = false;
      while (parent && parent !== document.body) {
        if (['auto', 'scroll', 'hidden', 'clip'].includes(getComputedStyle(parent).overflowX)) { contained = true; break; }
        parent = parent.parentElement;
      }
      if (!contained) culprits.push(name(el));
    }
    if (el.clientWidth <= 1 || el.clientHeight <= 1 || el.classList.contains('slide')) continue;
    const wider = el.scrollWidth > el.clientWidth + 1, taller = el.scrollHeight > el.clientHeight + 1;
    if (scrollers.length < 5 && ['auto', 'scroll'].includes(style.overflowX) && wider) scrollers.push(name(el));
    const hides = (v) => v === 'hidden' || v === 'clip';
    if (boxes.length < 5 && style.textOverflow !== 'ellipsis' &&
        ((hides(style.overflowX) && wider) || (hides(style.overflowY) && taller))) boxes.push(name(el));
  }
  const slides = [];
  for (const slide of document.querySelectorAll('.slide')) {
    if (getComputedStyle(slide).display === 'none') continue;
    const edge = slide.getBoundingClientRect(), scale = edge.height / slide.offsetHeight || 1;
    const pad = getComputedStyle(slide);
    let worst = null;
    for (const el of slide.querySelectorAll('*')) {
      const box = el.getBoundingClientRect();
      if (box.width === 0 && box.height === 0) continue;
      const cut = Math.max((box.bottom - edge.bottom) / scale, (box.right - edge.right) / scale);
      const margin = Math.max((box.bottom - edge.bottom) / scale + parseFloat(pad.paddingBottom),
                              (box.right - edge.right) / scale + parseFloat(pad.paddingRight));
      if (margin > 1 && (!worst || margin > worst.margin)) worst = {element: name(el), cut: Math.round(cut), margin: Math.round(margin)};
    }
    if (worst) slides.push({id: slide.id || 'slide', ...worst});
  }
  return JSON.stringify({scroll: root.scrollWidth, width, height: Math.ceil(root.scrollHeight),
                         culprits, scrollers, boxes, slides});
})()"""
SETTLE = "document.fonts.ready.then(() => new Promise(r => requestAnimationFrame(() => setTimeout(r, 300))))"


def describe_event(event):
    method, params = event["method"], event.get("params", {})
    if method == "Network.requestWillBeSent":
        url = params.get("request", {}).get("url", "")
        if url.split(":", 1)[0].lower() not in LOCAL_SCHEMES:
            return f"requested {url}"
    elif method == "Runtime.exceptionThrown":
        details = params.get("exceptionDetails", {})
        text = details.get("exception", {}).get("description") or details.get("text", "")
        return f"JS exception: {text.splitlines()[0] if text else 'unknown'}"
    elif method == "Runtime.consoleAPICalled" and params.get("type") == "error":
        args = " ".join(str(a.get("value", a.get("description", ""))) for a in params.get("args", []))
        return f"console.error: {args}"
    elif method == "Log.entryAdded" and params.get("entry", {}).get("level") == "error":
        entry = params["entry"]
        if entry.get("url", "").split(":", 1)[0].lower() not in LOCAL_SCHEMES:
            return None  # already reported as an outside request
        return f"browser error: {entry.get('text', '')} {entry.get('url', '')}".strip()
    return None


def safe_name(text):
    return re.sub(r"[^\w.-]+", "_", text).strip("_") or "page"


def browser_pass(page, shots, fragments, widths, schemes, binary):
    """Render every fragment x width x scheme; return findings keyed by message, each with its render labels."""
    found = {"problems": {}, "warnings": {}, "notes": {}}
    renders = []

    def note(kind, message, label):
        labels = found[kind].setdefault(message, [])
        if label not in labels:
            labels.append(label)

    chrome = Chrome(binary)
    try:
        version = chrome.send("Browser.getVersion").get("product", "Chrome")
        target = chrome.send("Target.createTarget", {"url": "about:blank"})["targetId"]
        session = chrome.send("Target.attachToTarget", {"targetId": target, "flatten": True})["sessionId"]
        for domain in ("Page", "Runtime", "Network", "Log"):
            chrome.send(f"{domain}.enable", session=session)
        for fragment in [None, *fragments]:
            url = page.as_uri() + (f"#{fragment}" if fragment else "")
            for width in widths:
                for scheme in schemes:
                    label = f"{fragment or 'page'}-{width}-{scheme}"
                    chrome.send("Emulation.setDeviceMetricsOverride",
                                {"width": width, "height": 900, "deviceScaleFactor": 1, "mobile": width < 600},
                                session=session)
                    chrome.send("Emulation.setEmulatedMedia",
                                {"features": [{"name": "prefers-color-scheme", "value": scheme}]}, session=session)
                    chrome.send("Page.navigate", {"url": "about:blank"}, session=session)
                    chrome.inbox.clear()
                    mark = len(chrome.events)
                    result = chrome.send("Page.navigate", {"url": url}, session=session)
                    if result.get("errorText"):
                        raise RuntimeError(f"Chrome could not open the page: {result['errorText']}")
                    chrome.wait(lambda m: m.get("method") == "Page.loadEventFired" and m.get("sessionId") == session)
                    chrome.send("Runtime.evaluate", {"expression": SETTLE, "awaitPromise": True}, session=session)
                    probe = chrome.send("Runtime.evaluate", {"expression": LAYOUT_PROBE, "returnByValue": True},
                                        session=session)
                    layout = json.loads(probe["result"]["value"])
                    total = max(layout["height"], 1)
                    captured = min(total, TILE_HEIGHT * MAX_TILES)
                    stem = safe_name(f"{fragment or 'page'}-{width}-{scheme}")
                    tiles = []  # (file name, identical to the file already there from an earlier run)
                    for index, top in enumerate(range(0, captured, TILE_HEIGHT), 1):
                        clip = {"x": 0, "y": top, "width": width, "height": min(TILE_HEIGHT, captured - top), "scale": 1}
                        shot = chrome.send("Page.captureScreenshot",
                                           {"format": "png", "captureBeyondViewport": True, "clip": clip},
                                           session=session, timeout=60)
                        path = shots / (f"{stem}.png" if captured <= TILE_HEIGHT else f"{stem}-{index}.png")
                        data = base64.b64decode(shot["data"])
                        tiles.append((path.name, path.exists() and path.read_bytes() == data))
                        path.write_bytes(data)
                    current = {name for name, _ in tiles}
                    for old in shots.glob(f"{stem}*.png"):
                        if old.name not in current and re.fullmatch(rf"{re.escape(stem)}(-\d+)?\.png", old.name):
                            old.unlink()  # left over from a longer render of the same page
                    renders.append((label, total, tiles))
                    if captured < total:
                        note("warnings", f"only the top {captured}px of {total}px were captured; the page is too "
                                         f"long to review or to read on a phone: shorten it or split it into pages",
                             label)
                    if layout["scroll"] > layout["width"] + 1:
                        culprits = ", ".join(layout["culprits"]) or "unknown element"
                        zoom = "; until fixed, phone-width tiles may look zoomed out" if width < 600 else ""
                        note("problems", f"page scrolls sideways ({layout['scroll']}px > {layout['width']}px); "
                                         f"widest: {culprits}{zoom}", label)
                    for slide in layout["slides"]:
                        if slide["cut"] > 1:
                            note("problems", f"slide {slide['id']}: {slide['element']} is cut off "
                                             f"{slide['cut']}px past the slide edge", label)
                        else:
                            note("warnings", f"slide {slide['id']}: {slide['element']} runs "
                                             f"{slide['margin']}px into the slide's margin", label)
                    if layout["boxes"]:
                        note("warnings", f"content is cut off inside: {', '.join(layout['boxes'])} "
                                         f"(overflow hidden); confirm in the screenshot that nothing needed is lost",
                             label)
                    if layout["scrollers"]:
                        note("notes", f"scrolls inside its own box: {', '.join(layout['scrollers'])} "
                                      f"(scrollbars are hidden in screenshots)", label)
                    for event in chrome.events[mark:]:
                        if event.get("sessionId") == session:
                            text = describe_event(event)
                            if text:
                                note("problems", text, label)
    finally:
        chrome.close()
    return version, renders, found


def main(argv=None):
    parser = argparse.ArgumentParser(description="Check a single-file HTML page for offline delivery.")
    parser.add_argument("page", type=Path)
    parser.add_argument("--no-browser", action="store_true", help="run only the static pass")
    parser.add_argument("--shots", type=Path, help="folder for screenshots (default: a new temp folder)")
    parser.add_argument("--fragment", action="append", default=[], help="also render PAGE#FRAGMENT (repeatable)")
    parser.add_argument("--widths", type=lambda v: [int(x) for x in v.split(",")], default=list(WIDTHS),
                        help="comma-separated CSS widths (default 400,1280)")
    parser.add_argument("--schemes", type=lambda v: v.split(","), default=list(SCHEMES),
                        help="comma-separated color schemes (default light,dark)")
    args = parser.parse_args(argv)

    if any(width < 200 for width in args.widths) or not set(args.schemes) <= set(SCHEMES):
        print("✗ --widths takes CSS pixels of at least 200; --schemes takes light and/or dark")
        return 2
    page = args.page.resolve()
    if not page.is_file():
        print(f"✗ no such file: {page}")
        return 2
    scan = static_scan(page.read_text(encoding="utf-8"))
    print(f"{page} ({page.stat().st_size / 1000:.0f} kB)")
    for message in scan.errors:
        print(f"✗ {message}")
    for message in scan.warnings:
        print(f"! {message}")
    if scan.links:
        print(f"· {scan.links} outbound link(s); they need a network only when clicked")
    if not scan.errors:
        print("✓ static: nothing loads from outside the file")
    failed = bool(scan.errors)

    if args.no_browser:
        print("· browser pass skipped (--no-browser): the page has not been rendered or looked at")
        return 1 if failed else 0
    if fcntl is None:
        print("! browser pass skipped: the DevTools pipe needs macOS or Linux; the page has not been rendered")
        return 1 if failed else 0
    binary = find_chrome()
    if not binary:
        print("! browser pass skipped: no Chrome found (set AWESOME_HTML_CHROME); the page has not been rendered")
        return 1 if failed else 0
    shots = args.shots.resolve() if args.shots else Path(tempfile.mkdtemp(prefix="awesome-html-shots-"))
    shots.mkdir(parents=True, exist_ok=True)
    try:
        version, renders, found = browser_pass(page, shots, args.fragment, args.widths, args.schemes, binary)
    except (RuntimeError, TimeoutError, OSError) as error:
        print(f"✗ browser pass failed: {error}")
        return 2
    print(f"· rendered offline with {version} (DNS blocked); screenshots in {shots}")
    seen_before = 0
    for label, total, tiles in renders:
        names = [name for name, _ in tiles]
        same = [name for name, unchanged in tiles if unchanged]
        seen_before += len(same)
        shown = names[0] if len(names) == 1 else f"{names[0]} … {names[-1]} ({len(names)} tiles)"
        if same and len(same) == len(names):
            shown += ", unchanged since the last run"
        elif same:
            shown += f", changed: {', '.join(name for name in names if name not in same)}"
        print(f"  {label}: {total}px tall → {shown}")

    def where(labels):
        return "every render" if len(labels) == len(renders) else ", ".join(labels)

    for kind, mark in (("problems", "✗"), ("warnings", "!"), ("notes", "·")):
        for message, labels in found[kind].items():
            print(f"{mark} {message} [{where(labels)}]")
    if not found["problems"]:
        print("✓ browser: no outside requests, no JS errors, no sideways scroll")
    if seen_before:
        print(f"· {seen_before} tile(s) are byte-identical to the last run in this folder; open the changed ones")
    print("· open every tile you have not seen before calling the page done")
    return 1 if failed or found["problems"] else 0


if __name__ == "__main__":
    sys.exit(main())
