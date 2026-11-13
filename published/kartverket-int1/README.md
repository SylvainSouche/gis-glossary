# Kartverket INT 1, Norwegian edition (held back)

The rows extracted from this publication are **not published here** until the licence is
clear. The extractor, `tools/extract_int1.py`, is in the repository; the generated
`int1_terms.csv` is kept out of git.

## The resource

*Symboler og forkortelser i norske sjøkart / Symbols, Abbreviations, Terms used on Charts*,
INT 1, 2020 edition, Kartverket (Norwegian Hydrographic Service), based on the chart
specifications of the International Hydrographic Organization (IHO).

- PDF: <https://kartverket.no/globalassets/nautiske-publikasjoner/symboler-og-forkortelser-i-norske-sjokart.pdf>
- Each symbol row gives the INT 1 code (K 20), a Bokmål and an English description, and the
  IHO S-4 reference (422.1).

## Why it matters

The S-4 reference is shared by every national INT 1 edition. It is a language-neutral key: a
row in the German, French, Danish, Swedish or Polish edition joins the Norwegian one by code,
with no matching of English words. The same idea applies to CORINE land cover codes and the
Geonorge code lists.

## Extraction

724 rows (682 with both languages, 515 with an S-4 reference), read by position and font:
Bokmål upright, English oblique. Known limits: an S-4 reference printed between two rows can be
assigned to the neighbouring row, and a few rows include the sub-heading above them. Review
before use.

## Licence question

The publication reserves all rights to reproduction of charts and states no terms for reuse
of its text. The INT 1 family as a whole is restrictive: see [docs/licensing.md](../../docs/licensing.md).
