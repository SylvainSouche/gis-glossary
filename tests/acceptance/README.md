# Search acceptance test

Answers one question: can an English search find GIS records written in another language,
well enough for the QGIS search plugins? Run it from the Actions tab (**Search acceptance
test**); it takes about an hour on a GitHub runner.

| File | Content |
|---|---|
| `acceptance.py` | The test: fetches records, embeds them, scores four methods |
| `corpus.tsv` | INSPIRE feature concepts in the EU languages, English name as query |
| `themes_no.tsv` | The 18 Geonorge national themes, Norwegian name and English name |
| `lexicon.tsv.xz` | Not in git: exported by `tools/export_lexicon.py` from the glossary build |

Records come live from Geonorge (Norway) and the LMI catalogue (Iceland). Pass marks and
results are in [docs/evaluations/embedding-tests.md](../../docs/evaluations/embedding-tests.md):
a language is **usable** when recall in the top 10 is at least 0.70 and at least 0.85 of
BGE-M3's; anything else is **not usable**.
