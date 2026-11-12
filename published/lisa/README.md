# LÍSA word list (held back)

The term pairs extracted from this resource are **not published here** while we ask its
authors about availability and licence. The extractor, `tools/extract_lisa.py`, is in the
repository; the generated `lisa_terms.csv` is kept out of git.

## The resource

*Orðalisti LÍSU* is the Icelandic GIS word list of **LÍSA – samtök um landupplýsingar á
Íslandi** (the Icelandic association for geographic information), compiled by its terminology
committee, **Orðanefnd LÍSU**. It is the most complete Icelandic GIS terminology we have found.

| Edition | Link |
|---|---|
| Icelandic–English, 6th edition, 2015 (PDF) | <https://landupplysingar.is/wp-content/uploads/2025/07/LISA-ISL-EN-6utg-2015-1-14-1.pdf> |
| English–Icelandic, 6th edition, 2015 (PDF) | <https://landupplysingar.is/wp-content/uploads/2025/07/LISA-EN-ISL-6utg-2015-1-14.pdf> |
| Icelandic–English, web page | <https://landupplysingar.is/index.php/ordalisti-islenska-enska/> |

- LÍSA: <https://landupplysingar.is/>
- Word lists page: <https://landupplysingar.is/index.php/ordalistar/>
- The page also points to the term bank of the Icelandic Language Institute (Orðabanki
  Íslenskrar málstöðvar): <http://www.ordabanki.hi.is/wordbank/search>

## How the project uses it

Only term pairs: the Icelandic headword, its synonyms and the English equivalent, about 9,000
pairs from the Icelandic–English edition, with no definitions or other text. In the glossary
they give Icelandic terms to GIS concepts and act as the bridge from English to the
Árni Magnússon Institute dictionaries (Danish, Norwegian, Swedish, French, Polish). In the
[search acceptance test](../../docs/evaluations/embedding-tests.md), English searches found
Icelandic metadata records only when these terms were included.

## Licence question

No licence or terms of use are stated on the site or in the PDFs. We have written to LÍSA
(lisa@landupplysingar.is) to ask:

1. under what terms the list may be used, and whether the term pairs may be redistributed
   in an open glossary with credit to Orðanefnd LÍSU (CC BY 4.0 or CC BY-SA 4.0 would suit);
2. whether the 2015 edition is the latest;
3. whether a machine-readable version exists;
4. whether the terms are maintained in the Icelandic Term Bank, and under which terms;
5. how the committee wishes to be credited.

Until there is an answer, a build from this repository runs without LÍSA. See
[docs/licensing.md](../../docs/licensing.md).
