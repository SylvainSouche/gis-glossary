# Embedding tests

**Goal:** English queries must find dataset sheets and metadata written in other
languages. The plugin has no model at query time: it adds up stored vectors from a
static model (`minishlab/potion-multilingual-128M`) and from the glossary.

Each test states its expected result before it runs, so a result can confirm or
contradict it. All tests run on GitHub, so they use none of the project owner's data.

Tests 1 to 3 ran on short-lived branches (`test/embeddings`, `test/lookup`,
`test/acceptance-fast` and others), removed when the repository was organised for
publication; their runs and logs stay in the Actions history under the run numbers cited
below. The search acceptance test now lives in [`tests/acceptance/`](../../tests/acceptance/README.md)
and runs from the Actions tab.

## Test 1: term alignment (`test/embeddings`)

**Question:** do an English term and its translation land close together?

**Data:** 16,496 pairs: glossary terms in 12 languages, QGIS labels in 12 languages
(the only Icelandic source), and SNORRE terms for Bokmål and Nynorsk.

**Measures:** cosine of true pairs against random pairs; R@1 and R@5, the share whose
true translation ranks first or in the top 5 among all translations in the same set.
Chance for R@1 is 1/n.

**Expected:**

| Expectation | Meaning if wrong |
|---|---|
| True pairs above random pairs in every language, for both models | The model does not share a space across languages |
| potion R@1 well above chance, highest in French, Spanish, German | potion cannot carry cross-language search alone |
| potion lowest in Icelandic, Nynorsk, Greek, Bulgarian | A weak language performs better than assumed |
| BGE-M3 on whole terms beats potion in every language | A custom distilled vocabulary would not help |
| GIS-specific SNORRE pairs align worse than general pairs | Technical vocabulary is not the weak point |

**Decision rule:** a language where potion R@5 is under 0.5 needs glossary vectors or a
learned alignment.

## Test 2: lookup (`test/lookup`)

**Question:** does adding glossary vectors help English queries find the right document?

**Data:** 346 INSPIRE feature concepts in 12 languages. Query: the English concept name.
Documents: the definitions in one language. The glossary sources (MLGT, IATE, QGIS) do not
include INSPIRE, so the test is not circular.

**Methods:** plain potion; potion plus glossary concept vectors; potion plus glossary and
GUI-label vectors; BGE-M3 as an upper bound that the plugin cannot use.

**Measures:** R@1, R@10, MRR; share of documents and queries containing at least one
glossary concept.

**Expected:**

| Expectation | Meaning if wrong |
|---|---|
| Plain potion R@10 above 0.3 in French, Spanish, German | The task or the definitions are harder than assumed |
| Glossary vectors raise MRR in most languages | Composition as designed does not help |
| The gain is largest where potion is weakest | Glossary help is not targeted where needed |
| Adding GUI labels helps less than the glossary, or hurts | Generic labels add noise; keep them out of document vectors |
| BGE-M3 stays above all potion variants | Results of the potion variants are suspect |
| Under half of the documents contain a glossary concept in small languages | Coverage is better than assumed |

**Decision rule:** keep a composition method if it raises MRR in at least two thirds of
languages and lowers it in none by more than 0.02.

## Known limits

- Queries are concept names, shorter and cleaner than real user queries.
- INSPIRE has no Icelandic or Norwegian definitions; those need other documents, such as
  Geonorge metadata.
- The glossary is unreviewed, so some concept vectors merge wrong senses.
- One weight (1.0) is tested for composition.

## Embedding database for INSPIRE documents (`build/inspire-embeddings`)

Built on GitHub from the INSPIRE registers (themes, feature concepts, code lists, glossary)
in every language they offer. Output `inspire_embeddings.sqlite`:

| Table | Content |
|---|---|
| `document` | One register item in one language: register, item id, language, label, text |
| `vector` | One vector per document and method: `potion` and `potion+glossary`, float32 |
| `concept_vector` | The glossary concept vectors, for query composition in the plugin |
| `meta` | Model, lexicon, sources and build date |

Only entries whose label is in the requested language are kept, because INSPIRE falls back
to English for untranslated items.

## Results, first runs (2026-11-10)

Raw tables: `build/mt_runs/alignment_results.md` and `build/mt_runs/lookup_results.md`.

**Test 1, alignment.** Confirmed: true pairs above random in every language; BGE-M3 on whole
terms beats potion everywhere (R@1 about 0.6 to 0.9 against 0.2 to 0.8). Weakest for potion:
Icelandic GUI labels (R@1 0.23, R@5 0.38), Greek glossary terms (0.35, 0.49), Nynorsk
general terms (0.38, 0.57). Contradicted: SNORRE GIS terms aligned better than general terms
(R@1 0.53 against 0.44), though the GIS set is ten times smaller. By the decision rule,
Icelandic and Greek need help.

**Test 2, lookup.** Plain potion R@10 is 0.39 to 0.55; BGE-M3 is 0.52 to 0.63. Adding
glossary concept vectors **lowered** MRR in most languages where documents contain concepts
(Spanish 0.301 to 0.264, French 0.262 to 0.230) and changed little where they contain none
(Slovak, Slovenian, Romanian: 0 to 1 %). GUI labels lowered it further. The composition as
designed fails its decision rule.

Likely cause: concept vectors are averages of potion term vectors, so they inherit potion's
weakness and pull documents towards generic term meaning. Next to test: concept vectors
from a stronger model brought into potion's space (custom distillation or a learned
alignment), a lower weight, and glossary coverage for the small languages.

## Results, lookup fixes (2026-11-10)

Raw table: `build/mt_runs/lookup2_results.md`. Glossary as before SNORRE and LÍSA were loaded.

| Method | Languages improved over plain potion (MRR) | Range of change |
|---|---:|---|
| potion concepts, weight 0.3 | 12 of 12 | +0.004 to +0.026 |
| **mapped concepts, weight 0.3** | **12 of 12** | **+0.002 to +0.034** |
| mapped concepts, weight 1 | 4 of 12 | -0.038 to +0.026 |
| rotation 0.5 | 10 of 12 | -0.011 to +0.017 |
| rotation 1 | 3 of 12 | -0.131 to +0.015 |

- Both concept methods at weight 0.3 pass the decision rule: no language falls. The weight,
  not the idea, was the problem in the first run.
- Concept vectors from BGE-M3 mapped into potion's space are best in 8 of 12 languages, but
  only slightly ahead of plain potion concepts.
- The per-language rotation does not help with these pair counts and harms Slovenian (57
  pairs) and Greek (259) badly; it is dropped.
- Gains are small next to the gap with BGE-M3 (about 0.1 MRR), and limited by low glossary
  coverage in the small languages.

Next: rerun with the glossary that includes SNORRE and LÍSA, tune the weight around 0.3, and
rebuild the INSPIRE database with the chosen method.

## Acceptance test: is it usable?

**Purpose:** decide whether the plugin's search (potion plus glossary concept vectors) is good
enough to ship, per language, rather than compare methods.

**Scenario:** a user types an English search; the plugin must show the right dataset among
the first 10 results, from records written in other languages.

**Data:** real metadata records from national catalogues, each with a title or abstract in
the national language and an English title or keywords written by the publisher:

| Languages | Catalogue |
|---|---|
| Bokmål, Nynorsk | Geonorge |
| Icelandic | Landmælingar Íslands (gatt.lmi.is) |
| EU languages | INSPIRE geoportal records, plus the INSPIRE registry as now |

Queries are the publisher's English titles or keywords; documents are the national-language
title and abstract, with English text removed. Records used to build or tune the glossary
are excluded.

**Measures per language:** R@10, the share of English queries whose record is in the top 10;
and the ratio to BGE-M3 on the same data, which shows how much the static model loses.

**Pass marks (decided 2026-11-10, `dec-acceptance-two-verdicts`):** two verdicts only. A
middle grade such as "usable with care" counts as not usable.

| Verdict | Condition |
|---|---|
| Usable | R@10 at least 0.70 **and** ratio to BGE-M3 at least 0.85 |
| Not usable | anything else |

**Current indication, INSPIRE concepts only:** potion with concepts reaches R@10 of about 0.40
to 0.55 and an MRR ratio to BGE-M3 of about 0.65 to 0.85. By these marks every
language would be "not usable". That data is harsher than real search (one
short name against 346 similar definitions), so the real-metadata run decides.

**If a language fails:** add glossary coverage for it, raise the composition weight within
the tested range, or compute BGE-M3 vectors on GitHub and accept that the plugin then needs a
query model.

## Results, vector database build with SNORRE and LÍSA (2026-11-10)

Vocabulary database: 40,585 concepts, 150,564 terms (125,055 distinct, embedded with BGE-M3 in
about an hour on GitHub). INSPIRE database: 9,238 documents, 2,060 containing a concept.
Artifacts: 58 MB, run 42779427380.

Lookup MRR at weight 0.3 improved in 8 of 12 languages and fell slightly in Polish and Swedish
(at most 0.003): it passes the decision rule, but by a narrow margin. Gains are smaller than with
the earlier glossary: French reached 0.268 here against 0.296 before. SNORRE's general
vocabulary dominates the concept set and the BGE-to-potion map, which likely dilutes the GIS
concepts. Next to test: restrict composition to GIS-relevant concepts, or train the map on GIS
terms only.

## Results, first acceptance run (2026-11-10)

Run 42803162435 (branch `test/acceptance-fast`: BGE-M3 capped at 256 tokens). Method: potion
plus glossary concepts at weight 0.3.

| Language | Data | n | potion R@10 | + concepts | BGE-M3 | Ratio | Verdict |
|---|---|---:|---:|---:|---:|---:|---|
| bg | INSPIRE concepts | 346 | 0.46 | 0.47 | 0.62 | 0.75 | not usable |
| da | INSPIRE concepts | 346 | 0.49 | 0.50 | 0.61 | 0.82 | not usable |
| de | INSPIRE concepts | 346 | 0.47 | 0.49 | 0.58 | 0.84 | not usable |
| el | INSPIRE concepts | 346 | 0.40 | 0.42 | 0.52 | 0.80 | not usable |
| es | INSPIRE concepts | 346 | 0.55 | 0.56 | 0.63 | 0.88 | not usable |
| fr | INSPIRE concepts | 346 | 0.48 | 0.51 | 0.61 | 0.83 | not usable |
| it | INSPIRE concepts | 346 | 0.49 | 0.51 | 0.63 | 0.81 | not usable |
| pl | INSPIRE concepts | 346 | 0.45 | 0.46 | 0.57 | 0.81 | not usable |
| ro | INSPIRE concepts | 346 | 0.52 | 0.54 | 0.61 | 0.88 | not usable |
| sk | INSPIRE concepts | 346 | 0.39 | 0.40 | 0.60 | 0.66 | not usable |
| sl | INSPIRE concepts | 346 | 0.39 | 0.41 | 0.58 | 0.71 | not usable |
| sv | INSPIRE concepts | 346 | 0.48 | 0.50 | 0.62 | 0.81 | not usable |
| nb | Geonorge records | 40 | 0.90 | 0.95 | 0.97 | 0.97 | usable |
| is | LMI, English title | 12 | 1.00 | 1.00 | 1.00 | 1.00 | usable (sample too small) |

Icelandic theme search (English INSPIRE theme name against 240 Icelandic records, 3 themes):
P@10 0.00 for both potion methods, 0.11 for BGE-M3.

**Reading:**

- By the two-verdict rule, no EU language passes on INSPIRE concepts: the best R@10 is 0.56
  (Spanish), far from 0.70. Only Bokmål passes, on real records.
- The verdict for real search is not yet settled. Real records are far easier than INSPIRE concepts: Bokmål
  goes from about 0.5 to 0.95. INSPIRE remains a worst case, not the real scenario.
- The real-record samples are too small. Only 40 Geonorge records passed the filters out of
  2,400 requested, most fetches timed out, and none were Nynorsk. Icelandic has 12 records with
  an English title.
- Glossary concepts add 0.01 to 0.05 R@10 everywhere and never hurt. The ratio to BGE-M3 is the
  binding limit for Slovak (0.66) and Slovenian (0.71).
- Bare theme names fail in Icelandic for potion. One-word queries against long Icelandic
  abstracts are where the static model is weakest.

**Next:** collect real records once (Geonorge with slow polite fetching, LMI, EU geoportal for
the EU languages), store them as a fixed test set, and rerun the verdicts on hundreds of real
records per language.

## Results, hybrid keyword method (2026-11-10)

Run 42838437853. Hybrid = potion + concepts plus a keyword boost, as in Semantic Plugin Search:
English query terms translated through the glossary (ambiguous concepts included), matched by
prefix in the title (+0.20) and body (+0.05). The lexicon used earlier had left out all 5,789
ambiguous concepts, which hold the core words (building, road, river, elevation, contour line).

| Language | Data | n | potion | + concepts | hybrid | BGE-M3 | Ratio | Verdict |
|---|---|---:|---:|---:|---:|---:|---:|---|
| bg | INSPIRE concepts | 346 | 0.46 | 0.47 | 0.46 | 0.62 | 0.75 | not usable |
| da | INSPIRE concepts | 346 | 0.49 | 0.50 | 0.51 | 0.61 | 0.84 | not usable |
| de | INSPIRE concepts | 346 | 0.47 | 0.49 | 0.52 | 0.58 | 0.89 | not usable |
| el | INSPIRE concepts | 346 | 0.40 | 0.42 | 0.42 | 0.52 | 0.81 | not usable |
| es | INSPIRE concepts | 346 | 0.55 | 0.56 | 0.57 | 0.63 | 0.90 | not usable |
| fr | INSPIRE concepts | 346 | 0.48 | 0.51 | 0.55 | 0.61 | 0.89 | not usable |
| it | INSPIRE concepts | 346 | 0.49 | 0.51 | 0.52 | 0.63 | 0.83 | not usable |
| pl | INSPIRE concepts | 346 | 0.45 | 0.46 | 0.47 | 0.57 | 0.83 | not usable |
| ro | INSPIRE concepts | 346 | 0.52 | 0.54 | 0.55 | 0.61 | 0.90 | not usable |
| sk | INSPIRE concepts | 346 | 0.39 | 0.40 | 0.41 | 0.60 | 0.68 | not usable |
| sl | INSPIRE concepts | 346 | 0.39 | 0.41 | 0.41 | 0.58 | 0.71 | not usable |
| sv | INSPIRE concepts | 346 | 0.48 | 0.50 | 0.52 | 0.62 | 0.85 | not usable |
| nb | Geonorge records | 40 | 0.95 | 0.95 | 0.95 | 1.00 | 0.95 | usable |
| is | LMI, English title | 12 | 1.00 | 1.00 | 1.00 | 1.00 | 1.00 | usable (sample too small) |

Icelandic theme search, P@10: potion 0.00, + concepts 0.00, **hybrid 0.11**, BGE-M3 0.11.

**Reading:**

- The keyword part helps where the glossary has the words: French +0.04, German +0.03, and the
  Icelandic theme search rises to BGE-M3's level. It never costs more than 0.01.
- INSPIRE concepts barely exercise it: the documents are definitions with no title, so only
  the body boost (+0.05) applies, and definitions rarely repeat the concept's own term.
- Geonorge: of 724 records fetched, 679 had no English title. Bilingual records are about 6 %
  of the catalogue, so a real test set needs the whole catalogue harvested, or another kind of
  ground truth such as keyword themes.
- Conclusion: the glossary as built (standards and general vocabulary) is too thin on the
  words of real metadata. Next is a glossary harvested from layer metadata and field names.

## Results, Norwegian theme search and larger Bokmål sample (2026-11-12)

Runs 43193920807 and the rerun after it (branch `test/acceptance-fast`). The Geonorge search API
returns title, abstract and theme for every dataset, so the whole catalogue is used.

**Known-item search, Bokmål records with an English title** (R@10):

| Run | n | potion | + concepts | hybrid | BGE-M3 | Ratio | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 43193920807 | 223 | 0.83 | 0.82 | 0.88 | 0.92 | 0.96 | usable |
| rerun | 140 | 0.84 | 0.86 | 0.90 | 0.94 | 0.96 | usable |

**Theme search:** the 18 English national theme names (Geonorge metadata code list) against 2,127
datasets (2,109 Bokmål, 18 Nynorsk); answer key = the theme the publisher set; precision in the
top 10.

| Method | P@10 | Ratio to BGE-M3 |
|---|---:|---:|
| potion | 0.42 | 0.74 |
| potion + concepts | 0.48 | 0.85 |
| hybrid | 0.53 | 0.93 |
| BGE-M3 | 0.57 | 1.00 |

Per theme, the hybrid fails on Elevation (0.0), Demography (0.1), Crisis management (0.1) and
Outdoor activities (0.0), and reaches 0.9 to 1.0 on Base maps, Nature, Cultural heritage and
Planning.

**Reading:**

- Bokmål known-item search is usable on real records, confirmed on two samples. The keyword
  part adds 0.04 to 0.06 R@10 there.
- Theme search is hard for every method: even BGE-M3 reaches 0.57, because a theme is broad and
  publishers set it with some freedom. The hybrid keeps 93 % of BGE-M3, and glossary concepts and
  keywords together add 0.11 over plain potion.
- The failing themes are those whose Norwegian name is a different word: Elevation/Høydedata,
  Demography/Befolkning, Crisis management/Samfunnssikkerhet. The run used the lexicon from before
  the Geonorge code lists were harvested; those pairs are now in the glossary. A rerun with them
  will be partly circular (query and answer key come from the same code list), so it would show
  what the plugin gains from carrying that list, not general vocabulary quality.

## Results, with the Geonorge code lists in the lexicon (2026-11-12)

Run 43213264433 (branch `test/acceptance-fast`, commit 299446c): same test, lexicon regenerated
after the Geonorge metadata code lists and application strings were added to the glossary.

**Known-item search** (R@10): Bokmål 208 records — potion 0.78, + concepts 0.77, hybrid 0.83,
BGE-M3 0.89, ratio 0.93, **usable** (third sample in a row). INSPIRE concepts in the EU languages
are unchanged: none passes (best Spanish 0.57, French 0.56).

**Theme search**, 2,047 datasets (2,029 Bokmål, 18 Nynorsk):

| Method | P@10 | Ratio to BGE-M3 | Previous run |
|---|---:|---:|---:|
| potion | 0.42 | 0.74 | 0.42 |
| potion + concepts | 0.45 | 0.79 | 0.48 |
| hybrid | 0.59 | 1.03 | 0.53 |
| BGE-M3 | 0.57 | 1.00 | 0.57 |

Hybrid per theme, before → after: Demography 0.1 → 0.8, Outdoor activities 0.0 → 0.8,
Pollution → 0.6, Elevation 0.0 → 0.3, Crisis management 0.1 → 0.3. Weakest now: Elevation and
Crisis management (0.3), Aerial photography (0.3).

**Reading:**

- The hybrid now matches BGE-M3 on theme search (0.59 against 0.57). The gain comes from the
  keyword part: concept vectors alone did not improve.
- The gain is partly circular: the English queries and the answer key come from the same
  Geonorge code list whose Norwegian names are now in the lexicon. It shows what the plugin gains
  from carrying the publisher's own code lists, which is the code-as-key approach, not general
  vocabulary quality.
- The catalogue sample differs between runs (2,127 then 2,047 datasets), so per-theme numbers move
  a little for every method; Base maps fell for potion itself, which does not use the lexicon.

## Results, with the Árni Magnússon dictionaries (2026-11-12)

Run 43254602987: lexicon regenerated after the ISLEX, Icelandic-French and Icelandic-Polish
dictionaries were linked to LÍSA concepts through Icelandic (Danish 416 → 1,290 concepts,
Swedish 823 → 1,661, Polish 245 → 1,253). The English-Icelandic glossary 21.09 was loaded
after this run and is not in it.

**Known-item search** (hybrid R@10, previous run in brackets):

| Language | hybrid | BGE-M3 | Ratio | Verdict |
|---|---:|---:|---:|---|
| da | 0.51 (0.51) | 0.61 | 0.83 | not usable |
| sv | 0.51 (0.52) | 0.62 | 0.84 | not usable |
| pl | 0.46 (0.47) | 0.57 | 0.80 | not usable |
| fr | 0.55 (0.56) | 0.61 | 0.90 | not usable |
| nb | 0.89 (0.83) | 0.93 | 0.96 | usable |

Norwegian theme search is unchanged: hybrid 0.59, BGE-M3 0.57.

**Reading:**

- The new Danish, Swedish and Polish terms do not move the INSPIRE test. Its 346 concepts are
  feature types (*Hydrographic network*, *Administrative unit*) whose names are mostly
  multi-word phrases; the dictionaries add single general words, linked through LÍSA's GIS
  vocabulary. The test measures the hard end of the problem, and the dictionaries do not
  reach it.
- The Bokmål rise (0.83 → 0.89) comes with a different sample of 208 records and is within
  the spread seen across samples (0.83 to 0.90); Bokmål stays usable.
- The EU languages remain not usable on INSPIRE concepts; a test on real catalogue records in
  those languages, as for Norwegian, is still missing.

## Results, public build without LÍSA (2026-11-12)

Run 43271325425, the first from `main`: the glossary is built on the runner from the public
repository, so without LÍSA (held back, see `published/lisa/`) and with the English-Icelandic
glossary 21.09. 40,891 concepts; with no LÍSA terms the Icelandic pivot links nothing, so the
Árni Magnússon dictionaries add no Danish, Swedish or Polish terms here.

| Test | Without LÍSA, with 21.09 | With LÍSA, without 21.09 (run 43254602987) | BGE-M3 |
|---|---:|---:|---:|
| Icelandic theme search, hybrid P@10 | **0.28** | 0.11 | 0.11 |
| Icelandic theme search, + concepts P@10 | 0.17 | 0.00 | |
| Norwegian theme search, hybrid P@10 | 0.58 | 0.59 | 0.57 |
| Bokmål known-item, hybrid R@10 | 0.89 (151 records) | 0.89 (208) | 0.95 |
| Danish / Swedish / Polish, hybrid R@10 | 0.50 / 0.52 / 0.47 | 0.51 / 0.51 / 0.46 | |

**Reading:**

- The public build works end to end on a fresh checkout, and its verdicts match the full
  build: Bokmål usable, EU languages on INSPIRE concepts not usable.
- On Icelandic themes the general English-Icelandic glossary does better than LÍSA alone
  (0.28 against 0.11, above BGE-M3), because the theme names are common words (*geology*,
  *elevation*, *transport*) it covers and LÍSA words differently. The sample is small: three
  themes, 14 tagged records out of 240. Both together have not been tested yet.
- Danish, Swedish and Polish are unchanged with or without the dictionaries' terms, which
  confirms that the INSPIRE test does not reach them.

## Results, with GEMET (2026-11-13)

Run 43415579509 on `main` (commit 5bdbb97): public build, so without LÍSA, now with GEMET
(15 languages) and the Norwegian CORINE nomenclature. GEMET Icelandic also feeds the Icelandic
pivot, which now links 3,372 dictionary senses without LÍSA.

**INSPIRE concepts, hybrid R@10** (previous public build, run 43271325425, in brackets):

| Language | hybrid | BGE-M3 | Ratio | Ratio ≥ 0.85 |
|---|---:|---:|---:|---|
| de | 0.55 (0.51) | 0.58 | 0.94 | yes |
| es | 0.59 (0.58) | 0.63 | 0.94 | yes |
| fr | 0.57 (0.54) | 0.61 | 0.93 | yes |
| ro | 0.55 (0.54) | 0.61 | 0.91 | yes |
| sv | 0.54 (0.52) | 0.62 | 0.88 | yes |
| it | 0.55 (0.52) | 0.63 | 0.87 | yes |
| el | 0.45 (0.42) | 0.52 | 0.86 | yes |
| da | 0.52 (0.50) | 0.61 | 0.85 | yes |
| pl | 0.49 (0.47) | 0.57 | 0.85 | yes |
| bg | 0.49 (0.47) | 0.62 | 0.79 | no |
| sl | 0.43 (0.41) | 0.58 | 0.74 | no |
| sk | 0.40 (0.40) | 0.60 | 0.67 | no |

Bokmål known-item search stays usable (0.89, ratio 0.95); Norwegian theme search 0.58
(unchanged); Icelandic theme search 0.28 (unchanged).

**Reading:**

- GEMET is the first source to move the INSPIRE test: every language except Slovak gains 0.01
  to 0.04, and nine of twelve now keep at least 85 % of BGE-M3, the ratio half of the pass mark.
- No language passes, because the other half, R@10 ≥ 0.70, is out of reach on this set for
  every method: BGE-M3 itself scores 0.52 to 0.63. The INSPIRE set (feature-type names against
  their definitions) is harder than real search. Real catalogue records in the EU languages, as
  for Norway, are needed before the verdict for those languages can mean "not usable" rather than
  "not measured on realistic data".
- Slovak (0.67 ratio), Slovenian and Bulgarian remain the weakest; their GEMET labels are present,
  so the gap is in potion's own vocabulary for these languages.
