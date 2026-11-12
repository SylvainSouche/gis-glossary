#!/usr/bin/env python3
"""
extract_qgis_headings.py - term equivalents from the QGIS user manual, in several
languages, aligned by section anchor.

Every section of the manual has the same anchor id in every language, so the
heading of a section can be paired across languages without any guessing. The
script walks the English manual by its "next page" links, fetches the same
pages in the other languages, and keeps the headings whose translation differs
from the English one (a heading that is the same in every language is not a term pair; an English term
kept in one language, such as "Layer" in German, is kept in the row as it is).

    python3 tools/extract_qgis_headings.py --langs fr,de,es,it [--limit 20]

Writes published/qgis-manual-headings/qgis_manual_headings.tsv. Each row records its source
address, the licence of the source (GNU Free Documentation License 1.3 or
later, per the manual's own licence page), the method and the retrieval date,
so rows can be filtered by licence before any publication. Only headings are
kept: short terms, never the running text of the manual.

Taken over from the SIGate project (catalog/glossary_qgis.py, commit cea1403).
"""

import argparse
import csv
import html
import re
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent
CACHE = ROOT_DIR / "cache" / "qgis_docs"
OUT = ROOT_DIR / "published" / "qgis-manual-headings" / "qgis_manual_headings.tsv"
ROOT = "https://docs.qgis.org/latest/{lang}/docs/user_manual/"
UA = "gis-glossary/0.1 (terminology extraction)"
LICENCE = "GFDL-1.3-or-later"

LINK = re.compile(r'href="([^"#]+\.html)')
NEXT = re.compile(r'<link rel="next"[^>]*href="([^"]+)"')
# a section may carry hidden marker elements (<span id=...></span>) before its title
SECTION = re.compile(
    r'<section id="([^"]+)">\s*(?:<span[^>]*></span>\s*)*<h[1-6]>(.*?)</h[1-6]>', re.S
)
NUMBER_PREFIX = re.compile(r"^\d+(\.\d+)*\.?\s+")


def fetch(url, lang, retries=3):
    path = urllib.parse.urlsplit(url).path.replace("/latest/", "", 1).lstrip("/")
    cached = CACHE / path
    if cached.exists():
        return cached.read_text(encoding="utf8", errors="replace")
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=40) as r:
                text = r.read().decode("utf8", errors="replace")
            cached.parent.mkdir(parents=True, exist_ok=True)
            cached.write_text(text, encoding="utf8")
            time.sleep(0.25)
            return text
        except Exception:
            time.sleep(2 * (attempt + 1))
    return ""


def clean(raw):
    text = html.unescape(re.sub(r"<[^>]+>", "", raw))
    text = text.replace("", "").replace("¶", "")
    return NUMBER_PREFIX.sub("", " ".join(text.split())).strip()


def page_list(limit):
    """English page addresses under the user manual: the 'next' chain gives
    the manual's order but skips branches, so every internal .html link is
    followed too (breadth first, each page once)."""
    root = ROOT.format(lang="en")
    queue, seen, pages = [root + "index.html"], set(), []
    while queue and len(pages) < limit:
        url = queue.pop(0).split("#")[0]
        if url in seen or not url.startswith(root):
            continue
        seen.add(url)
        text = fetch(url, "en")
        if not text:
            continue
        pages.append(url)
        for href in NEXT.findall(text) + LINK.findall(text):
            queue.append(urllib.parse.urljoin(url, html.unescape(href)))
    return pages


def headings(text):
    return {sid: clean(raw) for sid, raw in SECTION.findall(text)}


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--langs", default="fr,de,es,it")
    ap.add_argument("--limit", type=int, default=2000, help="maximum number of pages")
    ap.add_argument("--workers", type=int, default=3)
    args = ap.parse_args()
    langs = args.langs.split(",")

    pages = page_list(args.limit)
    print(f"{len(pages)} English pages in the user manual", flush=True)

    def work(task):
        lang, url = task
        return lang, url, headings(fetch(url.replace("/en/", f"/{lang}/", 1), lang))

    tasks = [(lang, url) for url in pages for lang in langs]
    found = {}
    with ThreadPoolExecutor(args.workers) as pool:
        for n, (lang, url, h) in enumerate(pool.map(work, tasks), 1):
            found[(lang, url)] = h
            if n % 200 == 0:
                print(f"  {n}/{len(tasks)} page fetches", flush=True)

    rows, seen = [], set()
    today = time.strftime("%Y-%m-%d")
    for url in pages:
        en = headings(fetch(url, "en"))
        for sid, en_text in en.items():
            translations = {lang: found[(lang, url)].get(sid, "") for lang in langs}
            if not any(t and t != en_text for t in translations.values()):
                continue
            key = (en_text, tuple(translations[l] for l in langs))
            if key in seen:
                continue
            seen.add(key)
            rows.append(
                [en_text]
                + [translations[l] for l in langs]
                + [
                    sid,
                    url,
                    "QGIS documentation",
                    LICENCE,
                    "manual heading, aligned by section id",
                    today,
                ]
            )
    OUT.parent.mkdir(exist_ok=True)
    with OUT.open("w", encoding="utf8", newline="") as f:
        w = csv.writer(f, delimiter="\t")
        w.writerow(
            ["en"]
            + langs
            + ["anchor", "page", "source", "source_licence", "method", "retrieved"]
        )
        w.writerows(rows)
    print(f"{len(rows)} term rows -> {OUT}")
    for i, lang in enumerate(langs, 1):
        print(f"  {lang}: {sum(1 for r in rows if r[i])} translated terms")


if __name__ == "__main__":
    sys.exit(main())
