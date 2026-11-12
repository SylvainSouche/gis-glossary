# Registry

What the project knows about its sources. No source data is stored here.

| File | Content |
|---|---|
| `sources.csv` | One row per source, with audit results |
| `languages.csv` | Target languages, tiers and codes |
| `restricted-manifest.tsv` | Address and checksum of each restricted document |
| `reference-only.md` | Pointers to sources that may not be used |
| `original-inventory.csv` | The inventory as first received; never edited |

Run `python3 tools/check_registry.py` after any edit.

## Columns in `sources.csv`

| Column | Values or meaning |
|---|---|
| `id` | Stable identifier, used across the repository |
| `category`, `name`, `description`, `url`, `comment` | Identification |
| `licence_claimed` | As stated by the inventory; unverified |
| `duplicate_of` | The `id` this row repeats |
| `priority` | Audit order; lower comes first |
| `role` | `terminology`, `corpus`, `training`, `method` |
| `distribution` | `open`, `restricted`, `reference`, blank if unclassified |
| `audit_status` | `todo`, `in_progress`, `done`, `duplicate`, `rejected` |
| `audited_on` | Date of the audit |
| `licence_verified` | What the source's own terms say |
| `redistribution` | What this project may do with it |
| `domain_coverage`, `concept_count`, `formats`, `bulk_access`, `last_update` | Audit facts |
| `has_definitions`, `human_validated` | Quality facts |
| `lang_<code>` | `yes` (at least 90% of entries), `partial`, `no`, blank if unknown |
| `notes` | Findings and caveats |

`rejected` means the source was examined and adds nothing useful; `notes` says why.

## Manifest columns

`id`, `method` (`file` or `git`), `url`, `target` (name under
`sources/restricted/`), `sha256` (`-` for git sources). One `id` may have several
lines.
