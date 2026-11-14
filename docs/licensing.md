# Licensing of the glossary and its search lexicon

What has to be true before the glossary, or the search lexicon exported from it, ships in
another product: the QGIS semantic plugin search (MIT) plans to use it to enrich its static
model, and a Hugging Face dataset is planned.

Project policy (`dec-glossary-vs-corpus-licensing`) holds that term equivalents with their
sense are not a derived work of a source. That is enough for research builds; for a
distributed product, sources with no stated licence still need confirmation from their
holder.

## Sources in the search lexicon

State on 2026-11-12. Rows are lexicon rows (terms per concept and language, abbreviations
excluded).

| Source | Rows | Licence | Status for shipping | Obligation |
|---|---:|---|---|---|
| SNORRE, Språkbanken sbr-24 | 167,911 | CC BY 4.0 | cleared | credit Standard Norge |
| LÍSA glossary | 16,178 | none stated | **to confirm** with LÍSA | — |
| ISLEX 2026-02 | 7,714 | CC BY-SA 4.0 | cleared | credit; share-alike |
| ISO/TC 211 MLGT | 4,041 | © ISO/TC 211, none stated | **to confirm**, or drop (no Nordic languages) | — |
| IATE download | 3,749 | not copyright protected | cleared | credit "Download IATE, European Union, 2026" |
| Icelandic-Polish dictionary | 3,236 | CC BY-SA 4.0 | cleared | credit; share-alike |
| Icelandic-French dictionary | 2,629 | CC BY-SA 4.0 | cleared | credit; share-alike |
| Geonorge metadata code lists | 525 | none stated | **to confirm** with Kartverket (likely NLOD) | — |
| English-Icelandic glossary 21.09 | not yet exported | CC BY 4.0 | cleared | credit the authors and the institute |
| INSPIRE regulation names | not yet exported | EU legal text; EEA translations | cleared | acknowledge the source (EUR-Lex, EEA Supplement) |
| OpenStreetMap tagging schema | not yet exported | ISC | cleared | keep the ISC notice |
| GEMET (EEA) | not yet exported | CC BY 4.0 | cleared | credit the EEA |
| CORINE Land Cover nomenclature (NIBIO) | not yet exported | NLOD 1.0 | cleared | credit NIBIO |

Not in the lexicon: QGIS GUI labels (GPL-2.0), Geonorge application strings (MIT), ensk.is
(PDDL, registered, not loaded).

## Consequences

- **Share-alike.** The Árni Magnússon dictionaries are CC BY-SA 4.0, so a lexicon or dataset
  that includes their terms is released under CC BY-SA 4.0. This answers
  `cand-glossary-licence` for any release that includes them. A CC BY-SA data file can ship
  next to MIT plugin code as a separate work; the plugin code keeps its licence.
- **Credits.** A release carries one attribution file naming Standard Norge, the EU (IATE),
  the Árni Magnússon Institute (with the dictionary handles) and any source confirmed later.
- **Unconfirmed sources.** A release can be built without LÍSA, MLGT and the Geonorge code
  lists. Without LÍSA, the English-Icelandic glossary 21.09 (CC BY 4.0) still covers 37 % of
  LÍSA's English terms and 28 % of its pairs, mostly single words; LÍSA's multi-word GIS terms
  and the Icelandic pivot to ISLEX would be lost. Each `source_id` is kept per row, so filtering is a one-line change. In the
  acceptance test most of the gain on Norwegian themes came from the keyword part and the
  Geonorge code lists, so confirming Kartverket matters most for search.
- **SNORRE release.** Språkbanken also publishes a 2018 XML export (sbr-48) under CC0 with
  Bokmål, Nynorsk and English only. Switching to it would remove the credit obligation for
  those languages but lose French and German.

## Nautical chart symbols (INT 1)

INT 1 editions key every chart symbol by the IHO S-4 reference, so they would join across
languages by code. Their licences are the obstacle (as reported by the project owner,
2026-11-13, texts still to be read):

| Edition | Languages | Terms as reported |
|---|---|---|
| Kartverket INT 1 (2020) | nb, en | all rights reserved for chart reproduction; nothing on text reuse |
| UKHO English edition, also distributed by IHO | en | UKHO: internal use only; IHO: its own restrictive licence (IHO redistributing a UKHO internal-use text is itself questionable) |
| Canadian Hydrographic Service, Chart 1 | en, fr | free download; private use allowed, commercial use forbidden; collective non-commercial use not addressed |

**IHO policy** on the use of its materials (iho.int, last modified 2025-10-02) allows reuse of
public IHO material for non-commercial, educational or research purposes *without modification*,
with attribution, date and version, keeping original notices. Adapting, translating or creating
derivative content needs prior approval from the IHO Secretariat (info@iho.int, subject
"Branding/Materials Use Request", stating intended use and audience, a sample, duration and
scope); commercial use needs a formal agreement. Extracting term equivalents and linking them
across languages is modified use, so IHO material (S-32 Hydrographic Dictionary, the English
INT 1, S-4, S-23) needs approval before it enters a released glossary.

The Norwegian extract is kept locally (`published/int1/README.md`). A request to
Kartverket can cover INT 1 and the Geonorge code lists together; an IP licence for CHS
Chart 1 / Carte 1 (October 2026 edition,
<https://waves-vagues.dfo-mpo.gc.ca/library-bibliotheque/chs-shc-chart1-carte1-202610-4134361x.pdf>)
was requested from CHS on 2026-11-13.

## Hugging Face dataset

The card must state the licence in YAML front matter at the top of `README.md`, and
document fields, counts, version and each source's licence and credit. The ensk.is dataset
on Hugging Face shows what happens otherwise: its licence block sits after the text, so the
site shows no licence.
