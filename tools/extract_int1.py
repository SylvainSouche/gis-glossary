#!/usr/bin/env python3
"""
extract_int1.py - extract the symbol rows of Kartverket's INT 1 (2020) to CSV.

    python3 tools/extract_int1.py      (needs pdfplumber)

Reads sources/restricted/symboler-og-forkortelser-i-norske-sjokart.pdf and writes
published/kartverket-int1/int1_terms.csv, which is kept out of git until Kartverket confirms
the licence (published/kartverket-int1/README.md).

Each row: section letter and number (the INT 1 code, K 20), the IHO S-4 reference (422.1),
the Bokmål description (upright) and the English one (oblique), and the page. The S-4
reference is the same in every national INT 1 edition, so it keys a concept across languages.
Layout read by position and font: row number at the left in 8.5 pt, descriptions in the
middle column in 7 pt, S-4 reference at the right in 6 pt, section letter bold 24 pt.
"""

import csv
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "restricted" / "symboler-og-forkortelser-i-norske-sjokart.pdf"
OUT = ROOT / "published" / "kartverket-int1" / "int1_terms.csv"
FIRST_PAGE, LAST_PAGE = 6, 78          # printed sections A to T (0-based page indexes)
NUMBER = re.compile(r"^(\d{1,3}(\.\d{1,2})?|[a-z])$")
DESCRIPTION_X = (205, 385)
S4_X = 470


def oblique(word):
    return "Oblique" in word["fontname"] or "Italic" in word["fontname"]


def clean(text, italic):
    if italic:  # the oblique font encodes spaces as dots
        text = re.sub(r"\.(?=\S)", " ", text)
    text = re.sub(r"\s+", " ", text).strip(" .")
    return text


def lines(words):
    """Group words of one language into lines by their top coordinate."""
    rows = []
    for word in sorted(words, key=lambda w: (round(w["top"]), w["x0"])):
        if rows and abs(rows[-1][0] - word["top"]) < 2.5:
            rows[-1][1].append(word)
        else:
            rows.append([word["top"], [word]])
    return [(top, " ".join(w["text"] for w in ws)) for top, ws in rows]


def join(parts, italic):
    text = ""
    for part in parts:
        part = clean(part, italic)
        if text.endswith("-") and part[:1].islower():
            text = text[:-1] + part
        else:
            text = f"{text} {part}".strip()
    return text


def page_rows(page, index):
    words = page.extract_words(extra_attrs=["fontname", "size"])
    for w in words:  # decimals come out with a space: "1 .1", "491 .1"
        if re.fullmatch(r"[\d .]+", w["text"]):
            w["text"] = w["text"].replace(" ", "")
    section = next((w["text"] for w in words if "Bold" in w["fontname"] and w["size"] > 20
                    and re.fullmatch(r"[A-Z]", w["text"])), None)
    if not section:
        return []
    numbers = sorted((w for w in words if w["x0"] < 100 and abs(w["size"] - 8.5) < 0.6
                      and NUMBER.match(w["text"])), key=lambda w: w["top"])
    if not numbers:
        return []
    centres = [(n["top"] + n["bottom"]) / 2 for n in numbers]
    bounds = [(centres[i - 1] + centres[i]) / 2 if i else -1 for i in range(len(centres))]
    bounds.append(page.height)
    text_words = [w for w in words if DESCRIPTION_X[0] <= w["x0"] < DESCRIPTION_X[1] and 6.5 <= w["size"] <= 7.5]
    s4_words = [w for w in words if w["x0"] >= S4_X and w["size"] <= 6.5 and re.match(r"^[\d.]+$", w["text"])]
    out = []
    for i, number in enumerate(numbers):
        top, bottom = bounds[i], bounds[i + 1]
        inside = lambda w: top <= (w["top"] + w["bottom"]) / 2 < bottom
        mine = [w for w in text_words if inside(w)]
        nb = join([t for _, t in lines([w for w in mine if not oblique(w)])], False)
        en = join([t for _, t in lines([w for w in mine if oblique(w)])], True)
        s4 = " ".join(dict.fromkeys(w["text"] for w in sorted(s4_words, key=lambda w: w["top"]) if inside(w)))
        if nb or en:
            out.append([section, number["text"], f"{section} {number['text']}", s4, nb, en, index + 1])
    return out


def main():
    rows = []
    with pdfplumber.open(SOURCE) as pdf:
        for index in range(FIRST_PAGE, min(LAST_PAGE, len(pdf.pages))):
            rows += page_rows(pdf.pages[index], index)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["section", "number", "int1_code", "s4", "nb", "en", "page"])
        writer.writerows(rows)
    print(f"{len(rows)} rows, {sum(1 for r in rows if r[3])} with an S-4 reference, "
          f"{sum(1 for r in rows if r[4] and r[5])} with both languages", file=sys.stderr)


if __name__ == "__main__":
    main()
