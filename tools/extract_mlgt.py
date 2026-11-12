#!/usr/bin/env python3
"""
extract_mlgt.py - publish the term equivalents of the ISO/TC 211 MLGT as CSV.

Reads the restricted copy in sources/restricted/isotc211-glossary, which
tools/fetch_restricted.sh collects, and writes published/iso-mlgt/. Only the
fields named below are copied: definitions, notes and examples are never read
into the output. Run through tools/publish_mlgt.sh.
"""

import csv
import datetime
import subprocess
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = ROOT / "sources" / "restricted" / "isotc211-glossary"
OUT_DIR = ROOT / "published" / "iso-mlgt"

LANGUAGES = {
    "eng": "en", "fra": "fr", "spa": "es", "deu": "de", "ita": "it",
    "nob": "nb", "nno": "nn", "isl": "is", "dan": "da", "pol": "pl",
    "slv": "sl", "ell": "el", "ron": "ro", "bul": "bg", "slk": "sk",
    "swe": "sv",
}
SOURCE = "ISO/TC 211 Multi-Lingual Glossary of Terms (MLGT), © ISO/TC 211"
ADDRESS = "https://github.com/geolexica/isotc211-glossary"
LICENCE = "No licence stated; made freely available according to ISO/TC 211 TMG"
METHOD = "automatic extraction of term equivalents by tools/extract_mlgt.py"
COLUMNS = [
    "concept_id", "concept_number", "language", "term", "term_type",
    "normative_status", "entry_status", "iso_reference", "source",
    "source_address", "source_commit", "source_licence", "method", "retrieved",
]


def iso_reference(entry):
    """The citation of the authoritative standard, without its text."""
    for item in entry.get("sources") or []:
        if item.get("type") == "authoritative":
            return ((item.get("origin") or {}).get("ref") or {}).get("source", "")
    return ""


def rows_of(path, commit, retrieved):
    documents = [d for d in yaml.safe_load_all(path.read_text(encoding="utf8")) if d]
    managed = next(d for d in documents if "localized_concepts" in d.get("data", {}))
    for document in documents:
        entry = document.get("data", {})
        language = LANGUAGES.get(entry.get("language_code"))
        if not language:
            continue
        for term in entry.get("terms") or []:
            designation = (term.get("designation") or "").strip()
            if not designation:
                continue
            yield {
                "concept_id": managed["id"],
                "concept_number": managed["data"].get("identifier", ""),
                "language": language,
                "term": designation,
                "term_type": term.get("type", ""),
                "normative_status": term.get("normative_status") or "",
                "entry_status": entry.get("entry_status") or "",
                "iso_reference": iso_reference(entry),
                "source": SOURCE,
                "source_address": ADDRESS,
                "source_commit": commit,
                "source_licence": LICENCE,
                "method": METHOD,
                "retrieved": retrieved,
            }


ATTRIBUTION = """# ISO/TC 211 MLGT term equivalents

Term equivalents from the ISO/TC 211 Multi-Lingual Glossary of Terms.

- **Credit:** ISO/TC 211, Geographic information/Geomatics, and its Terminology
  Maintenance Group, with translations from national standards bodies
- **Copyright of the source:** ISO/TC 211
- **Source data:** <{address}>, commit `{commit}`
- **ISO/TC 211 TMG:** <https://github.com/ISO-TC211/TMG>
- **Online edition:** <https://isotc211.geolexica.org/>
- **Availability statement:** the TMG says the glossary "is being made freely
  available to all interested people and organizations". No licence is stated.
- **Retrieved:** {retrieved}
- **Changes:** terms only, selected for this project's languages and converted
  to CSV. Definitions, notes and examples are not included.

ISO/TC 211 has not reviewed or endorsed this file. The source itself is not
redistributed here.
"""


def main():
    commit = subprocess.run(
        ["git", "-C", str(SOURCE_DIR), "rev-parse", "HEAD"],
        check=True, capture_output=True, text=True,
    ).stdout.strip()
    retrieved = datetime.date.today().isoformat()

    rows = []
    for path in sorted((SOURCE_DIR / "concepts").glob("*.yaml")):
        rows.extend(rows_of(path, commit, retrieved))
    rows.sort(key=lambda r: (r["concept_id"], r["language"], r["term"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "mlgt_terms.csv", "w", encoding="utf8", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (OUT_DIR / "ATTRIBUTION.md").write_text(
        ATTRIBUTION.format(address=ADDRESS, commit=commit, retrieved=retrieved),
        encoding="utf8",
    )
    print(f"{len(rows)} terms written to {OUT_DIR / 'mlgt_terms.csv'}")


if __name__ == "__main__":
    main()
