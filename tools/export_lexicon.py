#!/usr/bin/env python3
"""
export_lexicon.py - export the search lexicon from build/glossary.sqlite.

    python3 tools/export_lexicon.py [OUTPUT]   (default tests/acceptance/lexicon.tsv.xz)

One row per concept, language, term and source, for the 16 target languages, abbreviations
excluded. Columns: key (c<concept id>), label, language, term, source, ambiguous. Ambiguous
concepts are kept: search uses all their terms as keywords, but not as concept vectors.
"""
import csv
import lzma
import re
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LANGUAGES = {"en", "fr", "es", "de", "it", "nb", "nn", "is", "da", "pl", "sl", "el", "ro", "bg", "sk", "sv"}


def clean(text):
    return re.sub(r"[\t\r\n\\]+", " ", text or "").strip()


def main():
    output = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "tests" / "acceptance" / "lexicon.tsv.xz"
    db = sqlite3.connect(ROOT / "build" / "glossary.sqlite")
    rows, seen = [], set()
    for concept, label, ambiguous, language, text, term_type, source in db.execute(
            "SELECT concept_id, label, ambiguous, language, text, term_type, source_id FROM candidate_term"
            " ORDER BY concept_id"):
        if language not in LANGUAGES or term_type == "abbreviation" or not clean(text):
            continue
        key = (concept, language, clean(text).lower(), source)
        if key not in seen:
            seen.add(key)
            rows.append((f"c{concept}", clean(label), language, clean(text), source, str(ambiguous)))
    with lzma.open(output, "wt", encoding="utf8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
        writer.writerow(["key", "label", "language", "term", "source", "ambiguous"])
        writer.writerows(rows)
    print(f"{len(rows)} rows written to {output}")


if __name__ == "__main__":
    main()
