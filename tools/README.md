# Tools

Run from any directory.

| Script | Purpose |
|---|---|
| `check_registry.py` | Validates the registry and that published and open folders have attribution |
| `fetch_restricted.sh [--force]` | Collects restricted documents from their original sources |
| `publish_mlgt.sh` | Fetches the sources, then regenerates `published/iso-mlgt/` |
| `extract_mlgt.py` | Extracts MLGT terms to CSV; called by `publish_mlgt.sh` |
| `score_translation.py` | Counts terminology traps in machine translations against a reference |
| `build_glossary.py` | Builds `build/glossary.sqlite` from the published term lists |
| `export_lexicon.py [OUTPUT] [--holdout CORPUS]` | Exports the search lexicon; `--holdout` leaves out the regulation names of the INSPIRE feature types the acceptance test uses |
| `extract_qgis_gui.py [COMMIT]` | Publishes QGIS interface labels from a pinned commit |
| `assisted_translate.py` | Translates a text with Ollama, routed or with labels and terms |
| `extract_lisa.py` | Extracts LÍSA Icelandic-English term pairs |
| `extract_iate.py` | Selects GIS-related terms from the stored IATE export |
| `extract_qgis_headings.py` | Aligns QGIS manual headings across languages |
| `extract_geonorge.py codelists\|resources` | Publishes Geonorge metadata code lists (nb/en) or Geonorge application strings from pinned commits |
| `extract_gemet.py PATH` | Publishes GEMET labels for the target languages from `gemet.rdf.gz` (7.4 MB, CC BY 4.0) |
| `extract_inspire_reg.py pdf\|cellar` | Official INSPIRE names keyed by technical name: Bokmål and Icelandic from EEA Supplement PDFs, EU languages from the Cellar API (run on Actions) |
| `extract_int1.py` | Extracts the symbol rows of Kartverket's INT 1 (restricted copy) by position and font; output kept out of git; needs pdfplumber |
| `extract_arnastofnun.py` | Downloads and flattens the Árni Magnússon dictionaries from CLARIN-IS; run on GitHub Actions (about 43 MB download) |

`extract_mlgt.py` needs PyYAML (see `requirements.txt`). The project model is
written with the discovery-driven-dev `model.py`.
