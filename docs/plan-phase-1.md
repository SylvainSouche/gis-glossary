# Phase one plan

Goal: a GIS glossary in the 15 languages listed in the README, with Norwegian
in both written standards (Bokmål and Nynorsk), so 16 sets of terms. Nynorsk is
not derived from Bokmål: each needs its own source or review.

## 1. Audit the sources

Work through `registry/sources.csv` by `priority`, inspecting the actual files
rather than the project pages. Fill in the audit columns, then read across the
`lang_*` columns to see which languages have no real source.

| Priority | Sources |
|---|---|
| 1 | ISO/TC 211 MLGT (Geolexica, TMG) |
| 2 | GEMET |
| 3 | INSPIRE Registry, EU Vocabularies |
| 4 | GRASS GIS TBX glossary |
| 5 | CEOS EO Glossary |
| 6 | QGIS translation catalogues and documentation |
| 7 | GDAL, PROJ, PostGIS |
| 8 | EuroVoc |
| 9 | National mapping agencies and standards bodies |
| 10 | Esri documentation |

Points to settle during the audit:

- ISO MLGT: term equivalents may be used; its definitions stay out of versioned
  files.
- Nynorsk: no source found so far. National sources must supply it.
- Greek and Slovenian: no QGIS catalogue, so GIS-specific terms need other
  sources.

## 2. Define the data model

Proposed, not yet decided: SQLite keyed by concept id, with per-language terms,
definitions, synonyms, provenance, licence and validation status; TBX for
interchange only.

## 3. Harvest and reconcile

Import audited sources, link their entries to shared concepts, and separate
senses. Wikipedia and Wiktionary correspondences, especially interlanguage
links, are candidates only: they can join different senses or scopes, so each
needs confirmation from another source or human review. The QGIS manual headings in `published/qgis-manual-headings/` are raw candidates: many
are section titles such as "Getting Started", not terms.

## 4. Fill gaps and review

Measure coverage per language and concept. Machine translation may only propose
a term for a gap, must be marked as such, and needs human review.

## 5. Publish

Release the glossary under a Creative Commons licence, still to be chosen, with
per-row provenance and a TBX export.
