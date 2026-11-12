# Source audit: OGC definitions and ISO/TC 211 codesets

Audited 2026-11-09 from the OGC glossary in Turtle and the `ISO-TC211/codesets`
repository.

| Source | Concepts | Languages | Definitions | Licence |
|---|---:|---|---|---|
| OGC glossary | About 455 | English | Yes | OGC Document License; formal licences still being added to the service |
| ISO/TC 211 codesets | About 1,230 | English | Yes | CC BY 4.0, copyright ISO |

## Findings

- **Neither adds languages.** Their value is identifiers, English definitions
  and structure. The German and French labels in the codesets repository are
  only names of languages.
- **The codesets are openly licensed ISO content.** Unlike ISO MLGT, they can be
  versioned here with attribution. The README's CC BY 4.0 statement refers to a
  LICENSE file that the repository does not contain.
- **The OGC terms differ by document.** The Document License Agreement allows
  modification with a notice. The Definitions Service says reuse is "with
  attribution and without modification", and that licences will be added later.
  Keep OGC definitions verbatim until that is settled.

## Not checked

Other vocabularies hosted on the Definitions Service, and whether any of them
are multilingual.
