# Source audit: Kartverket PDFs

Audited 2026-11-09 from four PDFs supplied by the project owner. The PDFs are
not versioned: `tools/fetch_restricted.sh` collects them from Kartverket.

| Source | Languages | Terminology content |
|---|---|---|
| Den norske los 7 (Norwegian) | nb, en, de, fr, nl | About 260 glossary rows; WMO ice nomenclature |
| The Norwegian Pilot 7 (English) | en, with the same glossary | Parallel edition of 382 pages |
| Symbols and Abbreviations (INT 1, 2020) | nb, en | About 1,800 index entries across both languages, coded by INT 1 symbol |
| Toponymic Guidelines (2025) | nb and nn-type forms, en | About 230 place-name generics |

Counts are estimates from extracted text and include repeats.

## Findings

- **The Los glossary is a small, ready multilingual list.** It adds maritime
  terms in four target languages. Rows are loose and have typos, for example
  "moutain" and "côoté", so they need review.
- **The two Los editions are a parallel corpus candidate.** Full text falls under
  the corpus rule, and page alignment has not been tested.
- **INT 1 codes may be usable concept keys.** Codes such as K 14 are not tied to
  a language. Other national INT 1 editions could add languages; not checked.
- **Nynorsk gains only a lead.** The toponymic list has forms such as *vatn* and
  *botn*, but they are unlabelled and mixed with Bokmål-type forms, and many are
  dialect or place-name forms. The Los and INT 1 are Bokmål.

## Licence

Los and INT 1 state Kartverket copyright, and INT 1 requires written consent for
reproducing chart material. The toponymic guidelines have no statement. None
gives a reuse licence, so ask Kartverket before publishing anything taken from
these. Under `dec-glossary-vs-corpus-licensing`, term equivalents may still be
usable, but that does not cover definitions, the ice nomenclature text or the
full-text corpus.
