#!/usr/bin/env python3
"""Wrap the canonical page body into a deployable standalone HTML file.

``web/app.body.html`` is the single source of truth for the Little Wins page.
It is written in the shape a Claude Artifact expects - no ``<!doctype>``,
``<html>``, ``<head>`` or ``<body>`` tags, because the artifact host supplies
those. A static host such as Vercel does not, so this script adds the document
skeleton, the metadata and the small reset the artifact host would otherwise
inject, and writes ``public/index.html``.

Run it after any edit to the page:

    python tools/build_static.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "web" / "app.body.html"
TARGET = ROOT / "public" / "index.html"

TITLE = "Little Wins &mdash; Singapore child benefits, year by year"
DESCRIPTION = (
    "Work out every Singapore government child benefit your family is entitled to "
    "under the SG Child Support Package: a year-by-year payout timeline, totals by "
    "cash, education and healthcare, and your government-paid leave."
)
SOCIAL = (
    "Enter your children and see every benefit, payout year and leave entitlement "
    "under the SG Child Support Package."
)

HEAD = f"""<!doctype html>
<html lang="en-SG">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{TITLE}</title>
<meta name="description" content="{DESCRIPTION}">
<meta name="color-scheme" content="light dark">
<meta property="og:type" content="website">
<meta property="og:title" content="{TITLE}">
<meta property="og:description" content="{SOCIAL}">
<meta name="twitter:card" content="summary">
<link rel="icon" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 100 100%22><text y=%22.9em%22 font-size=%2290%22>&#128118;</text></svg>">
<style>
  /* The artifact host injects an equivalent reset; a static host does not. */
  html {{ -webkit-text-size-adjust: 100%; }}
  body {{ margin: 0; }}
  img {{ max-width: 100%; }}
  [hidden] {{ display: none !important; }}
</style>
"""

# Everything before this marker is head material (<link>, <style>); everything
# from it onwards is the rendered page.
BODY_MARKER = '<div class="wrap">'


def build() -> str:
    source = SOURCE.read_text(encoding="utf-8")

    # The <title> is supplied by the skeleton, so drop the artifact's own.
    source = re.sub(r"^<title>.*?</title>\n", "", source, count=1, flags=re.S)

    if BODY_MARKER not in source:
        raise SystemExit(f"{SOURCE}: expected to find {BODY_MARKER!r}")
    head_extra, body = source.split(BODY_MARKER, 1)

    return (
        HEAD
        + head_extra.strip()
        + "\n</head>\n<body>\n"
        + BODY_MARKER
        + body.rstrip()
        + "\n</body>\n</html>\n"
    )


def main() -> int:
    html = build()
    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(html, encoding="utf-8")

    # Cheap structural checks - a silently malformed page is worse than a crash.
    for fragment in ("<!doctype html>", "</head>", "<body>", "</body>", "</html>"):
        assert html.count(fragment) == 1, f"expected exactly one {fragment!r}"
    assert "<style>" in html.split("</head>")[0], "stylesheet did not land in <head>"

    print(f"wrote {TARGET.relative_to(ROOT)} ({len(html):,} bytes)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
