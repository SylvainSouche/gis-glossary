#!/usr/bin/env python3
"""
score_translation.py - count known terminology traps in machine translations.

    python3 tools/score_translation.py REFERENCE.txt NAME=OUTPUT.txt ...

Scored against the English original of QGIS Training Manual lesson 8.4. For each
trap, "right" counts the expected wording and "wrong" a known mistranslation.
"""

import difflib
import re
import sys
from pathlib import Path

# name, kind, expected wording, known mistranslations
TRAPS = [
    ("buffer", "term", r"(?<![_\w])buffer(ed)?\b",
     r"\bstamp\b|internal pattern|Clipboard|Tools ► mask|negative mask|\bTampon\b"),
    ("feature", "term", r"\bfeatures?\b", r"\bentit(y|ies)\b"),
    ("clip", "term", r"(?<![_\w])clip(ping)?\b",
     r"\bsegment(ation)?\b|rasterization op|rasterize from|\bslicing\b|\bsplitting?\b|Cutting|Cutout"),
    ("hillshade", "term", r"\b[Hh]illshade\b(?!\.tif)", r"\bshading\b|\bshadow(ing)?\b"),
    ("DEM", "term", r"\bDEM\b", r"\bMNEs?\b"),
    ("CRS", "term", r"\bCRS\b", r"\bSCR\b"),
    ("query", "term", r"\bquery\b", r"\brequest\b"),
    ("symbology", "term", r"\b[Ss]ymbology\b", r"\bSymbolism\b|\bSymbolology\b|\bsymbolization\b"),
    ("dataset", "term", r"dataset", r"data games"),
    ("Run", "gui", r"\bClick (on )?Run\b", r"\bClick (on )?[Ee]xecute\b"),
    ("Digitizing", "gui", r"\bDigitizing\b", r"\bNumeri[sz]ation\b|\bNumeration\b"),
    ("Join by nearest", "gui", r"(?i)Join Attributes by Nearest",
     r"Closest Neighbor Join|by proximity|Connect attributes"),
    ("Hide layers", "gui", r"\bHide all layers except\b", r"\bCache all layers\b|\bStore all layers\b"),
    ("Field calculator", "gui", r"field calculator", r"terrain calculator"),
    ("Left in French", "defect", r"$^",
     r"\bOmbrage\b|Reproject[ée]\b|Reprojett[ée]|Dissoudre|Bande grise|Jeu\(x\)|sauvharder"),
    ("Prompt leak", "defect", r"$^",
     r"Background Information|\[Source Text\]|It belongs to the field|Output only the translation"),
    ("Name shortened", "defect", r"$^", r"University of Cape(?! Town)"),
]
CODE = [
    '"suitable" = 1', "$area", "$id", "(aspect@1 > 45) AND (aspect@1 < 135)",
    "[aspect45_135] * [slope15_60] * [rainfall_1000]", '"Gen_Zoning" = \'Rural\'',
    '"area" > 6000', "Rainfall30@1 > 1000",
]


def score(text):
    result = {}
    for name, kind, right, wrong in TRAPS:
        result[name] = (kind, len(re.findall(right, text)), len(re.findall(wrong, text)))
    return result


def main():
    reference = Path(sys.argv[1]).read_text(encoding="utf8")
    outputs = {}
    for item in sys.argv[2:]:
        name, path = item.split("=", 1)
        outputs[name] = Path(path).read_text(encoding="utf8")
    names = list(outputs)
    scored = {name: score(text) for name, text in outputs.items()}
    baseline = score(reference)

    print("| Trap | Kind | Reference | " + " | ".join(names) + " |")
    print("|---|---|---:|" + "---:|" * len(names))
    for name, kind, _, _ in TRAPS:
        cells = [f"{scored[n][name][1]} / {scored[n][name][2]}" for n in names]
        print(f"| {name} | {kind} | {baseline[name][1]} | " + " | ".join(cells) + " |")

    print("\nCells are right / wrong.\n")
    for name in names:
        total = {"term": 0, "gui": 0, "defect": 0}
        for kind, _, wrong in scored[name].values():
            total[kind] += wrong
        kept = sum(code in outputs[name] for code in CODE)
        similarity = difflib.SequenceMatcher(
            None, reference.split(), outputs[name].split(), autojunk=False
        ).ratio()
        print(f"{name}: wrong terms {total['term']}, wrong GUI {total['gui']}, "
              f"defects {total['defect']}, code kept {kept}/{len(CODE)}, "
              f"word similarity {similarity:.3f}")


if __name__ == "__main__":
    main()
