#!/usr/bin/env python3
"""
extract_inspire_reg.py - official INSPIRE vocabulary from Regulation (EU) No 1089/2010.

    python3 tools/extract_inspire_reg.py pdf            # Bokmål and Icelandic, from local PDFs
    python3 tools/extract_inspire_reg.py cellar [LANG]  # EU languages, from the Publications Office

The regulation names every spatial object type, data type, enumeration and code list in a
heading that ends with its technical name: "8.4.1.1. Hydro Node (HydroNode)", "Hydrografisk
knutepunkt (HydroNode)", "Vatnahnúta (HydroNode)". The technical name is the same in every
language, so it keys the official translations; no word matching is needed.

pdf: reads sources/restricted/inspire-reg/{32010r1089,32013r1253}_{no,is}.pdf, the EEA
Supplement versions (Norwegian: EØS-tillegget; Icelandic: EES-viðbætir) of the base act and of
the amendment that adds the Annex II and III themes. Fetch them by hand (see the registry).
cellar: downloads the consolidated text 02010R1089-20231119 through the Cellar API (content
negotiation; EUR-Lex itself answers scripts with a bot challenge), about 2.6 MB per language.
Run it on GitHub Actions.

Writes published/inspire-regulation/inspire_reg_<lang>.csv: key, language, label, section, act.
"""
import csv
import html
import re
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PDFS = ROOT / "sources" / "restricted" / "inspire-reg"
OUT = ROOT / "published" / "inspire-regulation"
CONSOLIDATED = "02010R1089-20231119"
EU_LANGUAGES = {"en": "eng", "fr": "fra", "es": "spa", "de": "deu", "it": "ita", "da": "dan", "pl": "pol",
                "sl": "slv", "el": "ell", "ro": "ron", "bg": "bul", "sk": "slk", "sv": "swe"}
HEADING = re.compile(r"^(\d+(?:\.\d+)+)\.?\s+(.+?)\s*\(([A-Z][A-Za-z0-9]+)\)\s*$")
START = re.compile(r"^(\d+(?:\.\d+)+)\.?\s+\S")


def headings(lines):
    """Yield (section, label, key) from text lines, joining headings wrapped onto the next lines."""
    lines = [re.sub(r"[­‑]", "-", re.sub(r"\s+", " ", l)).strip() for l in lines]
    for i, line in enumerate(lines):
        if not START.match(line):
            continue
        text = line
        for extra in lines[i + 1:i + 3]:
            if HEADING.match(text) or not extra or START.match(extra):
                break
            text = f"{text} {extra}"
        match = HEADING.match(text)
        if match:
            label = re.sub(r"\s+", " ", match.group(2)).strip(" .")
            label = re.sub(r"(\w)- (\w)", r"\1\2", label) if not re.search(r"\w- og ", label) else label
            if 1 < len(label) <= 120:
                yield match.group(1), label, match.group(3)


def write(language, rows):
    OUT.mkdir(parents=True, exist_ok=True)
    seen, unique = set(), []
    for row in rows:
        if (row[0], row[2]) not in seen:
            seen.add((row[0], row[2]))
            unique.append(row)
    with open(OUT / f"inspire_reg_{language}.csv", "w", encoding="utf8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["key", "language", "label", "section", "act"])
        writer.writerows(unique)
    print(f"{language}: {len(unique)} keyed names", file=sys.stderr)


def from_pdfs():
    for code, language in (("no", "nb"), ("is", "is")):
        rows = []
        for act in ("32010r1089", "32013r1253"):
            path = PDFS / f"{act}_{code}.pdf"
            text = subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                                  check=True).stdout
            rows += [(key, language, label, section, act.upper()) for section, label, key in headings(text.splitlines())]
        write(language, rows)


def merge_numbers(raw):
    """XHTML puts a section number and its title on separate lines; join them."""
    lines = [l.replace("\u00a0", " ").strip() for l in raw]
    lines = [l for l in lines if l and not re.fullmatch(r"▼\w*", l)]
    merged, i = [], 0
    while i < len(lines):
        if re.fullmatch(r"\d+(\.\d+)+\.?", lines[i]) and i + 1 < len(lines):
            merged.append(f"{lines[i]} {lines[i + 1]}")
            i += 2
        else:
            merged.append(lines[i])
            i += 1
    return merged


def from_cellar(languages):
    for language in languages:
        request = urllib.request.Request(
            f"http://publications.europa.eu/resource/celex/{CONSOLIDATED}",
            headers={"Accept": "application/xhtml+xml", "Accept-Language": EU_LANGUAGES[language],
                     "User-Agent": "gis-glossary/0.1 (terminology research)"})
        page = urllib.request.urlopen(request, timeout=300).read().decode("utf8")
        text = html.unescape(re.sub(r"<[^>]+>", "\n", re.sub(r"</(p|td|div|h\d)>", "\n", page)))
        lines = merge_numbers(text.splitlines())
        write(language, [(key, language, label, section, CONSOLIDATED) for section, label, key in headings(lines)])


if __name__ == "__main__":
    if sys.argv[1] == "pdf":
        from_pdfs()
    else:
        from_cellar(sys.argv[2:] or list(EU_LANGUAGES))
