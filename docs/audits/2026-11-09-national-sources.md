# Source audit: national terminology, first pass

Audited 2026-11-09. The national rows in the inventory mostly point to home
pages, so this pass searched for actual terminology by language.

| Target | Best source found | Size | Licence or status |
|---|---|---|---|
| Nynorsk | SNORRE | 48,875 terms; about 99 GIS-related rows | CC BY, credit Standard Norge |
| Bokmål | SNORRE | 49,678 terms | CC BY |
| Icelandic | LÍSA glossary | 7,372 concepts, Icelandic-English | Reuse terms not confirmed |
| Slovak | ÚGKK dictionary | Size not established | Reuse terms not confirmed |
| Swedish | HMK Ordlista | About 600 rows | No reuse statement; restricted |
| Slovenian | ZRC SAZU geoinformatics dictionary | Project; publication not found | Unknown |
| EU languages | IATE | Needs EU Login to count | Redistribution allowed with acknowledgement |

## Findings

- **SNORRE supplies real Nynorsk, but mostly not GIS.** 20,114 Nynorsk entries
  differ from Bokmål. Keyword matching is rough, so the GIS count is indicative.
- **LÍSA is the first GIS-specific source for Icelandic.**
- **Slovak has a maintained GIS and geodesy dictionary** with definitions.
- **IATE is the one large EU source with explicit redistribution terms.** Its
  export needs a personal EU Login account.

- **SNORRE conditions differ by document.** The catalogue says CC BY. The 2013
  readme names Standard Norge as copyright holder and mentions distribution until
  2014-12-15. Confirm with Språkbanken before public release.

## Greek and Bulgarian

Targeted searches found no official or large GIS glossary in either language.

| Language | Term sources so far | GIS-specific additions |
|---|---|---|
| Greek | GEMET 5,349; INSPIRE 678; EuroVoc 7,515 | A 2017 paper on INSPIRE metadata terms, not inspected |
| Bulgarian | GEMET 5,353; INSPIRE 678; EuroVoc 7,478; QGIS 13,811 strings | QGIS.bg list, 42 rows |

Greek usage varies: ΓΣΠ, ΣΓΠ and Γεωγραφικά Πληροφοριακά Συστήματα all appear for
GIS. Greek therefore needs preferred terms chosen by review. A Bulgarian agency
document titled as a glossary holds only acronyms.

## Polish, Danish and Romanian

- **Polish:** PTIP's Internet Geomatics Lexicon is a dedicated resource with
  English search, and its entries are stated to be under CC BY 3.0. Its size is
  not yet counted.
- **Danish:** no official glossary found. Sources so far are GEMET, INSPIRE,
  EuroVoc, QGIS, MLGT (216 terms) and community pages.
- **Romanian:** no official glossary found. Sources so far are GEMET, INSPIRE,
  EuroVoc and QGIS.

## Not done

Standards bodies in the inventory
were not audited individually.
