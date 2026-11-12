#!/usr/bin/env python3
"""
extract_lisa.py - publish the term pairs of the LÍSA Icelandic-English GIS word list.

Reads the restricted PDF collected by tools/fetch_restricted.sh and writes
published/lisa/. Each entry is an Icelandic headword, optional synonyms ([sh.]) and an
English equivalent ([enska]). Only terms are kept; the list has no definitions.
"""

import csv
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "restricted" / "lisa-isl-en-2015.pdf"
OUT_DIR = ROOT / "published" / "lisa"
ADDRESS = "https://landupplysingar.is/wp-content/uploads/2025/07/LISA-ISL-EN-6utg-2015-1-14-1.pdf"
ATTRIBUTION = """# LÍSA term pairs

- **Credit:** Orðanefnd LÍSU, LÍSA samtök um landupplýsingar á Íslandi
- **Source:** Orðalisti LÍSU, Icelandic-English, 6th edition 2015
- **Address:** <{address}>
- **Licence:** none stated; the source is not redistributed here
- **Retrieved:** 2026-11-10
- **Changes:** Icelandic headwords, synonyms and English equivalents extracted to CSV by
  `tools/extract_lisa.py`.
"""


def entries(text):
    headword, synonyms = None, []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or re.fullmatch(r"[A-ZÁÉÍÓÚÝÞÆÖÐ]", line) or re.fullmatch(r"\d+", line):
            continue
        if line.startswith("[sh.]"):
            synonyms = [s.strip() for s in line[5:].split(",") if s.strip()]
        elif line.startswith("[enska]"):
            english = line[7:].strip()
            if headword and english:
                yield headword, synonyms, english
            synonyms = []
        elif not raw.startswith(" ") and not line.startswith("["):
            headword, synonyms = line, []


def main():
    text = subprocess.run(["pdftotext", "-layout", str(SOURCE), "-"], check=True,
                          capture_output=True, text=True).stdout
    rows, seen = [], set()
    for number, (headword, synonyms, english) in enumerate(entries(text), 1):
        key = (headword, english)
        if key in seen:
            continue
        seen.add(key)
        rows.append([f"lisa{number}", "is", headword, "preferred", english])
        rows += [[f"lisa{number}", "is", s, "admitted", english] for s in synonyms]
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_DIR / "lisa_terms.csv", "w", encoding="utf8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["entry", "language", "term", "status", "english"])
        writer.writerows(rows)
    (OUT_DIR / "ATTRIBUTION.md").write_text(ATTRIBUTION.format(address=ADDRESS), encoding="utf8")
    print(f"{len(seen)} entries, {len(rows)} Icelandic terms")


if __name__ == "__main__":
    main()
