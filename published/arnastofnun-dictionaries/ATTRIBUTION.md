# Árni Magnússon Institute bilingual dictionaries

| Dictionary | Languages | Handle | Released |
|---|---|---|---|
| ISLEX – Icelandic-Scandinavian multilingual dictionary (2026-02) | is → da, nb, nn, sv, fo, fi | <http://hdl.handle.net/20.500.12537/376> | 2026-02-11 |
| Icelandic-French dictionary (Lexía) | is → fr | <http://hdl.handle.net/20.500.12537/377> | 2026-02-13 |
| Icelandic-Polish dictionary (Íslensk-pólsk orðabók) | is → pl | <http://hdl.handle.net/20.500.12537/378> | 2026-02-16 |

- **Credit:** The Árni Magnússon Institute for Icelandic Studies (Stofnun Árna Magnússonar í
  íslenskum fræðum). ISLEX is a collaboration with institutes in Denmark, Norway, Sweden, the
  Faroe Islands and Finland; the French dictionary with the Vigdís Finnbogadóttir Institute.
  Authors are listed in each source file.
- **Licence:** CC BY-SA 4.0 <https://creativecommons.org/licenses/by-sa/4.0/>. This derived
  file is distributed under the same licence. Earlier ISLEX releases (2013, 2023) are
  CC BY-NC-ND 4.0 and are not used.
- **Retrieved:** 2026-11-12, from the CLARIN-IS repository, on GitHub Actions.
- **Changes:** the XML is flattened to one row per translation by
  `tools/extract_arnastofnun.py`: dictionary, entry id, sense path, unit type (Sense,
  SemanticCollocation, VerbPhrase, SemanticIdiomaticity, SenseExample), part of speech, Icelandic
  lemma, Icelandic text of the unit, target language, target text, and whether the target came
  from an `Equivalent` element or a `<text>` element. Grammar, compounds and cross-references are
  dropped. Row counts are in `counts.txt`.
