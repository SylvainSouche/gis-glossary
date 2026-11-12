# Source audit: EuroVoc, CEOS, GIS software and Wikimedia

Audited 2026-11-09 from the sources' data.

| Source | Size | Languages | Licence | Use |
|---|---|---|---|---|
| EuroVoc | 7,515 concepts | All targets except nb, nn, is | Not verified | Few GIS terms: 22 found by keyword |
| CEOS EO Glossary | 509 terms | English | CC BY 4.0 | Earth observation definitions |
| GDAL glossary | 73 entries | English | Documentation not confirmed | Small |
| PROJ glossary | 2 entries | English | MIT | Not useful |
| PostGIS manual | Not counted | Translations in da, de, es, fr, it, pl, ro, sv | CC BY-SA 3.0 | Corpus candidate |
| Wikipedia | Sample of 19 articles | Varies | CC BY-SA 4.0; links in Wikidata are CC0 | Candidates only |
| Wiktionary | Sample of 8 entries | Varies | CC BY-SA 4.0 | Candidates by sense |

## Wikipedia sample: articles linked per language, of 19

fr, es, de 18; pl 17; it 16; nb, ro, sv 14; bg 13; da 12; el 11; sl, sk 10;
nn, is 7.

## Findings

- **Wikipedia and Wiktionary are the first GIS-related sources with labelled
  Nynorsk.** `nn.wikipedia` is written in Nynorsk, and Wiktionary tables name
  it separately, though coverage in the sample is thin.
- **The link risk is real.** *Slope* links to the mathematical sense in many
  languages, *Contour line* to the wider isoline, and *Aspect (geography)* exists
  only in French, German and Bulgarian.
- **Wiktionary groups translations by sense,** but the GIS sense may be missing:
  *aspect* in its compass-position sense has only Polish and Slovak.
- **EuroVoc adds few GIS terms,** but those it has are official in 13 targets.

## Not checked

EuroVoc and EU Vocabularies licence pages, GDAL documentation licence, PostGIS
translation completion, and any Wikipedia or Wiktionary result beyond the samples.
