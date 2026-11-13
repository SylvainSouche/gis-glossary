#!/usr/bin/env python3
"""
export_lexicon.py - export the search lexicon from build/glossary.sqlite.

    python3 tools/export_lexicon.py [OUTPUT] [--holdout tests/acceptance/corpus.tsv]

Default OUTPUT: tests/acceptance/lexicon.tsv.xz. With --holdout, the INSPIRE regulation's names
for the feature types tested in that corpus (its `id` column holds their technical names) are
left out, so the INSPIRE part of the acceptance test does not see its own answers.

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


def held_out(db, corpus):
    """Concepts reached by the INSPIRE regulation for the technical names tested in the corpus."""
    with open(corpus, encoding="utf8", newline="") as f:
        ids = {row["id"] for row in csv.DictReader(f, delimiter="\t")}
    rows = db.execute("SELECT ce.concept_id, e.source_key FROM concept_entry ce JOIN entry e ON e.id = ce.entry_id"
                      " WHERE e.source_id = 'inspire-regulation'").fetchall()
    return {concept for concept, key in rows if key in ids}


def main():
    args = sys.argv[1:]
    corpus = None
    if "--holdout" in args:
        i = args.index("--holdout")
        corpus = args[i + 1]
        del args[i:i + 2]
    output = Path(args[0]) if args else ROOT / "tests" / "acceptance" / "lexicon.tsv.xz"
    db = sqlite3.connect(ROOT / "build" / "glossary.sqlite")
    skip = held_out(db, corpus) if corpus else set()
    rows, seen = [], set()
    for concept, label, ambiguous, language, text, term_type, source in db.execute(
            "SELECT concept_id, label, ambiguous, language, text, term_type, source_id FROM candidate_term"
            " ORDER BY concept_id"):
        if language not in LANGUAGES or term_type in ("abbreviation", "search") or not clean(text):
            continue
        if source == "inspire-regulation" and concept in skip:
            continue
        key = (concept, language, clean(text).lower(), source)
        if key not in seen:
            seen.add(key)
            rows.append((f"c{concept}", clean(label), language, clean(text), source, str(ambiguous)))
    with lzma.open(output, "wt", encoding="utf8", newline="") as f:
        writer = csv.writer(f, delimiter="\t", lineterminator="\n", quoting=csv.QUOTE_NONE, escapechar="\\")
        writer.writerow(["key", "label", "language", "term", "source", "ambiguous"])
        writer.writerows(rows)
    print(f"{len(rows)} rows written to {output}" + (f"; {len(skip)} tested concepts held out" if corpus else ""))


if __name__ == "__main__":
    main()
