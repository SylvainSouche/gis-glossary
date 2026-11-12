#!/usr/bin/env python3
"""
extract_geonorge.py - publish Norwegian-English term pairs from Geonorge.

    python3 tools/extract_geonorge.py codelists
    python3 tools/extract_geonorge.py resources

codelists: the metadata code lists of register.geonorge.no, read once in Norwegian and
once in English (Accept-Language) and paired by item id. Only names and code values are
kept; descriptions are not republished. Writes published/geonorge-metadata-codelists/.

resources: the .resx interface strings of the Geonorge web applications on
github.com/kartverket (MIT), Norwegian file paired with its .en.resx by key, at a pinned
commit per repository. Writes published/geonorge-resources/.
"""

import csv
import json
import lzma
import re
import sys
import time
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
USER_AGENT = "gis-glossary/0.1 (terminology research)"
TODAY = time.strftime("%Y-%m-%d")
REGISTER = "https://register.geonorge.no/api/metadata-kodelister.json"
REPOSITORIES = [
    "Geonorge.Kartkatalog", "Geonorge.Register", "Geonorge.NedlastingAPI", "Geonorge.Symbol",
    "Geonorge.Kartografi", "Geonorge.Produktark", "Geonorge.Forvaltningsinformasjon",
    "Geonorge.Rapportgenerator", "Geonorge.MinSide",
]
MAX_LENGTH = 120


def fetch(url, headers=None, raw=False):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, **(headers or {})})
    for attempt in range(3):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                data = response.read()
                return data if raw else json.loads(data)
        except Exception as error:
            last = error
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def write_csv(path, header, rows, compress=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    opener = (lambda p: lzma.open(p, "wt", encoding="utf8", newline="")) if compress else \
        (lambda p: open(p, "w", encoding="utf8", newline=""))
    with opener(path) as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(header)
        writer.writerows(rows)


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()


# Metadata code lists.

def api_url(register_id):
    return register_id.replace("https://register.geonorge.no/", "https://register.geonorge.no/api/") + ".json"


def codelists():
    out_dir = ROOT / "published" / "geonorge-metadata-codelists"
    top = fetch(REGISTER, {"Accept": "application/json"})
    rows = []
    for sub in top.get("containedSubRegisters", []):
        url = api_url(sub["id"])
        versions = {lang: fetch(url, {"Accept": "application/json", "Accept-Language": lang})
                    for lang in ("nb", "en")}
        nb, en = versions["nb"], versions["en"]
        list_nb, list_en = clean(nb.get("label")), clean(en.get("label"))
        rows.append([sub["id"], "", list_nb, list_en, "code list"])
        english = {item.get("uuid") or item["id"]: item for item in en.get("containeditems", [])}
        for item in nb.get("containeditems", []):
            other = english.get(item.get("uuid") or item["id"])
            if not other:
                continue
            rows.append([item["id"], clean(item.get("codevalue")), clean(item.get("label")),
                         clean(other.get("label")), list_en or list_nb])
        print(f"{list_nb}: {len(nb.get('containeditems', []))} values", flush=True)
    write_csv(out_dir / "geonorge_codelists.csv",
              ["id", "code", "nb", "en", "code_list"], rows)
    translated = sum(1 for r in rows if r[2] and r[3] and r[2] != r[3])
    (out_dir / "ATTRIBUTION.md").write_text(f"""# Geonorge metadata code lists

- **Credit:** Kartverket / Geonorge, metadata code lists
- **Address:** <https://register.geonorge.no/metadata-kodelister>
- **Licence:** none stated on the register; only names and code values are kept, as term
  equivalents. Descriptions are not republished.
- **Retrieved:** {TODAY}
- **Changes:** each list read in Norwegian and in English (Accept-Language) through the JSON
  API and paired by item id, by `tools/extract_geonorge.py codelists`.
""", encoding="utf8")
    print(f"{len(rows)} rows, {translated} with a distinct English name")


# Application resource files.

def resx(text):
    root = ET.fromstring(text)
    return {d.get("name"): clean(d.findtext("value")) for d in root.iter("data")
            if d.get("type") is None and d.get("mimetype") is None}


def usable(value):
    return value and len(value) <= MAX_LENGTH and not re.search(r"<[^>]+>|\{\d+\}|https?://", value)


def resources():
    out_dir = ROOT / "published" / "geonorge-resources"
    rows, commits = [], {}
    for repository in REPOSITORIES:
        info = fetch(f"https://api.github.com/repos/kartverket/{repository}")
        commit = fetch(f"https://api.github.com/repos/kartverket/{repository}/commits/{info['default_branch']}")["sha"]
        commits[repository] = (commit, (info.get("license") or {}).get("spdx_id"))
        tree = fetch(f"https://api.github.com/repos/kartverket/{repository}/git/trees/{commit}?recursive=1")
        paths = {t["path"] for t in tree["tree"] if t["type"] == "blob" and t["path"].endswith(".resx")}
        raw = f"https://raw.githubusercontent.com/kartverket/{repository}/{commit}/"
        pairs = 0
        for english_path in sorted(p for p in paths if p.endswith(".en.resx")):
            stem = english_path[:-len(".en.resx")]
            norwegian_path = next((p for p in (stem + ".nb.resx", stem + ".no.resx", stem + ".resx") if p in paths), None)
            if not norwegian_path:
                continue
            english = resx(fetch(raw + english_path, raw=True))
            norwegian = resx(fetch(raw + norwegian_path, raw=True))
            for key, nb in norwegian.items():
                en = english.get(key)
                if usable(nb) and usable(en) and nb != en:
                    rows.append([repository, stem, key, en, nb])
                    pairs += 1
        licence = fetch(raw + "LICENSE", raw=True) if commits[repository][1] else b""
        if licence:
            (out_dir / "licences").mkdir(parents=True, exist_ok=True)
            (out_dir / "licences" / f"{repository}.txt").write_bytes(licence)
        print(f"{repository}: {pairs} pairs, licence {commits[repository][1]}", flush=True)
    write_csv(out_dir / "geonorge_resources.csv.xz", ["repository", "file", "key", "en", "nb"], rows,
              compress=True)
    (out_dir / "commits.txt").write_text(
        "".join(f"{r}\t{c}\t{l}\n" for r, (c, l) in commits.items()), encoding="utf8")
    (out_dir / "ATTRIBUTION.md").write_text(f"""# Geonorge application interface strings

- **Credit:** Kartverket, Geonorge web applications on <https://github.com/kartverket>
- **Licence:** per repository, listed in `commits.txt`; MIT licence texts in `licences/`
- **Commits:** pinned per repository in `commits.txt`
- **Retrieved:** {TODAY}
- **Changes:** Norwegian `.resx` strings paired by key with their `.en.resx` counterparts;
  strings over {MAX_LENGTH} characters, with markup, placeholders or links are dropped. Made by
  `tools/extract_geonorge.py resources`.
""", encoding="utf8")
    print(f"{len(rows)} pairs")


if __name__ == "__main__":
    {"codelists": codelists, "resources": resources}[sys.argv[1]]()
