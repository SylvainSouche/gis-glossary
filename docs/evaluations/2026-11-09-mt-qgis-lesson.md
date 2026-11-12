# Machine translation test: QGIS lesson, French to English

Date: 2026-11-09. Text: QGIS Training Manual lesson 8.4. Reference: the English
original. Scored with `tools/score_translation.py` on 14 terminology traps and 3
defect types.

| Measure | Qwen 4B (`en`) | Hy-MT2 7B (`en_hy`) | Hy-MT2 7B (`mac_hy`) | Hy-MT2 1.8B (`small`) |
|---|---:|---:|---:|---:|
| Wrong GIS terms | 29 | 24 | 27 | 37 |
| Wrong GUI labels | 13 | 4 | 5 | 15 |
| Other defects (French left, prompt leak, shortened name) | 14 | 5 | 5 | 6 |
| Code lines kept, of 8 | 7 | 6 | 6 | 8 |

The mapping of files to models was confirmed by the project owner. Scores are counts
of patterns chosen after reading the outputs, on one text.

## Findings

- All models render *entité* as *entity* (feature), and all confuse hillshade.
- Word-level similarity does not separate the models usefully (0.69 to 0.74).
- Hy-MT2 7B lost two code lines and leaked its prompt twice. These are pipeline
  failures that a glossary cannot fix.
- The two 7B outputs differ, for example *clip* 3/4 against 0/5 (right/wrong), so
  run-to-run variation is a few errors.
- The French source has its own errors, which limit any score: *Masquer* where the
  English says *Unhide*, untranslated English lines, and *Aspect* left as a French
  word, so the *aspect* trap is not tested.

## Non-French source text

The French source keeps some English, reported by the project owner as a cause of
trouble. The outputs support this:

- Both Qwen prompt leaks occur on English-only source lines, and the 7B leak on a
  code-only line. In each case the segment had no French to translate.
- On the mixed line *Check checkbox Dissoudre le résultat*, both 7B runs left the
  French label untranslated.
- Label errors such as *Exécuter* and *Numérisation* occur on fully French text, so
  this is not their cause.

Segments should be routed by language first: only French goes to the model, while
English and code pass through unchanged. Working from the reStructuredText or PO
sources would keep `guilabel` markup, which identifies labels directly.

## Source format

The French source was copied from the rendered HTML page, as reported by the project
owner. It therefore contains artifacts absent from clean text: image alt names such as
`fileSave` and `checkbox`, leftovers such as `:guilabel:` and stray backticks, image
paths, and damaged words such as *résulta t*. The test was harder than a run on clean
input, and scores may overstate some model errors. A rerun should use clean source.

## Assisted runs

Same lesson, through `tools/assisted_translate.py` on the project owner's Mac. Baseline is
the earlier run; "routed" sends only cleaned French; "assisted" adds GUI labels and terms.
The scorer was corrected to accept "Click on Run" and to ignore case in algorithm names,
and all runs were rescored.

| Measure | 7B baseline | 7B routed | 7B assisted | 1.8B baseline | 1.8B routed | 1.8B assisted |
|---|---:|---:|---:|---:|---:|---:|
| Wrong GIS terms | 27 | 29 | **18** | 37 | 37 | **22** |
| Wrong GUI labels | 5 | 3 | **1** | 15 | 17 | **5** |
| Other defects | 5 | 2 | **1** | 6 | 4 | **3** |
| Code lines kept, of 8 | 6 | 8 | **8** | 8 | 8 | **8** |

- Routing fixes prompt leaks and lost code, but does not reduce terminology errors.
- Assistance reduces terminology and GUI errors on both models.
- A first version of the hints made *query* worse (*requête* to *request*) and produced a
  road-traffic sense for *intersection*. The final rules prefer GUI labels, and use single-word
  glossary hints only from MLGT.
- Those rules were adjusted after seeing errors on this same lesson, so a second, unseen lesson
  is needed to confirm the gain.
- Right counts for *query* are understated: hints produce capitalised *Query*, which the
  pattern misses. Hints can capitalise common words mid-sentence.

Each pass took about 2 minutes on 1.8B and 9 minutes on 7B on the Mac.

## QuickOSM strings against human translations

232 English GUI strings from QuickOSM 2.5.4, translated without assistance and compared
with the plugin's human translations. Similarity is character-level on lower-cased text.

| Language | NLLB 3.3B exact | Hy-MT2 1.8B exact | NLLB similarity | Hy-MT2 similarity |
|---|---:|---:|---:|---:|
| French | 46 | 66 | 0.766 | 0.770 |
| Spanish | 66 | 93 | 0.792 | 0.824 |
| German | 68 | 53 | 0.752 | 0.730 |
| Italian | 63 | 63 | 0.776 | 0.763 |
| Polish | 69 | 58 | 0.725 | 0.721 |
| Romanian | 24 | 26 | 0.731 | 0.726 |
| Icelandic | 39 | 24 | 0.663 | 0.635 |

Similarity to one human translation is not a measure of correctness. Very short strings are
poor tests: *Extent* has no context, and neither engine matched the GIS sense.

## QuickOSM: assisted Hy-MT2 against NLLB

The relevant comparison is the best available result of each: Hy-MT2 1.8B with labels and
glossary hints, against NLLB, which cannot take hints. Cells are exact matches with human
translations and mean similarity. "Whole label" strings match a QGIS label outright.

| Language | All 232: NLLB | All 232: Hy-MT2 assisted | Other strings: NLLB | Other strings: Hy-MT2 assisted | Whole labels: NLLB | Whole labels: Hy-MT2 assisted |
|---|---|---|---|---|---|---|
| French | 46, 0.766 | 73, 0.790 | 30, 0.781 | 36, 0.765 | 16, 0.712 | 37, 0.879 |
| Spanish | 66, 0.792 | 97, 0.847 | 42, 0.800 | 57, 0.820 | 24, 0.761 | 40, 0.951 |
| German | 68, 0.752 | 57, 0.738 | 44, 0.753 | 28, 0.723 | 24, 0.747 | 29, 0.790 |
| Italian | 63, 0.776 | 67, 0.771 | 42, 0.783 | 41, 0.771 | 21, 0.750 | 26, 0.770 |
| Polish | 69, 0.725 | 70, 0.736 | 46, 0.733 | 35, 0.701 | 23, 0.696 | 35, 0.869 |
| Romanian | 24, 0.731 | 30, 0.731 | 13, 0.736 | 11, 0.728 | 11, 0.710 | 19, 0.743 |
| Icelandic | 39, 0.663 | 41, 0.675 | 24, 0.691 | 11, 0.662 | 15, 0.559 | 30, 0.726 |

The whole-label gain may partly reflect plugin translators following QGIS wording. Icelandic
has no glossary terms loaded, so its hints are labels only.

## Index-Translate 9B, five sentences

Run on a GitHub runner (4 CPU cores), Q4_K_M, temperature 0, no hints. Every answer
ended normally. About 36 to 47 seconds per language, roughly 8 seconds per sentence.

- Correct language in all 15 targets, including real Nynorsk (*ein, dei, handsaminga*).
- Better GIS sense than earlier models: *aspect* became *orientation*, *Exposition*,
  *eksponering* or *azimut*; *hillshade* became *ombrage de relief*, *sombreado de relieve*.
- *Run* was translated as the button (*Exécuter, Kjør, Spustiť*) except in Romanian.
- Errors remain: *SRS* for CRS in French; *απόθεμα* (stock) for buffer in Greek; *buffur* in
  Icelandic; *features* as properties or attributes in several languages; some misspelt
  compounds (*vektellag*, *vektlager*).

## GUI lookup

Of 39 French labels taken from the lesson, 28 resolved exactly in `qgis_fr.ts`.
Some labels map to several English strings: *Exécuter* to Run and Execute, *Ombrage*
to Shading and Hillshade. These need context to choose.
