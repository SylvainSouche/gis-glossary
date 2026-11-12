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
| `export_lexicon.py [OUTPUT]` | Exports the search lexicon from the build, for the acceptance test and search plugins |
| `extract_qgis_gui.py [COMMIT]` | Publishes QGIS interface labels from a pinned commit |
| `assisted_translate.py` | Translates a text with Ollama, routed or with labels and terms |
| `extract_lisa.py` | Extracts LÍSA Icelandic-English term pairs |
| `extract_iate.py` | Selects GIS-related terms from the stored IATE export |
| `extract_qgis_headings.py` | Aligns QGIS manual headings across languages |
| `extract_geonorge.py codelists\|resources` | Publishes Geonorge metadata code lists (nb/en) or Geonorge application strings from pinned commits |
| `extract_arnastofnun.py` | Downloads and flattens the Árni Magnússon dictionaries from CLARIN-IS; run on GitHub Actions (about 43 MB download) |

`extract_mlgt.py` needs PyYAML (see `requirements.txt`). The project model is
written with the discovery-driven-dev `model.py`.
