#!/usr/bin/env python3
"""Generate or refresh a progress tracker page from a Markdown source file.

Usage: track.py SOURCE.md PAGE.html [--summary TEXT] [--title TEXT] [--lang TAG]

The source file is the record; the page is a view. This script reads the
layout below, writes the data into the page's #track-data block, and creates
the page from assets/track.html when it does not exist yet.

    # Project name (WIP)                    <- title; "(WIP)" is dropped
    Updated: 2026-10-06                     <- or 更新：2026-10-06; else today
    ## Decisions | ## 已定决策               <- table: date | decision | who
    ## Progress | ## 进度
    ### Milestone name                      <- one per milestone
    - [done] Item. Evidence: commit abc123  <- statuses: done doing blocked todo dropped
    - [完成] 条目。证据：提交 abc123          <- 完成 进行中 阻塞 待办 已放弃
    ## Not done | ## 还没做                  <- bullet list

Other sections are ignored. The one-sentence summary is a judgment, so it comes
from --summary; without it the page keeps the summary it already has.
"""

import argparse
import datetime
import json
import re
import shutil
import sys
from pathlib import Path

ASSETS = Path(__file__).resolve().parent.parent / "assets"
STATUS = {
    "done": "done", "完成": "done", "已完成": "done",
    "doing": "doing", "in progress": "doing", "进行中": "doing",
    "blocked": "blocked", "阻塞": "blocked",
    "todo": "todo", "to do": "todo", "待办": "todo", "未开始": "todo",
    "dropped": "dropped", "已放弃": "dropped", "放弃": "dropped",
}
SECTIONS = {
    "decisions": ("decisions", "已定决策", "决策"),
    "progress": ("progress", "进度"),
    "notdone": ("not done", "还没做", "未完成"),
}
ITEM = re.compile(r"^\s*[-*]\s+\[([^\]]+)\]\s+(.+?)\s*$")
EVIDENCE = re.compile(r"[。.;；]?\s*((?:证据|Evidence)\s*[：:]\s*)", re.I)
DATA_BLOCK = re.compile(r'(<script type="application/json" id="track-data">)(.*?)(</script>)', re.S)
PLACEHOLDER_SUMMARY = "One sentence on where the project stands and what happens next."


def plain(text):
    """Drop Markdown inline marks; the page renders text, not Markdown."""
    text = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)", r"\1 \2", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"(\*\*|__)(.+?)\1", r"\2", text)
    return text.strip()


def section_of(heading):
    lowered = heading.lower()
    for key, names in SECTIONS.items():
        if any(lowered.startswith(name) for name in names):
            return key
    return None


def parse(source):
    data = {"title": "", "updated": "", "milestones": [], "decisions": [], "notDone": []}
    errors, section, milestone = [], None, None
    for number, line in enumerate(source.splitlines(), 1):
        if line.startswith("# ") and not data["title"]:
            data["title"] = re.sub(r"\s*[(（]WIP[)）]\s*$", "", plain(line[2:]), flags=re.I)
            continue
        found = re.search(r"(?:更新|Updated)\s*[：:]\s*(\d{4}-\d{2}-\d{2})", line, re.I)
        if found and not data["updated"] and section is None:
            data["updated"] = found.group(1)
        if line.startswith("## "):
            section, milestone = section_of(line[3:].strip()), None
            continue
        if section == "progress":
            if line.startswith("### "):
                milestone = {"name": plain(line[4:]), "items": []}
                data["milestones"].append(milestone)
                continue
            item = ITEM.match(line)
            if not item:
                continue
            status = STATUS.get(item.group(1).strip().lower())
            if not status:
                errors.append(f"L{number}: unknown status [{item.group(1)}]; use one of {sorted(set(STATUS.values()))}")
                continue
            if milestone is None:
                errors.append(f"L{number}: item before any ### milestone heading")
                continue
            parts = EVIDENCE.split(plain(item.group(2)), maxsplit=1)
            entry = {"name": parts[0], "status": status}
            if len(parts) == 3:
                entry["note"] = parts[1] + parts[2]
            milestone["items"].append(entry)
        elif section == "decisions" and line.strip().startswith("|"):
            cells = [plain(cell) for cell in line.strip().strip("|").split("|")]
            if all(re.fullmatch(r":?-{3,}:?", cell) for cell in cells if cell):
                continue
            if not re.match(r"\d{4}-\d{2}-\d{2}", cells[0]):
                continue  # header row
            row = {"date": cells[0], "decision": cells[1] if len(cells) > 1 else ""}
            if len(cells) > 2:
                row["who"] = cells[2]
            data["decisions"].append(row)
        elif section == "notdone":
            bullet = re.match(r"^\s*[-*]\s+(.+)$", line)
            if bullet:
                data["notDone"].append(plain(bullet.group(1)))
    if not data["milestones"]:
        errors.append("no milestones found: expected '## Progress' (or '## 进度') with '### Milestone' headings")
    return data, errors


def looks_chinese(data):
    """True when Chinese characters are at least a fifth of the displayed letters."""
    shown = " ".join(
        [data["title"], *data["notDone"]]
        + [m["name"] for m in data["milestones"]]
        + [f"{i['name']} {i.get('note', '')}" for m in data["milestones"] for i in m["items"]]
        + [row.get("decision", "") for row in data["decisions"]]
    )
    han = len(re.findall(r"[一-鿿]", shown))
    latin = len(re.findall(r"[A-Za-z]", shown))
    return han > 0 and han >= 0.2 * (han + latin)


def repo_relative(path):
    for parent in path.parents:
        if (parent / ".git").exists():
            return path.relative_to(parent).as_posix()
    return path.name


def main(argv=None):
    parser = argparse.ArgumentParser(description="Write a Markdown progress file into a tracker page.")
    parser.add_argument("source", type=Path)
    parser.add_argument("page", type=Path)
    parser.add_argument("--summary", help="one sentence: where the project stands and what happens next")
    parser.add_argument("--title", help="override the title taken from the source's first heading")
    parser.add_argument("--lang", help="page language tag; default zh-CN for Chinese sources, else en")
    args = parser.parse_args(argv)

    source = args.source.resolve()
    if not source.is_file():
        print(f"✗ no such file: {source}")
        return 2
    text = source.read_text(encoding="utf-8")
    data, errors = parse(text)
    for message in errors:
        print(f"✗ {message}")
    if errors:
        print("nothing written")
        return 1

    page = args.page.resolve()
    created = not page.exists()
    if created:
        page.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ASSETS / "track.html", page)
    html = page.read_text(encoding="utf-8")
    block = DATA_BLOCK.search(html)
    if not block:
        print(f"✗ {page} has no #track-data block; it was not made from assets/track.html")
        return 1
    previous = json.loads(block.group(2))
    summary = args.summary or previous.get("summary", "")
    if summary == PLACEHOLDER_SUMMARY:
        summary = ""

    title = args.title or data["title"] or previous.get("title", "")
    record = {
        "title": title,
        "summary": summary,
        "updated": data["updated"] or datetime.date.today().isoformat(),
        "source": repo_relative(source),
        "milestones": data["milestones"],
        "decisions": data["decisions"],
        "notDone": data["notDone"],
    }
    # "</" inside a JSON string would end the <script> element early; "<\/" is the same JSON string.
    payload = json.dumps(record, ensure_ascii=False, indent=2).replace("</", "<\\/")
    html = html[:block.start(2)] + "\n" + payload + "\n" + html[block.end(2):]
    html = re.sub(r"<title>.*?</title>", lambda _: f"<title>{escape(title)}</title>", html, count=1, flags=re.S)
    lang = args.lang or (None if not created else ("zh-CN" if looks_chinese(data) else "en"))
    if lang:
        html = re.sub(r'<html lang="[^"]*">', f'<html lang="{lang}">', html, count=1)
    page.write_text(html, encoding="utf-8")

    items = [item for milestone in data["milestones"] for item in milestone["items"]]
    live = [item for item in items if item["status"] != "dropped"]
    done = sum(item["status"] == "done" for item in live)
    print(f"{'✓ created' if created else '✓ updated'} {page}")
    print(f"· {len(data['milestones'])} milestones, {len(items)} items, {done}/{len(live)} done, "
          f"{len(data['decisions'])} decisions, {len(data['notDone'])} not-done lines")
    for item in items:
        if item["status"] == "done" and not item.get("note"):
            print(f"! done without evidence: {item['name']}")
        if item["status"] == "blocked" and not item.get("note"):
            print(f"! blocked without saying what blocks it: {item['name']}")
    if not summary:
        print("! no summary yet: pass --summary with one sentence on where it stands and what is next")
    print("· next: run check.py on the page")
    return 0


def escape(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    sys.exit(main())
