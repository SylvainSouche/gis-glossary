# INT 1 national editions (held back)

Rows extracted from national INT 1 editions are **not published here** until each publisher
confirms the licence. The extractor, `tools/extract_int1.py`, is in the repository; the
generated `int1_<edition>.csv` files are kept out of git. Only codes and words are extracted:
no symbols, drawings or other images.

## The editions

INT 1 (*Symbols, Abbreviations and Terms used on Charts*) is published by national hydrographic
offices following the chart specifications of the International Hydrographic Organization
(IHO S-4). Each symbol row gives the INT 1 code (K 20), a national and an English description,
and the S-4 reference (422.1).

| Edition | Publisher | Languages | Rows | With both languages |
|---|---|---|---:|---:|
| `no` | Kartverket, *Symboler og forkortelser i norske sjøkart*, 2020 | nb, en | 725 | 683 |
| `da` | Geodatastyrelsen, *Kort 1*, 5th edition 2022 | da, en | 725 | 713 |
| `es` | Instituto Hidrográfico de la Marina, *Símbolos, abreviaturas y términos*, 2011 | es, en | 673 | 660 |

Further editions are held but not extracted: Lithuanian–English (LTSA 2021, a translation of the
German BSH edition), Brazilian Portuguese–English (DHN 2022) and Hong Kong Chinese–English (2019).

## Why it matters

The INT 1 code and the S-4 reference are the same in every edition, so they key a symbol's
terms across languages with no word matching. 593 codes appear in all three extracted editions,
and their S-4 references agree:

| INT 1 | S-4 | Bokmål | Danish | Spanish |
|---|---|---|---|---|
| K 20 | 422.1 | Vrak, helt synlig | Vrag hvor skroget ikke oversvømmes | Naufragio que siempre vela |
| N 41 | 440.3 | Riksgrense i sjøen | International grænse til søs | Frontera internacional marítima |
| C 25 | 353.8 | Isbre, snøbre, brefront i sjøen | Gletcher | Glaciar |

## Extraction limits

Rows are read by position and font. An S-4 reference printed between two rows can be assigned
to the neighbouring row, and a few rows include the sub-heading above them. Review before use.

## Licence question

Each edition reserves reproduction rights: Kartverket for its charts, Geodatastyrelsen for
analogue and digital reproduction, the Instituto Hidrográfico de la Marina for any reproduction
without written permission. The INT 1 content itself follows IHO specifications, and the IHO
policy requires approval for translation or adaptation of its material. Requests are being
made; see [docs/licensing.md](../../docs/licensing.md).
