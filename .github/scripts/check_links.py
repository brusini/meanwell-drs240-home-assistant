#!/usr/bin/env python3
"""Check relative links, image paths, and heading anchors in the Markdown files.

Usage:
    python .github/scripts/check_links.py              offline: files and anchors only
    python .github/scripts/check_links.py --external   also request every http(s) link once
"""
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKIP_DIRS = {"_internal", "node_modules", ".git"}
LINK = re.compile(r"!?\[[^\]]*\]\(([^)\s]+)(?:\s+\"[^\"]*\")?\)")
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
FENCE = re.compile(r"^\s*(```|~~~)")


def slug(text: str) -> str:
    """Return the anchor that GitHub generates for a heading."""
    text = re.sub(r"`([^`]*)`", r"\1", text)                 # code spans keep their text
    text = re.sub(r"\[([^\]]*)\]\([^)]*\)", r"\1", text)     # links keep their text
    text = text.strip().lower()
    text = re.sub(r"[^\w\- ]", "", text)                     # drop punctuation, keep letters, digits, _, -, space
    return text.replace(" ", "-")


def anchors(path: Path) -> set[str]:
    found: dict[str, int] = {}
    out = set()
    in_code = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if FENCE.match(line):
            in_code = not in_code
            continue
        if in_code:
            continue
        m = HEADING.match(line)
        if m:
            s = slug(m.group(2))
            n = found.get(s, 0)
            found[s] = n + 1
            out.add(s if n == 0 else f"{s}-{n}")
    return out


def main() -> int:
    files = [p for p in ROOT.rglob("*.md") if not SKIP_DIRS & set(p.relative_to(ROOT).parts)]
    errors, external = [], set()
    for md in sorted(files):
        in_code = False
        for n, line in enumerate(md.read_text(encoding="utf-8").splitlines(), 1):
            if FENCE.match(line):
                in_code = not in_code
                continue
            if in_code:
                continue
            for target in LINK.findall(line):
                where = f"{md.relative_to(ROOT).as_posix()}:{n}"
                if target.startswith(("http://", "https://")):
                    external.add((target, where))
                    continue
                if target.startswith("mailto:"):
                    continue
                path_part, _, frag = target.partition("#")
                dest = md if not path_part else (md.parent / path_part).resolve()
                if not dest.exists():
                    errors.append(f"{where}: missing file {target}")
                    continue
                if frag and dest.suffix == ".md" and frag not in anchors(dest):
                    errors.append(f"{where}: missing anchor {target}")
    if "--external" in sys.argv:
        for url, where in sorted(external):
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "link-check"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    if r.status >= 400:
                        errors.append(f"{where}: HTTP {r.status} {url}")
            except Exception as e:  # noqa: BLE001
                errors.append(f"{where}: {type(e).__name__} {url}")
    mode = "requested" if "--external" in sys.argv else "not requested"
    print(f"checked {len(files)} files, {len(external)} external links ({mode})")
    for e in errors:
        print("ERROR", e)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
