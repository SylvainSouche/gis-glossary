#!/usr/bin/env python3
"""
extract_iate.py - publish the GIS-related terms of the IATE export as CSV.

Reads sources/open/iate/IATE_export.tbx.xz and writes published/iate/. A concept
is kept when a subject field or one of its English terms matches the patterns
below. Matching is broad on purpose, so rows are candidates for review.
"""

import csv
import lzma
import re
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "open" / "iate" / "IATE_export.tbx.xz"
OUT_DIR = ROOT / "published" / "iate"

NS = "{urn:iso:std:iso:30042:ed-2}"
XML_LANG = "{http://www.w3.org/XML/1998/namespace}lang"
RETRIEVED = "2026-11-09"
ACKNOWLEDGEMENT = "Download IATE, European Union, 2026"
ADDRESS = "https://iate.europa.eu/download-iate"
METHOD = "automatic selection by tools/extract_iate.py"
LANGUAGES = {
    "en", "fr", "es", "de", "it", "da", "pl", "sl", "el", "ro", "bg", "sk", "sv",
}
SUBJECT = re.compile(
    r"cartograph|geodes|geomat|geographic(al)? information|remote sensing"
    r"|topograph|survey|photogrammetr|spatial",
    re.I,
)
ENGLISH_TERM = re.compile(
    r"geograph|geospatial|geodet|geodes|geomat|cartograph|\bmaps?\b"
    r"|remote sensing|\blidar\b|orthophoto|orthoimage|spatial data"
    r"|coordinate system|georeferenc|digital elevation|digital terrain"
    r"|contour line|contour interval|topograph|cadastr|land register"
    r"|land parcel|satellite imag|\bGIS\b|\bgeoid\b|geodetic datum"
    r"|\braster\b|aerial photo|photogrammetr|isoline",
    re.I,
)
COLUMNS = [
    "concept_id", "language", "term", "term_type", "reliability_code",
    "evaluation", "is_primary", "lifecycle", "subject_fields", "match",
    "source", "source_address", "method", "retrieved",
]
ATTRIBUTION = """# IATE GIS-related terms

- **Acknowledgement:** {acknowledgement}
- **Source:** {address}
- **Reuse:** IATE's legal notice says data in the download file is not copyright
  protected and may be reproduced for non-commercial or commercial dissemination.
- **Retrieved:** {retrieved}
- **Changes:** subset selected by subject field and English term with
  `tools/extract_iate.py`, limited to this project's languages, converted to CSV.

Selection is automatic and includes false positives. The European Union accepts
no responsibility for the data and does not endorse this file.
"""


def note(element, *kinds):
    for child in element:
        if child.get("type") in kinds and child.text:
            return child.text.strip()
    return ""


def subject_fields(entry):
    fields = []
    for child in entry.findall(NS + "descrip"):
        if child.get("type") == "subjectField" and child.text:
            fields += [p.strip() for p in re.split(r"[;,]", child.text)]
    return fields


def rows_of(entry):
    fields = subject_fields(entry)
    sections = entry.findall(NS + "langSec")
    english = " | ".join(
        (term.findtext(NS + "term") or "")
        for section in sections if section.get(XML_LANG) == "en"
        for term in section.findall(NS + "termSec")
    )
    by_subject = any(SUBJECT.search(field) for field in fields)
    by_term = bool(ENGLISH_TERM.search(english))
    if not (by_subject or by_term):
        return
    match = "+".join(n for n, hit in (("subject", by_subject), ("term", by_term)) if hit)
    for section in sections:
        language = section.get(XML_LANG)
        if language not in LANGUAGES:
            continue
        for term in section.findall(NS + "termSec"):
            text = (term.findtext(NS + "term") or "").strip()
            if text:
                yield {
                    "concept_id": entry.get("id"),
                    "language": language,
                    "term": text,
                    "term_type": note(term, "termType"),
                    "reliability_code": note(term, "reliabilityCode"),
                    "evaluation": note(term, "administrativeStatus", "evaluation"),
                    "is_primary": note(entry, "isPrimary"),
                    "lifecycle": note(entry, "lifecycle"),
                    "subject_fields": "; ".join(fields),
                    "match": match,
                    "source": ACKNOWLEDGEMENT,
                    "source_address": ADDRESS,
                    "method": METHOD,
                    "retrieved": RETRIEVED,
                }


def main():
    rows = []
    with lzma.open(SOURCE) as stream:
        for _, element in ET.iterparse(stream, events=("end",)):
            if element.tag == NS + "conceptEntry":
                rows.extend(rows_of(element))
                element.clear()
    rows.sort(key=lambda r: (int(r["concept_id"]), r["language"], r["term"]))

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "iate_gis_terms.csv", "w", encoding="utf8", newline="") as f:
        writer = csv.DictWriter(f, COLUMNS, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    (OUT_DIR / "ATTRIBUTION.md").write_text(
        ATTRIBUTION.format(
            acknowledgement=ACKNOWLEDGEMENT, address=ADDRESS, retrieved=RETRIEVED
        ),
        encoding="utf8",
    )
    print(f"{len(rows)} terms from {len({r['concept_id'] for r in rows})} concepts")


if __name__ == "__main__":
    main()
