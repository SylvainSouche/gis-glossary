# Glossary data model

The schema is [`schema/glossary.sql`](../schema/glossary.sql). The database is
built by `tools/build_glossary.py` into `build/glossary.sqlite`, which is not
versioned.

**Purpose:** two uses. Assisted translation of layer descriptions and documents, where the
target is consistent, correct technical terms, not publication-quality prose; and
multilingual search, where an English query must find metadata written in other languages
(a lexicon exported from `candidate_term`, tested in
[evaluations/embedding-tests.md](evaluations/embedding-tests.md)).

## Principles

1. **Keep what each source says apart from what the project decides.** Sources are
   rebuilt from `published/`; decisions must survive a rebuild.
2. **A concept is one sense.** Sharing an English word does not make two entries the
   same concept.
3. **Automatic links are candidates.** Only review confirms them.
4. **GUI labels are not terminology.** They are copied exactly, per application
   version, and never chosen.
5. **No definitions from restricted sources.** `sense_note` is written by this project.

## Tables

| Table | Holds | Filled by |
|---|---|---|
| `source` | Each loaded source, its address and licence | Loader |
| `entry` | One concept as one source records it | Loader |
| `term` | A term in a language, with type, status and reliability | Loader |
| `concept` | The project's unit of meaning | Automatic candidates, then review |
| `concept_entry` | Which entries express a concept, by what method | Automatic candidates, then review |
| `preferred_term` | The chosen term per concept and language | Review |
| `gui_label` | Exact software labels per version and context, indexed in both directions | Loader |

`candidate_term` is a view listing usable terms for each concept.

## Sources loaded

Counts from the build of 2026-11-12.

| Source | Licence | Entries | Concepts reached | Linked by |
|---|---|---:|---:|---|
| ISO/TC 211 MLGT | none stated; term equivalents only | 1,633 | 1,248 | English |
| IATE (GIS selection) | not copyright protected; credit | 533 | 488 | English |
| SNORRE (Standard Norge) | CC BY 4.0; credit Standard Norge | 50,616 | 39,292 | English |
| LÍSA glossary | none stated; term pairs only | 7,365 | 7,004 | English |
| Geonorge metadata code lists | none stated; names and codes only | 272 | 259 | English |
| GEMET (EEA) | CC BY 4.0 | 5,609 | 5,570 | English; Icelandic pivot |
| CORINE Land Cover nomenclature (NIBIO) | NLOD 1.0 (dataset legend) | 64 | 63 | English; keyed by CLC code |
| ISLEX (is → da nb nn sv fo fi) | CC BY-SA 4.0 | 80,489 | 910 | Icelandic |
| Icelandic-French dictionary | CC BY-SA 4.0 | 51,094 | 916 | Icelandic |
| Icelandic-Polish dictionary | CC BY-SA 4.0 | 57,876 | 1,036 | Icelandic |
| English-Icelandic glossary 21.09 | CC BY 4.0 | 113,566 | 11,205 | English, attach-only |

Totals (build of 2026-11-13): 47,439 concepts, of which 6,098 ambiguous. Most dictionary entries reach no concept:
they are general vocabulary, kept for later linking.

## Linking

Two automatic methods, both recorded in `concept_entry.method`; both give candidates.

- **`english-exact`:** entries sharing a current English term (normalised) are grouped with
  union-find. A group is marked ambiguous when one source has several entries in it, since
  that source distinguishes senses the English word merges.
- **`icelandic-pivot`:** the Árni Magnússon dictionaries have no English. A dictionary sense
  attaches to a concept that holds the same Icelandic term (from LÍSA or GEMET, both curated per concept). A headword with one
  sense links directly; with several senses (counted across homograph entries), only a sense
  whose Icelandic gloss is itself a term of the concept links (*kort*, gloss *landakort* →
  map). Otherwise nothing links: *lag* is layer, song and manner, and linking all senses put
  *melodi* under *layer*. A concept that still receives several senses from one dictionary is
  marked ambiguous.

**Attach-only sources** join concepts that other sources start but never start one, so
general vocabulary does not become concepts: the English-Icelandic glossary 21.09 has 113,000
English items and would otherwise triple the concept count. Its pairs were accepted when
valid in any context, so one English word carries several senses (*layer*: lag, varphæna);
pairs scoring under 0.05 are dropped and the best-scored Icelandic term is preferred. It is
not used as the Icelandic pivot, which stays on LÍSA terms.

Ambiguous concepts serve keyword search (all their terms are tried) but not concept vectors.

## How a translation uses it

1. Route each segment: only source-language text goes to the model.
2. Protect code, file names and icon names.
3. Match GUI labels against `gui_label` and copy them exactly.
4. Find concepts in the segment and supply their target terms to the model.
5. Restore protected text and check that it all survived.

## GUI label sources

QGIS labels come from a pinned commit, recorded in
`published/qgis-gui/commit.txt`. The catalogues have no Greek, Slovenian or Nynorsk.
Numerus forms, unfinished strings, markup and strings over 120 characters are left out.

One label can have several translations, because QGIS uses the same English string in
different contexts: *Buffer* is also a text-halo setting in map labelling. Use the
`context` column to choose, and do not treat a label match as a term decision.

## Known limits

- Linking is exact English match, or Icelandic match for the Árni Magnússon dictionaries;
  sources sharing neither language with a concept do not connect.
- SNORRE is general standards vocabulary and makes up most concepts; only a small part is
  GIS.
- `reliability` values are not comparable between sources.
- Review decisions need a versioned store outside the rebuilt database. This is not
  built yet.
