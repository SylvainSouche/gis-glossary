#!/usr/bin/env python3
"""
build_parallel_corpus.py - aligned paragraphs from EU environmental directives, for a search test
independent of INSPIRE.

    python3 tools/build_parallel_corpus.py      (about 60 MB of downloads: run on GitHub Actions)

EU legal acts are parallel by construction: every language version has the same articles. The
Publications Office (Cellar API) serves them as XHTML in which each article carries the same id
(art_5) in every language. Paragraphs are aligned within an article by order, and only where the
English and target versions have the same number of paragraphs. Acts, chosen because they use
geographic and environmental vocabulary without being INSPIRE:
- Water Framework Directive 2000/60/EC (consolidated 2026-05-10)
- Floods Directive 2007/60/EC
- Marine Strategy Framework Directive 2008/56/EC (consolidated 2017-06-07)

Query: the start of the English paragraph, at most QUERY_WORDS words, close to a search phrase.
Document: the whole paragraph in the target language. Paragraphs under MIN_WORDS words, or mostly
numbers and references, are left out. Writes tests/acceptance/parallel_eu.tsv.xz:
id, language, query_en, document.
"""
import csv
import html
import lzma
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "tests" / "acceptance" / "parallel_eu.tsv.xz"
ACTS = {"WFD": "02000L0060-20260510", "FD": "32007L0060", "MSFD": "02008L0056-20170607"}
LANGUAGES = {"fr": "fra", "es": "spa", "de": "deu", "it": "ita", "da": "dan", "pl": "pol", "sl": "slv",
             "el": "ell", "ro": "ron", "bg": "bul", "sk": "slk", "sv": "swe"}
MIN_WORDS, QUERY_WORDS = 15, 15
HEADERS = {"Accept": "application/xhtml+xml", "User-Agent": "gis-glossary/0.1 (terminology research)"}


def fetch(celex, language):
    request = urllib.request.Request(f"http://publications.europa.eu/resource/celex/{celex}",
                                     headers={**HEADERS, "Accept-Language": language})
    return urllib.request.urlopen(request, timeout=300).read().decode("utf8")


def articles(page):
    parts = re.split(r'(<div[^>]*\bid="art_[0-9a-z]+"[^>]*>)', page)
    out = {}
    for i in range(1, len(parts), 2):
        article = re.search(r'id="(art_[0-9a-z]+)"', parts[i]).group(1)
        paragraphs = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", p))).strip()
                      for p in re.findall(r"<p\b[^>]*>(.*?)</p>", parts[i + 1], re.S)]
        out[article] = [p for p in paragraphs if p]
    return out


def usable(text):
    letters = sum(c.isalpha() for c in text)
    return len(text.split()) >= MIN_WORDS and letters >= 0.6 * len(text)


def query(text):
    first = re.split(r"(?<=[.;:])\s", text)[0]
    return " ".join(first.split()[:QUERY_WORDS]).strip(" ,;:")


def main():
    rows, counts = [], {}
    for act, celex in ACTS.items():
        english = articles(fetch(celex, "eng"))
        for language, code in LANGUAGES.items():
            target = articles(fetch(celex, code))
            n = 0
            for article, paragraphs in english.items():
                other = target.get(article)
                if not other or len(other) != len(paragraphs):
                    continue
                for i, (en, tr) in enumerate(zip(paragraphs, other)):
                    if usable(en) and usable(tr):
                        rows.append((f"{act}/{article}/{i}", language, query(en), tr))
                        n += 1
            counts[(act, language)] = n
            print(act, language, n, file=sys.stderr, flush=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with lzma.open(OUT, "wt", encoding="utf8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
        writer.writerow(["id", "language", "query_en", "document"])
        writer.writerows((i, l, q.replace("\t", " "), d.replace("\t", " ")) for i, l, q, d in rows)
    print(f"{len(rows)} rows", file=sys.stderr)


if __name__ == "__main__":
    main()
