# gis-glossary

A multilingual glossary of GIS, geography and earth-science terms, built from audited
sources, with the origin and licence of every term recorded.

**What it is for:** search and translation inside a GIS, mainly QGIS.

- **Search across languages.** A user types an English query and finds layers, datasets and
  metadata written in Icelandic, Norwegian, Polish or French, and the reverse. The QGIS
  plugins this targets run a small static embedding model with no server; the glossary
  supplies the technical vocabulary those models lack, as keywords and as concept vectors.
- **Assisted translation.** Layer descriptions and documentation translated by a model,
  with the glossary supplying consistent, correct technical terms and exact QGIS interface
  labels.

## Languages

| Tier | Languages |
|---|---|
| 1 | English, French, Spanish, German, Italian |
| 2 | Norwegian (Bokmål and Nynorsk, held separately), Icelandic, Danish, Polish, Slovenian |
| 3 | Greek, Romanian, Bulgarian, Slovak, Swedish |

## Where it stands

- **Sources:** 84 sources audited ([registry](registry/sources.csv)); eleven loaded into the
  public glossary build (twelve with LÍSA), which links them into about 48,000 concepts by
  English term, by Icelandic term for the Icelandic dictionaries, and by code where a source
  has one ([data model](docs/data-model.md)).
- **Search test:** an [acceptance test](tests/acceptance/README.md) asks whether an English
  query finds records in another language well enough to be usable. On real Norwegian
  catalogue records (Geonorge) the answer is yes; on the EU languages, measured on INSPIRE
  concepts, not yet ([results](docs/evaluations/embedding-tests.md)).
- **Next:** review of automatic concept links, a glossary built from real layer metadata and
  field names, and a Hugging Face dataset.

## Sources and licences

The glossary keeps term equivalents with their sense, never definitions or running text
from a source unless its licence allows it. Each folder in [`published/`](published/README.md)
has an `ATTRIBUTION.md`.

| Source | Languages | Licence |
|---|---|---|
| SNORRE word list, Standard Norge (Språkbanken) | nb, nn, en, fr, de | CC BY 4.0 |
| INSPIRE Regulation (EU) 1089/2010, official names | 13 EU languages, nb, is | EU legal text, reuse with acknowledgement |
| GEMET, European Environment Agency | 15 of the 16 (no Nynorsk) | CC BY 4.0 |
| IATE, European Union (GIS selection) | EU languages | reuse allowed, with acknowledgement |
| CORINE Land Cover nomenclature, NIBIO | nb, en | NLOD 1.0 (dataset legend) |
| ISO/TC 211 Multi-Lingual Glossary of Terms | en and 6 others | © ISO/TC 211; term equivalents only |
| ISLEX, Icelandic-French and Icelandic-Polish dictionaries, Árni Magnússon Institute | is, da, nb, nn, sv, fo, fi, fr, pl | CC BY-SA 4.0 |
| English-Icelandic glossary 21.09, Árni Magnússon Institute | en, is | CC BY 4.0 |
| Geonorge metadata code lists and application strings, Kartverket | nb, en | code lists: to confirm; strings: MIT |
| QGIS interface labels | 12 languages | GPL-2.0 |
| **LÍSA word list (Orðalisti LÍSU)** | is, en | **held back: licence asked, see [published/lisa/](published/lisa/README.md)** |

What shipping the glossary in another product requires is set out in
[docs/licensing.md](docs/licensing.md).

## Repository layout

| Folder | Content |
|---|---|
| [`registry/`](registry/README.md) | What we know about each source: audit, licence, coverage |
| [`sources/`](sources/README.md) | Source files we may redistribute; restricted ones are fetched, not stored |
| [`published/`](published/README.md) | Term lists generated from the sources, with attribution |
| `schema/` | SQLite schema of the glossary |
| [`tools/`](tools/README.md) | Scripts that fetch, extract, build and export |
| [`tests/acceptance/`](tests/acceptance/README.md) | The search acceptance test |
| [`docs/`](docs/README.md) | Data model, licensing, audits and evaluations |
| `project-model/` | Requirements, observations and decisions, written by a script |

## Running it

```bash
pip install -r requirements.txt
python3 tools/check_registry.py      # validate the registry and attributions
python3 tools/build_glossary.py      # build build/glossary.sqlite (about 5 minutes)
python3 tools/export_lexicon.py      # export the search lexicon
```

The search acceptance test and the translation trial run on GitHub Actions
(**Search acceptance test** and **Translate**, from the Actions tab).

## Licence

The code is under the [MIT licence](LICENSE). Data keeps the licence of its source, stated
in each folder's `ATTRIBUTION.md`; a release that includes the Árni Magnússon Institute
dictionaries is CC BY-SA 4.0.

## Contact

Maintained by [SylvainSouche](https://github.com/SylvainSouche). Corrections, missing terms
and source suggestions are welcome as issues.
