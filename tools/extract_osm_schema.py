#!/usr/bin/env python3
"""
extract_osm_schema.py - publish OpenStreetMap tagging-schema names for the target languages.

    python3 tools/extract_osm_schema.py [COMMIT]

Reads dist/translations/<lang>.min.json of github.com/openstreetmap/id-tagging-schema (ISC) at a
pinned commit, about 5 MB for the 16 languages. Keeps, keyed by OSM tag:
- preset names (kind preset) and their search terms (kind search, loose associations such as
  glacier: ice, snow): key "natural=glacier" (preset id natural/glacier);
  deeper preset ids keep their path ("amenity=place_of_worship/christian");
- field labels: key "field:surface";
- field option labels: key "surface=asphalt" (the field id stands for the OSM key, which is
  the case for most fields).
Bokmål comes from both `no` (most of it) and `nb`. Crowd translations: terms are marked
admitted, except the English source names. Writes published/osm-tagging-schema/.
"""
import csv
import json
import lzma
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "published" / "osm-tagging-schema"
REPO = "openstreetmap/id-tagging-schema"
FILES = {"en": ["en"], "fr": ["fr"], "es": ["es"], "de": ["de"], "it": ["it"], "nb": ["no", "nb"], "nn": ["nn"],
         "is": ["is"], "da": ["da"], "pl": ["pl"], "sl": ["sl"], "el": ["el"], "ro": ["ro"], "bg": ["bg"],
         "sk": ["sk"], "sv": ["sv"]}
HEADERS = {"User-Agent": "gis-glossary/0.1 (terminology research)"}


def fetch(url):
    return urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=120).read()


def preset_key(preset_id):
    head, _, rest = preset_id.partition("/")
    return f"{head}={rest}" if rest else head


def rows_for(language, data):
    presets = data.get("presets", {})
    status = "preferred" if language == "en" else "admitted"
    for preset_id, preset in presets.get("presets", {}).items():
        if not isinstance(preset, dict) or not preset.get("name"):
            continue
        key = preset_key(preset_id)
        yield key, "preset", language, preset["name"].strip(), status
        terms = preset.get("terms") or ""
        for term in (terms.split(",") if isinstance(terms, str) else terms):
            if isinstance(term, str) and term.strip():
                yield key, "search", language, term.strip(), "admitted"
    for field_id, field in presets.get("fields", {}).items():
        if not isinstance(field, dict):
            continue
        if field.get("label"):
            yield f"field:{field_id}", "field", language, field["label"].strip(), status
        for value, option in (field.get("options") or {}).items():
            title = option.get("title") if isinstance(option, dict) else option
            if isinstance(title, str) and title.strip():
                yield f"{field_id}={value}", "value", language, title.strip(), status


def main():
    commit = sys.argv[1] if len(sys.argv) > 1 else json.loads(
        fetch(f"https://api.github.com/repos/{REPO}/commits/main"))["sha"]
    raw = f"https://raw.githubusercontent.com/{REPO}/{commit}/"
    rows = set()
    for language, codes in FILES.items():
        for code in codes:
            document = json.loads(fetch(f"{raw}dist/translations/{code}.min.json"))
            rows |= set(rows_for(language, document.get(code) or next(iter(document.values()))))
        print(language, sum(1 for r in rows if r[2] == language), file=sys.stderr)
    OUT.mkdir(parents=True, exist_ok=True)
    with lzma.open(OUT / "osm_terms.csv.xz", "wt", encoding="utf8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["key", "kind", "language", "text", "status"])
        writer.writerows(sorted(rows))
    (OUT / "LICENSE-ISC.md").write_bytes(fetch(f"{raw}LICENSE.md"))
    (OUT / "commit.txt").write_text(commit + "\n", encoding="utf8")
    (OUT / "ATTRIBUTION.md").write_text(f"""# OpenStreetMap tagging schema names

- **Credit:** id-tagging-schema contributors and translators, OpenStreetMap
- **Address:** <https://github.com/{REPO}>
- **Licence:** ISC; the licence text is in `LICENSE-ISC.md`
- **Commit:** `{commit}` (also in `commit.txt`)
- **Retrieved:** 2026-11-13
- **Changes:** preset names and search terms, field labels and field option labels for the
  target languages, keyed by OSM tag (`natural=glacier`, `field:surface`, `surface=asphalt`),
  extracted from `dist/translations/*.min.json` by `tools/extract_osm_schema.py`. Bokmål merges
  the `no` and `nb` files. Translations are crowdsourced and marked admitted.
""", encoding="utf8")
    print(f"{len(rows)} rows at {commit}", file=sys.stderr)


if __name__ == "__main__":
    main()
