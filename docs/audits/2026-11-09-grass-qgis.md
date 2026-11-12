# Source audit: GRASS and QGIS

Audited 2026-11-09 from the GRASS TBX files, the QGIS `.ts` catalogues and the
built QGIS manual.

## Coverage

| Language | GRASS terms (81) | QGIS UI finished strings | QGIS manual index headings translated (86) |
|---|---:|---:|---:|
| French | 65 | 31,287 | 79 |
| Spanish | 4 | 25,100 | 83 |
| German | 0 | 36,579 | 80 |
| Italian | 0 | 34,459 | 83 |
| Norwegian Bokmål | no file | 34,656 | 0 |
| Norwegian Nynorsk | no file | no catalogue | 0 |
| Icelandic | no file | 23,890 | 0 |
| Danish | no file | 27,141 | 0 |
| Polish | 0 | 29,072 | 34 |
| Slovenian | 0 | no catalogue | 0 |
| Greek | 0 | no catalogue | 0 |
| Romanian | 0 | 35,014 | 60 |
| Bulgarian | no file | 13,811 | 0 |
| Slovak | no file | 27,945 | 0 |
| Swedish | 53 | 36,459 | 83 |

QGIS UI coverage in the registry is relative to the largest catalogue (German,
36,580 strings), because `qgis_en.ts` is smaller than several translations. The
manual column is a proxy from one index page.

## Findings

- **The GRASS glossary is much smaller than the inventory suggests.** It has 81
  entries, and only French and Swedish have many translations.
- **QGIS UI is the widest GIS source.** It fills Italian, Bokmål, Icelandic and
  others that ISO MLGT lacks, but it gives strings, not concepts or definitions.
- **Translations of one word vary.** *Aspect* in QGIS: de and fr Exposition, it
  Esposizione, pl Ekspozycja, sv Lutningsriktning, da Hældningsretning, ro
  Orientare, but es Aspecto, nb and sk Aspekt, and Icelandic has both Ásýnd and
  Hallastefna. The English-looking forms need review; frequency alone will not
  pick the right sense.
- **QGIS documentation is GFDL 1.3 or later.** This resolves the conflict with
  the inventory's CC BY-SA 3.0.

## Still without a good GIS source

Nynorsk has none. Greek and Slovenian have no QGIS catalogue, leaving GEMET and
INSPIRE only. Bulgarian has GEMET, INSPIRE and a partial QGIS catalogue.

## Not checked

Translation quality, QGIS translation contribution terms, GRASS file-level
notices (Weblate was blocked by a bot challenge), and whether the 35 GRASS
entries with notes hold definitions.
