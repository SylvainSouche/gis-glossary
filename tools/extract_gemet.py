#!/usr/bin/env python3
"""
extract_gemet.py - publish GEMET labels for the target languages.

    python3 tools/extract_gemet.py PATH/TO/gemet.rdf.gz

GEMET, the GEneral Multilingual Environmental Thesaurus of the European Environment Agency,
is CC BY 4.0. Download gemet.rdf.gz from https://www.eionet.europa.eu/gemet/en/exports/rdf/latest
(7.4 MB). Keeps preferred and alternative labels of concepts, themes, groups and supergroups;
definitions are not kept. GEMET's `no` labels are Bokmål (checked in the audit) and are written
as nb. Writes published/gemet/gemet_labels.csv.xz and ATTRIBUTION.md.
"""
import csv
import gzip
import lzma
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "published" / "gemet"
LANGUAGES = {"en", "fr", "es", "de", "it", "no", "is", "da", "pl", "sl", "el", "ro", "bg", "sk", "sv"}
RDF = "{http://www.w3.org/1999/02/22-rdf-syntax-ns#}"
SKOS = "{http://www.w3.org/2004/02/skos/core#}"
XML = "{http://www.w3.org/XML/1998/namespace}"
KINDS = re.compile(r"^(concept|theme|group|supergroup)/(\d+)$")


def main():
    rows, version = [], ""
    with gzip.open(sys.argv[1]) as stream:
        for _, element in ET.iterparse(stream):
            if element.tag == "{http://www.w3.org/2000/01/rdf-schema#}label" and "GEMET" in (element.text or ""):
                version = version or element.text.strip()
            about = element.get(RDF + "about") or ""
            match = KINDS.match(about)
            if match:
                for label in element:
                    if label.tag not in (SKOS + "prefLabel", SKOS + "altLabel"):
                        continue
                    language = label.get(XML + "lang")
                    text = re.sub(r"\s+", " ", label.text or "").strip()
                    if language in LANGUAGES and text:
                        rows.append((about, match.group(1), "nb" if language == "no" else language, text,
                                     "preferred" if label.tag.endswith("prefLabel") else "admitted"))
                element.clear()
    rows = sorted(set(rows), key=lambda r: (r[1], int(r[0].split("/")[1]), r[2], r[4] != "preferred", r[3]))
    OUT.mkdir(parents=True, exist_ok=True)
    with lzma.open(OUT / "gemet_labels.csv.xz", "wt", encoding="utf8", newline="") as f:
        writer = csv.writer(f, lineterminator="\n")
        writer.writerow(["id", "kind", "language", "label", "status"])
        writer.writerows(rows)
    (OUT / "ATTRIBUTION.md").write_text(f"""# GEMET labels

- **Credit:** GEMET, GEneral Multilingual Environmental Thesaurus, European Environment Agency (EEA)
  and Eionet
- **Address:** <https://www.eionet.europa.eu/gemet/>
- **Licence:** CC BY 4.0, <https://creativecommons.org/licenses/by/4.0/> (stated in the export)
- **Version:** {version}
- **Retrieved:** 2026-11-13
- **Changes:** preferred and alternative labels of concepts, themes, groups and supergroups in
  the target languages, extracted from `gemet.rdf.gz` by `tools/extract_gemet.py`. Definitions are
  not kept. GEMET's `no` labels are Bokmål and are written as `nb`. Ids are GEMET's own
  (`concept/1234`), relative to <http://www.eionet.europa.eu/gemet/>.
""", encoding="utf8")
    print(f"{len(rows)} labels; {version}")


if __name__ == "__main__":
    main()
