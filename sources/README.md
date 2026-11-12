# Sources

The source files themselves. Each source's class is recorded in the
`distribution` column of [`registry/sources.csv`](../registry/sources.csv).

| Folder | Content | In git |
|---|---|---|
| `open/<source>/` | Files we may redistribute, each folder with `ATTRIBUTION.md` | Yes |
| `restricted/` | Files we may use but not distribute | No |

Sources that may not be used are not stored; see
[`registry/reference-only.md`](../registry/reference-only.md).

## Restricted files

Collect them from their original sources:

```bash
tools/fetch_restricted.sh
```

If a source publishes a new version, the script reports a checksum mismatch.
Review the new file before updating the checksum in
[`registry/restricted-manifest.tsv`](../registry/restricted-manifest.tsv).

Definitions and running text from these files must stay out of versioned files
unless permission is obtained.
