#!/usr/bin/env python3
"""
extract_int1.py - extract the symbol rows of national INT 1 editions to CSV.

    python3 tools/extract_int1.py [EDITION ...]     (needs pdfplumber; default: all)

Editions (restricted copies, see registry/restricted-manifest.tsv):
    no  Kartverket, Symboler og forkortelser i norske sjøkart, 2020 (Bokmål, English)
    da  Geodatastyrelsen, Kort 1, 5th edition 2022 (Danish, English)
    es  Instituto Hidrográfico de la Marina, Símbolos, abreviaturas y términos, 2011 (Spanish, English)
Writes published/int1/int1_<edition>.csv, kept out of git until each publisher confirms the
licence (published/int1/README.md). Only codes and words are extracted, never symbols.

Each row: section letter and number (the INT 1 code, K 20), the IHO S-4 reference (422.1),
the national description (upright) and the English one (oblique or italic), and the page. The
S-4 reference is the same in every national edition, so it keys a concept across languages.
The editions share a layout: row number at the left in 8.5 pt, descriptions in the middle
column in 7 pt, S-4 reference at the right in 6 pt, section letter about 24 pt.
"""

import csv
import re
import sys
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).resolve().parent.parent
RESTRICTED = ROOT / "sources" / "restricted"
EDITIONS = {  # edition: (file, language)
    "no": (RESTRICTED / "symboler-og-forkortelser-i-norske-sjokart.pdf", "nb"),
    "da": (RESTRICTED / "int1" / "int1_dk_gst_2022.pdf", "da"),
    "es": (RESTRICTED / "int1" / "int1_es_ihm_2011.pdf", "es"),
}
OUT = ROOT / "published" / "int1"
NUMBER = re.compile(r"^(\d{1,3}(\.\d{1,2})?|[a-z])$")
DESCRIPTION_X = (205, 385)
S4_X = 470


def oblique(word):
    return "Oblique" in word["fontname"] or "Italic" in word["fontname"]


def clean(text, italic):
    if italic and re.search(r"[^\W\d]\.[^\W\d].*[^\W\d]\.[^\W\d]", text) and " " not in text.strip():
        text = re.sub(r"\.(?=\S)", " ", text)  # Kartverket's oblique font encodes spaces as dots
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
    section = next((w["text"] for w in words if w["size"] > 20 and (w["x0"] > 400 or w["x0"] < 110)
                    and re.fullmatch(r"[A-Z]", w["text"])), None)
    if not section:
        return []
    numbers = sorted((w for w in words if 55 < w["x0"] < 100 and abs(w["size"] - 8.5) < 0.6
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
    OUT.mkdir(parents=True, exist_ok=True)
    for edition in sys.argv[1:] or list(EDITIONS):
        source, language = EDITIONS[edition]
        rows = []
        with pdfplumber.open(source) as pdf:
            for index, page in enumerate(pdf.pages):
                rows += page_rows(page, index)
        with open(OUT / f"int1_{edition}.csv", "w", encoding="utf8", newline="") as f:
            writer = csv.writer(f, lineterminator="\n")
            writer.writerow(["section", "number", "int1_code", "s4", language, "en", "page"])
            writer.writerows(rows)
        print(f"{edition}: {len(rows)} rows, {sum(1 for r in rows if r[3])} with an S-4 reference, "
              f"{sum(1 for r in rows if r[4] and r[5])} with both languages", file=sys.stderr)


if __name__ == "__main__":
    main()
